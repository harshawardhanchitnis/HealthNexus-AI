"""Diagnostic tests using the actual SDK HTTP mock and local read-only engines."""
import json
import pytest
from verify_final_gemini_matrix import run, MODELS, Allowance, classify


@pytest.mark.parametrize('outcomes,expected',[
    ({},5),
    ({(m,a):503 for m in MODELS for a in (1,2)},10),
    ({(MODELS[0],1):503},6),
    ({(MODELS[0],1):'unknown'},6),
    ({(MODELS[0],1):'schema'},6),
    ({(MODELS[0],1):401},5),
    ({(MODELS[0],1):400},5),
    ({(MODELS[0],1):429},1),
])
def test_sdk_wire_count_and_independent_acceptance(tmp_path,outcomes,expected):
    report=run(output=tmp_path/'mock.json',mock_outcomes=outcomes)
    assert report['mock_sends']==expected and report['new_provider_sends']==0
    assert all(row['wire_sends']==1 for row in report['attempts'])
    assert all(row['schema']=='PASS' and row['grounding']=='PASS' and row['unknown_ids']==0
               for row in report['attempts'] if row['accepted'])
    assert report['contract'].startswith('Frozen resilience-summary') and not report['semantic_slots']
    if 'unknown' in outcomes.values():
        first=report['attempts'][0]
        assert first['classification']=='AVAILABLE_APPLICATION_REJECTED' and first['unknown_ids']==1
    if 503 in outcomes.values():assert report['attempts'][0]['classification']=='503_HIGH_DEMAND'


def test_ledger_preserves_history_and_appends_only_new_sends(tmp_path):
    ledger=tmp_path/'ledger.json';journal=tmp_path/'journal.json'
    original={'day':'2026-09-28','used':42,'per_model':{'historical':42},'extra':'retain'}
    ledger.write_text(json.dumps(original))
    budget=Allowance(ledger,journal,pace=0)
    for model in MODELS:
        for attempt in (1,2):budget.reserve(model,attempt)
    budget.finish();saved=json.loads(ledger.read_text())
    assert saved['day']==original['day'] and saved['extra']=='retain' and saved['used']==52
    assert saved['per_model']['historical']==42 and len(saved['verification_sends'])==10
    with pytest.raises(ValueError):budget.reserve(MODELS[0],1)
    with pytest.raises(ValueError):Allowance(ledger,journal)


def test_retry_after_pacing_and_classification():
    from time import monotonic
    budget=Allowance(pace=0);budget.retry_after('30s')
    assert budget.not_before>monotonic()+29
    assert classify(dict(accepted=False,http_status=200))=='AVAILABLE_APPLICATION_REJECTED'
    assert classify(dict(accepted=False,http_status=429))=='429_RATE_LIMIT'


def test_live_requires_run_specific_quota_confirmation(tmp_path):
    with pytest.raises(ValueError,match='headroom'):
        run(True,tmp_path/'no-send.json',quota_confirmed=False)
