# ReefMind Research Program

## Mission
Discover optimal intervention strategies to restore coral reef health in a simulated
ecosystem suffering from bleaching, acidification, and biodiversity loss.

## Current best result
- Bleaching: 0.0%, coral cover 77.6%, pH 8.343, DHW 0.38, omega_arag 4.82, water_quality 0.929, adaptation_score 0.926, species 44

## Known findings
- Climate forcing actively worsens the reef without intervention.
- DHW is a primary threat: bleaching risk starts at DHW=4, mortality at DHW=8.
- Shading effectively reduces DHW.
- Alkalinity_enhancement raises omega_arag and pH, improving calcification.
- Pollution_reduction raises water_quality, boosting resilience and species diversity.
- Assisted_evolution raises adaptation_score, increasing long-term heat tolerance.
- Intervention effects are small per cycle – sustained pressure is required.
- Passive recovery occurs when DHW < 2.0.
- Intensity 0.75 is generally reliable.
- Repeating interventions >2 cycles yields diminishing returns.
- Low omega_arag impairs coral growth; target > 3.0.
- Adaptation score is a key indicator of long-term heat tolerance.
- Water quality improvements correlate with increased species diversity.
- Pollution_reduction followed by alkalinity_enhancement amplifies benefits.
- A brief alkalinity_enhancement cycle following pollution_reduction is beneficial.

## Research rules
1. Never repeat the same intervention more than 2 cycles in a row.
2. If DHW > 4.0, prioritize shading or combined immediately.
3. If DHW < 2.0 and omega_arag < 3.0, prioritize alkalinity_enhancement.
4. If water_quality < 0.5, prioritize pollution_reduction.
5. combined is the default when multiple metrics are lagging.
6. assisted_evolution is a long-term investment, best implemented when DHW is stable (<1.0).
7. Intensity 0.75 is the reliable sweet spot – avoid exceeding 0.85.
8. When 0 cycles kept in last 5, switch to combined as the reset intervention.
9. Given stable DHW (<1.0) and omega_arag > 2.8, prioritize assisted_evolution.
10. Following pollution_reduction, implement a single cycle of alkalinity_enhancement.
11. Given DHW < 0.5 and omega_arag > 3.4, prioritize assisted_evolution.
12. If DHW < 1.0 for 2 consecutive cycles, monitor for passive recovery of coral cover.
13. Given stable DHW and high omega_arag, prioritize assisted_evolution to observe adaptation score changes.
14. If adaptation_score > 0.8, consider reducing intervention frequency to observe natural fluctuations.

## Hypotheses to test
- CONFIRMED: Does raising adaptation_score above 0.3 meaningfully reduce bleaching susceptibility?
- IN PROGRESS: Is a cyclical shading/alkalinity_enhancement strategy more effective than alternating combined/alkalinity_enhancement?
- REJECTED: Can alternating combined → alkalinity_enhancement raise omega_arag to 3.0+?
- IN PROGRESS: Does sustained water_quality improvement correlate with increased species diversity?
- IN PROGRESS: Can targeted assisted_evolution accelerate adaptation to current conditions?
- NEW: Does increasing omega_arag above 3.18 significantly improve coral cover growth rates?
- CONFIRMED: Does a brief alkalinity_enhancement cycle following pollution_reduction amplify the benefits to water_quality?
- CONFIRMED: Can a pollution_reduction focused strategy, given stable DHW, significantly improve overall reef health?
- NEW: Is there a synergistic effect between water_quality and adaptation_score on species diversity?
- NEW: Does maintaining DHW < 1.0 for 3 consecutive cycles result in significant passive recovery of coral cover?
- CONFIRMED: Does a high adaptation_score (>0.4) buffer against minor fluctuations in DHW?
- NEW: Does continued assisted_evolution at 0.75 yield diminishing returns after 3 cycles?
- NEW: Is there a correlation between adaptation_score and coral cover growth rate?

## Next priority
Given the exceptionally stable conditions (DHW 0.38, omega_arag 4.82), we are implementing alkalinity_enhancement @ 0.75. This intervention will maintain a balanced approach to reef health and avoid repeating assisted_evolution for a third consecutive cycle. We will continue to monitor the adaptation_score for any signs of diminishing returns and track coral cover growth rates.