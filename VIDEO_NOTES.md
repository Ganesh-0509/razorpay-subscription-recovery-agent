# VIDEO_NOTES — pitch script, shot-by-shot

Personal prep document, not required for the submission itself — delete
before making the repo public if you don't want prep notes visible, or
leave it in, it doesn't hurt. Written as a script you can read close to
verbatim.

**Structure, and why it's in this order:** Problem → Solution → How it
works → Proof it works → Honest limitations → Close. Limitations get
their own dedicated beat near the end, stated on purpose, not tucked into
another segment as an aside — a limitation you say confidently reads as
self-awareness; one buried as a footnote reads like you're hoping it gets
skimmed past.

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
2. **You do NOT need to warm up Ollama.** This script never calls the
   model live — every segment shows a pre-generated file or a real
   dashboard.
3. **Tabs open, in this order, ready to alt-tab through:**
   - `README.md` top (title + intro) open on GitHub
   - `RESULTS.md` open in the editor
   - `README.md` §2 open on GitHub (renders the architecture diagram)
   - `METRICS.md` open in the editor, scrolled to §2.5 (the adversarial fraud-case miss)
   - `gate.py` open in the editor, scrolled near `def evaluate(`
   - `BUILD_LOG.md` open in the editor, scrolled to §9.2 (the accuracy table)
   - `REPORT.html` open in a browser tab (light, card-based layout — regenerate fresh per step 1 if you've re-run anything)
   - `POLICY_DASHBOARD.html` open in a second browser tab
   - `INTEGRATED_RESULTS.md` open in the editor
   - `README.md` §6 open on GitHub (Known Limitations)
   - Razorpay dashboard, **Test Mode → Payments → Payment Links**, with any real link from your account clicked open and scrolled to its **Notes** field (`source: recovery-agent`, a real `subscription_id`)
   - GitHub repo's **Actions** tab (green checkmarks) — repo is public
   - GitHub repo's **commits** page (real incremental history)
   - `README.md` §3 open on GitHub (the Agent Studio comparison table)
4. **Do one full silent read-through** of the script below before recording — out loud, no recording, just for pacing.

---

## PROBLEM

## 0:00–0:50 — Who's talking, what the brief asked for, then what I built against it

**Screen:** `README.md` top — title and intro paragraph.

**Say (close to verbatim):**
> "Hi, I'm Ganesh Kumar, and this is my submission for Track 3 of the
> Razorpay AI Buildathon — AI revenue recovery.
>
> So here's what the brief actually asks for: an agent that detects
> revenue at risk and wins it back, across three situations — a payment
> that failed, a checkout someone abandoned, and an invoice that's gone
> unpaid. And the bar isn't just spotting the problem — it's showing real
> money recovered, with rules that stop it from acting recklessly, and a
> full trail of every decision it makes.
>
> This is Recoup. Here's the most concrete version of that problem I
> anchored on first: Razorpay auto-retries a failed subscription payment
> 3 times over 3 days. If all 3 fail, it just stops — no more retries,
> nothing. Recoup picks up exactly there, and at the other two situations
> the brief names. 150 real halted subscriptions, ₹1,50,729 total value,
> and the safety gate only had to override the AI's own proposal 3
> times — 2%."

**Why this opening, in this order:** a real person presenting says who
they are before anything else — starting with "Track 3 asks for..."
sounds like reading the brief back to the judges, not a person talking to
camera. Say your name first, *then* the brief's own framing (so a judge
evaluates "does this solve what was asked," not "what is this thing"),
*then* name the project and land the headline number.

**Say it like you'd say it to a person, not read it like a report:**
pause after "Hi, I'm Ganesh Kumar" — don't rush into the next sentence.
That one beat of silence is what makes it sound like a person talking
instead of a script being read.

---

## SOLUTION — HOW IT WORKS

## 0:45–1:20 — Architecture in 35 seconds

**Screen:** `README.md` §2 on GitHub — the Mermaid diagram renders live there.

**Say:**
> "Two paths. The AI only ever *proposes* a decision through one tool
> call — it never touches Razorpay directly. Everything it proposes goes
> through a plain, deterministic gate: no model involved, just a policy
> table, a spending cap, and a duplicate check. Only after the gate
> approves does anything reach Razorpay — through their own official MCP
> server when real keys are set. Every decision, allowed or refused, gets
> one line in an audit log."

---

## PROOF IT WORKS

## 1:20–2:00 — The strongest moment: a fraud case the AI got wrong, and why it didn't matter

**Screen:** `METRICS.md` §2.5 — scroll to and highlight the exact quoted
case (`"High risk score triggered decline per issuer risk engine"`) and
the model's own reasoning quote underneath it.

**Say:**
> "I deliberately tried to break this with real payments jargon the
> model probably hasn't seen much of — 3DS, CNP, acquirer — plus one case
> written to be genuinely hard. One broke it: a fraud case, described as
> 'high risk score triggered decline per issuer risk engine' — the word
> 'risk' twice — and the model still proposed a payment link instead of
> flagging a human. Its own reasoning, right here: it said the
> description 'does not mention any technical/system problem.'"

