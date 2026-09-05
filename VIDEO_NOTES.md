# VIDEO_NOTES — pitch script, shot-by-shot

Personal prep document, not required for the submission itself — delete
before making the repo public if you don't want prep notes visible, or
leave it in, it doesn't hurt. Written as a script you can read close to
verbatim.

**Numbers below are final, from a clean, fully-verified re-run** (150/150
records, confirmed 0 real API calls, 0 failures — recovering from a real,
disclosed bug where some earlier checkpoint entries were real,
non-simulated API calls that silently failed and got miscounted as
"executed"; see `BUILD_LOG.md` §19). Final: **104/150 actions executed,
₹41,819.81 simulated recovered, override rate 3/150 (2%)**. This 2% is
higher than the 0.7% figure `METRICS.md`'s older analysis reports — that
was a real number for an earlier run, not this one. Say **"2%,"** never
"0.7%."

---

## Before you hit record — a 10-minute setup pass

1. **Numbers are already final** (see above) — `RESULTS.md`, `REPORT.html`,
   and `POLICY_DASHBOARD.html` are all regenerated and consistent. No need
   to re-run anything unless you change the data yourself.
2. **Ollama warm.** Run one throwaway `python agent.py` call earlier (even
   just a few seconds, Ctrl+C it) — a cold model load takes ~20s and will
   kill your pacing if it happens on camera.
