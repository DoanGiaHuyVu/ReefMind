import json
import os
import threading
import time
from collections import deque

from flask import Flask, jsonify, render_template, request

from reef_simulator import ReefSimulator
from agent import get_agent_decision
from reward import compute_reward, compute_health_score

app = Flask(__name__)

RESULTS_FILE = "experiments.json"
PROGRAM_FILE = "program.md"

# ── Runner state ──────────────────────────────────────────────────────────────
_runner = {
    "running": False,
    "thread": None,
    "target_cycles": None,   # None = run forever
    "completed": 0,
    "status": "idle",        # idle | running | stopped | done | error
    "last_error": None,
}
_run_lock = threading.Lock()


def load_history():
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE) as f:
            return json.load(f)
    return []


def save_history(history):
    with open(RESULTS_FILE, "w") as f:
        json.dump(history, f, indent=2)


def run_one_cycle():
    """Runs a single experiment cycle. Returns the result dict."""
    history = load_history()
    sim = ReefSimulator()

    if history:
        kept = [e for e in history if e.get("kept", False)]
        best_entry = kept[-1] if kept else history[-1]
        sim.state = dict(best_entry["state_after"])
        sim.state["time_step"] = len(history)
        best_reward = best_entry["reward"]

        # Restore DHW history context (approximate — back-fill 12-week buffer)
        restored_temp = sim.state.get("temperature_c", 29.5)
        restored_dhw  = sim.state.get("dhw", 0.0)
        weekly_hotspot = max(0.0, restored_temp - (sim.mmm_c + 1.0))
        approx_hotspot = restored_dhw / 12.0 if restored_dhw > 0 else weekly_hotspot
        sim._hotspot_history = deque([approx_hotspot] * 12, maxlen=12)
    else:
        # Use custom config if present
        if os.path.exists("config.json"):
            with open("config.json") as f:
                cfg = json.load(f)
            sim.state.update({k: v for k, v in cfg.items() if k in sim.state})
            sim.state["omega_arag"] = sim._omega_from_ph(sim.state["ph"])
            sim.state["time_step"] = 0
        best_reward = -float("inf")

    state_before = sim.get_state()

    try:
        decision = get_agent_decision(state_before, history)
    except Exception as e:
        decision = {
            "hypothesis": "Fallback after API error.",
            "intervention": "combined",
            "intensity": 0.75,
            "reasoning": str(e),
        }

    # Programmatic override
    if len(history) >= 5:
        last5 = [e["intervention"] for e in history[-5:]]
        last5_kept = sum(1 for e in history[-5:] if e.get("kept", False))
        dominant = max(set(last5), key=last5.count)
        if dominant in ("alkalinity_enhancement", "assisted_evolution") and last5_kept == 0:
            decision["intervention"] = "combined"
            decision["hypothesis"] = "Override: forcing combined to break exploitation trap."
        dhw = state_before.get("dhw", 0.0)
        if dhw > 1.0:
            decision["intervention"] = "shading"
            decision["hypothesis"] = f"Override: DHW={dhw} rising — forcing shading."

    state_after = sim.apply_intervention(
        decision["intervention"], float(decision["intensity"])
    )
    reward = compute_reward(state_before, state_after)
    health = compute_health_score(state_after)

    kept_history = [e for e in history if e.get("kept", False)]
    if len(kept_history) >= 5:
        recent_avg = sum(e["reward"] for e in kept_history[-5:]) / 5
        threshold = max(-0.02, recent_avg * 0.5)
    else:
        threshold = -0.05

    kept = reward >= threshold

    result = {
        "cycle": len(history) + 1,
        "hypothesis": decision["hypothesis"],
        "reasoning": decision.get("reasoning", ""),
        "intervention": decision["intervention"],
        "intensity": decision["intensity"],
        "state_before": state_before,
        "state_after": state_after,
        "reward": reward,
        "health_score": health,
        "kept": kept,
    }
    history.append(result)
    save_history(history)
    return result


def _background_runner(target_cycles, delay):
    """Runs in a background thread. target_cycles=None means run until stopped."""
    _runner["running"] = True
    _runner["status"] = "running"
    _runner["completed"] = 0

    try:
        while _runner["running"]:
            if target_cycles is not None and _runner["completed"] >= target_cycles:
                _runner["status"] = "done"
                break

            with _run_lock:
                run_one_cycle()

            _runner["completed"] += 1

            # Interruptible sleep
            for _ in range(int(delay * 10)):
                if not _runner["running"]:
                    break
                time.sleep(0.1)

        if _runner["running"]:
            _runner["status"] = "done"
    except Exception as e:
        _runner["status"] = "error"
        _runner["last_error"] = str(e)
    finally:
        _runner["running"] = False


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/experiments")
def get_experiments():
    history = load_history()
    if not history:
        return jsonify({"experiments": [], "summary": {}})

    rewards = [e["reward"] for e in history]
    health_scores = [e.get("health_score", 0) for e in history]

    summary = {
        "total_cycles": len(history),
        "best_reward": round(max(rewards), 3),
        "avg_reward": round(sum(rewards) / len(rewards), 3),
        "best_health": round(max(health_scores), 1),
        "current_health": round(health_scores[-1], 1),
        "baseline_health": 38.6,
        "current_state": history[-1]["state_after"],
        "kept_count": sum(1 for e in history if e.get("kept", False)),
    }
    return jsonify({"experiments": history, "summary": summary})


