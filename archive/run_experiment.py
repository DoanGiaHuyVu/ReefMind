import time, json, os
from reef_simulator import ReefSimulator
from agent import get_agent_decision
from reward import compute_reward

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
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  ⚠️  Attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                print(f"  🔄 Retrying in 3 seconds...")
                time.sleep(3)
            else:
                # Fallback: pick a safe default instead of crashing
                print(f"  🆘 All retries failed — using fallback decision")
                tried = {e['intervention'] for e in history}
                untried = [i for i in ["alkalinity_enhancement","shading",
                           "assisted_evolution","pollution_reduction","combined"]
                           if i not in tried]
                fallback_intervention = untried[0] if untried else "combined"
                return {
                    "hypothesis": "Fallback: exploring untried intervention after parse error.",
                    "intervention": fallback_intervention,
                    "intensity": 0.75,
                    "reasoning": "Automatic fallback due to API parse error."
                }

def run_cycles(num_cycles=100):
    history = load_history()
    sim = ReefSimulator()

    if history:
        best_entry = max(history, key=lambda e: e['reward'])
        best_state = dict(best_entry['state_after'])
        best_reward = best_entry['reward']
        sim.state = dict(best_state)
        sim.state['time_step'] = len(history)
    else:
        best_state = sim.get_state()
        best_reward = -float('inf')

    print(f"\n🪸 ReefMind — self-modifying research mode. {num_cycles} cycles.\n")

    for i in range(num_cycles):
        cycle_num = len(history) + 1
        state_before = sim.get_state()

        print(f"Cycle {cycle_num} — agent deciding + rewriting program.md...")
        decision = get_decision_with_retry(state_before, history)
        print(f"  Hypothesis:   {decision['hypothesis']}")
        print(f"  Intervention: {decision['intervention']} @ {decision['intensity']}")

        state_after = sim.apply_intervention(
            decision["intervention"], float(decision["intensity"])
        )
        reward = compute_reward(state_before, state_after)

        # ── SLIDING WINDOW KEEP/DISCARD ──────────────────────────────────────
        # Accept if reward beats the average of last 5 kept cycles (not all-time best)
        # This lets the reef advance incrementally instead of freezing at cycle 2
        kept_history = [e for e in history if e.get('kept', False)]
        if len(kept_history) >= 5:
            recent_kept = kept_history[-5:]
            acceptance_threshold = sum(e['reward'] for e in recent_kept) / len(recent_kept)
        else:
            acceptance_threshold = -0.05  # generous threshold early on

        kept = reward >= acceptance_threshold

        if kept:
            if reward > best_reward:
                best_reward = reward
                best_state = dict(state_after)
                print(f"  ✅ KEPT — new all-time best {reward}")
            else:
                best_state = dict(state_after)  # advance from this state even if not best
                print(f"  ✅ KEPT — reward {reward} (threshold was {round(acceptance_threshold,3)})")
        else:
            sim.state = dict(best_state)
            sim.state['time_step'] = cycle_num
            print(f"  ↩️  DISCARDED — reward {reward} below threshold {round(acceptance_threshold,3)}")

        print(f"  📋 program.md rewritten by agent\n")

        history.append({
            "cycle": cycle_num,
            "hypothesis": decision["hypothesis"],
            "reasoning": decision["reasoning"],
            "intervention": decision["intervention"],
            "intensity": decision["intensity"],
            "state_before": state_before,
            "state_after": state_after,
            "reward": reward,
            "kept": kept,
        })
        save_history(history)
        time.sleep(1)

    print(f"✅ Done. Best reward: {round(best_reward, 3)}")

if __name__ == "__main__":
    run_cycles(num_cycles=50)