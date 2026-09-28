"""Three lexicographic CP-SAT solves sharing one total wall-time budget."""
from collections import defaultdict
from time import perf_counter
import ortools
from ortools.sat.python import cp_model
from app.optimization.config import POLICY as P
from app.optimization.schemas import SolverMetadata, SolverStage


def validate_problem(donors, receivers, edges):
    for e in edges:
        d, r = donors[e.donor], receivers[e.receiver]
        if d.country_id != r.country_id or d.resource_id != r.resource_id or d.facility_id == r.facility_id:
            raise ValueError("Invalid transfer edge")
        if d.safe_surplus < 0 or r.deficit < 0 or d.safe_surplus > d.current_stock:
            raise ValueError("Invalid donor capacity or receiver deficit")


def objective(donors, receivers, edges, quantities):
    incoming = defaultdict(int)
    for e, q in zip(edges, quantities):
        incoming[e.receiver] += q
    residual = [r.deficit-incoming[i] for i, r in enumerate(receivers)]
    return [sum(u*P.critical_shortage_weight for r, u in zip(receivers, residual) if r.critical),
            sum(r.shortage_weight*u for r, u in zip(receivers, residual)),
            sum(q*e.unit_cost + P.transfer_count_penalty*(q > 0) for e, q in zip(edges, quantities))]


def solve(donors, receivers, edges, seconds=P.time_limit_seconds, require_full=False):
    validate_problem(donors, receivers, edges)
    start = perf_counter()
    model = cp_model.CpModel()
    x, used = [], []
    outgoing, incoming = defaultdict(list), defaultdict(list)
    for i, e in enumerate(edges):
        cap = min(donors[e.donor].safe_surplus, receivers[e.receiver].deficit)
        x.append(model.new_int_var(0, cap, f"x_{i}"))
        used.append(model.new_bool_var(f"used_{i}"))
        model.add(x[-1] <= cap*used[-1])
        model.add(x[-1] >= used[-1])
        outgoing[e.donor].append(x[-1])
        incoming[e.receiver].append(x[-1])
    for di, d in enumerate(donors):
        model.add(sum(outgoing[di]) <= d.safe_surplus)
    unmet = []
    for ri, r in enumerate(receivers):
        u = model.new_int_var(0, r.deficit, f"unresolved_{ri}")
        model.add(sum(incoming[ri])+u == r.deficit)
        if require_full:  # Internal diagnostic test only; public planning always permits partial service.
            model.add(u == 0)
        unmet.append(u)
    objectives = [sum(u*P.critical_shortage_weight for r, u in zip(receivers, unmet) if r.critical),
        sum(r.shortage_weight*u for r, u in zip(receivers, unmet)),
        sum(q*e.unit_cost + P.transfer_count_penalty*y for e, q, y in zip(edges, x, used))]
    construction_seconds = 0.
    stages, incumbent, all_proved = [], None, True
    final_status, termination = "UNKNOWN", "time_limit_no_incumbent"
    for name, expr in zip(("critical_unresolved_units", "weighted_unresolved_units", "transport_cost"), objectives):
        elapsed = perf_counter()-start
        if not stages:
            construction_seconds = elapsed
        remaining = seconds-elapsed
        if remaining <= 0:
            all_proved = False
            break
        model.minimize(expr)
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = remaining
        solver.parameters.num_search_workers = P.workers
        solver.parameters.random_seed = P.seed
        status = solver.solve(model)
        has_plan = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
        label = solver.status_name(status)
        stages.append(SolverStage(name=name, status=label,
            objective=solver.objective_value if has_plan else None,
            best_bound=solver.best_objective_bound if has_plan else None, seconds=solver.wall_time))
        if has_plan:
            incumbent = [solver.value(v) for v in x]
            final_status = "FEASIBLE"
        elif incumbent is None:
            final_status = label
        if status != cp_model.OPTIMAL:
            all_proved = False
            termination = "time_limit" if status in (cp_model.UNKNOWN, cp_model.FEASIBLE) else label.lower()
            break
        model.add(expr == round(solver.objective_value))
        model.clear_hints()
        for v in x + used + unmet:
            model.add_hint(v, solver.value(v))
    if all_proved and len(stages) == 3:
        final_status, termination = "OPTIMAL", "all_lexicographic_stages_proved"
    elif incumbent is not None:
        final_status, termination = "FEASIBLE", "time_limit_with_incumbent"
    quantities = incumbent if incumbent is not None else [0]*len(edges)
    return quantities, SolverMetadata(engine="Google OR-Tools CP-SAT", version=ortools.__version__, status=final_status,
        termination=termination, stages=stages, construction_seconds=construction_seconds, objective=objective(donors, receivers, edges, quantities) if incumbent is not None else None,
        time_limit_seconds=seconds, elapsed_seconds=perf_counter()-start,
        variables=len(model.proto.variables), constraints=len(model.proto.constraints))


def greedy(donors, receivers, edges):
    """Priority receivers, nearest safe donor first; identical feasible edges/caps."""
    validate_problem(donors, receivers, edges)
    supply = [d.safe_surplus for d in donors]
    need = [r.deficit for r in receivers]
    quantities = [0]*len(edges)
    order = sorted(range(len(receivers)), key=lambda i: (-receivers[i].critical, -receivers[i].shortage_weight, receivers[i].facility_id, receivers[i].resource_id))
    for ri in order:
        for ei in sorted((i for i, e in enumerate(edges) if e.receiver == ri), key=lambda i: (edges[i].distance_km, donors[edges[i].donor].facility_id)):
            di = edges[ei].donor
            qty = min(supply[di], need[ri])
            quantities[ei] = qty
            supply[di] -= qty
            need[ri] -= qty
    return quantities
