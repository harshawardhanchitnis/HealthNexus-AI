"""Explicit deterministic local templates; never represented as Gemini reasoning."""
import re
from app.ai.schemas import DraftAnswer, Claim, Reference


def clinical_request(message):
    return bool(re.search(r'\b(diagnos\w*|prescrib\w*|dosage|patient records?|medical records?)\b|'
        r'\b(what|which) medicine should (i|my|this patient)|\b(i|my|personally)\b.{0,50}\b(take|symptoms|treat|dengue|pain|fever)\b',message,re.I))


def offline_calls(request):
    args = {'country_id':request.country_id,'profile':request.profile,
            'state_id':request.state_id,'district_id':request.district_id}
    message = request.message.lower()
    if request.compare_profiles:
        return [('get_network_summary',{**args,'profile':p}) for p in ('constrained','redistribution-ready')]
    if any(x in message for x in ('live','government','provenance','data source')):
        calls=[('get_data_provenance',args)]
        if any(x in message for x in ('accuracy','reliability','performance')):calls.append(('get_model_performance',args))
        return calls
    if any(x in message for x in ('reliable','accuracy','accurate','performance')):
        return [('get_model_performance',args)]
    if request.optimization_run_id and any(x in message for x in ('donor','plan','redistribut')):
        return [('get_optimization_result',{**args,'run_id':request.optimization_run_id})]
    if request.allow_planning and any(x in message for x in ('simulate','run','what happens','redistribut','optimiz','plan')):
        calls = [('get_network_summary',args)]
        if 'dengue' in message and not request.scenario_id:
            days=re.search(r'(\d+)\s*[- ]?day',message)
            duration=int(days.group(1)) if days else 14
            severity='critical' if 'critical' in message else 'moderate' if 'moderate' in message else 'severe'
            calls += [('run_emergency_scenario',{**args,'scenario_type':'DENGUE_SURGE','severity':severity,'duration':duration,'seed':42})]
        calls += [('get_warnings',args),('get_redistribution_preview',{**args,'scope':'district' if request.district_id else 'state' if request.state_id else 'national'})]
        if any(x in message for x in ('redistribut','optimiz','plan')):
            calls += [('optimize_redistribution',{**args,'scope':'district' if request.district_id else 'state' if request.state_id else 'national'})]
        return calls
    return [('get_network_summary',args),('get_warnings',args)]


def offline_draft(records):
    eid, record = list(records.items())[-1]
    payload = record['payload']
    def claim(text, field):
        return Claim(text=text,references=[Reference(evidence_id=eid,field=field)])
    if 'solver' in payload:
        status = payload['solver']['status']
        text = 'OR-Tools proved an optimal recommendation under its configured constraints.' if status=='OPTIMAL' else f'OR-Tools returned {status}; optimality is not claimed.'
        if payload['safe_capacity']==0:
            text += ' No safe donor capacity is available; no transfers are proposed and the shortage remains unresolved.'
        return DraftAnswer(situation=claim(text,'solver.status'),
            recommended_actions=[claim('Review the proposed resource-specific transfers and protected donor reserves before any external operational decision.','impact.transferred_units')],
            remaining_gaps=[claim('The remaining target deficit is shown in the verified accounting tally; different medicine units are not interchangeable.','impact.after.target_deficit')])
    if 'live_government_inventory' in payload:
        return DraftAnswer(situation=claim('This is calibrated simulated facility operations, not live government inventory.','live_government_inventory'))
    if 'targets' in payload:
        return DraftAnswer(situation=claim('Review the measured forecasting evaluation on simulated histories; real-world or clinical validity is not established.','data_type'))
    field = 'summary.total' if 'summary' in payload and 'total' in payload['summary'] else 'summary.facilities'
    return DraftAnswer(situation=claim('The selected network has structured operational results. Review the verified facts and warning evidence below.',''+field))
