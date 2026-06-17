# 0017 — Math deep-dive (read every entry) + plan

- **Date:** 2026-06-17
- **Status:** analysis/plan — read all 8 train + 2 dev math entries and their HTML.
  Implementation queued for the next compute window (fastText sweep was running).

## What the gold does with math

The teacher keeps math as **LaTeX source as literal text** — `$$f(x)=\ln(3x^2+3)$$`,
`\(x^{b}\)`, `$\hat{\epsilon}'\hat{\epsilon}$`, `\dfrac{2x}{7}`. It does NOT render to
unicode or MathML. So the target representation is the LaTeX string.

## How math appears in the HTML (per entry)

- **SE (math/quant.stackexchange), LibreTexts (train#3,4)**: LaTeX is **literal text**
  in the page (`$...$`, `\(...\)`); MathJax renders it client-side. **jusText already
  keeps it** when it selects the right region (train#0/3/4 PRED contains `\dfrac`, `\hat`).
- **dev#0 (motls.blogspot)**: "MathJax" markers are just the **library loading** — the
  post has **no real math** (only `$500 bet`). Not a math case; its miss is ordinary.
- **Wiki equation images (train#2 haskell, train#6 mashpedia)**: math is `<img>` with the
  LaTeX in `alt` — but the **gold drops these** (0/24, 0/22 alts in gold). Extracting alt
  here would HURT.
- **LibreTexts figure images (train#4)**: `alt` holds figure *descriptions* the gold
  **keeps** (15/20 in gold). Extracting alt helps here.
- No `<script type="math/tex">` or MathML `<annotation>` in this set (SE/LibreTexts use
  literal `$`-text), so script-stripping is not the issue here.

## Diagnosis

The dominant math failure is **content selection, not math rendering**: dev#1 (math.SE)
extracted "100% free, no registration" boilerplate and **missed the Q&A** that holds the
LaTeX; train#1 kept a "JavaScript is disabled" notice. The LaTeX itself is preserved once
the right region is chosen → the **fastText content model is the main lever** here too.

## Plan for the math cycle (rules that DON'T hurt other domains)

1. **LaTeX-content keep rule (safe, primary).** A paragraph containing real LaTeX markup
   (`$$`, `\(`, `\[`, `\begin{`, `\frac/\dfrac/\sqrt/\sum/\int/\hat/\alpha…`) is almost
   never boilerplate → **bias-keep it**. **Safety verified: fires on only 0.07% of
   `general` paragraphs** (19/26,696) → negligible risk to other domains, while it recovers
   math Q&A/exercise blocks. Implement as a force-keep in `ParagraphClassifier.apply`
   (like the `<pre>` rule) and/or a binary feature.
2. **Rely on the fastText model for region selection** (SE Q&A vs boilerplate) — the
   shared lever; already improving.
3. **MathML annotation** (`<annotation encoding="application/x-tex">`): extract the LaTeX
   if such pages appear (none in this set, but cheap & safe to add to preprocessing).
4. **Do NOT** blanket-extract math-image `alt` — context-dependent (helps LibreTexts
   figures, hurts wiki equations). Skip unless a learned signal can separate them.

## Math-image detection recipe (reusable, safe for general)

Detecting "this `<img>` is math" is reliable and **does not touch general** (measured on
general/dev, 5,502 images):

| signal | general false-positive | catches |
|---|--:|---|
| `class="tex"` / `mwe-math*` | **5/5502 (0.09%)** | wiki/MediaWiki equation imgs |
| `src` = `/math/<hex>.png` or math CDN (`latex.codecogs`, `chart?…cht=tx`, `cgi-bin/mathtex`, `render.php?tex=`) | **5/5502 (0.09%)** | rendered-equation imgs |
| `alt` contains LaTeX (`\cmd`, `_{`, `^{`, `\;`) | 79/5502 (1.4%) | secondary confirmation |
| MathML `<math>` / `<annotation x-tex>` | 0 | MathML pages |

Primary detector = `class="tex"` OR math-`src`; both ~0.09% on general → inert there.
The LaTeX-`alt` signal is looser (use combined with class/src, not alone).

**Detection ≠ keep.** In our wiki cases the gold *dropped* the inline equation alts, so
the policy layer (keep display eqns, drop tiny inline, or let the model arbitrate) is the
nuance — but detection is free and safe to add.

## Gold-quality finding: the teacher drops image-rendered math (likely a bug)

Evidence the gold *erred* on wiki equation-images (not a deliberate "not content" call):
- **train#6 (mashpedia, eq `η=η_Receiver·η_Carnot`)**: gold keeps the surrounding prose
  and inline unicode **η** ("efficiency η can be deduced … Carnot's principle"), but
  **drops the defining equation** (the `class="tex"` image). Gold has **0 LaTeX commands**.
- **train#2 (haskell)**: surrounding text kept, the `x_1…x_n` equation images gone.

The teacher knew the topic but lost the formula because it lives in `<img alt=…>` it
didn't read. **Implication:** the benchmark gold systematically under-includes
image-rendered math, so *correct* math-image extraction will score slightly *lower* vs
this gold on such docs — a gold artifact, not a real regression. We do NOT modify the
eval data; we note it, and prioritize true extraction quality for the math goal (the
detector is safe for other domains regardless).

## Next (execute)

- Implement rule (1), measure on `math` (train+dev) and confirm `general/code/science`
  unchanged (expected, given 0.07% fire). Read each math entry's diff after, iterate to
  near-perfect on the ones that are content-selection-fixable.
