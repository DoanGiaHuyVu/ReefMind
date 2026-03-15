# 🪸 ReefMind

**An autonomous AI research agent that runs continuous experiments in a simulated coral reef ecosystem — discovering intervention strategies to reverse bleaching, restore biodiversity, and fight ocean acidification.**

Built for the **Google GenAI Genesis Hackathon** — Best Sustainability AI Hack challenge.

> *"Reef restoration experiments take 7 years in the real ocean. ReefMind runs 10,000 overnight."*

---

## Table of Contents

- [Inspiration](#inspiration)
- [What It Does](#what-it-does)
- [Architecture](#architecture)
- [How the RL Loop Works](#how-the-rl-loop-works)
- [The World Model](#the-world-model)
- [The AI Agent](#the-ai-agent)
- [Reward Function](#reward-function)
- [The Self-Modifying Research Program](#the-self-modifying-research-program)
- [Dashboard](#dashboard)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Running ReefMind](#running-reefmind)
- [API Reference](#api-reference)
- [Interventions](#interventions)
- [Key Metrics Explained](#key-metrics-explained)
- [Results](#results)
- [Known Issues & Improvements](#known-issues--improvements)
- [Tech Stack](#tech-stack)
- [Hackathon Judging Criteria](#hackathon-judging-criteria)

---

## Inspiration

At a Meta hackathon, a team of computational biologists demonstrated using AI agents to accelerate cancer research. Their approach: instead of training a model on a static dataset, create a simulated biological environment where AI agents run continuous experiments, observe outcomes, and improve through reinforcement learning — a digital researcher that learns from every experiment it runs.

ReefMind applies this exact architecture to one of Earth's most urgent environmental crises: **coral reef collapse**.

- **50% of coral reefs have been lost since 1950**
- **25% of all ocean species depend on reef ecosystems**
- **500 million people rely on reefs for food and coastal protection**
- Real-world reef restoration experiments take 5–20 years and cost millions
- Ocean acidification is listed as a top environmental problem by Earth.org

ReefMind compresses decades of potential research into hours.

---

## What It Does

ReefMind is a three-layer system:

1. **World Model** — A simulated coral reef ecosystem with realistic climate physics: background warming, ocean acidification, DHW (Degree Heating Weeks) heat stress accumulation, aragonite saturation chemistry, and ecological feedback loops.

2. **RL Agent** — A Gemini/LLM-powered AI marine biologist that reads its own evolving research program, forms hypotheses, selects interventions, observes outcomes, and updates its strategy through reinforcement learning signals.

3. **Live Dashboard** — A real-time web interface showing the reef environment as a live pixel-art 2D map, with charts tracking health score, reward curves, an agent reasoning chat feed, and an evolving `program.md` scientific log the agent writes and rewrites itself.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ReefMind System                          │
│                                                             │
│  ┌─────────────────┐    ┌──────────────────┐               │
│  │  Layer 1        │    │  Layer 2         │               │
│  │  World Model    │◄──►│  RL Agent        │               │
│  │                 │    │                  │               │
│  │  ReefSimulator  │    │  agent.py        │               │
│  │  • Climate      │    │  • Gemini LLM    │               │
│  │  • DHW stress   │    │  • Hypothesis    │               │
│  │  • Chemistry    │    │  • Intervention  │               │
│  │  • Ecology      │    │  • program.md    │               │
│  └────────┬────────┘    └────────┬─────────┘               │
│           │                      │                          │
│           └──────────┬───────────┘                          │
│                      │                                      │
│             ┌────────▼────────┐                             │
│             │  Layer 3        │                             │
│             │  Flask API      │                             │
│             │  app.py         │                             │
│             └────────┬────────┘                             │
│                      │                                      │
│             ┌────────▼────────┐                             │
│             │  Live Dashboard │                             │
│             │  index.html     │                             │
│             │  • Reef map     │                             │
│             │  • Charts       │                             │
│             │  • Agent chat   │                             │
│             └─────────────────┘                             │
└─────────────────────────────────────────────────────────────┘
```

---

## How the RL Loop Works

Each experiment cycle follows this sequence:

```
1. READ    → Agent reads current reef state + experiment history
2. THINK   → Agent reads program.md (its own evolving research brief)
3. DECIDE  → Agent forms hypothesis + selects intervention (LLM call 1)
4. ACT     → Simulator applies intervention + advances one time step
5. OBSERVE → New reef state is computed (ecology, chemistry, heat stress)
6. REWARD  → Reward signal computed from state improvement
7. KEEP/DISCARD → Sliding window acceptance: keep if reward ≥ 70% of recent avg
8. LEARN   → Agent rewrites program.md with lessons learned (LLM call 2)
9. REPEAT  → Next cycle uses updated reef state and research program
```

This is reinforcement learning without PyTorch or training — the LLM *is* the policy. The experiment history passed in context at each cycle is the agent's "memory". The `program.md` rewrite is explicit self-modification of strategy.

**Programmatic overrides** prevent exploitation traps:
- If the same intervention dominates 5 consecutive cycles with 0 kept → force `combined`
- If DHW exceeds 1.0 → force `shading` immediately regardless of agent decision

---

## The World Model

`reef_simulator.py` implements a synthetic reef ecosystem. Each call to `apply_intervention()` runs the following pipeline:

### 1. Background climate forcing (every step, regardless of intervention)
```
temperature += 0.0006°C/step (background warming ~0.03°C/year)
               + gaussian noise
               + heatwave spike (8% chance per step, up to +0.8°C)

pH -= 0.00004/step (ocean acidification ~0.02 pH/decade)

water_quality drifts toward baseline 0.45 (pollution creep)
adaptation_score *= 0.999 (tolerance fades without reinforcement)
```

> **Critical**: Without any intervention, DHW reaches 9+ in ~20 steps, triggering mass mortality. The world actively fights back.

### 2. Intervention effects
Applied after forcing — see [Interventions](#interventions) section.

### 3. DHW (Degree Heating Weeks) accumulation
```
hotspot = max(0, temperature - 29°C)  # only accumulates above thermal threshold
DHW = sum of last 12 weekly hotspots  # rolling 12-week window
```
- DHW > 4: bleaching risk begins
- DHW > 8: coral mortality begins

### 4. Ecological response
```
bleaching_risk  = sigmoid((DHW - 4) / 1.2)
mortality_risk  = sigmoid((DHW - 8) / 1.2)
susceptibility  = 1.0 + 0.70*(1-water_quality) + 0.35*OA_stress - 0.50*adaptation

bleaching_increase = 10.0 * bleaching_risk * susceptibility
passive_recovery   = 2.2 * water_quality * (1 + 0.8*adapt) * (omega/3.5) * coral_cover
                     [ONLY when DHW < 2.0]

coral_growth    = f(calcification, recruitment, cover headroom)
dissolution     = 0.35 * max(0, 3.0 - omega_arag)
mortality_loss  = 1.4 * mortality_risk * susceptibility * (0.4 + bleaching/100)
```

### 5. Chemistry
```
omega_arag = clamp(3.6 + 5.0 * (pH - 8.1), 1.0, 5.0)
```
Low omega_arag impairs calcification (coral skeleton building) and recruitment.

---

## The AI Agent

`agent.py` makes **two LLM calls** per cycle, separated to prevent JSON parsing failures from markdown-in-JSON escaping issues:

### Call 1 — Decision (returns compact JSON)
Sends the full reef state, last 6 experiment results, and the current `program.md` to the LLM. Returns:
```json
{
  "hypothesis": "one sentence prediction",
  "intervention": "exact_intervention_name",
  "intensity": 0.75,
  "reasoning": "two sentences referencing DHW, omega, water_quality"
}
```

### Call 2 — Research program rewrite (returns raw markdown)
After the experiment runs, the agent rewrites `program.md` to:
- Consolidate redundant findings (max 15 bullet points)
- Update current best result if improved
- Add/remove/update research rules based on what worked
- Mark hypotheses as CONFIRMED / REJECTED / IN PROGRESS
- Write a new "Next priority" section based on current metrics

The agent can **add and remove its own rules**, retire disproven hypotheses, and change strategic direction. Over 100+ cycles, `program.md` becomes a document the AI fully authored — the most compelling demo artifact.

### Models supported
The agent is configurable via `OPENROUTER_MODEL` environment variable (when using OpenRouter):

| Model | Notes |
|---|---|
| `meta-llama/llama-3.3-70b-instruct` | Recommended default — fast, reliable JSON |
| `deepseek/deepseek-chat-v3-0324:free` | Free tier, strong reasoning |
| `google/gemma-3-27b-it:free` | Original model, free but rate-limited |
| `anthropic/claude-3.5-haiku` | Best JSON reliability |
| `anthropic/claude-sonnet-4-5` | Strongest program.md rewrites |

---

## Reward Function

`reward.py` implements an **adaptive reward function** that shifts weights as metrics saturate:

```python
# Weights adapt based on how much headroom each metric has
dhw_weight    = 0.05 + 0.25 * (dhw / 4.0)            # high when DHW is dangerous
bleach_weight = 0.15 + 0.20 * (bleaching / 65.0)      # high when bleaching is severe
omega_weight  = 0.10 + 0.15 * ((3.5 - omega) / 0.9)   # high when far from target
wq_weight     = 0.05 + 0.15 * ((0.8 - wq) / 0.35)     # high when water quality is low
cover_weight  = 0.10  # constant
species_weight = 0.10 # constant
# All weights normalised to sum to 1.0
```

**Why adaptive?** Static weights depressed rewards once DHW was controlled (DHW = 0 → 0 contribution from 30% of the function). The adaptive version redistributes weight to the metrics that actually have room to improve.

### Health Score (0–100)
A separate composite score for dashboard display, tracking long-run reef progress:

| Component | Max pts | Target |
|---|---|---|
| Bleaching reduction | 30 | 0% bleaching |
| DHW control | 20 | DHW < 1 |
| omega_arag | 15 | 3.5 |
| Water quality | 15 | 0.8+ |
| Coral cover | 10 | 60%+ |
| Species count | 10 | 35+ |

### Keep / Discard (sliding window RL)
```python
# Accept experiment if reward beats 70% of last 5 kept experiments
kept_avg = mean(last_5_kept_rewards)
threshold = max(-0.02, kept_avg * 0.5)
kept = (reward >= threshold)

# If kept: advance reef state from this experiment
# If discarded: revert to last accepted state
```

---

## The Self-Modifying Research Program

`program.md` is the most distinctive feature inspired by [Karpathy's autoresearch](https://github.com/karpathy/autoresearch). Unlike autoresearch where the agent modifies training code, ReefMind's agent modifies its own **research strategy document**.

### Structure
```markdown
# ReefMind Research Program

## Mission        ← FROZEN — set by human, never changed by agent
## Current best result   ← agent updates when metrics improve
## Known findings        ← agent consolidates, max 15 bullet points
## Research rules        ← agent can ADD and REMOVE rules
## Hypotheses to test    ← agent marks CONFIRMED / REJECTED / IN PROGRESS
## Next priority         ← agent rewrites each cycle
```

### What the agent learns to write
After 50+ cycles, `program.md` typically contains agent-invented rules like:
- *"pollution_reduction at 0.75 consistently improves water_quality without hindering omega_arag"*
- *"combined intervention shows synergy — reward 0.302 vs 0.08 for single interventions"*
- *"alkalinity_enhancement yields diminishing returns after omega_arag exceeds 2.9"*

These are emergent discoveries — not hardcoded, written entirely by the agent from observing experiment outcomes.

---

## Dashboard

The live dashboard at `http://localhost:5000` has six main sections:

### Live reef environment (top-left)
A pixel-art 2D canvas rendering of the coral reef. Visual elements that change in real time:
- **Coral color**: transitions from vibrant orange/purple/teal → bleached white as `bleaching_pct` increases
- **Water color**: shifts from cool deep blue → warm orange tint as `temperature_c` and DHW rise
- **Fish population**: fish appear/disappear based on `species_count` (0 fish at 1 species → 8 fish at 35+)
- **Coral cover**: plate coral physically scales with `coral_cover_pct`
- **Water clarity**: light ray opacity increases with `water_quality`
- **HUD overlay**: real-time DHW / bleaching / omega / water quality indicators with traffic-light colors

### Environment state grid (below reef)
8 live metric cards with mini bar charts: bleaching, DHW, pH, omega_arag, temperature, water quality, adaptation score, coral cover.

### Metric cards (top-right)
4 primary KPIs: health score, bleaching, DHW stress, best reward — each showing delta from baseline.

### Charts
- **Health score over time**: line chart with 38.6 baseline reference
- **RL reward curve**: bar chart colored green (high reward) → red (negative reward)

### Agent reasoning chat feed (bottom-center)
A live chat-style feed showing the agent's internal monologue each cycle:
- Color-coded by intervention type
- Shows full hypothesis (main text) + reasoning (secondary detail)
- Status tags: `✓ kept`, `↩ discarded`, `⚡ override`
- Typing indicator (animated dots) while waiting for next LLM call
- Auto-scrolls, caps at 40 messages

### Research program viewer (bottom-right)
Live view of `program.md` with syntax highlighting. Updates every 30 seconds.

### Controls
| Button | Action |
|---|---|
| **Run ∞** | Start agent running forever in background thread |
| **Run N ↗** | Run exactly N cycles, then show results popup |
| **Stop ■** | Stop gracefully after current cycle completes |
| **+1** | Trigger a single manual cycle |
| **↺ Reset** | Stop run, delete all data, reopen setup screen |
| **⚙ Setup** | Opens configuration modal (locked while running) |

### End-of-run popup
When a finite N-cycle run completes, a modal shows:
- Summary cards: peak health, final bleaching, best reward, acceptance rate
- Top 4 discoveries ranked by reward with cycle/intervention details
- Auto-generated next-step recommendations based on final reef state

---

## Project Structure

```
reefmind/
├── app.py                  # Flask server — API endpoints + background runner
├── agent.py                # LLM agent — decision making + program.md rewriter
├── reef_simulator.py       # World model — synthetic reef ecosystem physics
├── reward.py               # RL reward function + health score calculator
├── run_experiment.py       # CLI runner — run cycles from terminal
├── program.md              # Agent's evolving research brief (auto-rewritten)
├── experiments.json        # Full experiment history (auto-generated)
├── config.json             # Initial reef configuration from setup modal
├── .env                    # API keys (never commit)
│
└── templates/
    └── index.html          # Full dashboard (all-in-one HTML/CSS/JS)
```

---

## Setup & Installation

### Prerequisites
- Python 3.10+
- A Gemini API key (Google AI Studio) **or** an OpenRouter API key

### 1. Clone and create virtual environment
```bash
git clone https://github.com/yourname/reefmind.git
cd reefmind
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install flask google-generativeai python-dotenv openai
```

### 3. Configure API keys

**Option A — Gemini (default `agent.py`)**
```bash
# .env
GEMINI_API_KEY=your_key_here
```

**Option B — OpenRouter (swap to `agent_openrouter.py`)**
```bash
# .env
OPENROUTER_API_KEY=your_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct
```

Then rename `agent_openrouter.py` → `agent.py`.

### 4. Create the templates folder
```bash
mkdir -p templates
# Place index.html inside templates/
```

---

## Running ReefMind

### Option A — Web dashboard (recommended)
```bash
python app.py
```
Open `http://localhost:5000`. Use the dashboard controls to configure and run experiments.

### Option B — Terminal only
```bash
python run_experiment.py
```
Runs 50 cycles by default. Edit the last line to change:
```python
run_cycles(num_cycles=100)
```

### Option C — Both simultaneously
Run the CLI agent overnight to accumulate data, while the dashboard displays live results:
```bash
# Terminal 1
python app.py

# Terminal 2
python run_experiment.py
```

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `GET /` | GET | Serve dashboard HTML |
| `GET /experiments` | GET | Full experiment history + summary stats |
| `GET /program` | GET | Current `program.md` content |
| `GET /runner-status` | GET | Background runner state (running/completed/status) |
| `POST /run` | POST | Run one cycle manually |
| `POST /start` | POST | Start background runner. Body: `{"cycles": N, "delay": 1.5}` |
| `POST /stop` | POST | Stop background runner gracefully |
| `POST /configure` | POST | Set initial reef state from setup modal |
| `POST /reset` | POST | Stop runner, delete experiments.json, reset program.md |
| `GET /health-check` | GET | Liveness check |

### `/start` body parameters
```json
{
  "cycles": 50,    // null = run forever
  "delay": 1.5     // seconds between cycles (respects rate limits)
}
```

---

## Interventions

Five interventions are available to the agent:

| Intervention | Primary effect | Secondary effects |
|---|---|---|
| `shading` | −1.6% bleaching, −0.45°C temp | Reduces DHW accumulation |
| `alkalinity_enhancement` | +0.012 pH, +omega_arag | −0.4% bleaching |
| `pollution_reduction` | +0.10 water_quality | −0.7% bleaching, +coral cover |
| `assisted_evolution` | +0.05 adaptation_score | +coral cover, +species |
| `combined` | All pathways simultaneously | −2.0% bleaching, +0.010 pH, +0.08 wq, +0.04 adapt, +0.50% cover, +0.8 species |

All effects use `intensity` as a multiplier (0.0–1.0, default 0.75) with Gaussian noise for realism.

**`combined` does not have a magical synergy bonus** — the synergy is emergent from simultaneously addressing multiple limiting factors.

---

## Key Metrics Explained

| Metric | Healthy | Dangerous | What it means |
|---|---|---|---|
| `bleaching_pct` | < 20% | > 70% | % of coral actively bleaching |
| `dhw` | < 2 | > 8 | Accumulated heat stress (12-week rolling) |
| `temperature_c` | < 28°C | > 30°C | Water temperature |
| `ph` | 8.1–8.3 | < 7.8 | Ocean acidity |
| `omega_arag` | > 3.5 | < 2.0 | Aragonite saturation — skeleton building capacity |
| `water_quality` | > 0.8 | < 0.3 | Resilience / disease resistance / recruitment |
| `adaptation_score` | > 0.5 | < 0.15 | Genetic heat tolerance of coral population |
| `coral_cover_pct` | > 60% | < 10% | % of reef covered by living coral |
| `species_count` | 35+ | < 5 | Biodiversity index |

---

## Results

After 150 cycles starting from a severely degraded reef (baseline health 38.6/100):

| Metric | Baseline | Best achieved | Change |
|---|---|---|---|
| Health score | 38.6 | **67.7** | +75% |
| Bleaching | 65% | 38.7% | −41% |
| Water quality | 0.45 | 0.886 | +97% |
| DHW | 0.0 | 0.0 | Controlled ✓ |
| omega_arag | 2.6 | 2.95 | +13% |
| Species count | 18 | 28 | +56% |
| Coral cover | 22% | 34.4% | +56% |

**Key discovery from `program.md`**: The agent independently discovered a two-phase strategy — first rebuild resilience infrastructure (water quality, DHW control, omega) before attacking bleaching directly. This sequencing was not hardcoded; the agent derived it from observing experiment outcomes over 50+ cycles.

---

## Known Issues & Improvements

### Critical bugs (to fix before production)
1. **Resume state** — Both `app.py` and `run_experiment.py` resume from the *highest-reward* cycle instead of the *last-kept* cycle. This can reset the simulator to ancient conditions. Fix: use `last(kept_entries)` instead of `max(reward)`.

2. **Canvas redraw** — `updateReef()` updates data but doesn't call `drawReef()`. Coral color changes only render if the rAF loop is running. Fix: call `if (!rafId) drawReef()` at end of `updateReef()`.

3. **config.json ignored by CLI** — `run_experiment.py` never reads `config.json`, so setup modal configuration only affects the Flask-run agent. Fix: check for `config.json` in `run_cycles()`.

### Medium improvements
4. **Reward weight saturation** — Static weights depress rewards once DHW and water quality are controlled. Implemented adaptive weights in latest `reward.py` — deploy this version.

5. **applyTheme thresholds** — Starts in red "bad" theme at baseline. Thresholds should be `<44 / <58 / ≥58` instead of `<40 / <62 / ≥62`.

6. **Temperature water color** — Canvas water color doesn't respond to `temperature_c`. Should warm to orange-red during heatwave events.

7. **DHW hotspot history** — Not restored on resume. Fix: back-fill `_hotspot_history` from saved DHW value.

8. **species_count** missing from environment grid cards.

---

## Tech Stack

| Layer | Technology |
|---|---|
| World model | Python — custom reef ecosystem simulator |
| AI agent | Google Gemini API / OpenRouter (any OpenAI-compatible model) |
| RL loop | Custom sliding-window keep/discard with adaptive reward |
| Self-modification | LLM rewrites `program.md` as raw markdown each cycle |
| Backend | Flask (Python) — threaded background runner |
| Frontend | Vanilla HTML/CSS/JS — no framework |
| Charts | Chart.js 4.4 |
| Reef animation | HTML5 Canvas — pixel-art 2D rendering with rAF loop |
| Fonts | Space Grotesk + JetBrains Mono |

---

## Hackathon Judging Criteria

### Innovation & Originality (×2.5)
ReefMind applies the cancer-research AI agent architecture from the Meta hackathon to coral reef ecology. The framing — "AI digital researcher discovering interventions" rather than "AI predicting reef health" — is novel. The self-modifying `program.md` inspired by Karpathy's autoresearch is the key differentiator: the agent writes its own evolving scientific brief.

### Technical Complexity & Execution (×3.0)
Real agentic system with: multi-step LLM calls passing full experiment history in context, a physics-based world model with DHW accumulation and ecological feedback, adaptive reward function, sliding-window RL keep/discard, and programmatic override logic. Not a wrapper — a real research loop.

### Product Experience & Design (×2.0)
Live pixel-art reef that visually responds to every experiment cycle. Agent reasoning feed showing the AI's hypothesis and logic in plain language. Color-coded intervention history. End-of-run results popup with auto-generated recommendations. Setup → run → reset user flow.

### Impact & Practical Value (×2.5)
One finding from simulation that would take 7 years to discover in the ocean. The agent discovered the correct two-phase recovery sequence (resilience first, then bleaching) without being told. Output is a `program.md` of AI-authored scientific insights that could inform real reef restoration strategy decisions.

---

## License

MIT

---

*Built in one night at GenAI Genesis 2026 — by an AI agent and a human who kept debugging it at 3 AM.*