**Screen:** `gate.py`, scrolled to `def evaluate(`, the `decline_code: str` line visible.

**Say:**
> "The gate doesn't look at what the AI said. It looks up the correct
> action from the real decline code independently, so the wrong answer
> never reaches Razorpay. This is a deliberate choice — I could have put
> another AI model in front of this one to double-check it. I didn't, on
> purpose: a check like this needs to be guaranteed, not just probably
> right, and only plain code gives you that."

---

## 2:00–2:25 — The debugging story, compressed

**Screen:** `BUILD_LOG.md` §9.2 table.

**Say:**
> "That 2% didn't come from nowhere. First run, the model was wrong 87%
> of the time — a schema bug reading 'fraud' as generic 'do nothing.'
> Fixed it, got to 46%. Found two more biases, got to 22% — but that fix
> broke three other codes, found only by re-running the batch. Fixed
> those too. A good model makes the gate cheap to run. It never makes the
> gate optional."

---

## 2:25–2:45 — What the actual output looks like

**Screen:** `REPORT.html`, then a quick cut to `POLICY_DASHBOARD.html`.

**Say:**
> "This page is generated straight from the audit log — no AI, no
> server. And this one's the merchant side: every decline code in plain
> English, so changing how the system handles one doesn't mean reading
> Python."

---

## 2:45–3:20 — All three required categories, one dispatcher

**Screen:** `INTEGRATED_RESULTS.md`.

**Say:**
> "All three categories the brief names are real, separate, tested
> pipelines — not one flow stretched to cover three. This file proves
> they're not disconnected: one mixed batch, 16 records spanning all of
> them, gets routed automatically to the right handler by record shape
> alone — zero misrouting, by construction. ₹7.15 lakh at risk in that
> one batch, real diagnosis and gate logic per category, one shared audit
> trail."

---

## HONEST LIMITATIONS

## 3:20–3:50 — What I didn't build, said plainly

**Screen:** `README.md` §6, Known Limitations.

**Say:**
> "Two things I want to say plainly rather than let you find out. First:
> the brief lists example directions beyond the three required categories
> — a Hinglish voice interface, a mandate retry sequencer, a
> promise-to-pay tracker. I didn't build those. They needed
> infrastructure outside this scope, and I chose to go deep on the three
> categories actually required instead of thin across every example
> suggested. Second: checkout abandonment and receivables are dispatched
> through one router, but they're still separate decision engines, not
> one merged brain — a deliberate boundary, documented, not a shortcut I
> tried to hide."

**Why this segment exists, and why here specifically:** stated with its
own timestamp, confidently, right before the closing proof — not
apologized for, not buried inside another point.

---

## WHAT'S REAL, NOT HYPOTHETICAL

## 3:50–4:20 — Independently verifiable proof

**Screen:** Razorpay dashboard, Test Mode on, Payments → Payment Links —
click into any real link from the list, scroll to its **Notes** field.

**Say, pointing at the Notes field:**
> "Every number so far comes from something you can check yourself. This
> payment link was created by this code, through Razorpay's own official
> MCP server — and this isn't something I could fake by hand: `source:
> recovery-agent`, and a real subscription ID, written into this link's
> notes by my code the moment it created it."

**Screen:** quick cut to GitHub Actions tab (green checks), then commits page.

**Say:**
> "206 automated tests run on every commit. The repo is public — this
> commit history is real, incremental work, not generated in one shot."

---

## CLOSE

## 4:20–4:50 — Close

**Screen:** README §3 comparison table (Agent Studio vs. this project).

**Say:**
> "Razorpay's own Agent Studio already ships a Subscription Recovery
> Agent — I know that, and I picked this problem anyway. Not to compete
> with it. Theirs is a voice call and a closed guardrail process. Recoup
> is a raw log anyone can grep, a policy file anyone can edit with no
> redeploy, and every claim backed by something you can independently
> check. The point was never to out-build a production team in a week —
> it's to prove I can build the exact pattern behind it, and be honest
> about every place it still falls short."

**Hard stop at ~4:50–5:00.** If running long, cut from the *end*
backward, but protect these two no matter what: the fraud-case segment
(1:20–2:00) and the honest-limitations segment (3:20–3:50) — those are
what a Track 3 judge is actually scoring, in that order.

---

## If something goes wrong live

- **A browser tab or the Razorpay dashboard is slow to load:** don't wait
  on camera — pause the recording, let it load, resume. Nothing in this
  script needs to happen live under time pressure; every screen is a file
  or page you already have open.
- **A number you say doesn't match what's on screen:** stop, don't paper
  over it — re-check against a freshly regenerated `RESULTS.md`, not this
  file or `METRICS.md` (both can drift after a rerun; a freshly
  regenerated `RESULTS.md` is always the source of truth).
- **Running short on time:** cut the debugging story (2:00–2:25) to just
  the headline number, one sentence. Never cut the fraud case or the
  honest-limitations segment.
