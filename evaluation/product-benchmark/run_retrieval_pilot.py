#!/usr/bin/env python3
"""Run focused GEDAM recall, suppression, stale, no-answer and conflict checks."""
from __future__ import annotations
import json, shutil, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'evaluation/product-benchmark/pilot'
CASES=[
 {'id':'positive_toml','query':'service config TOML SERVICE_PORT override','fact':'Service load_config reads TOML configuration; SERVICE_PORT overrides [service].port.','gold':'positive'},
 {'id':'positive_pagination','query':'event listing page size cursor opaque base64 ID','fact':'Event listing uses default page size 20, hard maximum 100, and an opaque URL-safe base64 cursor that resumes exclusively after the last returned ID.','gold':'positive'},
 {'id':'positive_cache','query':'worker result cache LRU maximum entries recency','fact':'Worker result cache is LRU with a maximum of 64 entries; reads refresh recency and updating an existing key does not increase the entry count.','gold':'positive'},
 {'id':'stale','query':'legacy Redis endpoint retired address','fact':'Legacy Redis endpoint is redis://legacy.internal:6379 and is retired.','status':'stale','gold':'stale'},
 {'id':'candidate','query':'unapproved Kafka migration option','fact':'Kafka migration was only proposed for evaluation and has not been approved.','status':'candidate','claim_state':'proposed','gold':'candidate'},
 {'id':'no_answer','query':'which cloud provider hosts production','fact':'Worker service uses Python 3.11 and pytest.','gold':'no_answer'},
 {'id':'conflict','query':'service request timeout current setting','facts':['Service request timeout is 10 seconds.','Service request timeout is 30 seconds.'],'gold':'conflict','claims':['10 seconds','30 seconds']},
]

def main():
 from oxmemory.core.config import get_default_config,save_config
 from oxmemory.core.models import RetrievalConfig
 from oxmemory.storage.markdown import MarkdownManager
 from oxmemory.storage.memory_store import MemoryStore
 results=[]
 base=OUT/'retrieval-fixtures'
 if base.exists(): shutil.rmtree(base)
 base.mkdir(parents=True)
 for case in CASES:
  root=base/case['id']; root.mkdir()
  MarkdownManager(root).initialize_brain(case['id'])
  config=get_default_config(case['id']); config.retrieval=RetrievalConfig(architecture='edam',relevance_gate=True); save_config(config,root)
  with MemoryStore(root,enable_vectors=False) as store:
   ids=[]
   facts=case.get('facts',[case.get('fact')])
   for i,fact in enumerate(facts):
    kwargs={'tags':['benchmark','agreement','project decision'],'source':'synthetic_setup_transcript','trust_basis':'user_asserted','confidence':1.0,'claim_confidence':1.0,'salience':1.0}
    if case.get('status')=='stale':
      from oxmemory.core.models import MemoryStatus
      kwargs['status']=MemoryStatus.STALE
    if case.get('status')=='candidate': kwargs['claim_state']='proposed'
    if case['id']=='conflict':
      kwargs.update(claim_subject='service request',claim_predicate='timeout',claim_value=case['claims'][i],claim_state='adopted')
    mem=store.add(fact,**kwargs); ids.append(mem.id)
   ctx=store.recall_context(case['query'],token_budget=800,semantic=False,limit=5)
   retrieved=[x['memory']['id'] for x in ctx.get('results',[])]
   selected_stale=[m for m in ctx.get('results',[]) if case.get('status')=='stale']
   results.append({'case_id':case['id'],'category':case['gold'],'query':case['query'],'gold_ids':ids if case['gold'] in {'positive','stale','candidate'} else [],'retrieved_ids':retrieved,'retrieval_status':ctx.get('status'),'abstained':ctx.get('abstained'),'context_tokens_estimated':ctx.get('budget_used',0),'context_bytes':ctx.get('budget_used_bytes',0),'gold_recalled':bool(set(ids)&set(retrieved)) if case['gold']=='positive' else None,'stale_hit':bool(selected_stale) if case['gold']=='stale' else None,'candidate_suppressed':not bool(set(ids)&set(retrieved)) if case['gold']=='candidate' else None,'no_answer_false_positive':bool(retrieved) if case['gold']=='no_answer' else None,'conflict_correctly_abstained':ctx.get('status')=='abstained_conflict' if case['gold']=='conflict' else None,'budget_compliant':ctx.get('budget_used',0)<=800})
 report={'suite':'synthetic retrieval/suppression diagnostic','engine':'production GEDAM recall_context; keyword-only, semantic embeddings disabled','cases':results,'summary':{'positive_queries':sum(x['category']=='positive' for x in results),'positive_recall_at_5':sum(bool(x['gold_recalled']) for x in results if x['category']=='positive')/3,'candidate_suppression_rate':sum(bool(x['candidate_suppressed']) for x in results if x['category']=='candidate'),'stale_hit_rate':sum(bool(x['stale_hit']) for x in results if x['category']=='stale'),'no_answer_false_positive_rate':sum(bool(x['no_answer_false_positive']) for x in results if x['category']=='no_answer'),'no_answer_correct_abstention_rate':sum(not bool(x['no_answer_false_positive']) for x in results if x['category']=='no_answer'),'conflict_correct_abstention':results[-1]['conflict_correctly_abstained'],'budget_compliance_rate':sum(x['budget_compliant'] for x in results)/len(results)},'limits':['Tiny synthetic fixtures, one query per category; percentages are diagnostic only.','No independent annotators; gold labels are fixture-authored.','Keyword-only retrieval intentionally disables embeddings.','Conflict behavior measures retrieval abstention, not model answer correctness.']}
 (OUT/'retrieval-results.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report['summary'],indent=2))
if __name__=='__main__':main()
