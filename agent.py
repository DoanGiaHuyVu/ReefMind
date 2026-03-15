from google import genai
import json, os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

INTERVENTIONS = ["alkalinity_enhancement", "shading",
                 "assisted_evolution", "pollution_reduction", "combined"]
PROGRAM_FILE = "program.md"


def read_program():
    if os.path.exists(PROGRAM_FILE):
        with open(PROGRAM_FILE) as f:
            return f.read()
    return "No program file found."


def get_agent_decision(reef_state: dict, experiment_history: list) -> dict:
    program = read_program()

    history_summary = ""
    tried_interventions = set()
    if experiment_history:
        tried_interventions = {e['intervention'] for e in experiment_history}
        for e in experiment_history[-6:]:
            s = e['state_after']
            history_summary += (
                f"- Cycle {e['cycle']}: {e['intervention']} @ {e['intensity']} "
                f"→ reward {e['reward']} | kept: {e.get('kept','?')} | "
                f"bleaching {s['bleaching_pct']}% | DHW {s.get('dhw','?')} | "
                f"pH {s['ph']} | omega {s.get('omega_arag','?')} | "
                f"wq {round(s.get('water_quality', 0),3)} | "
                f"adapt {round(s.get('adaptation_score',0),3)} | "
                f"species {s['species_count']} | cover {s['coral_cover_pct']}%\n"
            )

    untried = [i for i in INTERVENTIONS if i not in tried_interventions]
    last3 = [e['intervention'] for e in experiment_history[-3:]] if len(experiment_history) >= 3 else []
    stuck = len(set(last3)) == 1

    # Pull key state values for the prompt
    rs = reef_state
    dhw = rs.get('dhw', 0.0)
    omega = rs.get('omega_arag', 2.6)
    wq = round(rs.get('water_quality', 0.45), 3)
    adapt = round(rs.get('adaptation_score', 0.15), 3)

    # ── CALL 1: decision only — compact JSON ─────────────────────────────
    decision_prompt = f"""You are an autonomous AI marine biologist running ReefMind.

=== RESEARCH PROGRAM ===
{program}
========================

CURRENT REEF STATE (cycle {len(experiment_history) + 1}):
Core metrics:
- Bleaching:         {rs['bleaching_pct']}%  (target: 0%, higher = worse)
- Coral cover:       {rs['coral_cover_pct']}%  (target: 60%+)
- Species count:     {rs['species_count']}  (target: 35+)

Climate & chemistry (NEW — critical for strategy):
- DHW (heat stress): {dhw}  (DANGER if >4, MORTALITY if >8, target: <2)
- Temperature:       {rs['temperature_c']}°C  (bleaching threshold: 29°C)
- pH:                {rs['ph']}  (healthy: 8.1–8.3)
- omega_arag:        {omega}  (aragonite saturation, target: 3.5, starting: 2.6)

Resilience indicators:
- Water quality:     {wq}  (0-1 scale, target: 0.8+, starting: 0.45)
- Adaptation score:  {adapt}  (heat tolerance, target: 0.5+, starting: 0.15)

IMPORTANT CONTEXT:
- Climate forcing actively worsens the reef every step — inaction causes DHW to climb to 9+ in 20 steps
- Shading is the primary tool to reduce DHW and temperature
- combined addresses DHW + water quality + adaptation simultaneously
- alkalinity_enhancement raises omega_arag (chemistry fix) but barely affects DHW
- pollution_reduction raises water quality (resilience fix)
- assisted_evolution raises adaptation_score (long-term tolerance fix)

RECENT HISTORY:
{history_summary or "No experiments yet."}

{"UNTRIED INTERVENTIONS — try before repeating: " + ", ".join(untried) if untried else ""}
{"WARNING: Same intervention 3 cycles in a row — MUST switch." if stuck else ""}

AVAILABLE INTERVENTIONS: {", ".join(INTERVENTIONS)}

Respond ONLY in this exact JSON, nothing else, no markdown fences:
{{
  "hypothesis": "one sentence",
  "intervention": "exact name from list",
  "intensity": 0.75,
  "reasoning": "two sentences referencing DHW, omega, water_quality and past results"
}}"""

    response1 = client.models.generate_content(
        model="gemma-3-27b-it",
        contents=decision_prompt,
        config={"temperature": 0.85}
    )
    text1 = response1.text.strip()
    if text1.startswith("```"):
        text1 = text1.split("```")[1]
        if text1.startswith("json"):
            text1 = text1[4:]
    decision = json.loads(text1.strip())

    # ── CALL 2: program.md rewrite — raw markdown only ────────────────────
    rewrite_prompt = f"""You are an autonomous AI marine biologist. Rewrite the research program below
to reflect the latest experiment decision and what you now understand about the reef system.

DECISION JUST MADE: {decision['intervention']} @ {decision['intensity']}
HYPOTHESIS: {decision['hypothesis']}
REASONING: {decision['reasoning']}

CURRENT REEF STATE:
- Bleaching: {rs['bleaching_pct']}% | DHW: {dhw} | pH: {rs['ph']} | omega_arag: {omega}
- water_quality: {wq} | adaptation_score: {adapt}
- Species: {rs['species_count']} | Coral cover: {rs['coral_cover_pct']}%

CURRENT PROGRAM TO UPDATE:
{program}

Rewriting rules:
- ## Mission stays EXACTLY as-is — do not change a single word
- Consolidate redundant findings — max 15 bullet points in ## Known findings
- Update ## Current best result only if metrics improved
- In ## Research rules: update based on what DHW, omega, water_quality data shows
- Mark hypotheses CONFIRMED / REJECTED / IN PROGRESS — add new ones
- ## Next priority: 2-3 sentences on what to target next given current DHW={dhw} and omega={omega}
- Total file: under 85 lines

Output ONLY raw markdown. No explanation, no JSON, no code fences.
Start directly with: # ReefMind Research Program"""

    response2 = client.models.generate_content(
        model="gemma-3-27b-it",
        contents=rewrite_prompt,
        config={"temperature": 0.7}
    )
    new_program = response2.text.strip()

    if new_program.startswith("```"):
        new_program = new_program.split("```")[1]
        if new_program.startswith(("markdown", "md")):
            new_program = new_program.split("\n", 1)[1]
    new_program = new_program.strip()

    if new_program.startswith("# ReefMind") and "## Mission" in new_program:
        with open(PROGRAM_FILE, "w") as f:
            f.write(new_program)
    else:
        print("  ⚠️  program.md rewrite malformed — keeping existing version")

    return decision