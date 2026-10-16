# 02. Solution Design and Implementation

## Solution Overview
AgriRulePH is a **deterministic rule-based expert system** implemented as a Django web application. It evaluates user-provided farm conditions against a crop-rule knowledge base and returns ranked crop options, avoid flags, and explanation traces.

## Design Choice
- Core AI approach: **Rule-Based Reasoning (RBR)**
- Not used: ML model training, neural networks, probabilistic prediction
- Reason for approach: transparent, explainable, and suitable for academic DSS implementation

## High-Level Architecture

1. **Presentation Layer**
- Django templates (`templates/core/*.html`, `templates/dashboard/*.html`)
- Tailwind-style utility classes + custom CSS (`static/css/main.css`)

2. **Application Layer**
- Public workflow (`core/views.py`): consult, results, analytics, history
- Dashboard workflow (`dashboard/views.py`): crop/rule/consultation management

3. **Expert System Layer**
- Inference engine (`expert_system/services/inference_engine.py`)
- Formatting helpers (`expert_system/services/result_formatter.py`)
- Analytics helpers (`expert_system/services/analytics_service.py`)

4. **Data Layer**
- MySQL (primary runtime) with SQLite fallback
- Models in `expert_system/models.py`:
  - `Crop`
  - `Rule`
  - `Consultation`
  - `ConsultationResult`

## Core Rule Logic

### Rule Matching
- A rule matches when all non-empty condition fields match consultation facts.
- Blank condition fields are treated as wildcard.

### Scoring
- `positive` rules add points
- `negative` rules subtract points
- `avoid` rules heavily penalize and flag crops
- Avoid threshold and explicit avoid hits are both considered

### Output
- Top recommendations (ranked)
- Avoid list with reasons
- Score map and explanation trace map

## Implemented Features (Current System)

1. Public pages:
- Home, About, Consultation, Results, History

2. Dashboard:
- Staff-only access for crop/rule/consultation management

3. Results features:
- Top 3 cards
- Expandable top-10 options
- Crops to avoid
- Confidence legend
- Condition assessment
- Action recommendations

4. Analytics features:
- Top-10 comparison
- Top recommendation podium
- Category opportunity chart
- Condition match strength by factor
- Crop trade-off comparison
- Field adjustment opportunities
- Suitability tier groups
- What-if analysis
- Recommendation insights table
- Interpretation layer (`Key Insight`, `Recommended Action`) in selected sections

## Implementation Stack
- Python 3.x
- Django
- MySQL / MariaDB
- HTML/CSS/vanilla JavaScript
- Optional Jupyter notebook for rule-engine prototyping

## Why This Design Fits Intelligent Systems
- Uses symbolic reasoning and explicit knowledge base
- Produces explainable outputs
- Supports scenario analysis without black-box modeling
- Demonstrates practical DSS architecture end-to-end
