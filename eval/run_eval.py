"""Offline preflight first. Live execution requires --run; final requires frozen reviewed data."""
import argparse, hashlib, json, random, sys, time, uuid, subprocess, os
from importlib.metadata import version as package_version
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from eval.metrics import score

CATEGORIES={'empty','outside_scope','wrong_kind','abusive','malicious','invalid_value','altered_familiar'}
TAGS={'no_success_metric','no_user_segmentation','no_clear_problem_framing','no_prioritization_rationale',
      'no_tradeoffs_or_risks','off_topic','empty_or_too_short',
      'no_business_impact','vague_solution','unstructured'}
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def validate(data, final=False):
    ids=[c['id'] for c in data['cases']]
    if len(ids)!=len(set(ids)):
        raise ValueError('Duplicate case IDs')
    if not ids:
        raise ValueError('Dataset has no cases')
    if final and not data.get('reviewed_by'):
        raise ValueError('Team review is missing')
    for c in data['cases']:
        if not c.get('question','').strip() or not c.get('expected_behavior'):
            raise ValueError(f"{c['id']}: exact question and expected behavior required")
        if not set(c['expected_tags'])<=TAGS:
            raise ValueError('Unknown expected tag')
        if final and (not c.get('reviewed_by') or not c.get('provenance')):
            raise ValueError(f"{c['id']}: missing reviewer or provenance")
        if data.get('unit') == 'full_interview' and final:
            turns=c.get('transcript',[])
            if len(turns)!=4 or any(not t.get('follow_up_answer','').strip() for t in turns):
                raise ValueError('Final full-interview benchmark needs four turns and prepared follow-up answers')
        if c.get('transcript') and (c['transcript'][0]['question']!=c['question'] or c['transcript'][0]['answer']!=c['answer']):
            raise ValueError('Session first turn differs from explicit case question/answer')
    return True

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dataset',type=Path,default=ROOT/'eval/datasets/development.json')
    ap.add_argument('--modes',nargs='+',choices=['none','tool','embedding'],default=['tool','embedding'])
    ap.add_argument('--versions','--version',nargs='+',choices=['v3','v4'],default=['v3'],help='Final feedback prompt versions; other stages are unchanged')
    ap.add_argument('--repeats',type=int,default=5)
    ap.add_argument('--ids',nargs='+')
    ap.add_argument('--model',default='gemini-3.5-flash-lite')
    ap.add_argument('--seed',type=int,default=883)
    ap.add_argument('--sleep',type=float,default=4)
    ap.add_argument('--run',action='store_true')
    ap.add_argument('--final',action='store_true')
    ap.add_argument('--freeze',action='store_true')
    ap.add_argument('--out',type=Path,default=ROOT/'eval/runs')
    args=ap.parse_args()
    if len(args.versions)!=len(set(args.versions)) or len(args.modes)!=len(set(args.modes)):
        ap.error('Duplicate versions or modes are not allowed')
    if args.repeats<1 or args.sleep<0:
        ap.error('Positive repetitions and nonnegative sleep required')
    data=json.loads(args.dataset.read_text())
    try:
        validate(data,args.final or args.freeze)
    except ValueError as error:
        ap.error(str(error))
    lock=args.dataset.with_suffix('.sha256')
    if args.freeze:
        lock.write_text(digest(args.dataset)+'\n');print('Frozen:',lock);return
    if args.final and (not lock.exists() or lock.read_text().strip()!=digest(args.dataset)):
        ap.error('Freeze reviewed dataset first; hash must match')
    if args.final and len(args.modes)*len(args.versions)>1 and args.repeats<5:
        ap.error('Final comparison needs at least five repetitions per version')
    cases=[c for c in data['cases'] if not args.ids or c['id'] in args.ids]
    if not cases or args.ids and set(args.ids)!={c['id'] for c in cases}:
        ap.error('Empty selection or unknown IDs')
    print(json.dumps(dict(cases=len(cases),report_attempts=len(cases)*len(args.modes)*len(args.versions)*args.repeats,
        missing_required_categories=sorted(CATEGORIES-{c['category'] for c in data['cases']}),
        primary_metric='weakness_tag_recall',live=args.run),indent=2))
    if not args.run:
        return
    os.environ['CASECOACH_MODEL']=args.model
    os.environ['CASECOACH_DISABLE_FALLBACK']='1'
    from prompts import FEEDBACK_PROMPTS, FOLLOWUP_PROMPTS
    from feedback import generate_report
    from interviewer import generate_followup
    from telemetry import capture, stage
    from retrieval import reset_index
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]
    out=args.out/run_id;out.mkdir(parents=True,exist_ok=False)
    (out/'dataset.json').write_text(json.dumps(data,indent=2))
    paths=list(ROOT.glob('*.py'))+list((ROOT/'eval').glob('*.py'))+[ROOT/'sources/rubrics.json',ROOT/'requirements.txt']
    hashes={str(p.relative_to(ROOT)):digest(p) for p in paths}
    for p in paths:
        target=out/'source'/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read_bytes())
    try:
        commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    except Exception:
        commit='unknown'
    manifest=dict(python=sys.version,packages={p:package_version(p) for p in ['google-genai','pydantic','numpy','streamlit']},run_id=run_id,created=datetime.now(timezone.utc).isoformat(),dataset_sha256=digest(args.dataset),
        source_hashes=hashes,commit=commit,taxonomy_version='ten_weaknesses_2026-11-14',weakness_tags=sorted(TAGS),model=args.model,prompt=args.versions[0] if len(args.versions)==1 else 'comparison',versions=args.versions,
        feedback_prompts={v:FEEDBACK_PROMPTS[v] for v in args.versions},followup_prompt=FOLLOWUP_PROMPTS['v3'],temperature=.3,rubric_k=1,
        fallback=False,rate_limit_policy=dict(same_key_wait_seconds=10,key_circuits_per_request=2),seed=args.seed,repeats=args.repeats,modes=args.modes,selected_ids=[c['id'] for c in cases],
        final=args.final,primary_metric='weakness_tag_recall',unit=data.get('unit','single_answer_report'),
        note='Index resets once per repetition; latency excludes between-case sleep. No automatic repair of failed rows.')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    rng=random.Random(args.seed); results=[]
    for repeat in range(1,args.repeats+1):
        reset_index()
        jobs=[(mode,version,c) for c in cases for mode in args.modes for version in args.versions];rng.shuffle(jobs)
        for mode,version,c in jobs:
            calls=[]; start=time.perf_counter();res=None;error=None;followups=[]
            transcript=json.loads(json.dumps(c.get('transcript') or [dict(question=c['question'],answer=c['answer'])]))
            try:
                with capture(calls):
                    if data.get('unit')=='full_interview':
                        for t in transcript:
                            f=generate_followup(t['question'],t['answer'],version='v3');followups.append(f)
                            if not f['in_scope'] or f['fallback_used']:
                                raise ValueError('Session needs user correction or valid follow-up')
                            t['follow_up']=f['follow_up']
                            if not t.get('follow_up_answer'):
                                raise ValueError('Session needs a reviewed follow-up answer')
                    res=generate_report(transcript,retrieval_mode=mode,version=version)
            except Exception as e:
                error=type(e).__name__  # errors may contain keys or submitted text
            elapsed=time.perf_counter()-start
            report=res['report'] if res else None
            row=dict(id=c['id'],mode=mode,version=version,repeat=repeat,question=c['question'],transcript=transcript,
                expected_tags=c['expected_tags'],expected_behavior=c['expected_behavior'],category=c['category'],
                predicted_tags=sorted({w['tag'] for w in report['weaknesses']}) if report else [],
                completed=report is not None,report=report,meta=res['meta'] if res else {},
                error_type=error,seconds=elapsed,calls=calls,followups=followups,
                checks=dict(schema_valid=report is not None,
                    score_valid=(report is not None and (report['overall_score'] is None or 1<=report['overall_score']<=10))),
                human_review='pending',session_followup_fit='pending' if followups else 'not_applicable')
            results.append(row)
            with (out/'results.jsonl').open('a') as f:
                f.write(json.dumps(row)+'\n')
            print(f"{repeat} {version}/{mode} {c['id']} completed={row['completed']}",flush=True)
            time.sleep(args.sleep)
    summaries=[]
    for version in args.versions:
        for mode in args.modes:
            for repeat in range(1,args.repeats+1):
                group=[r for r in results if r['mode']==mode and r['version']==version and r['repeat']==repeat]
                summaries.append(dict(mode=mode,version=version,repeat=repeat,all=score(group),
                    model_only=score([r for r in group if not r['meta'].get('rule_based')])))
    (out/'metrics.json').write_text(json.dumps(summaries,indent=2))
    print('Saved:',out)

if __name__=='__main__':
    main()
