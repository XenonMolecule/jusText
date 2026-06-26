#!/usr/bin/env python3
"""Regression harness over user-flagged docs. Run after EVERY change to rewrite_data_tables / table
handling. Exit code 0 = all pass, 1 = a regression. Usage: JUSTEXT_NO_DOWNLOAD=1 python check_flagged.py
"""
import json, gzip, glob, sys, re
sys.path.insert(0, 'benchmark/eval')
sys.path.insert(0, '.')
import justext
from justext.classifier import ParagraphClassifier
from metrics import score_pair
try:
    import markdown as _md
except ImportError:
    _md = None

stop = justext.get_stoplist('English')
model = ParagraphClassifier.load('benchmark/eval/models/general-ftstack.joblib')

_general = glob.glob('benchmark/datasets_rawhtml/general/*.jsonl.gz')
_table_test = 'benchmark/datasets/table/test.jsonl.gz'


def _find(pred, files):
    for f in files:
        for l in gzip.open(f, 'rt'):
            r = json.loads(l)
            if pred(r):
                return r
    return None


def out(r):
    h = r.get('html')
    if not isinstance(h, str):
        return ''
    return '\n\n'.join(p.text for p in justext.justext(h, stop, model=model) if not p.is_boilerplate)


def by_url(sub, extra=''):
    return lambda r: sub in (r.get('url') or '') and (not extra or extra in (r.get('url') or ''))


def renders_clean(o):
    "True if every pipe-containing block renders as a GFM <table> (no pipe-text leaking as a <p>)."
    if _md is None:
        return True                                  # lib absent -> skip (don't false-fail)
    html = _md.markdown(o, extensions=['tables'])
    return not re.search(r'<p>[^<]*\|[^<]*</p>', html)


def min_tables(o, n):
    "True if the output renders at least n GFM tables."
    if _md is None:
        return True
    return _md.markdown(o, extensions=['tables']).count('<table>') >= n


# (name, finder, check(output)->bool, note). check returns True if OK.
CHECKS = [
    ('psypokes forum (no pipes)', by_url('psypokes.com/forums/viewtopic', 'p=335428'),
        lambda o: ' | ' not in o, 'forum must use normal extractor'),
    ('paia forum (no pipes)', by_url('paia.com/talk/viewtopic', 't=135'),
        lambda o: ' | ' not in o, 'forum must use normal extractor'),
    ('UniProt no <p> ANYWHERE', by_url('uniprot.org/uniprot/P45622'),
        lambda o: '<p>' not in o, 'display:none tooltip markup must not leak (headings too)'),
    ('UniProt keeps Active site', by_url('uniprot.org/uniprot/P45622'),
        lambda o: 'Active site' in o, 'cell/heading tail text must survive tooltip strip'),
    ('UniProt keeps Function heading', by_url('uniprot.org/uniprot/P45622'),
        lambda o: 'Function' in o, 'visible heading label must survive tooltip strip'),
    ('Pfam form box dropped', by_url('pfam', 'PF14029'),
        lambda o: 'Alignment: | &nbsp;' not in o, 'mostly-empty form table not piped'),
    ('atsdr table-1 piped+kept', by_url('atsdr.cdc.gov/HAC/pha', 'docid=873'),
        lambda o: 'Trichloroethylene (TCE)* | ND - 1,200' in o, 'uniform contaminant table piped'),
    ('atsdr table-2 ragged piped', by_url('atsdr.cdc.gov/HAC/pha', 'docid=873'),
        lambda o: 'Trichloroethylene (TCE)* | 15,000' in o, 'ragged multi-section table now piped'),
    ('genomebiology ragged piped', by_url('gb-2006-7-6-r47'),
        lambda o: 'One-half | 0.997 | 0.980' in o, 'ragged multi-level data table now piped'),
    ('atsdr renders valid GFM', by_url('atsdr.cdc.gov/HAC/pha', 'docid=873'),
        lambda o: renders_clean(o) and min_tables(o, 3), 'no pipe-text leaks as a paragraph'),
    ('genomebiology renders valid GFM', by_url('gb-2006-7-6-r47'),
        lambda o: renders_clean(o) and min_tables(o, 2), 'ragged table must render, not leak as text'),
    ('blog calendar dropped', by_url('profitfrominternet.eu/2012/06'),
        lambda o: ' | ' not in o, 'non-English month calendar must NOT pipe'),
    ('calendar first-cell nbsp', by_url('newenglandfilm.com/magazine/2012/04/stephenking'),
        lambda o: '&nbsp; |  |  | 1' in o, 'only leading empty cell -> &nbsp;'),
    ('sauer-thompson nav (no leak)', by_url('sauer-thompson.com', 'a-downbeat-nati'),
        lambda o: 'Foreign Policy Blogs' not in o, 'sidebar nav table must not pipe'),
    ('genomebiology data kept', by_url('gb-2006-7-6-r47'),
        lambda o: 'One-half' in o and '0.997' in o, 'ragged sci table data must survive (#2 target)'),
]


def main():
    fails = 0
    for name, finder, check, note in CHECKS:
        r = _find(finder, _general)
        if r is None:
            print('  SKIP  %-32s (doc not found)' % name)
            continue
        ok = check(out(r))
        print('%s  %-32s  %s' % ('  ok  ' if ok else 'FAIL!!', name, '' if ok else '<- ' + note))
        fails += not ok

    # TSA lives in the held-out table test set; assert F1 stays high.
    tsa = _find(lambda r: ' | ' in (r.get('final_output') or '') and 'CARRY-ON' in (r.get('final_output') or ''),
                [_table_test])
    if tsa is not None:
        f1 = score_pair(out(tsa), tsa['final_output'])['rougeL_f']
        ok = f1 >= 0.99
        print('%s  %-32s  F1=%.3f %s' % ('  ok  ' if ok else 'FAIL!!', 'TSA test table', f1,
                                         '' if ok else '<- expected >=0.99'))
        fails += not ok

    print('\n%s' % ('ALL PASS' if fails == 0 else '%d REGRESSION(S)' % fails))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
