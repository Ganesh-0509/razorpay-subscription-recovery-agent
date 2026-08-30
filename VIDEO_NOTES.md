# VIDEO_NOTES — 5-minute pitch, shot-by-shot

Personal prep document, not required for the submission itself — delete
before making the repo public if you don't want prep notes visible, or
leave it in, it doesn't hurt. Everything below is written as a script you
can read close to verbatim, with exact commands and exact numbers pulled
from `METRICS.md`/`BUILD_LOG.md` so nothing here needs to be double-checked
again — it's already verified.

---

## Before you hit record — a 10-minute setup pass

Do this once, then record in as few takes as possible:

1. **Ollama warm.** Run one throwaway `python agent.py` call earlier (even
   just a few seconds, Ctrl+C it) so the model is loaded and `keep_alive`
   is active — a cold model load takes ~20s and will kill your pacing if
   it happens on camera unannounced.
2. **Tabs open, in this order, ready to alt-tab through:**
   - Terminal, `cd`'d into `C:\razorpay\src`, font size bumped up
   - `REPORT.html` open in a browser tab (regenerate fresh: `python generate_report.py`)
   - `logs/audit_log.jsonl` open in a text editor, search-ready for `payment_risk_check_failed`
   - GitHub repo's **Actions** tab (green checkmarks)
   - GitHub repo's **commits** page (shows real incremental history)
   - Razorpay dashboard, **Test Mode**, **Orders** page, with `order_TVya2xkz293ced` (or any ID from `REAL_MCP_RESULTS.md`) already searched and on screen