@app.route("/run", methods=["POST"])
def run_one():
    if _runner["running"]:
        return jsonify({"error": "Runner already active."}), 409
    with _run_lock:
        result = run_one_cycle()
    return jsonify(result)


@app.route("/start", methods=["POST"])
def start_runner():
    """Start the background runner.
    POST body (JSON, all optional):
      cycles: int | null  — cycles to run (null = run forever)
      delay:  float       — seconds between cycles (default 1.5)
    """
    if _runner["running"]:
        return jsonify({"error": "Already running."}), 409

    body = request.get_json(silent=True) or {}
    target = body.get("cycles", None)
    delay  = float(body.get("delay", 1.5))

    t = threading.Thread(target=_background_runner, args=(target, delay), daemon=True)
    _runner["thread"] = t
    _runner["target_cycles"] = target
    _runner["last_error"] = None
    t.start()

    return jsonify({
        "started": True,
        "target_cycles": target,
        "delay": delay,
        "message": f"Running {'forever' if target is None else str(target) + ' cycles'}",
    })


@app.route("/stop", methods=["POST"])
def stop_runner():
    _runner["running"] = False
    _runner["status"] = "stopped"
    return jsonify({"stopped": True, "completed": _runner["completed"]})


@app.route("/runner-status")
def runner_status():
    return jsonify({
        "running": _runner["running"],
        "status":  _runner["status"],
        "completed": _runner["completed"],
        "target_cycles": _runner["target_cycles"],
        "last_error": _runner["last_error"],
    })


@app.route("/program")
def get_program():
    if os.path.exists(PROGRAM_FILE):
        with open(PROGRAM_FILE) as f:
            return jsonify({"content": f.read()})
    return jsonify({"content": "No program file found."})



@app.route("/configure", methods=["POST"])
def configure():
    """Set a custom initial reef state. Resets experiment history."""
    body = request.get_json(silent=True) or {}
    _runner["running"] = False
    _runner["status"] = "idle"
    _runner["completed"] = 0
    if os.path.exists(RESULTS_FILE):
        os.remove(RESULTS_FILE)
    # Save config for run_one_cycle to pick up
    with open("config.json", "w") as f:
        json.dump(body, f, indent=2)
    return jsonify({"configured": True, "initial_state": body})


@app.route("/reset", methods=["POST"])
def reset():
    """Stop any running experiment, wipe experiments.json, reset program.md to baseline."""
    # Stop runner first
    _runner["running"] = False
    _runner["status"] = "idle"
    _runner["completed"] = 0

    # Wipe experiment history
    if os.path.exists(RESULTS_FILE):
        os.remove(RESULTS_FILE)

    # Reset program.md to the baseline template
    baseline = """# ReefMind Research Program

## Mission
Discover optimal intervention strategies to restore coral reef health in a simulated
ecosystem suffering from bleaching, acidification, and biodiversity loss.

## Current best result
- Baseline: bleaching 65%, coral cover 22%, pH 7.9, DHW 0, omega 2.6, water_quality 0.45, adapt 0.15, species 18
- Health score baseline: ~38/100
- Best so far: (will be updated by agent)

## Known findings
- Climate forcing actively worsens the reef every step — inaction causes DHW to reach 9+ in 20 cycles.
- DHW (Degree Heating Weeks) is the primary threat: bleaching risk starts at DHW=4, mortality at DHW=8.
- Shading is the most effective DHW reducer: cuts temperature by ~0.45°C and DHW per cycle.
- combined addresses the most pathways simultaneously: DHW, water quality, adaptation, bleaching, cover, species.
- omega_arag (aragonite saturation) starts at 2.6, target is 3.5 — low omega impairs calcification.
- alkalinity_enhancement is the primary tool to raise omega_arag and pH.
- pollution_reduction raises water_quality, which boosts resilience and passive reef recovery rates.
- assisted_evolution raises adaptation_score, which reduces heat susceptibility over many cycles.
- Intervention effects are small per cycle — sustained pressure over many cycles is required.
- Passive recovery only occurs when DHW < 2.0.

## Research rules
1. Never repeat the same intervention more than 2 cycles in a row.
2. If DHW > 4.0, prioritize shading or combined immediately.
3. If DHW < 2.0 and omega_arag < 3.0, prioritize alkalinity_enhancement.
4. If water_quality < 0.5, prioritize pollution_reduction.
5. combined is the default when multiple metrics are lagging simultaneously.
6. assisted_evolution is a long-term investment — compounds slowly.
7. Intensity 0.75 is the reliable sweet spot — avoid exceeding 0.85.
8. When 0 cycles kept in last 5, switch to combined as the reset intervention.

## Hypotheses to test
- IN PROGRESS: Does sustained shading keep DHW below 2.0 and enable passive recovery?
- IN PROGRESS: Can alternating combined → alkalinity_enhancement raise omega_arag to 3.0+?
- NEW: Does raising adaptation_score above 0.3 meaningfully reduce bleaching susceptibility?
- NEW: What is the optimal intervention sequence to push health score above 60/100?

## Next priority
DHW is the first priority — it will accelerate to dangerous levels without active management.
Use shading or combined for the first several cycles to establish DHW < 2.0.
Once DHW is controlled, shift focus to raising omega_arag via alkalinity_enhancement
and water_quality via pollution_reduction to unlock passive reef recovery.
"""
    with open(PROGRAM_FILE, "w") as f:
        f.write(baseline)

    return jsonify({"reset": True, "message": "Experiment history cleared and program.md reset to baseline."})


@app.route("/health-check")
def health_check():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True, port=5000, threaded=True)