import random

class ReefSimulator:
    def __init__(self):
        self.state = {
            "temperature_c": 29.5,       # healthy = below 28
            "ph": 7.9,                   # healthy = 8.1–8.3
            "bleaching_pct": 65.0,       # % of coral bleached (lower = better)
            "species_count": 18,         # number of species observed
            "coral_cover_pct": 22.0,     # % of reef covered in live coral
            "time_step": 0
        }
        self.history = [dict(self.state)]

    def apply_intervention(self, intervention: str, intensity: float):
        # Normalize: lowercase + underscores, handles "Pollution Reduction" → "pollution_reduction"
        intervention = intervention.strip().lower().replace(" ", "_")
        
        s = self.state
        noise = lambda: random.gauss(0, 0.3)

        if intervention == "alkalinity_enhancement":
            s["ph"] += 0.04 * intensity + noise()
            s["bleaching_pct"] -= 2.5 * intensity + noise()
            s["coral_cover_pct"] += 0.8 * intensity + noise()

        elif intervention == "shading":
            s["temperature_c"] -= 0.3 * intensity + noise()
            s["bleaching_pct"] -= 3.0 * intensity + noise()
            s["coral_cover_pct"] += 0.5 * intensity + noise()

        elif intervention == "assisted_evolution":
            s["bleaching_pct"] -= 1.5 * intensity + noise()
            s["species_count"] += int(1.5 * intensity + noise())
            s["coral_cover_pct"] += 1.2 * intensity + noise()

        elif intervention == "pollution_reduction":
            s["ph"] += 0.02 * intensity + noise()
            s["species_count"] += int(2.0 * intensity + noise())
            s["coral_cover_pct"] += 0.6 * intensity + noise()

        elif intervention == "combined":
            # Synergy bonus — this is what the agent should discover
            s["ph"] += 0.05 * intensity + noise()
            s["temperature_c"] -= 0.2 * intensity + noise()
            s["bleaching_pct"] -= 5.0 * intensity + noise()
            s["species_count"] += int(2.5 * intensity + noise())
            s["coral_cover_pct"] += 2.0 * intensity + noise()

        # Clamp values to realistic ranges
        s["ph"] = round(max(7.6, min(8.4, s["ph"])), 3)
        s["temperature_c"] = round(max(25.0, min(33.0, s["temperature_c"])), 2)
        s["bleaching_pct"] = round(max(0.0, min(100.0, s["bleaching_pct"])), 1)
        s["species_count"] = max(1, s["species_count"])
        s["coral_cover_pct"] = round(max(0.0, min(100.0, s["coral_cover_pct"])), 1)
        s["time_step"] += 1

        self.history.append(dict(s))
        return dict(s)

    def get_state(self):
        return dict(self.state)