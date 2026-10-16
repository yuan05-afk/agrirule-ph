# 04. Project Report Template (AgriRulePH Filled Guide)

Use this as the direct writing guide for your final PDF report.

---

## 1. Cover Page
- **Project Title:** AgriRulePH: A Rule-Based Crop Planning Decision Support System for Small-Scale Farmers in the Philippines
- **Group Members and IDs:** [FILL]
- **Course:** Intelligent Systems
- **Instructor:** [FILL]
- **Submission Date:** [FILL]

## 2. Table of Contents
- Auto-generate based on section headers in your final document.

## 3. Executive Summary
Include:
- Brief project overview
- Problem addressed (crop planning uncertainty for small-scale farmers)
- Solution approach (rule-based expert system with explainable outputs)
- Key results (ranked crops, avoid list, analytics insights, what-if behavior)

## 4. Introduction
Include:
- Background of crop planning challenges
- Motivation for explainable DSS in agriculture
- Scope and objectives
- High-level boundaries (no ML, no real-time feeds)

## 5. Literature Review / Related Work
Include:
- Rule-based expert systems in agriculture
- Crop recommendation systems and explainability
- How AgriRulePH differs:
  - deterministic scoring
  - trace visibility
  - avoid-focused warnings
  - integrated analytics page

## 6. Methodology / System Design
Include:
- Rule-based reasoning flow
- IF-THEN rule structure
- Matching and scoring strategy
- Avoid/disqualification logic
- System architecture diagram:
  - UI -> Django Views -> Inference/Analytics Services -> Models/DB
- Optional pseudocode of `run_inference`

## 7. Implementation
Include:
- Tools: Python, Django, MySQL, HTML/CSS/JS
- Core modules:
  - `core/views.py`
  - `expert_system/services/inference_engine.py`
  - `expert_system/services/analytics_service.py`
  - `expert_system/services/result_formatter.py`
  - templates in `templates/core/`
- Seed data summary:
  - crop count
  - rule count
- Screenshots:
  - Consultation page
  - Results page
  - Analytics page
  - Dashboard pages

## 8. Results & Analysis
Include:
- Test scenarios and outputs
- Ranking outcomes
- Avoid outcomes
- Interpretation of what-if scenario changes
- Metrics summary table (consistency, explainability coverage, avoid detection)

## 9. Ethical Considerations
Include:
- System is advisory and educational, not a replacement for expert agronomy
- Potential bias from rule design and limited knowledge base
- Need for local validation before real farming investment decisions

## 10. Conclusion & Recommendations
Include:
- Summary of what was achieved
- What worked well
- Key limitations
- Future improvements (localized rules, richer scenario controls, domain validation)

## 11. References
List all:
- Books/articles used
- Official documentation
- Agricultural references
- Websites/datasets

## 12. Appendices
Include:
- Full source code snapshots or repository structure
- Extra diagrams/flowcharts
- Raw scenario outputs
- Additional tables not in main report

---

## PDF Assembly Checklist
- All required sections present
- Figures/tables numbered and captioned
- In-text references included
- Final formatting checked
- Exported to PDF
