# Razorpay AI Buildathon — Easy Explainer: What Each Piece Actually Does

**Purpose of this file:** plain-language, example-driven explanations of every technical piece in the project. No jargon walls — if a term shows up here, it's explained the moment it's used. Pair this with `BUILD_LOG.md`, which has the same pieces but with the formal reasoning, real numbers, and "why this and not that" comparisons.

**Read this file when:** you want to understand *what a piece does and why it matters* before diving into the technical decision behind it.

**Companion files:** `BUILD_LOG.md` (formal decisions, reasoning, and real results) · `GLOSSARY.md` (every acronym/term, expanded — look here first if a term is unfamiliar).

**Running example used throughout:** one subscription, **`sub_042`** — a ₹499/month streaming plan. Razorpay tried charging the customer's card 3 times over 3 days, it kept failing (card expired), and Razorpay's own system gave up and marked it `halted`. Every layer below is explained through what happens to `sub_042` at that layer.

Think of the system as a stack — each layer sits on top of the one below it, and each solves exactly one job.

---

## Layer 1 — Razorpay test mode: "the practice version of real payments"

**Plain job:** a completely free, fake-money version of Razorpay's real payment system. Same behavior, same rules, zero real money, zero cost to use.

**Analogy:** a flight simulator for a pilot — every switch and screen behaves like the real cockpit, but nothing can actually crash.

**Example:** when our system decides to send `sub_042`'s customer a payment link, that link is a real, working Razorpay payment link — it's just running in "practice mode," so no real card ever gets charged through it.

---

## Layer 2 — MCP: "the standard way an AI is allowed to take an action"

**Plain job:** MCP is a common format for saying "here are the specific actions an AI is allowed to request, and here's exactly what information each one needs." Instead of an AI freely doing whatever it wants, it can only ask for one of a fixed, pre-approved list of actions.

**Analogy:** a restaurant menu, not a full kitchen. A customer (the AI) can only order what's on the menu (a fixed list of tools) — they can't walk into the kitchen and start cooking whatever they imagine.

