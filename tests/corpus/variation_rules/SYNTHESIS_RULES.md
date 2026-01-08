# Workout Log Synthesis Rules

This document describes how to convert raw CSV workout data into natural, unstructured Korean workout journal entries. The goal is to create realistic test data that mimics the user's actual writing style.

## Purpose

The synthesized logs are used for testing the Swealog framework's ability to:
1. Parse unstructured text input
2. Extract structured data (exercises, weights, reps, sets)
3. Handle natural language variations

## Reference: User's Actual Writing Style

### Example 1 (2025-12-31)
```
데빌 프레스 덤벨 10키로씩 총 20키로 들고 2분 동안 10개하고 알아서 휴식 10세트 진행했음.
심박수 190근처까지 찍고 생각보다 힘들어서 중간에 포기하고 싶었으나 끝까지 해냈음.
다시 생각해보니 12키로로 했어도 어떻게든 끝까지 했을수도 있었겠다는 생각이 듬.
```

### Example 2 (2026-01-02)
```
인클라인 덤벨프레스 25키로 한쪽씩 해서 3세트 10개씩 진행함. 마지막 세트에서 힘들긴 했지만 전체으로 큰 무리는 없던걸로 봐서 더 할수도 있을듯? 그러면서 동시에 슈퍼세트로 행잉레그이즈 10개와 풀업 병행함. 풀업 처음에는 맨몸으로 9개 그 뒤는 5키로 매달고 네거티브로 진행함.
그리고나서 푸쉬프레스 10개씩 EMOM으로 함. 숨이 차지는 않았는데 어깨가 너무 털려서 힘들었음. 4라운드 까지는 5키로씩 양쪽에 달고 총 30키로로 진행. 어깨가 너무 털려서 2.5키로씩 양쪽에 달고 2라운드 진행 그리고 이것도 너무 어깨가 힘들어서 나머지는 빈봉 20키로로 계속 진행함. 숨은 전혀 차지 않았음. 심박수 160대 유지한거같음
```

### Example 3 (2026-01-03)
```
러닝머신에서 5키로 뜀. 천천히 시작해서 9kph로 뛰었을때 심박수 172정도 계속 유지함.
기존에 러닝시 왼쪽 정강이가 먼저 지치는 경향이 있었는데 팔치기에서 어깨에 힘을 푸니 이런 현상이 거의 없었음. 기존에 어깨에 너무 힘을 주고 러닝을 했던걸로 생각이 됨.
```

## Key Writing Style Characteristics

### 1. Language
- Written entirely in Korean
- Casual, conversational tone (반말)
- No formal structure or headers

### 2. Exercise Descriptions
- Exercise names in Korean (abbreviated or full)
  - 덤벨프레스, 인클라인 프레스, 푸쉬프레스, 데드리프트, 스쿼트, 벤치프레스, etc.
- Weight notation patterns:
  - Dumbbells: "25키로 한쪽씩", "10키로씩 양손에", "10키로씩 총 20키로"
  - Barbells: "30키로", "총 30키로", "80키로로"
  - Bodyweight: "맨몸으로"
- Sets/Reps patterns:
  - "3세트 10개씩", "5세트 진행함", "10개하고", "렙수는 8, 6, 5개씩"
  - Progressive weight: "80키로에서 시작해서 60키로까지 드랍"

### 3. Feelings & Observations (mix in naturally)
- Difficulty: "힘들었음", "너무 힘들었음", "생각보다 힘들어서", "어깨가 털렸음"
- Easy: "큰 무리없이", "무난하게", "수월했음"
- Body sensations: "어깨가 뻐근함", "허리가 뻣뻣했음", "무릎이 찌릿"
- Heart rate (optional): "심박수 190근처", "심박수 160대 유지"
- Breathing: "숨이 차지는 않았음", "숨이 찼음"

### 4. Reflections (occasional)
- "다음에는 무게를 올려봐야겠다"
- "폼에 더 집중해야할듯"
- "더 할수도 있을듯?"
- "이 무게에서 좀 더 안정화되면 올려야겠다"

