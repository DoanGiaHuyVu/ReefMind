import random
import math
from collections import deque


class ReefSimulator:
    """
    Synthetic reef ecosystem simulator with:
    - background climate forcing
    - DHW-like accumulated heat stress
    - approximate carbonate saturation state (omega_arag)
    - slower recovery than damage
    - more realistic intervention pathways

    Assumption: 1 time step = 1 week
    """

    def __init__(self, seed=None):
        self.rng = random.Random(seed)

        # Reef-specific constants
        self.mmm_c = 28.0  # Maximum Monthly Mean-like bleaching baseline
        self.baseline_water_quality = 0.45

        # Slow background forcing per weekly step
        self.background_warming_per_step = 0.0006      # ~0.03 C / year synthetic drift
        self.background_ph_decline_per_step = 0.00004  # ~0.021 pH / decade

        self.state = {
            "temperature_c": 29.5,
            "ph": 7.9,
            "omega_arag": 0.0,        # derived from pH with a simple proxy
            "dhw": 0.0,               # Degree Heating Weeks-like heat stress memory
            "bleaching_pct": 65.0,
            "species_count": 18,
            "coral_cover_pct": 22.0,
            "water_quality": 0.45,    # 0..1, higher is better
            "adaptation_score": 0.15, # 0..1, higher means more heat tolerance
            "time_step": 0
        }

        self._hotspot_history = deque([0.0] * 12, maxlen=12)  # 12-week rolling window
        self.state["omega_arag"] = self._omega_from_ph(self.state["ph"])
        self.history = [dict(self.state)]

    @staticmethod
    def _clamp(x, lo, hi):
        return max(lo, min(hi, x))

    @staticmethod
    def _sigmoid(x):
        return 1.0 / (1.0 + math.exp(-x))

    def _omega_from_ph(self, ph):
        """
        Very rough proxy mapping pH -> aragonite saturation state.
        This is intentionally simple for a synthetic world model.
        For research-grade chemistry, replace with a carbonate system solver.
        """
        omega = 3.6 + 5.0 * (ph - 8.1)
        return round(self._clamp(omega, 1.0, 5.0), 2)

    def _normalize_intervention(self, intervention):
        return intervention.strip().lower().replace(" ", "_")

    def _apply_background_forcing(self):
        s = self.state

        # Long-run warming + local variability + occasional marine heatwave spike
        heatwave = 0.0
        heatwave_prob = 0.08 + min(0.10, 0.0004 * s["time_step"])
        if self.rng.random() < heatwave_prob:
            heatwave = self.rng.uniform(0.15, 0.80)

        s["temperature_c"] += (
            self.background_warming_per_step
            + self.rng.gauss(0.0, 0.05)
            + heatwave
        )

        # Long-run acidification + small local variability
        s["ph"] -= self.background_ph_decline_per_step
        s["ph"] += self.rng.gauss(0.0, 0.003)

        # Water quality drifts slowly toward its baseline unless managed
        s["water_quality"] += 0.01 * (self.baseline_water_quality - s["water_quality"])
        s["water_quality"] += self.rng.gauss(0.0, 0.005)

        # Adaptation persists but is not perfectly permanent
        s["adaptation_score"] *= 0.999

    def _apply_intervention_effects(self, intervention, intensity):
        s = self.state
        n_small = lambda sigma: self.rng.gauss(0.0, sigma)

        if intervention in ("none", "", None) or intensity <= 0:
            return

        if intervention == "alkalinity_enhancement":
            # Mostly chemistry / calcification pathway, not instant reef regrowth
            s["ph"] += 0.012 * intensity + n_small(0.002)
            s["bleaching_pct"] -= 0.4 * intensity + n_small(0.15)

        elif intervention == "shading":
            # Mainly cuts acute thermal/light stress
            s["temperature_c"] -= 0.45 * intensity + n_small(0.03)
            s["bleaching_pct"] -= 1.6 * intensity + n_small(0.20)

        elif intervention == "assisted_evolution":
            # Shifts tolerance distribution upward
            s["adaptation_score"] += 0.05 * intensity + n_small(0.01)
            s["coral_cover_pct"] += 0.35 * intensity + n_small(0.08)
            s["species_count"] += int(round(0.4 * intensity + n_small(0.20)))

        elif intervention == "pollution_reduction":
            # Improves resilience, recruitment, disease pressure, sediment stress
            s["water_quality"] += 0.10 * intensity + n_small(0.01)
            s["bleaching_pct"] -= 0.7 * intensity + n_small(0.15)
            s["coral_cover_pct"] += 0.20 * intensity + n_small(0.05)

        elif intervention == "combined":
            # No magic bonus; synergy emerges from several pathways improving together
            s["ph"] += 0.010 * intensity + n_small(0.002)
            s["temperature_c"] -= 0.35 * intensity + n_small(0.03)
            s["water_quality"] += 0.08 * intensity + n_small(0.01)
            s["adaptation_score"] += 0.04 * intensity + n_small(0.01)
            s["bleaching_pct"] -= 2.0 * intensity + n_small(0.20)
            s["coral_cover_pct"] += 0.50 * intensity + n_small(0.08)
            s["species_count"] += int(round(0.8 * intensity + n_small(0.25)))

        else:
            raise ValueError(f"Unknown intervention: {intervention}")

    def _update_heat_stress(self):
        """
        DHW-like stress:
        weekly hotspot contribution accumulates only when temp exceeds MMM + 1 C.
        """
        s = self.state
        hotspot = max(0.0, s["temperature_c"] - (self.mmm_c + 1.0))
        self._hotspot_history.append(hotspot)
        s["dhw"] = round(sum(self._hotspot_history), 2)

    def _apply_ecology(self):
        s = self.state

        # Update carbonate saturation proxy from pH
        s["omega_arag"] = self._omega_from_ph(s["ph"])

        dhw = s["dhw"]
        omega = s["omega_arag"]
        wq = self._clamp(s["water_quality"], 0.0, 1.0)
        adapt = self._clamp(s["adaptation_score"], 0.0, 1.0)

        # Heat-driven bleaching / mortality risk
        bleaching_risk = self._sigmoid((dhw - 4.0) / 1.2)
        mortality_risk = self._sigmoid((dhw - 8.0) / 1.2)

        # Additional susceptibility from poor chemistry / poor water quality
        oa_stress = max(0.0, 3.4 - omega)
        susceptibility = 1.0 + 0.70 * (1.0 - wq) + 0.35 * oa_stress - 0.50 * adapt
        susceptibility = self._clamp(susceptibility, 0.5, 2.2)

        # Bleaching rises quickly under accumulated heat stress
        bleaching_increase = 10.0 * bleaching_risk * susceptibility

        # Recovery only happens when heat stress is low
        passive_recovery = 0.0
        if dhw < 2.0:
            passive_recovery = (
                2.2
                * wq
                * (1.0 + 0.8 * adapt)
                * max(0.4, omega / 3.5)
                * (s["coral_cover_pct"] / 100.0)
            )

        s["bleaching_pct"] += bleaching_increase - passive_recovery + self.rng.gauss(0.0, 0.25)

        # Calcification / recruitment side
        calcification_factor = self._clamp(1.0 + 0.15 * (omega - 3.5), 0.45, 1.20)
        recruitment_penalty = max(0.0, 7.8 - s["ph"]) * 0.5
        recruitment_factor = self._clamp(
            wq * (1.0 + 0.6 * adapt) - recruitment_penalty,
            0.0,
            1.5
        )

        # Cover grows slowly, especially when much of the reef is already dead
        growth = (
            0.9
            * calcification_factor
            * recruitment_factor
            * max(0.0, 1.0 - s["bleaching_pct"] / 100.0)
            * max(0.0, 1.0 - s["coral_cover_pct"] / 100.0)
        )

        # Dissolution / erosion pressure rises as saturation drops
        dissolution = 0.35 * max(0.0, 3.0 - omega)

        # Mortality hits cover more strongly once DHW is high and bleaching is already severe
        mortality_loss = (
            1.4
            * mortality_risk
            * susceptibility
            * (0.4 + s["bleaching_pct"] / 100.0)
        )

        cover_delta = growth - mortality_loss - dissolution + self.rng.gauss(0.0, 0.08)
        s["coral_cover_pct"] += cover_delta

        # Biodiversity follows habitat quality and living coral cover with inertia
        target_species = (
            6.0
            + 0.30 * s["coral_cover_pct"]
            + 10.0 * wq
            + 5.0 * adapt
            - 0.04 * s["bleaching_pct"]
        )
        species_adjustment = 0.18 * (target_species - s["species_count"]) + self.rng.gauss(0.0, 0.35)
        s["species_count"] += int(round(species_adjustment))

    def _clamp_state(self):
        s = self.state

        s["ph"] = round(self._clamp(s["ph"], 7.6, 8.4), 3)
        s["temperature_c"] = round(self._clamp(s["temperature_c"], 25.0, 33.5), 2)
        s["omega_arag"] = round(self._clamp(s["omega_arag"], 1.0, 5.0), 2)
        s["dhw"] = round(self._clamp(s["dhw"], 0.0, 30.0), 2)
        s["bleaching_pct"] = round(self._clamp(s["bleaching_pct"], 0.0, 100.0), 1)
        s["coral_cover_pct"] = round(self._clamp(s["coral_cover_pct"], 0.0, 100.0), 1)
        s["water_quality"] = round(self._clamp(s["water_quality"], 0.0, 1.0), 3)
        s["adaptation_score"] = round(self._clamp(s["adaptation_score"], 0.0, 1.0), 3)
        s["species_count"] = max(1, s["species_count"])

    def apply_intervention(self, intervention: str, intensity: float):
        intervention = self._normalize_intervention(intervention)
        intensity = self._clamp(float(intensity), 0.0, 1.0)

        # Advance the world first: climate keeps worsening unless managed
        self._apply_background_forcing()

        # Apply management action
        self._apply_intervention_effects(intervention, intensity)

        # Translate environment -> accumulated stress -> reef response
        self._update_heat_stress()
        self._apply_ecology()
        self._clamp_state()

        self.state["time_step"] += 1
        self.history.append(dict(self.state))
        return dict(self.state)

    def step(self):
        """Advance one step with no intervention."""
        return self.apply_intervention("none", 0.0)

    def get_state(self):
        return dict(self.state)