**Example:** our AI can ask for `create_payment_link` (send `sub_042`'s customer a link to fix their payment) or `flag_for_manual_review` (hand it to a human) — and nothing else. It cannot invent a new action on the spot.

**Why this specific menu format, not a custom one we invented:** Razorpay itself just built its own official "menu" of actions in this exact same format for its own AI products. Using the same format means our system speaks the same language Razorpay's own tools do.

---

## Layer 3 — The local AI model (Ollama): "the brain that suggests what to do"

**Plain job:** looks at one halted subscription's details and suggests one action from the menu (Layer 2) — but only *suggests*. It never gets to act on its own.

**Analogy:** a junior employee who's allowed to recommend a decision, but every recommendation has to be signed off by a supervisor before anything actually happens.

**Example:** the model reads `sub_042`'s decline reason ("card expired") and says: "I suggest sending a payment link, because the customer's card has expired and they need to update it." That suggestion goes to Layer 5 next — it does *not* go straight to sending the link.

**Why a model running on our own computer, not a paid cloud AI service:** this whole project has a $0 budget. A local model costs nothing to run, however many times we need it, with no risk of a surprise bill.

---

## Layer 4 — The decline-code policy table: "the answer key"

**Plain job:** a fixed list, written by us in advance, saying exactly one correct action for every possible reason a payment can fail. This is what Layer 5 checks the AI's suggestion against.

**Analogy:** an answer key a teacher grades against — the AI's suggestion (Layer 3) is the student's answer; this table is what "correct" actually means.

**Example:** for "card expired" (exactly `sub_042`'s case), the answer key says: **send a payment link.** For "the bank flagged this as fraud," the answer key says: **never retry, just flag it for a human** — no matter what the AI suggests.

---

## Layer 5 — The gate: "the supervisor who has the actual final say"

**Plain job:** takes the AI's suggestion (Layer 3), checks it against the answer key (Layer 4), checks it against a couple of hard safety rules, and only *then* decides what really happens. This is plain, predictable code — not another AI — on purpose.

**Analogy:** airport security. It doesn't matter how confidently a passenger says "I definitely don't have anything to declare" — the same checklist gets applied to everyone, every time, regardless of what they claim.

**Example, the interesting case:** for `sub_042`, the model actually said (in a real run of this project): the case is about insufficient funds and needs no further action — and picked "no action needed" as its answer. That's wrong twice over: the real answer for "card expired" is "send a payment link," not "do nothing." The gate catches this, throws out the AI's incorrect suggestion, and does the correct thing instead — automatically, every single time, no exceptions.

**Four extra safety checks, beyond just "was the AI right":**
- **A spending limit** — even a *correct* action gets blocked if it would move too much money at once, or too much money across the whole batch.
- **A duplicate check** — the same action can't be taken twice on the same subscription in one run.
- **A "stop nagging" limit** — if this same subscription has already been nudged 3 times before (checked against the permanent log, not just this run), the gate stops trying automatically and hands it to a human instead of nudging a fourth time.
- **A "too cold to bother" limit** — if a subscription has been sitting halted for 12+ days, the gate treats it as unlikely to still be worth an automated nudge and hands it to a human too, instead of pretending a fresh case and a two-week-old one deserve the exact same automated treatment.

**The single most important number in this whole project came directly from this layer:** across 150 real subscriptions, the AI's suggestion was wrong **87% of the time** on the very first run. Three rounds of finding and fixing real prompt bugs brought that down to 46%, then 22%, then **0.7%** (see `METRICS.md` §2) — and the gate corrected every single wrong one, in every round, at every stage of that improvement. That's the actual, measured proof that a supervisor layer is necessary regardless of how good the model gets: even at 0.7% wrong, one mismatch out of 150 real money-adjacent decisions is exactly the kind of thing you want a deterministic layer catching, not a probabilistic one.

---

## Layer 6 — Where the action actually goes: Razorpay's own official toolkit, or practice mode

**Plain job:** once the gate approves an action, something has to actually go talk to Razorpay. There are two possible destinations, and the system picks automatically based on whether real (but still free) credentials exist yet.

**Analogy:** ordering food through the restaurant's *own* official delivery app, versus play-cooking in a toy kitchen when you don't have real ingredients yet — same order format either way, only the destination changes.

**Example:** with real (free) test credentials set up, sending `sub_042`'s payment link goes through **Razorpay's own official AI toolkit** — the exact same one their real product is built on. Without those credentials yet, the same request instead goes to our own "practice mode" that behaves the same way but doesn't need an account — so the whole system still runs and can be demoed for free either way.

---

## Layer 7 — The audit log: "the diary that remembers everything"

**Plain job:** every single decision — what the AI suggested, whether the gate agreed or overruled it, what actually happened — gets written down, permanently, one line at a time. Nothing is ever secretly skipped.

**Analogy:** a flight data recorder ("black box") — after anything happens, you can always go back and see exactly what the system was "thinking" at each step, in order.

**Example:** `sub_042`'s full story — the AI's wrong suggestion, the gate's correction, the payment link that got sent — is sitting in the log as a few lines anyone can open and read, in plain order, forever.

---

## Layer 8 — Not losing work when things get interrupted

**Plain job:** if a long run of 150 subscriptions gets stopped partway through (a computer hiccup, anything), starting over shouldn't mean redoing work that's already done.

**Analogy:** a video game that autosaves after every level, instead of only at the very end — getting kicked offline mid-game doesn't mean replaying from zero.

**Example:** this actually happened for real during development — a run got interrupted at 141 out of 150 subscriptions done. Instead of starting over, the system picked up exactly at #142 and finished the rest — nothing was lost or redone.

---

## Layer 9 — The bonus feature: splitting money between two people (Route)

**Plain job:** sometimes a recovered payment shouldn't go 100% to one place — for example, a referral partner who brought in that customer might deserve a small cut, with the rest going to the merchant, all in one step.

**Analogy:** a delivery app automatically sending the restaurant its share and the driver their tip from the same order, instead of the restaurant manually paying the driver afterward.

**Example:** in a small standalone demo, a recovered subscription's value is automatically split — most of it to the merchant, a slice to a referral partner — and, just like Layer 5's gate, one deliberately oversized example is correctly blocked by the same spending-limit check.

---

## Architecture — what actually runs where, and why nothing can be secretly trusted

**Plain job:** everything in Layers 1–9 describes *what each piece does*. This is about *which pieces are allowed to actually move money*, and which aren't.

**The one rule that makes this safe:** the AI (Layer 3) is never, under any circumstance, connected directly to a real money-moving action. It can only *suggest* — every suggestion has to pass through the gate (Layer 5) first. Nothing about the AI's confidence, wording, or reasoning changes that; the gate treats every suggestion identically, whether it "sounds" right or not.

**The two kinds of things in the system:**
- **Things that must never be trusted blindly** (the AI's suggestion) — always reviewed, never acted on directly.
- **Things that always have the final say, no exceptions** (the gate, the answer key it checks against) — plain, boring, predictable code, on purpose.

**Analogy:** think of a company where a junior analyst can recommend anything they want, but literally nothing gets approved without going through the same fixed checklist, applied identically regardless of who's asking or how confident they sound.

**Why this matters for the demo:** you can point at any one of the 150 real decisions this system made and ask "why did it do that?" — and the honest answer is always sitting in the audit log (Layer 7), never "because the AI said so."

---

## How it all connects — one subscription, start to finish

A halted subscription like `sub_042` exists
→ **Layer 3** (the AI) looks at it and suggests an action
→ **Layer 4** (the answer key) says what should actually happen
→ **Layer 5** (the gate) compares the two, corrects the AI if it's wrong, and checks the safety limits
→ **Layer 6** carries out the approved action — through Razorpay's real official toolkit, or practice mode
→ **Layer 7** writes down everything that just happened
→ **Layer 8** makes sure none of this work gets lost if something gets interrupted partway through.

---

## Communication protocol — what the AI's "menu order" actually looks like

**Plain job:** Layer 2 said the AI can only pick from a fixed menu. This is what's actually on one specific order.

**Analogy:** a form with a dropdown menu instead of a blank text box — you can only pick one of the listed options, you can't write in something else.

**Example:** the AI's entire "vote" on `sub_042` is exactly two things: which option it picked from a short fixed list (retry now, retry later, send a link, flag as fraud, or do nothing), and one or two sentences explaining why. That's it — it can't ask for a specific dollar amount to be moved, or invent a brand-new kind of action. All of that structure and every safety limit lives one layer further down, in the gate (Layer 5), completely outside the AI's control.

---

## The policy table and the gate — the actual difference between "suggested" and "correct"

**Plain job:** expanding on Layers 4–5 — what it actually looked like, for real, when the AI got something wrong.

**Analogy:** a spell-checker that doesn't just flag a typo but automatically fixes it to the one correct spelling, every time, regardless of what you typed.

**Example, a real one from an actual run:** for a case where the payment failed because of a **technical glitch on the bank's side** (nothing to do with fraud), the AI's own written reasoning said, in effect, "this looks like a technical issue, not fraud" — and then it still picked "treat this as fraud" as its answer anyway. The gate caught the contradiction immediately, ignored the AI's picked answer, and did the actually-correct thing (retry it) instead. This exact kind of mismatch is *why* the gate exists, not a rare edge case — it happened on 87% of all 150 real subscriptions on the first run, and even after three rounds of finding and fixing real prompt bugs, it still happens on one case out of 150 (down from 46%, then 22% — see `METRICS.md` §2 for exactly which cases and why, at every stage).

---

## Data & simulation — the practice subscriptions we actually test against

**Plain job:** since we don't have real customers' real failed payments to test with, we generate 150 realistic, made-up ones — with a fair, honest mix of situations, not a mix rigged to make the system look good.

**Analogy:** crash-testing a car design against a wide range of made-up accident scenarios, including the unflattering ones, instead of only testing the crash you're confident you'll survive.

**Example:** most of the 150 fake subscriptions fail for common, fixable reasons (expired card, low balance) — but a small deliberate handful are genuinely unfixable (customer cancelled on purpose) or fraud-flagged, so the system actually has to prove it handles the hard cases too, not just the easy majority.

---

## Reporting — what stands in for a live dashboard

**Plain job:** this project doesn't have a live on-screen dashboard — instead, every run produces a plain, honest results file with the real numbers, plus the full diary (Layer 7) behind it.

**Analogy:** a report card instead of a live scoreboard — generated fresh after the fact, but showing exactly what happened, not a polished summary.

**Example:** after running all 150 subscriptions, one file says, plainly: how many were processed, how much money was involved, how many actions actually happened, and — most importantly — how often the AI's first suggestion had to be corrected. Nothing in that file is hand-written after the fact; it's generated directly from the diary (Layer 7) every single run.

---

## Open questions — the honest "here's what's still rough" list

**Plain job:** the stuff that isn't fully solved yet, said out loud on purpose, instead of quietly hoping nobody asks.

**Analogy:** a pre-flight checklist that includes "we haven't tested this in heavy rain yet" — better to know that now than find out mid-flight.

**Example, a few real ones:** the "don't do the same thing twice" safety check (Layer 5) is proven to work in an isolated test, but with 150 different real subscriptions in one run, it never actually gets triggered for real, since nothing repeats — so it's tested, but not battle-tested at scale. Also, the connection to Razorpay's real official toolkit (Layer 6) has been built and directly checked that it starts up correctly, but hasn't yet been run start-to-finish with a real (free) account, since one hasn't been created yet.

---

*Full version of every piece above, with exact tables, real numbers, and the formal reasoning behind each choice: `BUILD_LOG.md`.*

*Companion file: `BUILD_LOG.md` — same pieces, with the "why this and not that" comparisons and the actual measured results from real runs.*
