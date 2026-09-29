"""Fact IDs select server facts, never aliases or model-written paths. ZERO live calls."""
import json
from types import SimpleNamespace
import pytest
from pydantic import ValidationError
from app.ai.facts import FactCatalogue,MAX_FACTS,fact_label
from app.ai.schemas import FactDraftAnswer
from app.ai.citations import build_evidence
from app.ai.client import CopilotError

SCOPE='0123456789abcdef'
ORIGIN='2026-09-27'


def setup(**values):
    records={'e1':{'tool':'get_network_summary','payload':{
        'context':{'country_id':'IN','profile':'redistribution-ready','origin':ORIGIN},
        'summary':{'bed_utilisation':79.8,'staff_availability':92.5,**values}},
        'request_scope':{'state_id':'MH','district_id':'MH-PUNE','facility_id':None}}}
    catalog=FactCatalogue(SCOPE)
    catalog.envelope('e1','get_network_summary',records['e1']['payload'],summary_only=True)
    return catalog,records


def fid(catalog,path,eid='e1'):
    return next(f.fact_id for f in catalog.facts.values() if f.path==path and f.evidence_id==eid)


def answer(text,ids):
    return FactDraftAnswer.model_validate({'situation':{'text':text,'evidence_refs':ids}})


def context(**changes):
    return SimpleNamespace(country_id='IN',profile='redistribution-ready',state_id='MH',
        district_id='MH-PUNE',facility_id=None,compare_profiles=False,**changes)


def test_exact_latest_failure_reproduces_and_migrates_without_path_repair():
    catalog,records=setup();bed=fid(catalog,'summary.bed_utilisation')
    text='Bed utilisation reflects notable operational pressure.'
    resolved,evidence,_=catalog.validate(answer(text,[bed]),records,context(),ORIGIN)
    assert resolved.situation.references[0].field=='summary.bed_utilisation'
    assert evidence[0].value==79.8 and evidence[0].unit=='%'
    with pytest.raises(CopilotError) as error:catalog.validate(answer(text,['bed_utilisation']),records)
    assert error.value.code=='evidence_invalid'
    assert error.value.citation_diagnostic['unknown_fact_ids']==['bed_utilisation']


@pytest.mark.parametrize('invalid',['unknown','e1_f001','summary.bed_utilisation','e1_'+SCOPE+'_f999','',
    'e1_'+SCOPE+'_f001 ', 'E1_'+SCOPE+'_f001'])
def test_unknown_malformed_ids_have_no_alias_or_typo_repair(invalid):
    catalog,records=setup()
    with pytest.raises((CopilotError,ValidationError)):
        catalog.validate(answer('Bed utilisation reflects pressure.',[invalid]),records)


def test_previous_request_id_cannot_select_current_same_label_and_value():
    first,records=setup();second=FactCatalogue('fedcba9876543210')
    second.envelope('e1','get_network_summary',records['e1']['payload'],summary_only=True)
    stale=fid(first,'summary.bed_utilisation')
    assert stale!=fid(second,'summary.bed_utilisation')
    with pytest.raises(CopilotError):second.validate(answer('Bed utilisation reflects pressure.',[stale]),records)


def test_equal_labels_in_two_objects_retain_source_identity():
    catalog,records=setup()
    records['e2']={'tool':'get_network_summary','payload':{
        'context':records['e1']['payload']['context'],'summary':{'bed_utilisation':34.5}}}
    catalog.envelope('e2','get_network_summary',records['e2']['payload'],summary_only=True)
    _,evidence,_=catalog.validate(answer('Bed utilisation is 34.5%.',[fid(catalog,'summary.bed_utilisation','e2')]),records)
    assert evidence[0].evidence_id=='e2' and evidence[0].value==34.5
    with pytest.raises(CopilotError):
        catalog.validate(answer('Bed utilisation is 34.5%.',[fid(catalog,'summary.bed_utilisation')]),records)


def test_same_leaf_at_distinct_paths_is_unambiguous():
    payload={'context':{'country_id':'IN','profile':'redistribution-ready','origin':ORIGIN},
        'impact':{'before':{'target_deficit':10},'after':{'target_deficit':4}}}
    catalog=FactCatalogue(SCOPE);catalog.envelope('e1','get_optimization_result',payload)
    records={'e1':{'tool':'get_optimization_result','payload':payload}}
    a=fid(catalog,'impact.before.target_deficit');b=fid(catalog,'impact.after.target_deficit');assert a!=b
    _,evidence,_=catalog.validate(answer('The remaining target is 4.',[b]),records)
    assert evidence[0].field=='impact.after.target_deficit'
    with pytest.raises(CopilotError):catalog.validate(answer('The remaining target is 4.',[a]),records)


