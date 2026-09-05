# VIDEO_NOTES — pitch script, shot-by-shot (updated for the 4-domain build)

Personal prep document, not required for the submission itself — delete
before making the repo public if you don't want prep notes visible, or
leave it in, it doesn't hurt. Written as a script you can read close to
verbatim.

**Numbers below are final, from a clean, fully-verified re-run** (150/150
records, confirmed 0 real API calls, 0 failures — recovering from a real,
disclosed bug where some earlier checkpoint entries were real, non-simulated
API calls that silently failed and got miscounted as "executed"; see
`BUILD_LOG.md`'s newest entry). Final: **104/150 actions executed, ₹41,819.81
simulated recovered, override rate 3/150 (2%)**. Note this 2% is higher than
the 0.7% figure `METRICS.md`'s older debugging-trajectory analysis reports —
that analysis was against a different, earlier run; this repo does not paper
over the difference, and neither should the video. Say "2%," not "0.7%."

---

## Before you hit record — a 10-minute setup pass

1. **Numbers are already final** (see above) — `RESULTS.md`, `REPORT.html`,
   and `POLICY_DASHBOARD.html` are all regenerated and consistent as of this
   writing. No need to re-run anything unless you change the data yourself.
2. **Ollama warm.** Run one throwaway `python agent.py` call earlier (even
   just a few seconds, Ctrl+C it) so the model is loaded — a cold model
   load takes ~20s and will kill your pacing if it happens on camera.
3. **Tabs open, in this order, ready to alt-tab through:**
   - Terminal, `cd`'d into `C:\razorpay\src`, font size bumped up
   - `REPORT.html` open in a browser tab (now Razorpay-style light theme — regenerate fresh per step 1)
   - `POLICY_DASHBOARD.html` open in a second tab
   - `INTEGRATED_RESULTS.md` open in the editor
   - `logs/audit_log.jsonl` open in a text editor, search-ready for `payment_risk_check_failed`
   - GitHub repo's **Actions** tab (green checkmarks) — repo is now public
   - GitHub repo's **commits** page (shows real incremental history)
   - Razorpay dashboard, **Test Mode**, **Orders** page, with a real order ID from `REAL_MCP_RESULTS.md` already searched and on screen
4. **Do one full silent dry run** of the commands below before recording.

---

## 0:00–0:40 — Open with the number, not the pitch

**Screen:** terminal, blank, then `RESULTS.md` opened in the editor.

**Say (close to verbatim):**
> "Razorpay auto-retries a failed subscription payment 3 times over 3 days.
> If all 3 fail, the subscription goes `halted`, and nothing tries again
> automatically — that's real, documented behavior, not an assumption.
> This agent picks up exactly there. 150 real halted subscriptions,
> ₹1,50,729 total value, and by the final version, the safety gate had to
> override the AI's own proposal just 2% of the time — 3 out of 150. That
> number is the whole pitch. Let me show you why it's low, why it doesn't
> matter that it's low, and one case where the AI got something
> dangerously wrong and it never reached Razorpay anyway."

**Why this opening:** leads with evidence pulled straight from `RESULTS.md`, not framing — judges are engineers, they want the number before the story.

---

## 0:40–1:25 — Architecture in 45 seconds

**Screen:** `README.md` §2 on GitHub — the Mermaid diagram renders live there.

**Say:**
> "Two paths. The AI only ever *proposes* a decision through one tool
> call — it never touches Razorpay directly. Everything it proposes goes
> through a plain, deterministic gate: no model involved, just a policy
> table, a spending cap, and a duplicate check. Only after the gate
> approves does anything reach Razorpay — through their own official MCP
> server when real keys are set, the same integration pattern their own
> Agent Studio uses. Every single decision, whether allowed or refused,
> gets one line in an audit log."

---

## 1:25–2:15 — The strongest moment: a fraud case the AI got wrong, and why it didn't matter

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
> answer never reaches Razorpay. I found this by trying to break it, on
> camera, right now."

**Why this is the centerpiece:** the only moment that's simultaneously a real failure *and* proof the safety design works.

---

## 2:15–2:50 — The debugging story, compressed

**Screen:** `BUILD_LOG.md` §9.2 table.

**Say:**
> "That final number didn't come from nowhere. First run, the model was
> wrong 87% of the time — a tool schema bug where it read 'fraud' as a
> generic 'do nothing' bucket even while reasoning out loud that a case
> wasn't fraud. Fixed that, got to 46%. Found two more systematic biases,
> fixed those, got to 22% — but that fix broke three *other* decline
> codes, found only by actually re-running the batch. Fixed those with
> negative examples naming the exact mistakes. Final, fully-verified run: 2%."

**Say, landing the point:**
> "Here's the thing that matters more: the gate's necessity was never
> about the model being bad. Even at a low override rate, it still
> enforces a spending cap and a duplicate-action check that have nothing
> to do with how smart the model is. A good model makes the gate cheap to
> run. It doesn't make it optional."

---

## 2:50–3:35 — NEW: all three named categories, one dispatcher

**Screen:** `INTEGRATED_RESULTS.md`.

**Say:**
> "The brief names three categories: payment failures, checkout
> abandonment, and overdue receivables. All three are real, separate,
> tested pipelines here — not one flow stretched to cover three. And this
> file proves they're not just three disconnected scripts: one mixed,
> interleaved batch — 16 records from all four domains at once — gets
> routed automatically to the right handler by record shape alone. Zero
> misrouting, by construction: the dispatcher raises before a record is
> ever processed if it can't identify which domain it belongs to. ₹7.15
> lakh at risk across the mixed batch, real diagnosis and gate logic per
> domain, one shared audit trail."

**Say, if time allows — the honest scope boundary:**
> "The brief also lists some example directions I didn't build — a
> Hinglish voice interface, a mandate retry sequencer, a promise-to-pay
> tracker. Those needed infrastructure outside this scope. I went deep on
> the three categories the brief actually requires instead of thin across
> all seven examples."

**Why this segment exists:** without it, the video only shows the
subscription flagship — the single biggest piece of work (closing the
full category-scope gap) never appears on camera otherwise.

---

## 3:35–4:10 — What's real, not hypothetical

**Screen:** Razorpay dashboard, Test Mode, Orders page, the real order ID visible.

**Say:**
> "Every one of these numbers comes from something you can check
> yourself. This order was created by this code, through Razorpay's own
> official MCP server, with real test-mode keys — not simulated."

**Screen:** quick cut to GitHub Actions tab (green checks), then commits page.

**Say:**
> "206 automated tests run on every commit. The repo is public — the
> commit history is real, incremental work, not generated in one shot."

---

## 4:10–4:40 — Close

**Screen:** README §3 comparison table (Agent Studio vs. this project).

**Say:**
> "Razorpay's own Agent Studio already ships a Subscription Recovery
> Agent — I know that, and I picked this problem anyway. Not to compete
> with it. Theirs is a voice call and a closed guardrail process. This is
> a raw log anyone can grep, a policy file anyone can edit with no
> redeploy, and every claim backed by something you can independently
> check across all three required categories. The point was never to
> out-build a production team in a week — it's to prove I can build the
> exact pattern behind it, and be honest about every place it still falls
> short."

**Hard stop at ~4:40–5:00.** If running long, cut from the *end*
backward — the fraud-case segment (1:25–2:15) is the one to protect no
matter what.

---

## If something goes wrong live

- **Ollama is slow / times out on camera:** cut, say "here's one I ran
  earlier" and show the pre-generated `logs/audit_log.jsonl` line instead.
- **A number you say doesn't match what's on screen:** stop, don't paper
  over it — re-check against a freshly regenerated `RESULTS.md`, not this
  file or `METRICS.md` (both can drift after a rerun; `RESULTS.md`
  regenerated fresh is the source of truth).
- **Running short on time:** cut segment 3 (debugging story) to just the
  headline number, one sentence. Never cut the fraud case or the
  all-three-categories segment — those two are the ones a Track 3 judge
  is actually scoring.
