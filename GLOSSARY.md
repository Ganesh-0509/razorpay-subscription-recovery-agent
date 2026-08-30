# Razorpay AI Buildathon — Glossary / Word Expander

**Purpose:** every acronym or piece of jargon used anywhere in `BUILD_LOG.md` or `EASY_EXPLAINER.md`, expanded in one place. This file is append-only — every time a new term shows up in the project, it gets added here before it gets used anywhere else.

**How to use it:** if you hit an unfamiliar term in either file, look it up here first. Each entry has: the full form (if it's an acronym), a one-line plain-English meaning, and which part of the project it's relevant to.

---

### A

**Agent Studio** — Razorpay's own real, live product (launched March 2026, at an event called FTX'26), built on Anthropic's Claude Agent SDK and exposed via MCP, for building AI agents that operate on payments/business tasks. This project is a small, honest, independently-built version of the same pattern, not an official Razorpay product.

**Audit trail** — a permanent, ordered, append-only record of every decision a system made and why. *Used for:* `logs/audit_log.jsonl` — the project's "black box recorder."

---

### C

**Checkpoint / resume** — saving progress to a file as you go, so an interrupted run can pick up where it left off instead of starting over and redoing finished work. *Used for:* `logs/results_checkpoint.jsonl`, built after a real background run got killed mid-batch twice.

**Claude Agent SDK** — Anthropic's toolkit for building AI agents using their Claude models. Razorpay's real Agent Studio is built on this. This project references it as the pattern being mirrored, but defaults to a free local model (Ollama) instead of the paid Claude API — see `BUILD_LOG.md` §2.2.

**CVV** — Card Verification Value. The 3-digit security code on a card. `incorrect_cvv` is one of Razorpay's real documented decline codes.

---

### D

**Decline code** — the specific, documented reason a payment failed (e.g. `insufficient_funds`, `card_expired`, `payment_risk_check_failed`). Pulled directly from Razorpay's own error-code documentation, not invented. *Used for:* the entire policy table (`decline_codes.py`, `BUILD_LOG.md` §6).

**Decline source** — Razorpay's own tag on *who/what* caused a decline: `customer`, `bank`, `gateway`, or `network`. Useful for deciding whether retrying even makes sense (a `network` glitch is worth retrying; a `customer`-cancelled payment isn't).

**Docker** — software for running a program in an isolated, pre-packaged container, so it runs the same way on any machine without manually installing its dependencies. *Used for:* running Razorpay's official MCP server (`mcp/razorpay` image) locally.

---

### E

**`execute` (gate field)** — whether the gate's final decision actually gets carried out. Only `False` for a hard block (spending cap exceeded, duplicate action) — **not** the same thing as whether the AI's original suggestion was correct (see `llm_matched_policy`). Conflating these two was a real bug caught during development — see `BUILD_LOG.md` §5.2, §12.

---

### G

**Gate** — the plain, deterministic (non-AI) code layer that checks every action the agent wants to take against a fixed policy table and hard safety limits, before anything is allowed to reach Razorpay. The single most important safety component in the project. *Used for:* `gate.py`, `BUILD_LOG.md` §5.

---

### H

**Halted (subscription state)** — what a Razorpay subscription becomes after its automatic 3-day retry cycle (see **T+3**) fails all 3 times. Nothing tries to charge it again automatically after this point — this is exactly the gap this project's agent exists to fill.

**HMAC signature** — a cryptographic stamp attached to a webhook request, proving it genuinely came from Razorpay and wasn't faked by someone else. Checked using a secret key from the Razorpay dashboard. Relevant background for a production version of this system; not exercised directly in the current build.

---

### I

**Idempotency / idempotency key** — a way of tagging a request so that if it accidentally gets sent twice, the system only actually performs the action once, instead of double-acting. *Used for:* one of the gate's three checks (`BUILD_LOG.md` §5.1) — proven correct by a dedicated unit test, though not exercised at scale against the real 150-record dataset since no subscription ID repeats within one run (a known, documented limitation — see `BUILD_LOG.md` §12).

---

### J

**JSONL** ("JSON Lines") — a file format where each line is its own independent, complete JSON object. Easy to append to safely (just add a new line) and easy to read partially without parsing the whole file. *Used for:* `audit_log.jsonl` and `results_checkpoint.jsonl`.

---

### K

**`keep_alive`** — an Ollama setting that tells it to keep a model loaded in memory for a set duration instead of unloading it after every single call. Without this, a real batch run was reloading the ~5GB model from disk on every call (~20 seconds each) and eventually crashed under that churn — fixed during development, see `BUILD_LOG.md` §3.6.

**KYC** — "Know Your Customer," the identity/business verification Razorpay requires before you can accept *real* money (live mode). Not needed for test mode, so not needed anywhere in this project.

---

### L

**Linked Account (Route)** — a sub-account that can receive a portion of a payment via Razorpay's Route feature. A real one requires manual onboarding through the Razorpay dashboard, so this project uses a clearly labeled fake one (`acc_sim_partner001`) by default — see `BUILD_LOG.md` §7.4.

