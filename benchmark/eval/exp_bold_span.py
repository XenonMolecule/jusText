#!/usr/bin/env python3
"""Cycle 0024b: PER-SPAN bold trigger. For each source <strong>/<b> span occurring in the
kept output, predict whether the gold bolds it; bold only high-confidence (precision-favoring
threshold) spans, so we capture the helpful subset without the blanket-bold regression."""
import sys, re, gzip, json, os, pickle
from time import perf_counter
_HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,_HERE)
sys.path.insert(0,os.path.dirname(os.path.dirname(_HERE)))
import justext, lxml.html
from metrics import rouge_l, levenshtein
STOP=justext.get_stoplist("English")
WS=re.compile(r'\s+')
def norm(s): return WS.sub(' ',s).strip()
DS="benchmark/datasets/general"; CACHE="/tmp/bold_span_cache.pkl"

def extract(r):
    g=r['final_output']; gn=norm(g)
    gbold=set(norm(m) for m in re.findall(r'\*\*([^*\n]{2,120}?)\*\*', g))
    paras=[p for p in justext.justext(r['html'],STOP) if not p.is_boilerplate]
    plain="\n\n".join(p.text for p in paras)
    try: dom=lxml.html.fromstring(r['html'])
    except Exception: return None
    spans={}
    for el in dom.iter('strong','b'):
        t=norm(el.text_content())
        if 2<=len(t)<=120 and t in plain: spans[t]=el.tag
    # doc-level context
    klen=max(1,len(plain)); kw=max(1,len(plain.split()))
    ndensity=len(spans)/kw*100
    rows=[]
    for t,tag in spans.items():
        # is this span its own whole line/paragraph in the output?
        whole=any(norm(line)==t for line in plain.split('\n'))
        rows.append({
            'feats':[len(t), len(t.split()), 1 if tag=='strong' else 0,
                     1 if whole else 0, ndensity, len(spans), kw,
                     1 if t.endswith(('.','!','?',':')) else 0,
                     1 if t[0].isupper() else 0, sum(c.isdigit() for c in t)/len(t)],
            'label':1 if t in gbold else 0,
            'span':t,
        })
    return {'plain':plain,'gold':g,'rows':rows}

def build(split,limit=None):
    recs=[json.loads(l) for l in gzip.open(f"{DS}/{split}.jsonl.gz",'rt',encoding='utf-8') if l.strip()]
    if limit: recs=recs[:limit]
    out=[]
    for r in recs:
        try:
            d=extract(r)
            if d: out.append(d)
        except Exception: pass
    return out

if __name__=="__main__":
    if os.path.exists(CACHE): tr,dv=pickle.load(open(CACHE,'rb')); print("cache loaded")
    else:
        t0=perf_counter(); print("extract train...",flush=True); tr=build("train",3000)
        print(f"  {perf_counter()-t0:.0f}s; extract dev...",flush=True); dv=build("dev")
        pickle.dump((tr,dv),open(CACHE,'wb')); print("cached")
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    Xtr=np.array([row['feats'] for d in tr for row in d['rows']])
    ytr=np.array([row['label'] for d in tr for row in d['rows']])
    print(f"train spans {len(ytr)}, gold-bolds rate {ytr.mean():.2f}")
    clf=RandomForestClassifier(n_estimators=60,max_depth=10,min_samples_leaf=15,random_state=0,n_jobs=-1)
    clf.fit(Xtr,ytr)
    # dev: sweep precision threshold; bold spans with prob>=thr
    def score(thr):
        fp=fb=lp=lb=0;n=len(dv);nb=0
        for d in dv:
            out=d['plain']
            if d['rows']:
                probs=clf.predict_proba(np.array([r['feats'] for r in d['rows']]))[:,1]
                for r,pr in sorted(zip(d['rows'],probs),key=lambda x:-len(x[0]['span'])):
                    if pr>=thr and r['span'] in out and '**'+r['span']+'**' not in out:
                        out=out.replace(r['span'],'**'+r['span']+'**'); nb+=1
            fp+=rouge_l(d['plain'],d['gold'])[2]; lp+=levenshtein(d['plain'],d['gold'])[1]
            fb+=rouge_l(out,d['gold'])[2]; lb+=levenshtein(out,d['gold'])[1]
        return fp/n,lp/n,fb/n,lb/n,nb
    fp,lp,_,_,_=score(2.0)  # thr>1 => never bold => plain baseline
    print(f"\nplain         F1={fp:.4f} Lev={lp:.4f}")
    for thr in [0.5,0.6,0.7,0.8,0.9]:
        _,_,fb,lb,nb=score(thr)
        print(f"gated thr={thr} F1={fb:.4f} Lev={lb:.4f}  (Δ {fb-fp:+.4f}/{lb-lp:+.4f})  spans bolded {nb}")
    names=['len','words','is_strong','whole_line','doc_density','n_spans','doc_words','ends_punct','title_case','digit_frac']
    print("top feats:",[(names[i],round(float(v),3)) for i,v in sorted(enumerate(clf.feature_importances_),key=lambda kv:-kv[1])[:5]])
