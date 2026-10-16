# 07. AgriRulePH Tech Stack

## A. Core Stack
- **Language:** Python 3.x
- **Web Framework:** Django
- **Database:** MySQL / MariaDB (primary), SQLite (development fallback)
- **Frontend:** Django Templates (HTML), Tailwind-style utility classes, custom CSS, vanilla JavaScript

## B. Project Components by Layer

### 1) Presentation Layer
- `templates/core/*.html`
- `templates/dashboard/*.html`
- `templates/admin/base_site.html`
- `static/css/main.css`

Purpose:
- Render public pages, results, analytics, and dashboard pages
- Handle lightweight client-side interaction (guidance panel, expand/collapse, transitions)

### 2) Application/Controller Layer
- `core/views.py`
- `dashboard/views.py`

Purpose:
- Handle request-response lifecycle
- Orchestrate consultation submission, result rendering, analytics rendering, and history
- Enforce staff-only dashboard access

### 3) Expert System Layer
- `expert_system/services/inference_engine.py`
- `expert_system/services/result_formatter.py`
- `expert_system/services/analytics_service.py`

Purpose:
- Execute deterministic rule-matching and scoring
- Build explanation traces and avoid logic
- Build analytics structures and dynamic interpretation text

### 4) Data Layer
- `expert_system/models.py`
- Django ORM + migrations

Primary entities:
- `Crop`
- `Rule`
- `Consultation`
- `ConsultationResult`

## C. Supporting Tooling
- `manage.py` commands:
  - migrations
  - seed command
  - runserver
  - createsuperuser
- Jupyter Notebook prototype:
  - `notebooks/agriruleph_rule_engine_demo.ipynb`

## D. AI/IS Method Classification
- **Method Used:** Rule-Based Reasoning (RBR), Expert System
- **Method Not Used:** Machine Learning model training/inference, deep learning, probabilistic forecasting

## E. Why This Stack Fits the Project
1. Django provides fast full-stack delivery for academic DSS projects.
2. Rule-based logic is explainable and matches Intelligent Systems expert-system objectives.
3. MySQL persistence supports consultations, dashboard CRUD, and analytics history.
4. Lightweight frontend keeps system maintainable and presentation-ready.

## F. Environment Notes
- Recommended:
  - Python 3.11+ (project may run on newer versions with dependency compatibility)
  - MySQL 8+ or MariaDB version compatible with selected Django release
- If MySQL client driver is unavailable in a specific local setup, SQLite fallback can be used temporarily for development.