**LLM** — Large Language Model. The general category of AI model used here (specifically, a small local one run via Ollama) to *propose* — never directly execute — a recovery action.

---

### M

**MCP** ("Model Context Protocol") — an open standard for exposing a fixed, well-defined set of "tools" (actions an AI can request) to an AI model, instead of letting it act freely. This project's agent and Razorpay's own official Agent Studio product both use this same standard. *Used for:* `mcp_server.py`, `agent.py`'s tool-calling logic, and — once real keys are set — a direct bridge to Razorpay's own official MCP server (`razorpay_mcp_client.py`).

**`llm_matched_policy` (gate field)** — a pure metric on the AI model's accuracy: did its suggestion match what the policy table says should happen? `False` does not by itself mean nothing happened — see **`execute`**.

---

### O

**Official Razorpay MCP server** — a real MCP server Razorpay itself publishes and maintains (`razorpay/razorpay-mcp-server` on GitHub, Docker image `mcp/razorpay`), exposing 50+ of their own real API operations as agent-callable tools. This project's money-moving tool calls route through this directly once real test-mode keys are set, instead of only ever using a hand-written wrapper — verified by directly starting the real server and listing its tools, not assumed from documentation. Has no Route/transfer tools as of this build (checked directly), so the Route stretch goal still uses Razorpay's SDK directly instead.

**Ollama** — free, open-source software that runs AI models directly on your own computer instead of through a paid cloud API. Used here so the entire project costs $0 to run, with a real tool-calling model (`llama3.1:8b`) already available locally.

**Order (Razorpay)** — a Razorpay object representing "I intend to collect this much money for this reason." Used here to represent a retry attempt on a halted subscription.

---

### P

**Payment Link** — a shareable URL Razorpay generates that lets a customer pay without a full checkout page. *Used for:* the "nudge the customer to fix their payment" recovery action.

**Policy override** — when the gate replaces the AI's suggested action with the correct one from the policy table, because the two didn't match. Happened on 22% of all 150 real subscriptions in the final run (down from 46%, and originally 87%, across two rounds of prompt fixes) — see `BUILD_LOG.md` §9.2.

---

### R

**Retry with backoff** — when a request fails, wait a bit and try again, waiting longer each subsequent failure, instead of giving up immediately or hammering the server nonstop. *Used for:* `ollama_client.py`'s handling of transient failures, added after a real crash during development.

**Route** — Razorpay's split-settlement feature: part of a single payment can be automatically transferred to a second party (a Linked Account) at the same time it's collected, instead of one party getting all of it. *Used for:* this project's stretch goal, `route_demo.py`.

**`rzp_test_` / `rzp_live_`** — the prefixes on Razorpay API keys that mark them as test-mode (fake money, free, no KYC) or live-mode (real money, requires KYC) respectively. This project's code actively refuses to run if it ever detects an `rzp_live_` key — see `BUILD_LOG.md` §7.1.

---

### S

**Settlement** — the process of Razorpay actually transferring collected money to a bank account (as opposed to just having "collected" it). Relevant background for Route (a settlement can be split across multiple recipients).

**Simulate mode** — this project's fallback behavior when no real Razorpay test keys are set: the same code path runs, but returns realistic fake responses instead of calling a real API — so the whole pipeline works for free before a Razorpay account even exists. *Used for:* `razorpay_client.py`.

**Spending cap** — a hard limit (per single action, and per full run) on how much money the gate will ever allow to move, regardless of what any other check concluded. One of the gate's three checks — see `BUILD_LOG.md` §5.1.

**stdio** — "standard input/output," the plain text-in/text-out channel programs normally use. *Used for:* how this project's MCP components (and Razorpay's official MCP server, when connected to directly) communicate.

---

### T

**T+3** — Razorpay's real, documented subscription retry cadence: a failed recurring payment is retried automatically once a day for 3 days after the original charge date, then the subscription becomes **halted** if all 3 fail. The exact gap this entire project's agent is built to fill.

**Test mode** — Razorpay's free practice environment. Fake money, real API behavior, no KYC/business verification needed. API keys start with `rzp_test_`. The only mode this project's code is allowed to run in.

**Tool calling / function calling** — the mechanism where an AI model, instead of just replying with text, says "call this specific function with these specific arguments." *Used for:* the AI's structured `record_decision` proposal — the only tool call the model itself is ever allowed to make directly.

**Track** — one of the five problem categories in the Razorpay AI Buildathon (this project targets **Track 1 — AI Growth & Agentic Commerce**). See `BUILD_LOG.md` §1 for why this track was chosen over the other four.

---

### U

**UPI** — India's real-time bank-to-bank payment system. Mentioned because Razorpay's real Agent Studio/Agentic Payments product features "UPI Reserve Pay" (consent-based, pre-authorized AI-agent payments) — relevant background context, not something this project's own code touches directly.

---

*New terms get appended here as they come up — alphabetically, in the matching letter section.*
