# 0072 — phpBB: date-before-author skins + byline/title leak

- **Date:** 2026-06-25
- **Tag:** `current-phpbb` (baseline: `current-workitmom`)
- **Status:** landed — phpBB handler fix, 11 forum docs ΣΔF1 +0.155, zero regression.

## Trigger

User: `ethicalhacker.net/forums/viewtopic.php?t=2995` — phpBB fires but F1 0.56. Two bugs on
its WP-integrated skin:

```
gold:  don (Wed Oct 15, 2008 10:52 am):  Hey EH-Netters,…
ours:  **don**                            ← no date
       Wed Oct 15, 2008 10:52 am by don   ← byline leaks into body
       [Article]-Daemon - A Contest        ← per-post subject heading leaks
       Hey EH-Netters,…
```

1. **Date dropped:** the byline is "Wed Oct 15, 2008 10:52 am **by** don" (date *before*
   author); our regex only matched "by X **on** DATE", so no date.
2. **Leak:** this skin nests the byline (`p.wpuauthor`, class contains "author") and the
   per-post subject (`h3.first`) *inside* `.content`, so they leak into the post body.

## Fix

- **Date fallback** `_PHPBB_DATE`: if "on DATE" isn't found, search the byline for a
  "Mon DD, YYYY [HH:MM am]" date (optional leading weekday).
- **De-leak:** strip descendants matching `.author` and `h3.first` from the body before
  paragraph-making. No-op on standard phpBB3 / punbb (the body *is* the whole `.content`).

## Rejected (regression hunt)

A first attempt also (a) took the first *non-empty* username and (b) selected the *innermost*
`.content`. (a) made the handler fire on punbb where the model was better; (b) picked a nested
`*content*`-classed quote inside `entry-content`, dropping ~3 KB of body — **cholangiocarcinoma
punbb −0.236**. Both reverted; strip-meta on the full `.content` keeps all wins with no
regression.

## Results (5 datasets dev, vs current-workitmom)

- ethicalhacker: date now in the marker, byline/title leak gone (`**don** (Wed Oct 15, 2008
  10:52 am)`); the only residual diff is the `**user** (date)` vs gold's `user (date):` format
  (consistent across all our forum handlers, not chased).
- 11 phpBB docs (train+dev) **ΣΔF1 +0.155 / ΣΔLev +0.263, all positive** (carveraudio,
  chesscube, sscycle, ethicalhacker…).
- general dev F1 +0.000010 / Lev +0.000016 (only 1 phpBB doc in dev); other datasets flat;
  61 tests pass.
