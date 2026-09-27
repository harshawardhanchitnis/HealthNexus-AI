"""Scheduled-receipt projection and reproducible empirical path bootstrap."""
from datetime import timedelta
import hashlib
import numpy as np


def known_receipts(orders, as_of, horizon=14):
    receipts = np.zeros(horizon)
    for order in orders:
        if order.ordered_at <= as_of < order.expected_at:
            day = (order.expected_at-as_of).days
            if day <= horizon:
                receipts[day-1] += order.quantity
    return receipts


def demand_paths(point, scale, residuals, key, simulations=500):
    seed = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "little")
    rng = np.random.default_rng(seed)
    # Whole 14-day residual vectors retain within-path error dependence.
    sampled = residuals[rng.integers(0, len(residuals), size=simulations), :len(point)]
    return np.maximum(0, np.asarray(point)[None, :] + sampled*scale)


def project_stock(current, safety, point, paths, receipts, as_of):
    if current < 0 or safety < 0 or np.any(receipts < 0) or np.any(point < 0):
        raise ValueError("Inventory projection inputs must be nonnegative")
    point = np.asarray(point)
    stock, simulated = float(current), np.full(len(paths), float(current))
    exhausted = np.full(len(paths), current <= 0, dtype=bool)
    safety_date = str(as_of) if current <= safety else None
    stockout_date = str(as_of) if current <= 0 else None
    trajectory, risk = [], {}
    for day, demand in enumerate(point):
        available = stock + receipts[day]
        unmet = max(0.0, demand-available)
        stock = max(0.0, available-demand)
        simulated = np.maximum(0, simulated + receipts[day]-paths[:, day])
        exhausted |= simulated <= 0
        future = str(as_of+timedelta(days=day+1))
        if safety_date is None and stock <= safety:
            safety_date = future
        if stockout_date is None and stock <= 0:
            stockout_date = future
        trajectory.append({"date": future, "expected_receipts": float(receipts[day]),
            "demand": float(demand), "closing_stock": stock, "unmet_demand": unmet,
            "lower95": float(np.quantile(simulated, .025)), "upper95": float(np.quantile(simulated, .975))})
        if day+1 in (3, 7, 14):
            risk[str(day+1)] = float(exhausted.mean())
    mean = float(point.mean())
    return {"current_stock": current, "safety_stock": safety,
        "days_of_cover": current/mean if mean > 0 else None,
        "cover_method": "Current stock / mean 14-day forecast demand; excludes receipts.",
        "safety_breach_date": safety_date, "stockout_date": stockout_date,
        "probabilities": risk, "simulations": len(paths), "trajectory": trajectory,
        "status": "HIGH" if risk.get("7", 0) >= .5 else "WATCH" if safety_date or risk.get("14", 0) >= .2 else "LOW",
        "method": "Estimated model-based stock-out probability: fraction of 500 bootstrapped 14-day residual paths reaching zero. Known scheduled receipts only, assumed on time; no future orders or transfers. Probabilities are not real-world guarantees."}
