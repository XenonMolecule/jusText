# 0060 — vBulletin handler: first *non-empty* username (androidcentral)

- **Date:** 2026-06-18
- **Tag:** `current-vbfix` (baseline: `current-seaccept`)
- **Status:** landed — one-line bug fix, surgical (1 doc), zero regression.

## Trigger

User flagged `forums.androidcentral.com/.../372361-possible-limit-mobile-data...` as "a forum
failure too — sad because we have all the pieces." Correct: it's vBulletin (`post_message_`
× 5, `id="post"` × 17), the handler exists, the bodies are clean — but the handler **didn't
fire** and the doc fell to the model (F1 0.9294 / Lev 0.8882).

## Bug

`vbulletin_paragraphs` read the author as `users[0]`:

```python
users = container.xpath('.//a[contains(@class,"username")]')
username = users[0].text_content().strip() if users else ""
if not username:
    continue        # <- skipped EVERY post
```

The androidcentral skin emits an **empty avatar** `<a class="username">` *before* the text
one, so `users[0]` is `""` → every post is skipped → `<2 posts` → handler returns None. Fix:
take the first **non-empty** username.

```python
username = next((u.text_content().strip() for u in users if u.text_content().strip()), "")
```

This can't change an already-correct attribution (a non-empty `users[0]` is still returned
first); it only rescues posts whose `users[0]` was blank.

## Results

- androidcentral: F1 0.9294 → **0.9828**, Lev 0.8882 → **0.9360** (+0.053 / +0.048).
- **Exactly 1 doc changes** across all of train+dev (measured: of the 293 train docs where
  the old handler returned None, only this skin has the empty-avatar-then-username pattern
  with ≥2 posts; the rest legitimately don't fire — single-post or no username links).
- general dev F1 +0.000053 / Lev +0.000048; code/math/science/table flat; 61 tests pass.

## Insight

The gold here uses the **Question/Answer role** format (`**Question (f2k8)**`,
`**Answer (trivor)**`), not the vBulletin `**username** (date)` the handler emits — yet the
username form still scores 0.98 because the bodies and authors match on tokens. No need to
chase the role format; the body extraction is what mattered.

## Next

- Other forum skins with the same empty-leading-`username` anchor would now also fire; none
  present in this dataset beyond androidcentral.