3. **Tabs open, in this order, ready to alt-tab through:**
   - Terminal, `cd`'d into `C:\razorpay\src`, font size bumped up
   - `REPORT.html` open in a browser tab (light, card-based layout — regenerate fresh per step 1 if you've re-run anything)
   - `POLICY_DASHBOARD.html` open in a second browser tab
   - `gate.py` open in the editor, scrolled near `def evaluate(`
   - `INTEGRATED_RESULTS.md` open in the editor
   - GitHub repo's **Actions** tab (green checkmarks) — repo is public
   - GitHub repo's **commits** page (real incremental history)
   - Razorpay dashboard, **Test Mode → Orders**, with a real order ID from `REAL_MCP_RESULTS.md` (e.g. `order_TVya2xkz293ced`) already searched and on screen
4. **Do one full silent dry run** of the commands below before recording.

---

## 0:00–0:45 — Open with the number, not the pitch

**Screen:** terminal, blank, then `RESULTS.md` opened in the editor.

**Say (close to verbatim):**
> "This is Recoup. Razorpay auto-retries a failed subscription payment 3
> times over 3 days. If all 3 fail, the subscription goes `halted`, and
> nothing tries again automatically — that's real, documented behavior,
> not an assumption. Recoup picks up exactly there. 150 real halted
> subscriptions, ₹1,50,729 total value, and the safety gate only had to
> override the AI's own proposal 3 times — 2%. That number is the whole
> pitch, and I'm going to spend this video proving it, not just stating
> it: why the number is low, and one case where the AI got something
> dangerously wrong that never reached Razorpay anyway."

**Why this opening:** name the project first (it's on the application
form), then lead with evidence from `RESULTS.md`, not framing — judges
are engineers, they want the number before the story.

---

## 0:45–1:25 — Architecture in 40 seconds

**Screen:** `README.md` §2 on GitHub — the Mermaid diagram renders live there.

**Say:**
> "Two paths. The AI only ever *proposes* a decision through one tool
> call — it never touches Razorpay directly. Everything it proposes goes
> through a plain, deterministic gate: no model involved, just a policy
> table, a spending cap, and a duplicate check. Only after the gate
> approves does anything reach Razorpay — through their own official MCP
> server when real keys are set, the same integration pattern their own
> Agent Studio uses. Every decision, whether allowed or refused, gets one
> line in an audit log."

---

## 1:25–2:10 — The strongest moment: a fraud case the AI got wrong, and why it didn't matter

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

**Screen:** `gate.py`, scrolled to `def evaluate(`, the `decline_code: str` line visible.

**Say:**
> "The gate doesn't look at what the AI said, or the description text at
> all. It looks up the correct action from the real, structured decline
> code Razorpay sends — `payment_risk_check_failed` — independently. So
> even in the one case where I proved the model gets it wrong, the wrong
> answer never reaches Razorpay. And this is a deliberate choice, not a
> default: I could have put another AI model in front of this one to
> double-check it. I didn't, on purpose — a check like this needs to be
> guaranteed, not just probably right, and only plain code gives you that."

**Why this is the centerpiece:** it's simultaneously a real failure, proof
the safety design works, and your clearest answer to "where did you choose
not to use AI, and why."

---

## 2:10–2:40 — The debugging story, compressed

**Screen:** `BUILD_LOG.md` §9.2 table.

**Say:**
> "That 2% didn't come from nowhere. First run, the model was wrong 87%
> of the time — a tool schema bug where it read 'fraud' as a generic 'do
> nothing' bucket even while reasoning out loud that a case wasn't fraud.
> Fixed that, got to 46%. Found two more systematic biases, fixed those,
> got to 22% — but that fix broke three *other* decline codes, found only
> by actually re-running the batch. Fixed those with negative examples
> naming the exact mistakes. Final, fully-verified run: 2%. A good model
> makes the gate cheap to run. It never makes the gate optional."

---

## 2:40–3:05 — What the actual output looks like

**Screen:** `REPORT.html`, then a quick cut to `POLICY_DASHBOARD.html`.

**Say:**
> "This page is generated straight from the audit log — no AI, no server,
> just the raw decisions rendered readable. And this one is the merchant
> side: every decline code in plain English, so changing how the system
> handles one doesn't mean reading Python."

**Why this segment exists:** these two pages are the closest thing this
backend-only project has to a UI, and they were never on camera in the
previous cut of this script — worth 25 seconds to prove this isn't just a
folder of JSON.

---

## 3:05–3:45 — All three required categories, one dispatcher

**Screen:** `INTEGRATED_RESULTS.md`.

**Say:**
> "The brief names three categories: payment failures, checkout
> abandonment, and overdue receivables. All three are real, separate,
> tested pipelines — not one flow stretched to cover three. And this file
> proves they're not disconnected scripts: one mixed batch, 16 records
> spanning all of them at once, gets routed automatically to the right
> handler by record shape alone — zero misrouting, by construction. ₹7.15
> lakh at risk in that one batch, real diagnosis and gate logic per
> category, one shared audit trail."

**Say, if time allows — the honest scope boundary:**
> "The brief also lists example directions I didn't build — a Hinglish
> voice interface, a mandate retry sequencer, a promise-to-pay tracker.
> Those needed infrastructure outside this scope. I went deep on the
> three categories the brief actually requires instead of thin across
> every example it suggests."

---

## 3:45–4:15 — What's real, not hypothetical

**Screen:** Razorpay dashboard, Test Mode, Orders page, the real order ID visible.

**Say:**
> "Every one of these numbers comes from something you can check
> yourself. This order was created by this code, through Razorpay's own
> official MCP server, with real test-mode keys — not simulated."

**Screen:** quick cut to GitHub Actions tab (green checks), then commits page.

**Say:**
> "206 automated tests run on every commit. The repo is public — this
> commit history is real, incremental work, not generated in one shot."

---

## 4:15–4:45 — Close

**Screen:** README §3 comparison table (Agent Studio vs. this project).

**Say:**
> "Razorpay's own Agent Studio already ships a Subscription Recovery
> Agent — I know that, and I picked this problem anyway. Not to compete
> with it. Theirs is a voice call and a closed guardrail process. Recoup
> is a raw log anyone can grep, a policy file anyone can edit with no
> redeploy, and every claim backed by something you can independently
> check across all three required categories. The point was never to
> out-build a production team in a week — it's to prove I can build the
> exact pattern behind it, and be honest about every place it still falls
> short."

**Hard stop at ~4:45–5:00.** If running long, cut from the *end*
backward — the fraud-case segment (1:25–2:10) is the one to protect no
matter what.

---

## If something goes wrong live

- **Ollama is slow / times out on camera:** cut, say "here's one I ran
  earlier" and show a line from `logs/audit_log.jsonl` instead.
- **A number you say doesn't match what's on screen:** stop, don't paper
  over it — re-check against a freshly regenerated `RESULTS.md`, not this
  file or `METRICS.md` (both can drift after a rerun; a freshly
  regenerated `RESULTS.md` is always the source of truth).
- **Running short on time:** cut the debugging story (2:10–2:40) to just
  the headline number, one sentence. Never cut the fraud case or the
  all-three-categories segment — those two are what a Track 3 judge is
  actually scoring.
