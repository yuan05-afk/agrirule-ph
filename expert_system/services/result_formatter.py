import re


def confidence_label(score_percent):
    if score_percent >= 85:
        return 'Very Strong Match'
    if score_percent >= 70:
        return 'Strong Match'
    if score_percent >= 50:
        return 'Moderate Match'
    return 'Limited Match'


def short_explanation_summary(lines):
    if not lines:
        return 'This option is included as a fallback based on available rule coverage.'
    top = [line for line in lines[:2] if line]
    return ' '.join(top)


def build_decision_summary(consultation, top3, avoid_results):
    if not top3:
        return [
            'No strong recommendation was found from current rules.',
            'Review the consultation inputs and verify field conditions before deciding.',
            'Consult your local agriculture office for site-specific validation.',
        ]

    def _name(item):
        return item.get('crop_name') or item.get('crop_obj').name

    top_name = _name(top3[0])
    alternatives = [_name(item) for item in top3[1:3]]
    strongest_conditions = [
        f"season is {consultation.get_season_display()}",
        f"water availability is {consultation.get_water_availability_display()}",
        f"soil type is {consultation.get_soil_type_display()}",
    ]

    points = [
        f"{top_name} is the top recommendation based on your current farm profile.",
        f"The next best alternatives are {', '.join(alternatives)}." if alternatives else 'No strong alternatives were found beyond the top recommendation.',
        f"The strongest matched conditions include {', '.join(strongest_conditions)}.",
    ]

    if avoid_results:
        avoid_names = ', '.join([x.crop.name for x in avoid_results[:3]])
        points.append(f"Avoid-list crops include {avoid_names} due to critical mismatches in current conditions.")

    return points


def build_condition_assessment(consultation):
    season = consultation.get_season_display()
    water = consultation.get_water_availability_display()
    soil = consultation.get_soil_type_display()
    ph = consultation.get_soil_ph_category_display()
    farm = consultation.get_farm_type_display()
    budget = consultation.get_budget_level_display()

    return [
        {
            'label': 'Season Fit',
            'meta': f'{season}',
            'note': f'{season} conditions favor crops with matching growth windows.',
        },
        {
            'label': 'Water Profile',
            'meta': f'{water}',
            'note': f'{water} water availability supports crops that perform under current irrigation assumptions.',
        },
        {
            'label': 'Soil Compatibility',
            'meta': f'{soil} + {ph} pH',
            'note': f'{soil} soil and {ph} pH are key drivers behind suitability differences.',
        },
        {
            'label': 'Operations Fit',
            'meta': f'{farm} + {budget} budget',
            'note': f'{farm} setup with {budget.lower()} budget suggests practical planting scope.',
        },
    ]


def _sentence_bullets(text):
    parts = [part.strip() for part in re.split(r'(?<=[.!?])\s+', text.strip()) if part.strip()]
    return parts or [text.strip()]


def build_action_recommendations(consultation, top3, avoid_results):
    top_crop = (top3[0].get('crop_name') if top3 else None) or 'your selected crop set'
    alt_crop = (top3[1].get('crop_name') if len(top3) > 1 else None) or 'a secondary suitable crop'
    avoid_crop = avoid_results[0].crop.name if avoid_results else 'high-risk crops in current conditions'

    season = consultation.get_season_display()
    soil = consultation.get_soil_type_display()
    water = consultation.get_water_availability_display()
    farm = consultation.get_farm_type_display()
    ph = consultation.get_soil_ph_category_display()
    budget = consultation.get_budget_level_display()
    preference = consultation.get_crop_preference_display()

    preference_advice = {
        'Staple': 'food-security priorities',
        'Vegetable': 'faster market turnover',
        'Resilient Crop': 'climate-risk tolerance',
    }
    budget_advice = {
        'Low': 'Use a phased input plan to protect cash flow during early crop establishment.',
        'Medium': 'Balance input spending across land prep, nutrition, and basic crop protection.',
        'High': 'Allocate budget to better seed quality, irrigation stability, and preventive field monitoring.',
    }

    avoid_reason = 'rule-based suitability is low under the current profile'
    if avoid_results:
        avoid_lines = [line.strip() for line in avoid_results[0].explanation_text.splitlines() if line.strip()]
        negative_lines = [line for line in avoid_lines if line.lower().startswith('-') or 'avoid' in line.lower() or 'unsuitable' in line.lower()]
        if negative_lines:
            avoid_reason = negative_lines[0]

    primary_text = (
        f"Prioritize {top_crop} for the next planting cycle because {season} season conditions, "
        f"{soil} soil, {water} water availability, and {farm} setup align with its current suitability profile. "
        f"Use the planting note as your first field-level guide."
    )
    alternative_text = (
        f"Keep {alt_crop} as a strong backup crop since it also aligns with the current condition set and your "
        f"{preference.lower()} preference focus. This gives flexibility if market demand, seed availability, or "
        f"field preparation constraints affect {top_crop} execution."
    )
    avoidance_text = (
        f"Delay or avoid {avoid_crop} under the current setup because {avoid_reason}. "
        f"Re-evaluate this crop only after key limiting conditions are improved."
    )
    farm_text = (
        f"Before final planting, confirm real water reliability, field {ph} pH behavior, and near-term land readiness. "
        f"{budget_advice.get(budget, 'Review input plan and field constraints carefully.')} "
        f"Small shifts in irrigation, soil suitability, or operational conditions can change final rankings."
    )

    return {
        'primary_action': _sentence_bullets(primary_text),
        'alternative_action': _sentence_bullets(alternative_text),
        'avoidance_action': _sentence_bullets(avoidance_text),
        'farm_management_advice': _sentence_bullets(farm_text),
    }


def confidence_legend_items():
    return [
        {'label': 'Very Strong Match', 'range': '85-100%', 'note': 'Most key rules aligned with current farm conditions.'},
        {'label': 'Strong Match', 'range': '70-84%', 'note': 'Good alignment with minor mismatches.'},
        {'label': 'Moderate Match', 'range': '50-69%', 'note': 'Useful option with notable tradeoffs.'},
        {'label': 'Limited Match', 'range': 'Below 50%', 'note': 'Low confidence; consider alternatives.'},
    ]


def extract_numeric_points(line):
    match = re.search(r'([+-]?\d+)\s*points?', line.lower())
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return 0
    return 0