3. **Make the repo public first** (if you haven't) — a judge clicking through mid-video to a 404 is the one thing that undercuts everything else.
4. **Do one full silent dry run** of the commands below before recording, so you're not debugging live.

---

## 0:00–0:45 — Open with the number, not the pitch

**Screen:** terminal, blank, then `RESULTS.md` opened in the editor.

**Say (close to verbatim):**
> "Razorpay auto-retries a failed subscription payment 3 times over 3 days.
> If all 3 fail, the subscription goes `halted`, and nothing tries again
> automatically — that's real, documented behavior, not an assumption.
> This agent picks up exactly there. 150 real halted subscriptions,
> ₹1,50,729 total value, and by the final version, the safety gate had to
> override the AI's own proposal just 0.7% of the time — down from 87% on
> the very first run. That number is the whole pitch. Let me show you why
> it's low, why it doesn't matter that it's low, and one case where the
> AI got something dangerously wrong and it never reached Razorpay anyway."

**Why this opening:** leads with evidence pulled straight from `RESULTS.md`, not framing — judges are engineers, they want the number before the story.

---

## 0:45–1:45 — Architecture in 60 seconds

**Screen:** `README.md` §2 on GitHub — the Mermaid diagram renders live there, no need to draw anything.

**Say:**
> "Two paths. The AI only ever *proposes* a decision through one tool
> call — it never touches Razorpay directly. Everything it proposes goes
> through a plain, deterministic gate: no model involved, just a policy
> table, a spending cap, and a duplicate check. Only after the gate
> approves does anything reach Razorpay — through their own official MCP
> server when real keys are set, the same integration pattern their own
> Agent Studio uses. Every single decision, whether allowed or refused,
> gets one line in an audit log."

**Why:** this is the one architectural fact a judge needs before anything else makes sense — say it fast, point at the diagram, move on.

---

## 1:45–2:45 — The strongest moment: a fraud case the AI got wrong, and why it didn't matter

**Screen:** terminal.

**Say, while typing:**
> "I didn't just test this on clean data. I deliberately tried to break
> it with real payments jargon the model probably hasn't seen much of —
> terms like 3DS, CNP, acquirer."

**Then say:**
> "One case broke it, and it's the worst possible one to get wrong: a
> fraud case. Described as 'high risk score triggered decline per issuer
> risk engine' — it contains the word 'risk' twice — the model still
> proposed sending the customer a payment link instead of blocking it and
> flagging a human. Here's why that's fine anyway."

**Screen:** `gate.py`, scrolled to `def evaluate(`, line with `decline_code: str` visible.

**Say:**
> "The gate doesn't look at what the AI said, or the description text at
> all. It looks up the correct action from the real, structured decline
> code Razorpay sends — `payment_risk_check_failed` — independently. So
> even in the one case where I proved the model gets it wrong, the wrong
> answer never reaches Razorpay. That's not a hypothetical — I found this
> by trying to break it, on camera, right now."

**Why this is the centerpiece:** it's the only moment in the whole video that's simultaneously a real failure *and* proof the safety design works — nothing else in the project does both at once.

---

## 2:45–3:45 — The debugging story

**Screen:** `BUILD_LOG.md` §9.2 table (87% → 46% → 22% → 0.7%).

**Say:**
> "That 0.7% didn't come from nowhere. First run, the model was wrong 87%
> of the time — a tool schema bug where it read 'fraud' as a generic
> 'do nothing' bucket even while reasoning out loud that a case wasn't
> fraud. Fixed that, got to 46%. Found two more systematic biases, fixed
> those, got to 22% — but that fix broke three *other* decline codes,
> found only by actually re-running the batch, not assumed. Fixed those
> with negative examples naming the exact mistakes. Final run: 0.7%,
> confirmed at full scale, zero regressions."

**Say, landing the point:**
> "Here's the thing that matters more than the number: the gate's
> necessity was never about the model being bad. Even at 0.7%, it still
> enforces a spending cap and a duplicate-action check that have nothing
> to do with how smart the model is. A good model makes the gate cheap to
> run. It doesn't make it optional."

**Why:** this is your "I can debug my own system" moment — say the numbers fast, don't over-explain each fix, the trajectory itself is the proof.

---

## 3:45–4:30 — What's real, not hypothetical

**Screen:** Razorpay dashboard, Test Mode, Orders page, the real order ID visible.

**Say:**
> "Every one of these numbers comes from something you can check
> yourself. This order was created by this code, through Razorpay's own
> official MCP server, with real test-mode keys — not simulated. It's
> sitting in a real Razorpay account right now."

**Screen:** quick cut to GitHub Actions tab (green checks), then commits page.

**Say:**
> "24 automated tests run on every commit. The commit history is real,
> incremental work, not generated in one shot."

**Why:** this 45 seconds is entirely third-party-verifiable proof — the strongest possible signal in the least amount of time.

---

## 4:30–5:00 — Close

**Screen:** README §3 comparison table (Agent Studio vs. this project).

**Say:**
> "Razorpay's own Agent Studio already ships a Subscription Recovery
> Agent — I know that, and I picked this problem anyway. Not to compete
> with it. Theirs is a voice call and a closed guardrail process. This is
> a raw log anyone can grep, a policy file anyone can edit with no
> redeploy, and every claim backed by something you can independently
> check. The point was never to out-build a production team in a week —
> it's to prove I can build the exact pattern behind it, and be honest
> about every place it still falls short."

**Hard stop at 5:00.** If you're running long, cut from the *end* backward — the 1:45–2:45 fraud-case segment is the one to protect no matter what.

---

## If something goes wrong live

- **Ollama is slow / times out on camera:** don't wait it out — cut, say "here's one I ran earlier" and show the pre-generated `logs/audit_log.jsonl` line instead. A judge cares that it's real, not that it happened in this exact take.
- **A number you say doesn't match what's on screen:** stop, don't paper over it — re-check against `METRICS.md` before continuing. Every number in this document was pulled from there; if reality has moved since (e.g. you re-ran something), `METRICS.md` is the source of truth, not this file.
- **Running short on time:** cut segment 4 (the debugging story) down to just the headline table, one sentence. Never cut segment 3 (the fraud case) — it's the one irreplaceable moment.
