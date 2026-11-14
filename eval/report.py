"""Generate Session 9 tables from one measured run, never invent missing costs."""
import argparse,csv,json,statistics,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from eval.costs import price_call,economics

def mean(xs):
    return statistics.mean(xs) if xs else None

def display(x):
    return 'NOT MEASURED / UNVERIFIED' if x is None else f'{x:.6f}'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('run',type=Path)
    ap.add_argument('--prices',type=Path,default=Path(__file__).parent/'config/prices.json')
    ap.add_argument('--assumptions',type=Path,default=Path(__file__).parent/'config/assumptions.json')
    args=ap.parse_args()
    rows=[json.loads(x) for x in (args.run/'results.jsonl').read_text().splitlines()]
    manifest=json.loads((args.run/'manifest.json').read_text())
    for row in rows:
        row.setdefault('version',manifest.get('prompt','v3'))
    prices=json.loads(args.prices.read_text());a=json.loads(args.assumptions.read_text())
    from eval.metrics import score
    lines=['# Session 9 evaluation and cost report',
        f"Run: {manifest['run_id']}. Unit: {manifest['unit']}. Final frozen run: {manifest['final']}.",
        f"Taxonomy: {manifest.get('taxonomy_version', 'not recorded in this archive')}. Tags: {manifest.get('weakness_tags', 'not recorded')}.",
        'Primary metric remains workshop weakness-tag recall. Human behavior checks remain separate.',
        '## Testing evidence',
        '| Prompt / mode | Recall mean (range) | Precision mean | F1 mean | Completion | Known warm cost / attempt (USD) | Unknown calls | Median / p95 seconds |',
        '|---|---|---|---|---|---|---|---|']
    costs={};exports=[];details=[]
    for version,mode in sorted({(r['version'],r['mode']) for r in rows}):
        label=f'{version} / {mode}'
        group=[r for r in rows if r['mode']==mode and r['version']==version]
        per=[score([r for r in group if r['repeat']==i]) for i in sorted({r['repeat'] for r in group})]
        recalls=[s['recall'] for s in per if s['recall'] is not None]
        warm=[c for r in group for c in r['calls'] if c['stage']!='rubric_index_embedding']
        index=[c for r in group for c in r['calls'] if c['stage']=='rubric_index_embedding']
        vals=[price_call(c,prices) for c in warm];unknown=sum(v is None for v in vals)
        known=sum(v for v in vals if v is not None); c=known/len(group) if not unknown else None
        costs[label]=c
        secs=sorted(r['seconds'] for r in group)
        p95=secs[max(0,__import__('math').ceil(.95*len(secs))-1)]
        rec=f'{mean(recalls):.3f} ({min(recalls):.3f}–{max(recalls):.3f})' if recalls else 'N/A'
        lines.append(f"| {label} | {rec} | {display(mean([s['precision'] for s in per if s['precision'] is not None]))} | {display(mean([s['f1'] for s in per if s['f1'] is not None]))} | {score(group)['completion']:.3f} | {display(c)} | {unknown} | {statistics.median(secs):.2f} / {p95:.2f} |")
        for repeat in sorted({r['repeat'] for r in group}):
            rr=[r for r in group if r['repeat']==repeat]
            cc=[c for r in rr for c in r['calls']]
            exports.append(dict(version=version,mode=mode,repeat=repeat,**{k:v for k,v in score(rr).items() if k!='per_tag'},
                input_tokens=sum((c.get('usage') or {}).get('prompt_token_count') or 0 for c in cc),
                candidate_tokens=sum((c.get('usage') or {}).get('candidates_token_count') or 0 for c in cc),
                thought_tokens=sum((c.get('usage') or {}).get('thoughts_token_count') or 0 for c in cc),
                calls_without_usage=sum(not c.get('usage') for c in cc)))
        details.extend([f"\n{label}: {len(index)} measured index-build calls. Warm known subtotal ${known:.6f}; "
                      f"{unknown} calls remain unpriced. Latency includes cold starts and retries; sleep excluded.",
            f"{label}: warm cost per completed report (including spend on failures) = "
            f"{display(known / sum(r['completed'] for r in group) if not unknown and any(r['completed'] for r in group) else None)} USD. "
            f"First-attempt completion = {sum(r['completed'] and not r['meta'].get('formatting_failures') and all(c['status']=='ok' for c in r['calls']) for r in group)}/{len(group)}."])
    lines.extend(details)
    with (args.run/'comparison.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(exports[0]));w.writeheader();w.writerows(exports)
    ledger=[]
    for r in rows:
        for c in r['calls']:
            ledger.append(dict(case_id=r['id'],version=r['version'],mode=r['mode'],repeat=r['repeat'],call_id=c['call_id'],
                stage=c['stage'],model=c['model'],usd=price_call(c,prices),status=c['status'],
                seconds=c['seconds'],usage=json.dumps(c.get('usage'))))
    if ledger:
        with (args.run/'cost_ledger.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(ledger[0]));w.writeheader();w.writerows(ledger)
    review=args.run/'human_review.csv'
    if not review.exists():
        with review.open('w',newline='') as f:
            fields=['id','version','mode','repeat','reviewer','behavior_pass','evidence_supported','fix_actionable',
                    'session_followup_fit','metric_blind_failure_quote','explanation']
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
            w.writerows({k:r[k] for k in ['id','version','mode','repeat']} for r in rows)
    with review.open() as review_file:
        reviews=list(csv.DictReader(review_file))
    expected_keys={(r['id'],r['version'],r['mode'],str(r['repeat'])) for r in rows}
    review_keys=[(r['id'],r.get('version',manifest.get('prompt','v3')),r['mode'],r['repeat']) for r in reviews]
    if len(review_keys)!=len(set(review_keys)) or set(review_keys)!=expected_keys:
        raise ValueError('Review sheet keys do not match measured results')
    dataset=json.loads((args.run/'dataset.json').read_text())
    from eval.run_eval import CATEGORIES
    missing=sorted(CATEGORIES-{c['category'] for c in dataset['cases']})
    lines += [f"Dataset: {len(dataset['cases'])} unique cases. Required categories missing: {missing}. Selected: {len(manifest['selected_ids'])}."]
    expected_rows=len(manifest['selected_ids'])*len(manifest['modes'])*len(manifest.get('versions',[manifest.get('prompt','v3')]))*manifest['repeats']
    lines += [f'Completed recorded attempts: {len(rows)}/{expected_rows}. A partial run is not a complete comparison.']
    for review_row in reviews:
        if review_row['reviewer'] and review_row['metric_blind_failure_quote']:
            lines += [f"Observed metric-blind failure proposed by {review_row['reviewer']} — {review_row['id']} / {review_row.get('version',manifest.get('prompt','v3'))} / {review_row['mode']} / repeat {review_row['repeat']}:", review_row['metric_blind_failure_quote'],review_row['explanation']]
    reviewed=sum(bool(r['reviewer'] and r['behavior_pass'] in ['yes','no']) for r in reviews)
    lines += [f'\nHuman behavior assessments recorded: {reviewed}/{len(rows)}. See human_review.csv.',
        '## 1 Measured cost per interaction',
        'Per call: ((input − cached) × input rate + cached × cached rate + billable output × output rate) / 1,000,000. '
        'Embedding input uses the explicitly verified usage field. Sum distinct requests, including retries, then divide by attempts. '
        'See cost_ledger.csv and comparison.csv; token subtotals are observed values, not imputed usage. '
        'A missing price or usage value prevents a complete dollar claim.',
        '## 2 Projected running cost',
        'Annual sessions = users × sessions per user per year. Operating cost = sessions × measured warm session cost '
        '+ annual hosting/storage/other + maintenance + index rebuilds. Development is added separately in year one.']
    session_ready=manifest['unit']=='full_interview' and all(r['completed'] for r in rows) and all(r.get('session_followup_fit')=='yes' and r.get('reviewer') for r in reviews) and len(reviews)==len(rows)
    projections={mode:economics(c,a['values']) if session_ready else None for mode,c in costs.items()}
    lines += ['## 3 Value and break-even',
        'Benefit per session = net minutes saved / 60 × hourly time value. This is time value, not cash revenue. '
        'First-year break-even sessions = (upfront + annual fixed costs) / (benefit per session − variable session cost); '
        'no positive break-even exists when benefit does not exceed variable cost.',
        json.dumps(projections,indent=2) if any(v is not None for v in projections.values()) else
        'PENDING: reviewed full-interview traces, complete pricing, and populated assumptions are required.',
        '## 4 Assumptions', '```json\n'+json.dumps(a,indent=2)+'\n```',
        '## 5 Sensitivity',
        'The projections above halve and double net minutes saved, retaining all other assumptions. '
        'Report explicitly if net first-year value changes sign. If adoption or another assumption dominates, '
        'also vary that input in assumptions.json and regenerate with the changed file.',
        '## 6 Build versus buy',
        'Hosted APIs charge for use and reduce model-serving work. Self-hosted open weights require compute capacity, '
        'deployment, monitoring, updates, and staff; low utilization can leave paid hardware idle. Latency depends on '
        'hardware and concurrency. Self-hosting gives more control over deployment and data handling, but privacy still '
        'depends on access and logging practices. Compare an open model on the same tests before assuming equal quality.',
        '## Interpretation to complete',
        '- Compare per-tag counts, model-only scores, and clean-answer false positives in metrics.json. Behavioral pass rates require human review.',
        '- State whether any quality gain is worth its measured extra cost. Inspect selected rubrics on disagreements; '
        'do not infer training-data recall or reasoning from a score alone.',
        '- Quote one observed failure that recall passes and identify the additional check needed.',
        '- Explain input provenance, reviewer agreement, comparison selection, and remaining limitations. '
        'Repetitions are not independent new inputs. Archive flawed historical runs separately.']
    (args.run/'session09_report.md').write_text('\n'.join(lines)+'\n')
    (args.run/'pricing_snapshot.json').write_text(json.dumps(prices,indent=2))
    (args.run/'assumptions_snapshot.json').write_text(json.dumps(a,indent=2))
    print('Written report, comparison, cost ledger, and review sheet:',args.run)

if __name__=='__main__':
    main()
