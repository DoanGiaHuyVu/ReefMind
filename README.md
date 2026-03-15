# 🪸 ReefMind

**An autonomous AI research agent that runs continuous experiments in a simulated coral reef ecosystem — discovering intervention strategies to reverse bleaching, restore biodiversity, and fight ocean acidification.**

Built for the **Google GenAI Genesis Hackathon** — Best Sustainability AI Hack challenge.

> *"Reef restoration experiments take 7 years in the real ocean. ReefMind runs 10,000 overnight."*

---

## Results First

After 150 cycles starting from a severely degraded reef:

| Metric | Baseline | Final | Change |
|---|---|---|---|
| **Health score** | 38.6 / 100 | **98.1 / 100** | **+154%** |
| **Bleaching** | 65.0% | **0.0%** | **−100%** |
| **Coral cover** | 22.0% | **78.0%** | **+255%** |
| **Species count** | 18 | **44** | **+144%** |
| **pH** | 7.9 | **8.35** | In healthy range |
| **omega_arag** | 2.6 | **4.83** | Above target (3.5) |
| **water_quality** | 0.45 | **0.921** | Near maximum |
| **adaptation_score** | 0.15 | **0.925** | Near maximum |
| **DHW heat stress** | 0.0 | **0.35** | Fully controlled |

