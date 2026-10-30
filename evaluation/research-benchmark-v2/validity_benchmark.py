#!/usr/bin/env python3
"""Fresh labeled safety/validity benchmark for memory retrieval policies."""
from __future__ import annotations
import argparse, json, re, statistics
from pathlib import Path
from types import SimpleNamespace
from oxmemory.core.models import Memory, RetrievalConfig
from oxmemory.relevance_cases import dataset
from oxmemory.storage.retrieval import rank_memories, build_context

STOP=set('a an the is are was were be been do does did how what which who when where why can could should would we our it its of for to in on at by with and or this that these those as from have has use used using tell me about'.split())
def toks(s): return {x for x in re.findall(r'\w+', str(s).lower()) if x not in STOP and len(x)>2}
def lexical(q, memories, k=5):
    qw=toks(q); scored=[]
    for m in memories:
        mw=toks(' '.join([m.content,*m.tags,*m.symbols])); scored.append((len(qw&mw)/max(len(qw),1),m.id))
    return [mid for score,mid in sorted(scored,key=lambda x:(-x[0],x[1]))[:k] if score>0]

def run(out):
    rows=[]
    for case in dataset():
        memories=[Memory(id=f'm{i}', **({'content':v} if isinstance(v,str) else v)) for i,v in enumerate(case['memories'])]
        def semantic_search(q, limit=5, **_kw):
            qw=toks(q); scored=[]
            for m in memories:
                mw=toks(' '.join([m.content,*m.tags,*m.symbols]))
                scored.append({'id':m.id,'similarity':len(qw&mw)/max(len(qw),1)})
            return sorted(scored,key=lambda x:(-x['similarity'],x['id']))[:limit]
        store=SimpleNamespace(markdown=SimpleNamespace(get_all_memories=lambda:memories),vector_store=SimpleNamespace(search=semantic_search),project_dir=Path('.'))
        arms={"no_memory":[],"similarity":lexical(case['query'],memories)}
        for name,arch,gate in (("basic","baseline",False),("gedam","edam",True)):
            policy=RetrievalConfig(architecture=arch,relevance_gate=gate)
            ranked=rank_memories(store,case['query'],5,None,name=='gedam',[],[],False,relevance_gate=gate,min_similarity=policy.min_similarity,policy=policy)
            arms[name]=[x['memory'].id for x in ranked]
            if name=='gedam': gedam_status=getattr(ranked,'status','')
        for arm,ids in arms.items():
            relevant=set(case.get('relevant',[])); answerable=bool(relevant)
            rows.append({'id':case['id'],'arm':arm,'answerable':answerable,'relevant':sorted(relevant),'retrieved':ids,'hit':bool(set(ids)&relevant),'no_answer_fp':(not answerable and bool(ids)),'correct_abstention':(not answerable and not ids),'conflict':case.get('expected_conflict'),'conflict_detected':(getattr(locals().get('ranked',None),'status','')=='abstained_conflict' if arm=='gedam' else False)})
    summary=[]
    for arm in ('no_memory','basic','similarity','gedam'):
        rr=[r for r in rows if r['arm']==arm]; pos=[r for r in rr if r['answerable']]; neg=[r for r in rr if not r['answerable']]
        conflicts=[r for r in rr if r['conflict'] is not None]
        summary.append({'arm':arm,'n':len(rr),'answer_recall':sum(r['hit'] for r in pos)/len(pos),'false_abstention':sum(not r['retrieved'] for r in pos)/len(pos),'no_answer_fp':sum(r['no_answer_fp'] for r in neg)/len(neg),'correct_abstention':sum(r['correct_abstention'] for r in neg)/len(neg),'conflict_detection_recall':sum(r['conflict_detected'] for r in conflicts if r['conflict'])/sum(r['conflict'] for r in conflicts) if any(r['conflict'] for r in conflicts) else None})
    report={'benchmark':'GEDAM validity and abstention benchmark v2','case_count':len(dataset()),'arms':summary,'rows':rows,'limitations':['Synthetic labeled cases measure policy safety, not external factual QA.','Validity/suppression labels are defined by the case construction.']}
    out.mkdir(parents=True,exist_ok=True); (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    lines=['# GEDAM validity benchmark v2','',f"Labeled cases: {len(dataset())}.",'','| Arm | Answer recall | False abstention | No-answer FP | Correct abstention | Conflict detection recall |','|---|---:|---:|---:|---:|---:|']
    for s in summary: lines.append('| {arm} | {answer_recall:.3f} | {false_abstention:.3f} | {no_answer_fp:.3f} | {correct_abstention:.3f} | {conflict_detection_recall} |'.format(**s))
    lines += ['','This safety suite is reported separately from LoCoMo because LoCoMo does not label stale, no-answer, or contradictory memories.']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--output',type=Path,required=True); a=p.parse_args(); run(a.output)
