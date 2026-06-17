#!/usr/bin/env python3
"""Cycle 0024 experiment: a per-doc classifier that decides WHEN to apply inline-bold
markdown (wrap source <strong>/<b> spans in **). Blanket bolding regresses (-0.0018 Lev);
the hypothesis is that doc-level features predict the subset where bolding matches the gold.

Stage 1 (cache): extract per-doc features + plain/bold F1&Lev for train+dev.
Stage 2: train RF on train, gate bolding on dev, measure net vs plain. Report runtime.
"""
import sys, re, gzip, json, os, pickle
from time import perf_counter
_HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,_HERE)
sys.path.insert(0,os.path.dirname(os.path.dirname(_HERE)))
import justext, lxml.html
from metrics import rouge_l, levenshtein
STOP=justext.get_stoplist("English")
WS=re.compile(r'\s+')
def norm(s): return WS.sub(' ',s).strip()
DS="benchmark/datasets/general"
CACHE="/tmp/bold_trigger_cache.pkl"

def emphasis_spans(html):
    try: dom=lxml.html.fromstring(html)
    except Exception: return []
    out=[]
    for el in dom.iter('strong','b'):
        t=norm(el.text_content())
        if 2<=len(t)<=120: out.append(t)
    return out

def apply_bold(plain, spans):
    out=plain
    for e in sorted(set(spans),key=len,reverse=True):
        if e in out and '**'+e+'**' not in out:
            out=out.replace(e,'**'+e+'**')
    return out

def doc_row(r):
    g=r['final_output']
    paras=[p for p in justext.justext(r['html'],STOP) if not p.is_boilerplate]
    plain="\n\n".join(p.text for p in paras)
    spans=emphasis_spans(r['html'])
    # spans that actually occur in the kept output (the ones we'd bold)
    occ=[e for e in set(spans) if e in plain]
    bolded=apply_bold(plain,spans)
    fp,lp=rouge_l(plain,g)[2],levenshtein(plain,g)[1]
    fb,lb=rouge_l(bolded,g)[2],levenshtein(bolded,g)[1]
    klen=max(1,len(plain)); kw=max(1,len(plain.split()))
    nhead=sum(1 for p in paras if p.is_heading)
    feats=[
        len(occ),                              # bold-able spans in output
        len(occ)/kw*100,                       # spans per 100 words
        sum(len(e) for e in occ)/klen,         # frac of chars that would be bolded
        len(paras),                            # kept paragraphs
        klen,                                  # kept char length
        kw,                                    # kept words
        nhead,                                 # headings kept
        klen/max(1,len(paras)),                # avg paragraph length
        sum(1 for e in occ if len(e.split())<=3)/max(1,len(occ)),  # frac short spans
        sum(1 for e in occ if len(e.split())>=8)/max(1,len(occ)),  # frac long(sentence) spans
    ]
    return feats, (fp,lp,fb,lb), len(occ)

def build(split, limit=None):
    recs=[json.loads(l) for l in gzip.open(f"{DS}/{split}.jsonl.gz",'rt',encoding='utf-8') if l.strip()]
    if limit: recs=recs[:limit]
    rows=[]
    for r in recs:
        try: rows.append(doc_row(r))
        except Exception: pass
    return rows

if __name__=="__main__":
    if os.path.exists(CACHE):
        tr,dv=pickle.load(open(CACHE,'rb'))
        print("loaded cache")
    else:
        t0=perf_counter(); print("extracting train...",flush=True)
        tr=build("train",4000)
        print(f"  {len(tr)} train rows {perf_counter()-t0:.0f}s; extracting dev...",flush=True)
        dv=build("dev")
        pickle.dump((tr,dv),open(CACHE,'wb'))
        print(f"  {len(dv)} dev rows; cached")

    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    # train only on docs with >=1 boldable span (decision matters)
    trf=[r for r in tr if r[2]>0]
    X=np.array([r[0] for r in trf])
    # label: bolding does NOT hurt Lev (>= plain) -> 1 (safe to bold)
    y=np.array([1 if r[1][3]>=r[1][1] else 0 for r in trf])
    print(f"train docs w/ spans: {len(trf)}, label+rate(bold-safe) {y.mean():.2f}")
    clf=RandomForestClassifier(n_estimators=40,max_depth=8,min_samples_leaf=25,random_state=0,n_jobs=-1)
    clf.fit(X,y)

    # evaluate on dev: net F1/Lev of (plain) vs (blanket bold) vs (gated bold)
    n=len(dv)
    fp=sum(r[1][0] for r in dv)/n; lp=sum(r[1][1] for r in dv)/n
    fb=sum(r[1][2] for r in dv)/n; lb=sum(r[1][3] for r in dv)/n
    # gated: use bold only when clf predicts 1 AND doc has spans
    fg=lg=0; nbold=0
    t0=perf_counter()
    for feats,(f0,l0,f1,l1),ns in dv:
        use_bold = ns>0 and clf.predict([feats])[0]==1
        if use_bold: nbold+=1; fg+=f1; lg+=l1
        else: fg+=f0; lg+=l0
    dt=(perf_counter()-t0)/n*1000
    fg/=n; lg/=n
    print(f"\n{'plain':12} F1={fp:.4f} Lev={lp:.4f}")
    print(f"{'blanket bold':12} F1={fb:.4f} Lev={lb:.4f}  (Δ {fb-fp:+.4f}/{lb-lp:+.4f})")
    print(f"{'gated bold':12} F1={fg:.4f} Lev={lg:.4f}  (Δ {fg-fp:+.4f}/{lg-lp:+.4f})  bolded {nbold}/{n} docs")
    print(f"classifier predict overhead: {dt:.3f} ms/doc")
    names=['n_spans','spans_per100w','frac_bold_chars','n_paras','klen','kw','nhead','avg_para_len','frac_short','frac_long']
    print("top feats:",[(names[i],round(float(v),3)) for i,v in sorted(enumerate(clf.feature_importances_),key=lambda kv:-kv[1])[:5]])
