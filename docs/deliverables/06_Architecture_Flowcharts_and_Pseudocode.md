# 06. Architecture Diagram, Flowcharts, and Pseudocode

This document provides architecture and logic-flow artifacts for AgriRulePH.

## A. System Architecture Diagram (Mermaid)

```mermaid
flowchart LR
    U[Farmer/User] --> UI[Web UI<br/>Django Templates]
    UI --> V[core/views.py]
    V --> IE[Inference Engine<br/>run_inference()]
    V --> RF[Result Formatter]
    V --> AS[Analytics Service]

    IE --> DB[(MySQL / SQLite)]
    RF --> DB
    AS --> DB
    V --> DB

    DB --> M[Models:<br/>Crop, Rule,<br/>Consultation, ConsultationResult]
    M --> V

    A[Staff/Admin] --> D[Dashboard Views]
    D --> DB
    A --> DA[Django Admin]
    DA --> DB
```

## B. Consultation-to-Results Flowchart

```mermaid
flowchart TD
    S[Start Consultation] --> F[User submits farm conditions]
    F --> VAL{Form valid?}
    VAL -- No --> ERR[Show validation errors]
    VAL -- Yes --> SAVE1[Save Consultation record]
    SAVE1 --> RUN[Run rule-based inference]
    RUN --> SCORE[Compute crop scores + avoid flags + traces]
    SCORE --> SAVE2[Persist ConsultationResult rows]
    SAVE2 --> RES[Render Results page]
    RES --> ANA[Open Decision Analytics page]
```

## C. Rule Matching and Scoring Flowchart

```mermaid
flowchart TD
    A[Load active crops and active rules] --> B[Initialize all crop scores = 0]
    B --> C[For each rule: check condition match]
    C --> M{Rule matched?}
    M -- No --> C
    M -- Yes --> T{Rule type}
    T -- positive --> P[Add score]
    T -- negative --> N[Subtract score]
    T -- avoid --> V[Apply strong penalty + mark avoid]
    P --> TR[Append explanation trace]
    N --> TR
    V --> TR
    TR --> C
    C --> RANK[Rank crops by score]
    RANK --> FILTER[Exclude avoid crops from main recommendations]
    FILTER --> OUT[Return recommendations + avoid list + traces]
```

## D. Decision Analytics Flowchart

```mermaid
flowchart TD
    R[Load Consultation + Result rows] --> TOP10[Build top-10 ranked rows]
    TOP10 --> POD[Build top recommendation podium]
    TOP10 --> CAT[Build category opportunity chart]
    TOP10 --> FACT[Build factor match strength]
    TOP10 --> TIER[Build suitability tiers]
    TOP10 --> TAB[Build recommendation insights table]
    R --> WHATIF[Generate what-if scenarios via re-run inference]
    WHATIF --> ADJ[Build field adjustment opportunities]
    TOP10 --> TRADE[Build crop trade-off comparison]
    POD --> INT[Generate dynamic interpretation layer]
    CAT --> INT
    FACT --> INT
    WHATIF --> INT
    TAB --> INT
    INT --> PAGE[Render analytics page]
```

## E. Core Pseudocode

### 1) Inference Engine (Simplified)
```text
function run_inference(facts, top_n=3):
    active_crops = get_active_crops()
    active_rules = get_active_rules_for_active_crops()

    scores = {crop_id: 0}
    avoid_flags = {crop_id: false}
    trace_map = {crop_id: []}

    for rule in active_rules:
        if rule_matches_facts(rule, facts):
            if rule.type == "positive":
                scores[rule.crop_id] += abs(rule.score)
            else if rule.type == "negative":
                scores[rule.crop_id] -= abs(rule.score)
            else if rule.type == "avoid":
                scores[rule.crop_id] -= strong_penalty
                avoid_flags[rule.crop_id] = true
            trace_map[rule.crop_id].append(rule.explanation)

    avoid_list = build_avoid_list(avoid_flags, scores, trace_map)
    ranked = rank_crops(scores, exclude_avoid=true)
    recommendations = ranked[0:top_n]

    return {
        recommendations,
        avoid_list,
        all_scores: scores,
        trace_map
    }
```

### 2) Consultation Flow (Simplified)
```text
on POST /consult:
    validate input form
    save Consultation
    inference = run_inference(cleaned_data)

    for each active crop:
        create ConsultationResult(
            score,
            explanation_text,
            is_recommended,
            is_avoid,
            rank_order
        )

    redirect to /results/<consultation_id>/
```

### 3) Analytics Interpretation Layer (Simplified)
```text
function build_interpretations(analytics_data):
    derive section-level summaries from:
      - top10 pattern
      - podium gaps
      - category dominance
      - factor strengths
      - what-if sensitivity
      - insights table indicators

    return {
      top10_key_insight,
      top10_recommended_action,
      ...
      table_key_insight,
      table_recommended_action
    }
```

## F. Notes for Report Use
- Copy diagrams into your report under Methodology/System Design.
- If Mermaid rendering is unavailable in your editor, export diagrams using a Mermaid live renderer and insert as images.
- Keep pseudocode synchronized with actual service code before final submission.