@pytest.mark.parametrize('text,accepted',[
    ('Bed utilisation is 79.8%.',True),('Bed utilisation is 80%.',False),
    ('Bed utilisation is 79.80%.',True),('Bed utilisation is 79.81%.',False),
    ('Bed utilisation reflects notable operational pressure.',True),
    ('Bed utilisation is 999%.',False)])
def test_numeric_and_qualitative_claims_keep_existing_exact_rules(text,accepted):
    catalog,records=setup();draft=answer(text,[fid(catalog,'summary.bed_utilisation')])
    if accepted:assert catalog.validate(draft,records)[1][0].value==79.8
    else:
        with pytest.raises(CopilotError) as error:catalog.validate(draft,records)
        assert error.value.code=='unsupported_number'


def test_qualitative_unrelated_fact_is_rejected_without_numbers():
    catalog,records=setup()
    with pytest.raises(CopilotError) as error:
        catalog.validate(answer('Bed utilisation reflects pressure.',[fid(catalog,'summary.staff_availability')]),records)
    assert error.value.citation_diagnostic['reason']=='unrelated_fact'


@pytest.mark.parametrize('change',[{'country_id':'BR'},{'profile':'constrained'},{'origin':'2026-09-28'}])
def test_cross_country_profile_origin_isolation(change):
    _,records=setup();records['e1']['payload']['context'].update(change)
    catalog=FactCatalogue(SCOPE);catalog.envelope('e1','get_network_summary',records['e1']['payload'],summary_only=True)
    with pytest.raises(CopilotError):
        catalog.validate(answer('Bed utilisation reflects pressure.',[fid(catalog,'summary.bed_utilisation')]),records,context(),ORIGIN)


@pytest.mark.parametrize('key,value',[('district_id','OTHER'),('state_id','OTHER'),('facility_id','OTHER')])
def test_cross_geography_membership_cannot_bypass_scope(key,value):
    catalog,records=setup();records['e1']['request_scope'][key]=value
    with pytest.raises(CopilotError):
        catalog.validate(answer('Bed utilisation reflects pressure.',[fid(catalog,'summary.bed_utilisation')]),records,context(),ORIGIN)


@pytest.mark.parametrize('text', ['Forecast accuracy is 0.0895.','Forecast accuracy is 91.05%.'])
def test_wape_is_not_accuracy_even_when_original_numeric_value_is_copied(text):
    payload={'context':{'country_id':'IN','profile':'redistribution-ready','origin':ORIGIN},
        'targets':{'medicine':{'champion':'actual-model','models':{'actual-model':{'test':{'wape':0.0895}}}}}}
    catalog=FactCatalogue(SCOPE);catalog.envelope('e1','get_model_performance',payload)
    with pytest.raises(CopilotError):
        catalog.validate(answer(text,[fid(catalog,'targets.medicine.models.actual-model.test.wape')]),{'e1':{'tool':'get_model_performance','payload':payload}})


def test_server_derived_fact_is_allowed_and_absent_arithmetic_is_not():
    payload={'context':{'country_id':'IN','profile':'redistribution-ready','origin':ORIGIN},
        'impact':{'transferred_units':15679,'percent_deficit_resolved':37.5428010439863}}
    catalog=FactCatalogue(SCOPE);catalog.envelope('e1','optimize_redistribution',payload)
    records={'e1':{'tool':'optimize_redistribution','payload':payload}}
    text='The resolved fraction is 37.5428010439863%.'
    assert catalog.validate(answer(text,[fid(catalog,'impact.percent_deficit_resolved')]),records)[1]
    with pytest.raises(CopilotError):catalog.validate(answer(text,[fid(catalog,'impact.transferred_units')]),records)


def test_duplicate_ids_in_one_claim_are_rejected():
    catalog,records=setup();bed=fid(catalog,'summary.bed_utilisation')
    with pytest.raises(CopilotError) as error:catalog.validate(answer('Bed utilisation reflects pressure.',[bed,bed]),records)
    assert error.value.citation_diagnostic['reason']=='duplicate_fact_id'


