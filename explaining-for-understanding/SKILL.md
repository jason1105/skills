---
name: explaining-for-understanding
description: Use when explaining a technical concept, mechanism, decision, bug, or piece of code to the user — especially if they say they don't get it (看不懂/没明白), ask "why", re-ask the same thing, or seem confused, or a first explanation didn't land. Also use the moment your draft would open with a method name, line number, config key, or 3+ new terms in one sentence.
---

# Explaining for Understanding

## Overview
Explain **outside-in**: from what the listener can already see, inward to the mechanism, on one everyday analogy, with jargon in parentheses. The job is to move understanding into their head — not to prove you understand it, not to make it auditable. **Rigor ≠ clarity**: line numbers make an explanation *verifiable*, not *understandable*.

## When to use
- Any explanation to the user; **especially** on a re-ask / "看不懂" / "why" / a failed first attempt — a re-ask usually means a *category/purpose* block ("what even is this / why does it exist"), not a missing detail.
- **STOP-and-use trigger:** your draft opens with a symbol the reader hasn't met (method/file/line/config key), or stacks 3+ new terms in one sentence.
- **NOT** here → use audit mode: they ask for the "audit version" → give exact refs, line numbers, names; skip the analogy.

## The recipe (in order)
1. **Name the real confusion first, then dissolve it** — "what is this / why does it matter" before any mechanism. On a re-ask, this step is usually the whole fix.
2. **Open on the observable** — a symptom, screen, or number they've actually seen — then move inward. Never mechanism-first.
3. **One everyday analogy = the load-bearing beam.** Explain the whole thing through it; hang the real terms on it as labels.
4. **Jargon lives in parentheses.** Plain words in the main clause; the true term is an optional footnote — `…立刻上锁(技术上叫半关)`.
5. **Cut audit-noise** — no line numbers / method names / file paths in the understanding pass. Save them for audit mode.
6. **One new concept per step**, each resting on the last. Sentence needs several unknowns at once? Split it.
7. **Say "so what / why care"** out loud.
8. **If they handed you a structure** (e.g. "1 现状 2 遗留"), fill in theirs, not yours.
9. **Offer audit mode** at the end: "要带行号、可回源码复核的审计版就说一声".

## Before / after (real)
- ❌ **inside-out, failed:** opened with method names + `行 269/332`; reader stayed 迷糊.
- ✅ **outside-in, landed:** opened with "this isn't a live bug — here's what you'd see", carried on a revolving-door analogy, jargon in parens, followed their 1/2 structure → "这样我就明白了".

## Red flags — slipped into audit-by-default
- First sentence names an identifier the reader hasn't met.
- Citing *where in the code* it is before they know *what it does*.
- Walking the mechanism mainly to prove you understand it.
- Never stating why they should care.

→ Restart outside-in: symptom first, analogy as the beam, jargon to parentheses.