### 5. Flow & Connectors
- Between exercises: "그리고나서", "이어서", "그 뒤는", "그다음"
- Supersets: "동시에", "슈퍼세트로", "병행함"
- No explicit separations - just flows naturally

## CSV Column Reference

The raw CSV has these columns:
- 날짜: Date and time
- 워크아웃 이름: Workout session name (e.g., "저녁 워크아웃", "오후 워크아웃")
- 지속 시간: Duration
- 운동 이름: Exercise name in English (convert to Korean)
- 세트 순서: Set number
- 체중: Weight in kg
- 렙: Reps
- 거리: Distance (for cardio)
- 초: Seconds (for timed exercises)
- RPE: Rate of Perceived Exertion (rarely used)

## Exercise Name Translations

| English | Korean |
|---------|--------|
| Trap Bar Deadlift | 트랩바 데드리프트 |
| Push Press | 푸쉬프레스 |
| Bench Press (Barbell) | 바벨 벤치프레스 / 벤치프레스 |
| Bench Press (Dumbbell) | 덤벨 벤치프레스 |
| Front Squat (Barbell) | 프론트 스쿼트 |
| Squat (Barbell) | 바벨 스쿼트 / 스쿼트 |
| Incline Bench Press (Barbell) | 인클라인 벤치프레스 |
| Incline Bench Press (Dumbbell) | 인클라인 덤벨프레스 |
| Deadlift (Barbell) | 데드리프트 |
| Sumo Deadlift (Barbell) | 스모 데드리프트 |
| Overhead Press (Barbell) | 오버헤드프레스 |
| Seated Overhead Press (Barbell) | 시티드 프레스 |
| Strict Military Press (Barbell) | 밀리터리프레스 |
| T Bar Row | 티바로우 |
| Bent Over One Arm Row (Dumbbell) | 원암 덤벨로우 |
| Bent Over Row (Dumbbell) | 덤벨로우 |
| Pull Up | 풀업 |
| Lat Pulldown (Cable) | 랫풀다운 |
| Seated Row (Cable) | 시티드 로우 |
| Arnold Press (Dumbbell) | 아놀드프레스 |
| Lateral Raise (Dumbbell) | 레터럴레이즈 |
| Lateral Raise (Cable) | 케이블 레터럴레이즈 |
| Bicep Curl (Barbell) | 바벨컬 |
| Bicep Curl (Dumbbell) | 덤벨컬 |
| Floor Press (Barbell) | 플로어프레스 |
| Ab Mat Sit-up | 싯업 |
| Sit Up | 싯업 |
| Push Up | 푸쉬업 |
| Decline Crunch | 크런치 |
| Iso-Lateral Chest Press (Machine) | 머신 체스트프레스 |
| Iso-Lateral Row (Machine) | 머신 로우 |
| Overhead Squat (Barbell) | 오버헤드 스쿼트 |
| Standing Calf Raise (Dumbbell) | 카프레이즈 |

## Synthesis Guidelines

### DO:
1. Write in natural, flowing Korean without structure
2. Vary sentence patterns and connectors
3. Occasionally add feelings, reflections, or body observations
4. Round weights to natural numbers when they look awkward (e.g., 22.68 → 약 23키로 or 22키로 좀 넘게)
5. Combine multiple sets into summaries rather than listing each
6. Use casual abbreviations (키로 instead of 킬로그램)

### DON'T:
1. Don't use bullet points, headers, or structured format
2. Don't list every single set explicitly
3. Don't use formal language (존댓말)
4. Don't include the date in the content (it's in the filename)
5. Don't make it too long - keep it natural and concise

### Variation Ideas (add occasionally):
- Mention superset combinations
- Comment on weight progression patterns
- Note if something felt different than usual
- Reference past performance (짧막하게)
- Mention training method (EMOM, 드랍세트, 네거티브, etc.)

## Output Structure

- Input: `raw/YYYY-MM-DD.md` (contains raw CSV data)
- Output: `synthesized/YYYY-MM-DD.md` (unstructured Korean journal entry)

Each synthesized file should contain ONLY the unstructured text - no headers, no metadata, just the journal entry as the user would write it.
