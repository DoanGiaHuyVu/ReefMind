def compute_reward(state_before: dict, state_after: dict) -> float:
    score = 0.0

    # pH — highest priority now, reef is stuck at 7.894 far from healthy 8.2
    ph_before_dist = abs(state_before["ph"] - 8.2)
    ph_after_dist = abs(state_after["ph"] - 8.2)
    score += ((ph_before_dist - ph_after_dist) / 0.3) * 0.40

    # Species recovery
    species_delta = state_after["species_count"] - state_before["species_count"]
    score += (species_delta / 5.0) * 0.25

    # Bleaching — still matters but diminishing as it approaches 0
    bleach_delta = state_before["bleaching_pct"] - state_after["bleaching_pct"]
    score += (bleach_delta / 10.0) * 0.20

    # Coral cover
    cover_delta = state_after["coral_cover_pct"] - state_before["coral_cover_pct"]
    score += (cover_delta / 5.0) * 0.15

    return round(max(-1.0, min(1.0, score)), 3)