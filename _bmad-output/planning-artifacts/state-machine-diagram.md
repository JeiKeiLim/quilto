# Agent System State Machine

## Main Flow

```mermaid
stateDiagram-v2
    [*] --> ROUTE: User Input

    ROUTE --> BUILD_CONTEXT: Select domains

    state input_type <<choice>>
    BUILD_CONTEXT --> input_type
    input_type --> PLAN: QUERY
    input_type --> PARSE: LOG
    input_type --> BOTH_SPLIT: BOTH

    state BOTH_SPLIT {
        [*] --> PARSE_BRANCH
        [*] --> PLAN_BRANCH
        PARSE_BRANCH --> STORE_BRANCH
        PLAN_BRANCH --> QUERY_FLOW
    }

    PLAN --> RETRIEVE: Normal
    PLAN --> EXPAND_DOMAIN: Domain gap (proactive)
    PLAN --> CLARIFY: Non-retrievable gaps
    PLAN --> SYNTHESIZE: Already sufficient

    RETRIEVE --> ANALYZE

    state analysis_result <<choice>>
    ANALYZE --> analysis_result
    analysis_result --> SYNTHESIZE: Sufficient
    analysis_result --> PLAN: Insufficient (re-plan)
    analysis_result --> EXPAND_DOMAIN: Domain gap detected

    EXPAND_DOMAIN --> BUILD_CONTEXT: Rebuild with new domains

    CLARIFY --> WAIT_USER

    state user_response <<choice>>
    WAIT_USER --> user_response
    user_response --> ANALYZE: User provided info
    user_response --> SYNTHESIZE: User declined

    SYNTHESIZE --> EVALUATE

    state eval_result <<choice>>
    EVALUATE --> eval_result
    eval_result --> OBSERVE: Pass
    eval_result --> PLAN: Fail (retry)
    eval_result --> OBSERVE: Fail (over limit, partial)

    PARSE --> STORE
    STORE --> OBSERVE: Check significant log

    OBSERVE --> COMPLETE
    COMPLETE --> [*]
```

## Query Flow Detail

```mermaid
flowchart TD
    subgraph Entry
        A[User Input] --> B[ROUTE]
        B -->|classify + select domains| C[BUILD_CONTEXT]
    end

    subgraph QueryFlow[Query Flow]
        C -->|QUERY| D[PLAN]

        D -->|normal| E[RETRIEVE]
        D -->|domain gap| X[EXPAND_DOMAIN]
        D -->|non-retrievable| G[CLARIFY]
        D -->|already sufficient| I[SYNTHESIZE]

        E --> F[ANALYZE]

        F -->|sufficient| I
        F -->|insufficient| D
        F -->|domain gap| X

        X -->|rebuild context| C

        G --> H[WAIT_USER]
        H -->|info provided| F
        H -->|declined| I

        I --> J[EVALUATE]

        J -->|pass| K[OBSERVE]
        J -->|fail, retry| D
        J -->|fail, over limit| K
    end

    subgraph LogFlow[Log Flow]
        C -->|LOG| L[PARSE]
        L --> M[STORE]
        M --> K
    end

    subgraph Terminal
        K --> N[COMPLETE]
    end

    style X fill:#ffcccc
    style K fill:#ccffcc
    style N fill:#ccccff
```

## State Transitions Table

| From | To | Condition |
|------|-----|-----------|
| ROUTE | BUILD_CONTEXT | Always (domains selected) |
| BUILD_CONTEXT | PLAN | input_type == QUERY |
| BUILD_CONTEXT | PARSE | input_type == LOG |
| BUILD_CONTEXT | PLAN + PARSE | input_type == BOTH |
| PLAN | RETRIEVE | Normal planning |
| PLAN | EXPAND_DOMAIN | Proactive domain gap detected |
| PLAN | CLARIFY | Non-retrievable gaps exist |
| PLAN | SYNTHESIZE | Already have sufficient context |
| RETRIEVE | ANALYZE | Always |
| ANALYZE | SYNTHESIZE | verdict == SUFFICIENT |
| ANALYZE | PLAN | verdict == INSUFFICIENT |
| ANALYZE | EXPAND_DOMAIN | gap.outside_current_expertise |
| EXPAND_DOMAIN | BUILD_CONTEXT | Always (rebuild with new domains) |
| CLARIFY | WAIT_USER | Always |
| WAIT_USER | ANALYZE | User provided info |
| WAIT_USER | SYNTHESIZE | User declined |
| SYNTHESIZE | EVALUATE | Always |
| EVALUATE | OBSERVE | verdict == PASS |
| EVALUATE | PLAN | verdict == FAIL, retry_count < max |
| EVALUATE | OBSERVE | verdict == FAIL, retry_count >= max |
| PARSE | STORE | Always |
| STORE | OBSERVE | Always |
| OBSERVE | COMPLETE | Always |

## Domain Expansion Flow

```mermaid
sequenceDiagram
    participant P as Planner
    participant A as Analyzer
    participant F as Framework
    participant R as Retriever

    Note over P: Query mentions unfamiliar topic
    P->>F: domain_expansion_request: ["recovery"]
    F->>F: Load RecoveryModule
    F->>F: Rebuild ActiveDomainContext
    F->>P: New context with recovery expertise
    P->>R: Retrieve with expanded vocabulary
    R->>A: Entries

    Note over A: Found data needing expertise
    A->>F: gap.outside_current_expertise = true
    A->>F: gap.suspected_domain = "nutrition"
    F->>F: Load NutritionModule
    F->>F: Rebuild ActiveDomainContext
    F->>A: Re-analyze with nutrition expertise
```

## Observer Integration

```mermaid
flowchart LR
    subgraph Triggers
        A[Query Complete] -->|post_query| O[OBSERVE]
        B[User Correction] -->|user_correction| O
        C[Significant Log] -->|significant_log| O
    end

    O --> D{Should Update?}
    D -->|yes| E[Update Global Context]
    D -->|no| F[Skip]

    E --> G[COMPLETE]
    F --> G
```
