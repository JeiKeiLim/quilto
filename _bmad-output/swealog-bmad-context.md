# Swealog (쇠록) — BMAD Context Document

## Project Name
**Swealog (쇠록)**

- Korean: 쇠 (iron) + 록 (record) — "Iron Log"
- English: Sweat + Log — "Sweat Log"

---

## Origin Story

I did devil press for the first time. I asked ChatGPT for a recommendation — it suggested 20kg each hand, 10 reps, 90 seconds rest. It was way too hard. I couldn't do it. I adjusted to 10kg each hand, 10 reps, 120 seconds rest for 10 rounds.

When I questioned ChatGPT, it admitted the recommendation was based on someone who does CrossFit-style conditioning regularly. But I don't — I've been doing bodybuilding-style training. The AI didn't know me.

**That was the moment:** If an AI agent knew my workout style and history, it would have given me proper suggestions.

---

## Problem Statement

**AI fitness advice is generic because it has no memory of you.**

Current AI assistants (ChatGPT, Gemini, etc.) give recommendations for "someone who matches your age/weight/stated goal" — not for *you*, the person with a specific training history, style, and accumulated context.

Current workout apps think they're in the logging business. AI companies think they're in the general assistant business. The gap is **persistent, domain-specific personal context.**

---

## Solution

An AI-native fitness app where:

1. Users log workouts freely via text or voice (no rigid forms)
2. AI structures and stores the data
3. Over time, AI builds deep context about the user's training
4. When users ask for advice, the AI responds as **a coach who's watched every session**

**The logging is the mechanism, not the product. The context IS the product.**

---

## Value Proposition

> "The AI that remembers every rep."

Or: "A coach who's watched every session."

Unlike traditional logging apps that compete on UI and feature checklists, Swealog competes on interpretation quality and insight generation — AI that actually knows your training history when it gives advice.

---

## What Makes This AI-Native

| Traditional Apps | Swealog |
|------------------|---------|
| User conforms to app's data schema | User speaks naturally, AI handles the schema |
| AI as feature layer on structured data | AI as the core, data organized around AI understanding |
| "Personalized" = picked muscle building vs weight loss | Personalized = knows you don't do conditioning work |
| Competes with Strong/Hevy | Competes with generic ChatGPT conversations |

---

## Target Users

**Sweet spot:** Intermediate lifters who want to track but find current apps tedious.

- Serious lifters already have logging habits (might resist losing structured data)
- Casual gym-goers might not care enough to log at all
- Intermediate folks want to track, appreciate lower friction, and would value contextualized advice

---

## Interaction Models

All three, not just one:

1. **Log → Passive insights**
   - "Noticed your pressing volume dropped — fatigue?"
   - "You mention knee tightness after heavy deadlift weeks"

2. **Ask questions → Contextualized answers**
   - "What weight for devil press?" uses your history
   - "Should I deload?" considers your recent sessions

3. **Proactive suggestions**
   - "You haven't hit shoulders directly in 2 weeks"
   - "Based on your last 30 sessions, your squat is plateauing — here's why"

---

## Cold Start Solution

**Onboarding interview** — like a personal trainer on day one.

Questions to capture:
- Training style/background (bodybuilding, CrossFit, powerlifting, casual)
- Current frequency and typical split
- Experience level / years training
- Any injuries or limitations
- Goals (strength, hypertrophy, conditioning, general health)
- Anchor lifts (what do you bench/squat/deadlift)

5-10 minutes of conversation. Now the AI knows you're a bodybuilding-style lifter who trains 4x/week, hasn't done much conditioning work, and has a tweaky lower back. Devil press recommendation instantly gets better.

---

## Why Not Just Paste Workout History Into ChatGPT?

1. **Context length limits** — ChatGPT can't hold 6 months of logs
2. **No continuity** — loses context over time, across sessions
3. **Friction** — copy/paste every time is tedious
4. **No structure** — raw logs don't provide the patterns

Swealog is a **structured, growing context** that gets more valuable over time. Six months in, you have:
- Every exercise you've done and at what intensity
- Patterns the AI can reference ("last time you tried a new movement, X happened")
- Your own language and how you describe effort

That's not reproducible by pasting logs into ChatGPT.

---

## Technical Approach (Phased)

### Phase 1: Local Web App (MVP for personal use)
- FastAPI or Flask backend
- SQLite or markdown files for storage (Obsidian-compatible option)
- Minimal frontend — textarea input, history list view
- Claude API for structuring input and generating insights

**Core loop:**
```
Raw input → Claude structures to JSON/markdown → Store → Display history
```

### Phase 2: Expand & Validate
- Voice input (browser Web Speech API or paste from phone)
- Insight generation ("what patterns do you see in my last month?")
- Recommendation engine ("what should I do for my new exercise?")

### Phase 3: Standalone iOS App
- Once validated and core features proven
- Native iOS development
- Potential cloud sync

---

## Data Model (Initial Thinking)

Let Claude infer from freeform input, normalize to structure like:

```markdown
## 2024-01-15 - Upper Body
- Bench Press: 5x5 @ 185lb (RPE 8, last set grind)
- Incline DB Press: 4x10 @ 60lb
- Notes: Shoulder felt tight on warmup
- Energy: Medium
- Style: Hypertrophy
```

Key attributes to capture:
- Date
- Exercises, sets, reps, weight
- Subjective effort (RPE, "felt heavy", "had more in the tank")
- Physical notes (tightness, pain, energy level)
- Workout style/type

---

## Key Differentiators

1. **Input freedom** — No forms, no dropdowns. Just talk/type naturally.
2. **Accumulated context** — AI knows your 6-month history, not just today's session.
3. **Proactive intelligence** — Doesn't wait for questions. Notices patterns.
4. **Style-aware** — Knows you're a bodybuilder, not a CrossFitter.
5. **Memory that grows** — More valuable the longer you use it.

---

## Risks & Assumptions to Validate

| Assumption | Risk | Validation |
|------------|------|------------|
| Users will log consistently with lower friction | Might be habit issue, not friction issue | Dogfood myself for 4-6 weeks |
| AI can reliably structure freeform input | Edge cases, inconsistencies | Test with messy real inputs |
| Cold start interview provides enough context | Might need more sessions before useful | Compare day-1 advice vs week-4 advice |
| Context makes advice meaningfully better | Might be marginal improvement | A/B test generic vs contextualized recs |

---

## Founder Context

- PhD in Computer Engineering, thesis on automatic assessment of anaerobic workout using single inertial sensor (uLift)
- Same problem domain (understanding workouts automatically), new approach (AI context instead of hardware sensors)
- Training background: bodybuilding-style, intermediate lifter
- Will dogfood extensively before any external release

---

## Open Questions for BMAD

1. What's the minimum context needed before advice becomes meaningfully better than generic?
2. How to handle conflicting information in logs (user says different things on different days)?
3. Privacy model — local-only vs. cloud sync?
4. Should there be explicit "training style" classification or let it emerge from logs?
5. Integration with existing tools (Apple Health, Strava) — value or distraction?

---

## Success Criteria (Personal MVP)

1. I actually use it consistently for 30+ days
2. I ask it for advice and it gives better answers than ChatGPT would
3. It catches a pattern I didn't notice myself
4. The friction of logging feels lower than my current method (or no method)

---

## The Pitch (One-liner)

> "I asked AI for a workout recommendation. It was wrong because it didn't know me. Swealog is the AI that does."