Health milestones: 50 → cycle 1, 70 → cycle 30, 90 → cycle 73, **99 → cycle 90**.
115 out of 150 cycles kept (77% acceptance rate).

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
- [Code Changes & Bug Fixes](#code-changes--bug-fixes)
- [Known Remaining Issues](#known-remaining-issues)
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

2. **RL Agent** — A Gemini-powered AI marine biologist that reads its own evolving research program, forms hypotheses, selects interventions, observes outcomes, and updates its strategy through reinforcement learning signals. It also rewrites its research program every cycle.

3. **Live Dashboard** — A real-time web interface showing the reef as a live pixel-art 2D map, with charts tracking health score and reward curves, an agent reasoning chat feed showing the AI's live thinking, and the evolving `program.md` scientific log the agent writes itself.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ReefMind System                          │
│                                                             │
│  ┌─────────────────┐    ┌──────────────────┐                │
│  │  Layer 1        │    │  Layer 2         │                │
│  │  World Model    │◄──►│  RL Agent        │                │
│  │                 │    │                  │                │
│  │  ReefSimulator  │    │  agent.py        │                │
│  │  • Climate      │    │  • Gemini LLM    │                │
│  │  • DHW stress   │    │  • Hypothesis    │                │
│  │  • Chemistry    │    │  • Intervention  │                │
│  │  • Ecology      │    │  • program.md    │                │
│  └────────┬────────┘    └────────┬─────────┘                │
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
│             │  • Pixel reef   │                             │
│             │  • Charts       │                             │
│             │  • Agent chat   │                             │
│             └─────────────────┘                             │
└─────────────────────────────────────────────────────────────┘
```

---

## How the RL Loop Works

Each experiment cycle follows this sequence:

```
1. READ       → Agent reads current reef state + last 6 experiment results
2. THINK      → Agent reads program.md (its own evolving research brief)
3. DECIDE     → Agent forms hypothesis + selects intervention (LLM call 1)
4. ACT        → Simulator applies intervention + advances one time step
5. OBSERVE    → New reef state computed (ecology, chemistry, heat stress)
6. REWARD     → Adaptive reward signal computed from state improvement
7. KEEP/DISC  → Sliding window: keep if reward ≥ 50% of recent kept avg
8. LEARN      → Agent rewrites program.md with lessons learned (LLM call 2)
9. REPEAT     → Next cycle uses updated reef state and research program
```

**Programmatic overrides** prevent exploitation traps:
- If the same intervention dominates 5 consecutive cycles with 0 kept → force `combined`
- If DHW exceeds 1.0 → force `shading` immediately regardless of agent decision

---

## The World Model

`reef_simulator.py` implements a synthetic reef ecosystem. Each call to `apply_intervention()` runs four steps:

### 1. Background climate forcing (every step, regardless of intervention)
```
temperature += 0.0006°C/step (background warming ~0.03°C/year)
               + gaussian noise
               + heatwave spike (8% chance per step, up to +0.8°C)

pH -= 0.00004/step (ocean acidification ~0.02 pH/decade)

water_quality drifts toward baseline 0.45 (pollution creep)
adaptation_score *= 0.999 (tolerance fades without reinforcement)
```

> **Critical**: Without any intervention, DHW reaches dangerous levels in ~20 steps, triggering mass bleaching. The world actively degrades every cycle.

### 2. Intervention effects
Applied after forcing — see [Interventions](#interventions) section.

### 3. DHW accumulation
```
hotspot = max(0, temperature - 29°C)   # only above thermal threshold
DHW     = sum of last 12 weekly hotspots  # rolling 12-week window
```
DHW > 4: bleaching risk. DHW > 8: coral mortality.

### 4. Ecological response
```
bleaching_risk  = sigmoid((DHW - 4) / 1.2)
susceptibility  = 1.0 + 0.70*(1-wq) + 0.35*OA_stress - 0.50*adapt
passive_recovery = 2.2 * wq * (1+0.8*adapt) * (omega/3.5) * coral_cover
                   [ONLY when DHW < 2.0]
```

### 5. Chemistry
```
omega_arag = clamp(3.6 + 5.0 * (pH - 8.1), 1.0, 5.0)
```

---

## The AI Agent

`agent.py` makes **two LLM calls** per cycle, deliberately separated to prevent JSON parse failures from markdown-in-JSON escaping:

### Call 1 — Decision (compact JSON)
```json
{
  "hypothesis": "one sentence prediction",
  "intervention": "exact_intervention_name",
  "intensity": 0.75,
  "reasoning": "two sentences referencing DHW, omega, water_quality"
}
```

### Call 2 — Research program rewrite (raw markdown)
After the experiment runs, the agent rewrites `program.md` to consolidate findings, update rules, mark hypotheses, and set next priority. The agent can add and remove its own rules. Over 150 cycles, `program.md` becomes a document the AI fully authored.

---

## Reward Function

`reward.py` uses **adaptive weights** that shift as metrics saturate — a critical fix from the original static weights:

```python
# Each weight scales with remaining headroom toward its target
dhw_headroom    = min(1.0, dhw_after / 4.0)
omega_headroom  = max(0.0, (3.5 - omega_after) / 0.9)
wq_headroom     = max(0.0, (0.8 - wq_after) / 0.35)
bleach_headroom = min(1.0, bleaching_after / 65.0)

raw = {
    "dhw":     0.05 + 0.25 * dhw_headroom,
    "bleach":  0.15 + 0.20 * bleach_headroom,
    "omega":   0.10 + 0.15 * omega_headroom,
    "wq":      0.05 + 0.15 * wq_headroom,
    "cover":   0.10,
    "species": 0.10,
}
# Normalised to sum to 1.0
```

### Health Score (0–100)

| Component | Max pts | Final value |
|---|---|---|
| Bleaching reduction | 30 | 30.0 (bleaching 0%) |
| DHW control | 20 | 19.3 (DHW 0.35) |
| omega_arag | 15 | 15.0 (omega 4.83) |
| Water quality | 15 | 15.0 (wq 0.921) |
| Coral cover | 10 | 10.0 (cover 78%) |
| Species count | 10 | 10.0 (species 44) |
| **Total** | **100** | **98.1** |

### Keep / Discard
```python
threshold = max(-0.02, mean(last_5_kept_rewards) * 0.5)
kept = (reward >= threshold)
```

---

## The Self-Modifying Research Program

`program.md` is the most distinctive feature, inspired by [Karpathy's autoresearch](https://github.com/karpathy/autoresearch). The agent rewrites it every cycle — adding rules it discovers, removing ones that are wrong, changing strategic direction.

### Structure
```markdown
## Mission          ← FROZEN — set by human, never changed by agent
## Current best result   ← agent updates when metrics improve
## Known findings        ← agent consolidates, max 15 bullets
## Research rules        ← agent can ADD and REMOVE rules
## Hypotheses to test    ← CONFIRMED / REJECTED / IN PROGRESS
## Next priority         ← agent rewrites every cycle
```

### Agent-written rules after 150 cycles (selected)
- *"Given stable DHW (<1.0) and omega_arag > 2.8, prioritize assisted_evolution"*
- *"Following pollution_reduction, implement a single cycle of alkalinity_enhancement"*
- *"If adaptation_score > 0.8, consider reducing intervention frequency to observe natural fluctuations"*
- *"If DHW < 1.0 for 2 consecutive cycles, monitor for passive recovery of coral cover"*

### Confirmed hypotheses (agent-validated)
- ✓ Raising adaptation_score above 0.3 meaningfully reduces bleaching susceptibility
- ✓ pollution_reduction followed by alkalinity_enhancement amplifies both metrics
- ✓ High adaptation_score buffers against minor DHW fluctuations
- ✓ pollution_reduction focused strategy, given stable DHW, significantly improves reef health

---

## Dashboard

### Live reef environment
Pixel-art 2D canvas that changes every cycle:
- Coral color: vivid → bleached white as `bleaching_pct` rises
- Water color: cool blue → warm orange as temperature and DHW climb  
- Fish count: tracks `species_count` (18 → 44 in final run)
- Coral cover: plate coral scales with `coral_cover_pct`
- Water clarity: light rays respond to `water_quality`

### Controls
| Button | Action |
|---|---|
| **Run ∞** | Run forever in background thread |
| **Run N ↗** | Run exactly N cycles, show results popup |
| **Stop ■** | Stop after current cycle |
| **+1** | One manual cycle |
| **↺ Reset** | Stop, delete data, reopen setup |
| **⚙ Setup** | Configure initial reef (locked while running) |

### End-of-run popup
Fires automatically when a finite run completes. Shows top 4 discoveries, summary stats, and auto-generated next-step recommendations based on final reef state.

---

## Project Structure

```
reefmind/
├── app.py                  # Flask server — API + background runner
├── agent.py                # LLM agent — decisions + program.md rewriter
├── reef_simulator.py       # World model — reef ecosystem physics
├── reward.py               # Adaptive reward function + health score
├── run_experiment.py       # CLI runner
├── program.md              # Agent's evolving research brief
├── experiments.json        # Experiment history (auto-generated)
├── config.json             # Initial reef config from setup modal
├── .env                    # API keys
└── templates/
    └── index.html          # Full dashboard (all-in-one)
```

---

## Setup & Installation

```bash
git clone https://github.com/yourname/reefmind.git
cd reefmind
python -m venv .venv
source .venv/bin/activate
pip install flask google-generativeai python-dotenv openai
```

**`.env` for Gemini:**
```
GEMINI_API_KEY=your_key_here
```

**`.env` for OpenRouter:**
```
OPENROUTER_API_KEY=your_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct
```

---

## Running ReefMind

```bash
# Web dashboard
python app.py
# Open http://localhost:5000

# Terminal only
python run_experiment.py

# Both simultaneously (dashboard + overnight CLI run)
python app.py          # terminal 1
python run_experiment.py  # terminal 2
```

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `GET /` | GET | Serve dashboard |
| `GET /experiments` | GET | Full history + summary stats |
| `GET /program` | GET | Current `program.md` |
| `GET /runner-status` | GET | Runner state |
| `POST /run` | POST | Run one cycle |
| `POST /start` | POST | Start runner. Body: `{"cycles": N, "delay": 1.5}` |
| `POST /stop` | POST | Stop runner |
| `POST /configure` | POST | Set initial reef state |
| `POST /reset` | POST | Stop, delete data, reset program.md |
| `GET /health-check` | GET | Liveness check |

---

## Interventions

| Intervention | Primary effect | Per-cycle magnitude |
|---|---|---|
| `shading` | −temp, −bleaching | −0.45°C, −1.6% bleaching |
| `alkalinity_enhancement` | +pH, +omega_arag | +0.012 pH |
| `pollution_reduction` | +water_quality | +0.10 wq |
| `assisted_evolution` | +adaptation_score | +0.05 adapt |
| `combined` | All pathways | −2.0% bleaching, all metrics |

In the final run, the agent's emergent strategy was: `alkalinity_enhancement` (52×) and `pollution_reduction` (46×) as the primary pair, cycling between them to simultaneously raise omega_arag and water_quality — unlocking passive reef recovery.

---

## Key Metrics Explained

| Metric | Healthy | Dangerous | Final |
|---|---|---|---|
| `bleaching_pct` | < 20% | > 70% | **0.0%** |
| `dhw` | < 2 | > 8 | **0.35** |
| `temperature_c` | < 28°C | > 30°C | **28.89°C** |
| `ph` | 8.1–8.3 | < 7.8 | **8.35** |
| `omega_arag` | > 3.5 | < 2.0 | **4.83** |
| `water_quality` | > 0.8 | < 0.3 | **0.921** |
| `adaptation_score` | > 0.5 | < 0.15 | **0.925** |
| `coral_cover_pct` | > 60% | < 10% | **78.0%** |
| `species_count` | 35+ | < 5 | **44** |

---

## Code Changes & Bug Fixes

All critical bugs identified during development were fixed before final submission:

**Resume state** — both `app.py` and `run_experiment.py` now resume from the last *kept* entry, not the highest-reward entry:
```python
kept = [e for e in history if e.get("kept", False)]
best_entry = kept[-1] if kept else history[-1]
```

**DHW hotspot history** — restored on resume to prevent a blank 12-week window:
```python
approx_hotspot = restored_dhw / 12.0 if restored_dhw > 0 else weekly_hotspot
sim._hotspot_history = deque([approx_hotspot] * 12, maxlen=12)
```

**config.json** — read by both `app.py` and `run_experiment.py` so setup modal applies to CLI runs.

**Adaptive reward weights** — replaced static weights so the reward signal stays meaningful after DHW and water quality reach their targets.

---

## Known Remaining Issues

- Canvas `updateReef()` doesn't call `drawReef()` explicitly — coral colors rely on the rAF loop already running
- `applyTheme()` thresholds are fixed numbers rather than relative to baseline health
- Water temperature doesn't yet affect pixel art water color
- `species_count` not shown in the environment state grid cards

---

## Tech Stack

| Layer | Technology |
|---|---|
| World model | Python — custom reef simulator |
| AI agent | Google Gemini API (`gemma-3-27b-it`) / OpenRouter |
| RL loop | Custom sliding-window keep/discard, adaptive reward |
| Self-modification | LLM rewrites `program.md` raw markdown each cycle |
| Backend | Flask — threaded background runner, 9 endpoints |
| Frontend | Vanilla HTML/CSS/JS |
| Charts | Chart.js 4.4 |
| Reef animation | HTML5 Canvas pixel-art with rAF loop |
| Fonts | Space Grotesk + JetBrains Mono |
| Storage | JSON flat files |

---

## Hackathon Judging Criteria

**Innovation & Originality (×2.5)** — The framing is the differentiator: an AI agent that *discovers* restoration strategies, not one that predicts reef health. The self-modifying `program.md` means the agent improves its own research strategy over time. After 150 cycles, the brief contains 14 rules the agent invented and validated itself.

**Technical Complexity (×3.0)** — Real agentic system: two-call LLM architecture, physics-based world model (DHW accumulation, carbonate chemistry, ecological feedback), adaptive reward function, sliding-window RL, programmatic override logic, Flask background threading. All critical bugs fixed in final version.

**Product Experience (×2.0)** — Pixel-art reef that responds to every cycle, agent reasoning chat feed with typing indicator, end-of-run results popup, setup → run → reset flow with setup locked during active runs.

**Impact & Practical Value (×2.5)** — Reached 0% bleaching, 78% coral cover, 44 species in 150 cycles from a severely degraded baseline. The agent independently discovered the correct two-phase strategy: build resilience first, attack bleaching second. All five interventions are techniques trialled at real reef restoration sites today.

---

## License

MIT

---

*Built overnight at GenAI Genesis 2026 — health score 38.6 → 99.9.*
