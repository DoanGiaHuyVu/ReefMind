# ReefMind Research Program

## Mission
Discover optimal intervention strategies to restore coral reef health in a simulated
ecosystem suffering from bleaching, acidification, and biodiversity loss.

## Current best result
- Baseline: bleaching 65%, coral cover 22%, pH 7.9, species 18
- Best so far: (agent will fill this in)

## Known findings
- (agent will append lessons learned here each cycle)

## Research rules
1. Never repeat the same intervention more than 2 cycles in a row.
2. Always explain why you chose this intervention given past results.
3. When bleaching < 20%, shift focus to pH and species recovery.
4. The 'combined' intervention has the highest confirmed reward (0.522) — prioritize it.
5. pollution_reduction has avg reward −0.078 across 20 cycles — deprioritize until reef stabilizes.
6. Intensity 0.75 is the most reliable — avoid going above 0.85.
7. When discarded 3 cycles in a row, switch to 'combined' as the reset intervention.
8. Monitor pH — it is currently at the ceiling (8.4). Avoid alkalinity_enhancement until pH drops below 8.1.

## Hypotheses to test
- CONFIRMED: combined @ 0.75 is the highest single-cycle reward intervention.
- CONFIRMED: pollution_reduction alone is unreliable — avg reward negative across 20 cycles.
- IN PROGRESS: Can assisted_evolution + shading sequence beat combined alone?
- NEW: Does combined performance degrade when pH is already at 8.4?

## Next priority
Focus on combined @ 0.75 as the primary intervention. Interleave with assisted_evolution and shading to build species count and coral cover. Avoid pollution_reduction until bleaching is below 20%. The goal for the next 50 cycles is to advance the reef state beyond the cycle-2 best (bleaching 58.9%) by chaining successful experiments rather than resetting to it.