# 0082 — DSpace item metadata (split-cell skins drop the author list)

- **Date:** 2026-06-25
- **Tag:** `dspace-dev2` (baseline: `0081`)
- **Status:** landed — hub.hku.hk 0.87→1.00, dev2 +~0.0001 F1, dev/train flat (zero regression).

## Trigger

User flag: `hub.hku.hk/handle/10722/231252` (DSpace repository) drops the author list. Gold:
```
An SCO-enabled logistics and supply chain management system in construction
Authors: NIU, Y; Lu, W; LIU, D; CHEN, K
Issue Date: 2016
Citation: ...
Abstract: ...
```
We emitted a **bare `Authors` label** with no names: the item-view `table.itemDisplayTable`
splits label and value into separate `<td>` cells, and the value cell (4 `<a class="author">`
links) is dropped as link-dense, leaving the orphan label. The raw `dc.contributor.author`
second table also leaked.

## Why a blanket handler is the wrong tool

Of the 6 DSpace docs across general/{dev,dev2,train}, **only HKU fails** — the others already
score 0.94–0.995 because their skins render label+value in one block the classifier keeps:

| doc | base | full replace-handler |
|---|--:|--:|
| hub.hku.hk (split-cell) | 0.872 | **0.996** |
| digital.library.adelaide | 0.943 | 0.936 ❌ |
| lirias.kuleuven | 0.995 | 0.984 ❌ |
| qspace.library.queensu | 0.946 | 0.973 |
| econstor.eu | 0.986 | 0.992 |

An unconditionally-firing handler regresses adelaide/kuleuven (their golds de-label the author /
are already near-perfect). Violates the no-regression rule.

## Fix (gated rebuild)

`_dspace_metadata(dom)` rebuilds the labeled block from the first `itemDisplayTable` (Title →
bare heading, author `<a>` links joined with `; `, every other row → `Label: value`, plus
`Appears in Collections`). It is **applied only when the base extraction shows the split-cell
failure** — a kept paragraph that is exactly a metadata label (`_has_bare_dspace_label`). That
signature is present on HKU and **absent** on the four already-good skins, so the handler fires
on HKU alone. Double-gated (needs `itemDisplayTable` *and* a bare label), so no non-DSpace page
can be touched — `_dspace_metadata` returns None without the table.

## Results

| set | F1 | Lev |
|---|--:|--:|
| hub.hku.hk (doc) | 0.872 → **0.996** | 0.822 → 0.994 |
| dev2 | 0.8802 → 0.8803 (+~0.0001) | flat |
| dev | flat (gate fires on no dev doc) | flat |
| train | flat | flat |

61 tests pass. The four already-good DSpace skins are byte-unchanged.

## Cost

One `itemDisplayTable` xpath per page (cheap); the rebuild runs only on split-cell DSpace pages.
