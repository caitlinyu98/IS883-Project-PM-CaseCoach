"""Deterministic scoring; recall remains the workshop primary metric."""
def ratio(a,b):
    return a/b if b else None

def score(rows):
    tp=fp=fn=exact=complete=clean_bad=clean=0
    per_tag={}
    for r in rows:
        g,p=set(r['expected_tags']),set(r['predicted_tags'])
        tp+=len(g&p); fp+=len(p-g); fn+=len(g-p)
        complete+=r['completed']; exact+=bool(r['completed'] and g==p)
        if not g:
            clean+=1; clean_bad+=bool(p)
        for tag in g|p:
            counts=per_tag.setdefault(tag,dict(tp=0,fp=0,fn=0))
            counts['tp']+=int(tag in g and tag in p)
            counts['fp']+=int(tag in p-g); counts['fn']+=int(tag in g-p)
    return dict(n=len(rows),tp=tp,fp=fp,fn=fn,recall=ratio(tp,tp+fn),
                precision=ratio(tp,tp+fp),f1=ratio(2*tp,2*tp+fp+fn),
                exact_set_accuracy=ratio(exact,len(rows)),completion=ratio(complete,len(rows)),
                clean_false_positive_rate=ratio(clean_bad,clean),per_tag=per_tag)
