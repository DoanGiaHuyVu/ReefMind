import time, json, os
from collections import deque
from reef_simulator import ReefSimulator
from agent import get_agent_decision
from reward import compute_reward, compute_health_score

RESULTS_FILE = "experiments.json"


def load_history():
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE) as f:
            return json.load(f)
    return []


def save_history(history):
    with open(RESULTS_FILE, "w") as f:
        json.dump(history, f, indent=2)


def get_decision_with_retry(state, history, max_retries=3):
    for attempt in range(max_retries):
        try:
            return get_agent_decision(state, history)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"  ⚠️  Attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                print(f"  🔄 Retrying in 3 seconds...")
                time.sleep(3)
            else:
                print(f"  🆘 All retries failed — using fallback decision")
                tried = {e['intervention'] for e in history}
                untried = [i for i in ["alkalinity_enhancement", "shading",
                           "assisted_evolution", "pollution_reduction", "combined"]
                           if i not in tried]
                fallback = untried[0] if untried else "combined"
                return {
                    "hypothesis": "Fallback: exploring untried intervention after parse error.",
                    "intervention": fallback,
                    "intensity": 0.75,
                    "reasoning": "Automatic fallback due to API parse error."
                }

def get_intervention_override(state: dict, history: list) -> str | None:
    """
    Bypasses the LLM when it's demonstrably stuck.
    Returns a forced intervention name, or None to let the agent decide.
    """
    if not history:
        return None

    # Count last 5 interventions
    last5 = [e['intervention'] for e in history[-5:]]
    last5_kept = sum(1 for e in history[-5:] if e.get('kept', False))

    # Force combined if alkalinity or assisted_evolution dominated last 5 and nothing kept
    dominant = max(set(last5), key=last5.count)
    if dominant in ('alkalinity_enhancement', 'assisted_evolution') and last5_kept == 0:
        print(f"  🔧 Override: agent stuck on {dominant} with 0 kept — forcing combined")
        return 'combined'

    # Force shading if DHW is creeping up
    dhw = state.get('dhw', 0.0)
    if dhw > 1.0:
        print(f"  🔧 Override: DHW={dhw} rising — forcing shading")
        return 'shading'

    return None

def run_cycles(num_cycles=100):
    history = load_history()
    sim = ReefSimulator()

    # Resume from best known state
    if history:
        kept_entries = [e for e in history if e.get('kept', False)]
        best_entry = kept_entries[-1] if kept_entries else history[-1]
        best_state = dict(best_entry['state_after'])
        best_reward = best_entry['reward']
        sim.state = dict(best_state)
        sim.state['time_step'] = len(history)

        # Restore DHW history context (approximate — back-fill 12-week buffer)
        restored_temp = sim.state.get("temperature_c", 29.5)
        restored_dhw  = sim.state.get("dhw", 0.0)
        weekly_hotspot = max(0.0, restored_temp - (sim.mmm_c + 1.0))
        approx_hotspot = restored_dhw / 12.0 if restored_dhw > 0 else weekly_hotspot
        sim._hotspot_history = deque([approx_hotspot] * 12, maxlen=12)
    else:
        best_state = sim.get_state()
        best_reward = -float('inf')

    initial_health = compute_health_score(sim.get_state())
    print(f"\n🪸 ReefMind v2 — new simulator, {num_cycles} cycles.")
    print(f"   Starting health score: {initial_health}/100")
    print(f"   Starting state: bleaching {sim.state['bleaching_pct']}% | "
          f"DHW {sim.state.get('dhw',0)} | omega {sim.state.get('omega_arag',2.6)} | "
          f"pH {sim.state['ph']}\n")

    for i in range(num_cycles):
        cycle_num = len(history) + 1
        state_before = sim.get_state()

        print(f"Cycle {cycle_num} — deciding...")
        override = get_intervention_override(state_before, history)
        if override:
            decision = {
                "hypothesis": f"Override: applying {override} to break out of exploitation trap.",
                "intervention": override,
                "intensity": 0.75,
                "reasoning": "Programmatic override — agent was stuck with 0 kept in last 5 cycles."
            }
        else:
            decision = get_decision_with_retry(state_before, history)
        print(f"  Hypothesis:   {decision['hypothesis']}")
        print(f"  Intervention: {decision['intervention']} @ {decision['intensity']}")

        state_after = sim.apply_intervention(
            decision["intervention"], float(decision["intensity"])
        )
        reward = compute_reward(state_before, state_after)
        health = compute_health_score(state_after)

        # ── SLIDING WINDOW KEEP/DISCARD ───────────────────────────────────
        kept_history = [e for e in history if e.get('kept', False)]
        if len(kept_history) >= 5:
            recent_avg = sum(e['reward'] for e in kept_history[-5:]) / 5
            acceptance_threshold = max(-0.02, recent_avg * 0.5)  # was max(0.02, recent_avg * 0.7)
        else:
            acceptance_threshold = -0.05

        kept = reward >= acceptance_threshold

        if kept:
            best_state = dict(state_after)
            if reward > best_reward:
                best_reward = reward
                print(f"  ✅ KEPT — new best reward {reward} | health {health}/100")
            else:
                print(f"  ✅ KEPT — reward {reward} | health {health}/100")
        else:
            sim.state = dict(best_state)
            sim.state['time_step'] = cycle_num
            print(f"  ↩️  DISCARDED — reward {reward} below threshold {round(acceptance_threshold,3)}")

        # State summary line
        sa = state_after
        print(f"  📊 bleaching {sa['bleaching_pct']}% | DHW {sa.get('dhw',0)} | "
              f"omega {sa.get('omega_arag',2.6)} | wq {round(sa.get('water_quality',0),3)} | "
              f"adapt {round(sa.get('adaptation_score',0),3)}")
        print(f"  📋 program.md rewritten\n")

        history.append({
            "cycle": cycle_num,
            "hypothesis": decision["hypothesis"],
            "reasoning": decision["reasoning"],
            "intervention": decision["intervention"],
            "intensity": decision["intensity"],
            "state_before": state_before,
            "state_after": state_after,
            "reward": reward,
            "health_score": health,
            "kept": kept,
        })
        save_history(history)
        time.sleep(1)

    final_health = compute_health_score(sim.get_state())
    print(f"✅ Done.")
    print(f"   Final health score: {final_health}/100 (started: {initial_health}/100)")
    print(f"   Best reward: {round(best_reward, 3)}")


if __name__ == "__main__":
    run_cycles(num_cycles=50)