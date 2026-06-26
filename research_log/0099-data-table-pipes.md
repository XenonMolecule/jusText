# 0099 — Data-table pipe rendering (rewrite_data_tables)

## Problem
The gold transcribes a genuine data table as markdown pipes — ``cell | cell | cell`` rows, one
newline apart, with a ``--- | ---`` header separator — whereas jusText emitted each ``<tr>`` as a
space-joined paragraph in double-spaced blocks (the TSA "CAN I TAKE IT | CARRY-ON | CHECKED LUGGAGE"
table was unreadable; user: *"they look really ugly"*). We want to render the clear data tables as
the gold does, without touching layout/nav/forum tables.

## What shipped
``rewrite_data_tables(dom)`` (runs after ``rewrite_code_blocks`` in ``justext()``): rewrites a table
to a verbatim ``<pre>`` **only** when its type is unambiguous, else leaves it to the normal path.

Gate (all required): not nested, not DSpace ``itemDisplayTable``, ≥3 rows, **uniform** column count
≥2 (a single ragged row → skip), link chars ≤50 % of text, median cell ≤80 chars, and **≤40 % empty
cells** (drops form/layout boxes). Then:
* first row all ``<th>`` → **pipe table** with a ``--- | ---`` separator.
* else first-row cells all end in ``:`` → **label-value** block (single-newline rows).
* else skip.

Two rendering rules from user review:
* **First-cell-only ``&nbsp;``** (``_pipe_row``): only an empty *leading* cell needs ``&nbsp;`` to
  keep the column from collapsing; other empty cells render blank (calendar: ``&nbsp; |  |  | 1``).
* **``_clean_cell_text``** drops ``display:none`` / ``<script>`` / ``<style>`` *inside cells* before
  reading text — UniProt stores escaped ``<p>`` help markup in a ``display:none`` tooltip span on
  each cell; text_content() otherwise slurped literal ``<p>…`` into the table. Tail-preserving via
  deep-copy (keeps the visible "Active site" that is the hidden span's tail).

## Results
dev2 0.8804→**0.8802** (−0.0002), dev3 0.8867→**0.8867** (flat). Quality wins at ~flat metric
(cf. [[data-quality-counts-without-metrics]]): TSA test doc F1=**0.994** (perfect pipes), calendar
empty-day alignment, UniProt table ``<p>`` leak gone, atsdr contaminant table-1 preserved. Clean on
forums (psypokes/paia), the Pfam download box, and the sauer-thompson sidebar nav (all correctly
left to the normal extractor).

## Rejected / reverted
* **Ragged tolerance** (pad rows to max width, 1-cell rows → section labels). Preserved the atsdr
  multi-section table's data but **false-fired on forums** (psypokes, paia "totally ruined"), the
  Pfam form box, and UniProt's sparse feature table, for −0.0004 dev3. Reverted to the strict
  uniform-width gate. The genuine ragged *data* tables (atsdr table-2, genomebiology multi-level
  header) are queued for a **narrow** per-section / numeric-density-gated rule (#2) — see QUEUE.md.
* **Global ``display:none`` strip** in ``preprocessor`` (vs the cell-local one). Fixed UniProt's
  *section-heading* tooltip leaks too, but cost **−0.0056 dev2** — the benchmark gold is distilled
  from raw HTML, so most hidden content (tabs, accordions, "read more") is *in* the gold. UniProt
  tooltips are the exception, not the rule. Reverted; kept only the table-cell-local strip.
