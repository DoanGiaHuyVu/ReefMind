# ReefMind Research Program

## Mission
Discover optimal intervention strategies to restore coral reef health in a simulated
ecosystem suffering from bleaching, acidification, and biodiversity loss.

## Current best result
- health 66.6/100 | bleaching 57% | coral cover 24.5% | omega 2.92 | water_quality 0.842 | DHW 0.0 | adapt 0.205 | species 19
- Best single reward: 0.302 (combined @ 0.75, cycle 12)

## Known findings
- DHW is fully controlled at 0.0 — thermal threat is neutralised.
- water_quality reached 0.842 (target 0.8+) — resilience infrastructure is complete.
- omega_arag reached 2.92 — chemistry is improving but target is 3.5, still work to do.
- combined @ 0.75 is the highest-reward intervention (0.302, 0.263, 0.184) — used only 3/100 cycles.
- alkalinity_enhancement was overused (52/100 cycles) with diminishing returns after cycle 20.
- Bleaching (57%) is now the primary bottleneck — it has barely moved in 80 cycles.
- Shading directly reduces bleaching by ~1.6% per cycle — essential now that DHW is controlled.
- The agent correctly rebuilt resilience first. Now it must attack bleaching directly.
- Passive recovery (bleaching self-healing) requires DHW < 2.0 AND coral cover > 25% — we are close.

## Research rules
1. Never repeat the same intervention more than 2 cycles in a row.
2. DHW = 0.0 and water_quality = 0.84 — resilience phase is COMPLETE. Now attack bleaching.
3. combined @ 0.75 MUST be the primary intervention — it is the proven highest-reward action.
4. Alternate: combined → shading → combined to drive bleaching below 40%.
5. Avoid alkalinity_enhancement for at least 5 cycles — it has been exhausted.
6. If 0 cycles kept in last 3, immediately switch to combined.
7. Target: bleaching below 40%, health score above 70/100 within 20 cycles.

## Hypotheses to test
- CONFIRMED: Rebuilding resilience (water_quality, omega, DHW) before attacking bleaching is optimal sequencing.
- CONFIRMED: combined @ 0.75 is the highest single-cycle reward intervention.
- IN PROGRESS: Can combined → shading alternation push bleaching below 40%?
- NEW: Does passive recovery accelerate once bleaching drops below 50%?
- NEW: Can health score reach 75/100 by combining bleaching reduction with continued omega improvement?

## Next priority
Bleaching at 57% is the only remaining bottleneck. Run combined @ 0.75 for the next 3 cycles,
alternating with shading @ 0.75 every 3rd cycle. Do NOT use alkalinity_enhancement.
Target: bleaching below 40%, health score above 70/100.