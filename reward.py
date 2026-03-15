def compute_reward(state_before: dict, state_after: dict) -> float:
    score = 0.0

    dhw_before  = state_before.get("dhw", 0.0)
    dhw_after   = state_after.get("dhw", 0.0)
    omega_before = state_before.get("omega_arag", 2.6)
    omega_after  = state_after.get("omega_arag", 2.6)
    wq_before   = state_before.get("water_quality", 0.45)
    wq_after    = state_after.get("water_quality", 0.45)

    # ── Adaptive weights based on how much headroom each metric has ────────
    # When a metric is near its target, reduce its weight and redistribute
    dhw_headroom   = min(1.0, dhw_after / 4.0)          # 0 when controlled, 1 at danger
    omega_headroom = max(0.0, (3.5 - omega_after) / 0.9) # 1 when far, 0 when at target
    wq_headroom    = max(0.0, (0.8 - wq_after) / 0.35)  # 1 when low, 0 when near target
    bleach_headroom = min(1.0, state_after["bleaching_pct"] / 65.0)

    # Normalise weights so they always sum to 1.0
    raw = {
        "dhw":     0.05 + 0.25 * dhw_headroom,
        "bleach":  0.15 + 0.20 * bleach_headroom,
        "omega":   0.10 + 0.15 * omega_headroom,
        "wq":      0.05 + 0.15 * wq_headroom,
        "cover":   0.10,
        "species": 0.10,
    }
    total = sum(raw.values())
    w = {k: v / total for k, v in raw.items()}

    # ── Score each component ───────────────────────────────────────────────
    dhw_delta = dhw_before - dhw_after
    score += (dhw_delta / 1.5) * w["dhw"]

    bleach_delta = state_before["bleaching_pct"] - state_after["bleaching_pct"]
    score += (bleach_delta / 5.0) * w["bleach"]

    omega_delta = omega_after - omega_before
    score += (omega_delta / 0.15) * w["omega"]

    wq_delta = wq_after - wq_before
    score += (wq_delta / 0.10) * w["wq"]

    cover_delta = state_after["coral_cover_pct"] - state_before["coral_cover_pct"]
    score += (cover_delta / 2.0) * w["cover"]

    species_delta = state_after["species_count"] - state_before["species_count"]
    score += (species_delta / 3.0) * w["species"]

    return round(max(-1.0, min(1.0, score)), 3)

def compute_health_score(state: dict) -> float:
    """
    Composite 0-100 reef health score for dashboard display.
    Useful for tracking long-run progress independent of per-cycle reward.
    """
    score = 0.0

    # Bleaching (0-30 pts): 0% bleaching = 30 pts, 100% = 0 pts
    score += max(0.0, (100.0 - state["bleaching_pct"]) / 100.0) * 30

    # DHW (0-20 pts): DHW=0 = 20 pts, DHW=10+ = 0 pts
    score += max(0.0, 1.0 - state.get("dhw", 0.0) / 10.0) * 20

    # omega_arag (0-15 pts): target 3.5, starting 2.6
    score += min(1.0, max(0.0, (state.get("omega_arag", 2.6) - 1.0) / 2.5)) * 15

    # water_quality (0-15 pts)
    score += min(1.0, state.get("water_quality", 0.45)) * 15

    # Coral cover (0-10 pts): target 60%
    score += min(1.0, state["coral_cover_pct"] / 60.0) * 10

    # Species (0-10 pts): target 35
    score += min(1.0, state["species_count"] / 35.0) * 10

    return round(score, 1)