@pytest.mark.parametrize('override',[{'field_path':'summary.bed_utilisation'},{'numeric_value':79.8},{'unit':'%'},
    {'references':[{'evidence_id':'e1','field':'bed_utilisation'}]}])
def test_provider_cannot_supply_paths_values_units_or_old_contract(override):
    with pytest.raises(ValidationError):
        FactDraftAnswer.model_validate({'situation':{'text':'Bed utilisation reflects pressure.','evidence_refs':['id'],**override}})


def test_catalogue_is_stable_deterministic_bounded_and_paths_are_private():
    first,records=setup();payload=records['e1']['payload'];second=FactCatalogue(SCOPE)
    a=first.envelope('e1','get_network_summary',payload,summary_only=True)
    b=second.envelope('e1','get_network_summary',dict(reversed(list(payload.items()))),summary_only=True)
    assert a==b and len({f['fact_id'] for f in a['facts']})==len(a['facts'])
    assert 'path' not in json.dumps(a) and 'result' not in a
    assert len(FactCatalogue(SCOPE).envelope('e1','test',{'values':list(range(1000))})['facts'])<=MAX_FACTS
    assert all(f['unit']=='%' for f in a['facts'] if f['label']==fact_label('summary.bed_utilisation'))
    # Provider mutations cannot replace the server-owned value.
    next(f for f in a['facts'] if f['label']==fact_label('summary.bed_utilisation'))['value']=1
    assert first.facts[fid(first,'summary.bed_utilisation')].value==79.8


def test_current_schema_enumerates_only_ids_and_has_no_output_path_fields():
    catalog,_=setup();schema=catalog.schema()
    claim=schema['properties']['situation']
    assert set(claim['properties'])=={'text','evidence_refs'}
    assert claim['properties']['evidence_refs']['items']['enum']==list(catalog.facts)
    assert claim['additionalProperties'] is False


def test_literal_dotted_source_keys_are_not_published_as_invalid_paths():
    catalogue=FactCatalogue(SCOPE)
    catalogue.envelope('e1','test',{'coverage':{'0.8':0.75},'wape':0.0895})
    assert not any(f.path=='coverage.0.8' for f in catalogue.facts.values())
    assert any(f.path=='coverage' for f in catalogue.facts.values())
    assert any(f.path=='wape' for f in catalogue.facts.values())


def test_diagnostics_keep_index_text_unknown_ids_and_resolved_context():
    catalog,records=setup();good=fid(catalog,'summary.bed_utilisation')
    with pytest.raises(CopilotError) as error:catalog.validate(answer('Bed utilisation reflects pressure.',[good,'unknown']),records)
    info=error.value.citation_diagnostic
    assert info['claim_index']==0 and info['claim_text']=='Bed utilisation reflects pressure.'
    assert info['unknown_fact_ids']==['unknown'] and good in info['supplied_fact_ids']
    assert info['resolved_facts'][0]['path']=='summary.bed_utilisation'
    assert info['resolved_facts'][0]['context']['profile']=='redistribution-ready'


def test_source_mutation_after_catalogue_registration_is_rejected():
    catalog,records=setup();bed=fid(catalog,'summary.bed_utilisation')
    records['e1']['payload']['summary']['bed_utilisation']=1
    with pytest.raises(CopilotError) as error:catalog.validate(answer('Bed utilisation reflects pressure.',[bed]),records)
    assert error.value.citation_diagnostic['reason']=='fact_source_changed'


def test_warning_aggregate_units_distinguish_facilities_resources_and_warnings():
    catalogue=FactCatalogue(SCOPE)
    envelope=catalogue.envelope('e1','get_warning_summary',{'summary':{
        'facilities_affected':3,'medicines_at_risk':5,'total':26}})
    facts={f['label']:f for f in envelope['facts']}
    assert facts['Summary / Facilities affected']['unit']=='facilities'
    assert facts['Summary / Medicines at risk']['unit']=='medicine resource types'
    assert facts['Summary / Total']['unit']=='warnings'


def test_envelope_and_ids_are_sticky_within_request_but_new_requests_are_fresh():
    first,records=setup();payload=records['e1']['payload']
    a=first.envelope('e1','get_network_summary',payload,summary_only=True)
    assert first.envelope('e1','get_network_summary',payload,summary_only=True)==a
    second=FactCatalogue();second.envelope('e1','get_network_summary',payload,summary_only=True)
    assert set(first.facts).isdisjoint(second.facts)
