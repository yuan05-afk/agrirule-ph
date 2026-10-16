from collections import Counter, defaultdict

from expert_system.models import ConsultationChoices, Crop, Rule
from expert_system.services.inference_engine import run_inference
from expert_system.services.result_formatter import confidence_label, extract_numeric_points, short_explanation_summary


FACTOR_KEYWORDS = {
    'season': ['season'],
    'soil_type': ['soil'],
    'water_availability': ['water'],
    'farm_type': ['farm'],
    'soil_ph': ['ph', 'alkaline', 'acidic', 'neutral'],
    'budget': ['budget', 'capital'],
    'crop_preference': ['preference', 'staple', 'vegetable', 'resilient'],
}


def build_ranked_rows(non_avoid_results):
    top_score = max([item.score for item in non_avoid_results], default=0)
    denom = max(top_score, 1)
    rows = []
    for idx, item in enumerate(non_avoid_results, start=1):
        percent = max(0, min(100, int(round((item.score / denom) * 100))))
        lines = [line for line in item.explanation_text.splitlines() if line.strip()]
        rows.append(
            {
                'rank': idx,
                'crop_id': item.crop_id,
                'crop_name': item.crop.name,
                'category': item.crop.get_category_display(),
                'score': item.score,
                'score_percent': percent,
                'normalized_score': percent,
                'confidence_label': confidence_label(percent),
                'explanation_lines': lines,
                'explanation_count': len(lines),
                'short_reason': short_explanation_summary(lines),
                'is_avoid': item.is_avoid,
                'status': 'Recommended' if idx <= 3 else 'Secondary',
                'crop_obj': item.crop,
                'display_rank': idx,
            }
        )
    return rows


def build_factor_contributions(top_row):
    totals = defaultdict(int)
    for line in top_row.get('explanation_lines', []):
        points = extract_numeric_points(line)
        lower = line.lower()
        matched_factor = None
        for factor, keywords in FACTOR_KEYWORDS.items():
            if any(keyword in lower for keyword in keywords):
                matched_factor = factor
                break
        if matched_factor is None:
            continue
        totals[matched_factor] += points

    factors = [
        ('season', 'Season'),
        ('soil_type', 'Soil Type'),
        ('water_availability', 'Water Availability'),
        ('farm_type', 'Farm Type'),
        ('soil_ph', 'Soil pH'),
        ('budget', 'Budget'),
        ('crop_preference', 'Crop Preference'),
    ]

    max_val = max([abs(v) for v in totals.values()], default=1)
    payload = []
    for key, label in factors:
        value = totals.get(key, 0)
        width = int((abs(value) / max_val) * 100) if max_val else 0
        payload.append({'factor_key': key, 'factor_label': label, 'value': value, 'width': width})
    return payload


def build_category_distribution(top10_rows):
    counter = Counter([row['category'] for row in top10_rows])
    total = max(len(top10_rows), 1)
    payload = []
    for category, count in counter.items():
        payload.append({'category': category, 'count': count, 'percent': int(round((count / total) * 100))})
    payload.sort(key=lambda x: x['count'], reverse=True)
    return payload


def _consultation_to_facts(consultation):
    return {
        'season': consultation.season,
        'soil_type': consultation.soil_type,
        'water_availability': consultation.water_availability,
        'farm_type': consultation.farm_type,
        'soil_ph_category': consultation.soil_ph_category,
        'budget_level': consultation.budget_level,
        'crop_preference': consultation.crop_preference,
    }


def _water_downshift(value):
    order = [
        ConsultationChoices.WaterAvailability.LOW,
        ConsultationChoices.WaterAvailability.MODERATE,
        ConsultationChoices.WaterAvailability.HIGH,
    ]
    idx = order.index(value) if value in order else 0
    return order[max(0, idx - 1)]


def generate_what_if_scenarios(consultation):
    base_facts = _consultation_to_facts(consultation)
    active_crops = list(Crop.objects.filter(is_active=True).order_by('name'))
    active_rules = list(
        Rule.objects.filter(is_active=True, crop__is_active=True)
        .select_related('crop')
        .order_by('crop__name', 'name')
    )

    scenarios = [
        {
            'name': 'Season Shift Scenario',
            'change': 'Season flip',
            'facts': {**base_facts, 'season': ConsultationChoices.Season.DRY if consultation.season == ConsultationChoices.Season.WET else ConsultationChoices.Season.WET},
        },
        {
            'name': 'Reduced Water Scenario',
            'change': 'Water one-step lower',
            'facts': {**base_facts, 'water_availability': _water_downshift(consultation.water_availability)},
        },
        {
            'name': 'Farm Type Switch Scenario',
            'change': 'Farm type flip',
            'facts': {**base_facts, 'farm_type': ConsultationChoices.FarmType.RAINFED if consultation.farm_type == ConsultationChoices.FarmType.IRRIGATED else ConsultationChoices.FarmType.IRRIGATED},
        },
    ]

    base_result = run_inference(base_facts, top_n=10, crops=active_crops, rules=active_rules)
    base_top = base_result['recommendations'][0] if base_result['recommendations'] else None
    base_top_score = base_top['score'] if base_top else 0

    payload = []
    for scenario in scenarios:
        result = run_inference(scenario['facts'], top_n=10, crops=active_crops, rules=active_rules)
        top = result['recommendations'][0] if result['recommendations'] else None
        score = top['score'] if top else 0
        payload.append(
            {
                'name': scenario['name'],
                'change': scenario['change'],
                'top_crop': top['crop_name'] if top else 'No clear recommendation',
                'top_score': score,
                'score_delta': score - base_top_score,
                'facts': scenario['facts'],
                'changed_fields': _diff_facts(base_facts, scenario['facts']),
            }
        )
    return payload


def _diff_facts(base_facts, new_facts):
    changes = []
    for key, value in new_facts.items():
        if base_facts.get(key) != value:
            changes.append({'field': key, 'from': base_facts.get(key), 'to': value})
    return changes


def build_suitability_tiers(top10_rows):
    tiers = {'Tier 1 - Best Match': [], 'Tier 2 - Strong Alternatives': [], 'Tier 3 - Lower Priority': []}
    if not top10_rows:
        return tiers

    for row in top10_rows:
        pct = row.get('score_percent', 0)
        rank = row.get('rank', 99)
        if rank <= 2 or pct >= 85:
            tiers['Tier 1 - Best Match'].append(row)
        elif pct >= 65:
            tiers['Tier 2 - Strong Alternatives'].append(row)
        else:
            tiers['Tier 3 - Lower Priority'].append(row)
    return tiers


def build_tradeoff_comparison(top_rows, avoid_rows):
    avoid_names = ', '.join([r.crop.name for r in avoid_rows[:2]]) if avoid_rows else 'No major avoid crop'
    cards = []
    for idx, row in enumerate(top_rows[:3], start=1):
        if idx == 1:
            flexibility = 'Best immediate option under current conditions'
            risk = f'Can drop in rank if key conditions shift. Watch nearby alternatives.'
        elif idx == 2:
            flexibility = 'Strong fallback if top option becomes less feasible'
            risk = f'Slightly lower fit than rank 1; may need tighter field management'
        else:
            flexibility = 'Viable reserve option for contingency planning'
            risk = f'More condition-sensitive than higher-ranked crops'

        cards.append(
            {
                'crop_name': row['crop_name'],
                'category': row['category'],
                'score': row['score'],
                'strength': row['confidence_label'],
                'planning_note': row.get('short_reason') or 'Rule matches indicate usable suitability.',
                'risk_note': risk,
                'flexibility_note': flexibility,
                'avoid_context': avoid_names,
            }
        )
    return cards


def build_most_influential_conditions(top_rows):
    factor_scores = defaultdict(int)
    factor_hits = defaultdict(int)
    for row in top_rows[:5]:
        for line in row.get('explanation_lines', []):
            lower = line.lower()
            points = abs(extract_numeric_points(line))
            for factor, keywords in FACTOR_KEYWORDS.items():
                if any(keyword in lower for keyword in keywords):
                    factor_scores[factor] += max(points, 1)
                    factor_hits[factor] += 1
                    break

    factor_labels = {
        'season': 'Season',
        'soil_type': 'Soil Type',
        'water_availability': 'Water Availability',
        'farm_type': 'Farm Type',
        'soil_ph': 'Soil pH',
        'budget': 'Budget',
        'crop_preference': 'Crop Preference',
    }
    max_score = max(factor_scores.values(), default=1)
    rows = []
    for key in factor_labels:
        score = factor_scores.get(key, 0)
        hits = factor_hits.get(key, 0)
        pct = int(round((score / max_score) * 100)) if max_score else 0
        if pct >= 70:
            label = 'High Influence'
        elif pct >= 35:
            label = 'Moderate Influence'
        else:
            label = 'Low Influence'
        rows.append(
            {
                'factor_key': key,
                'factor_label': factor_labels[key],
                'influence_label': label,
                'influence_score': pct,
                'hit_count': hits,
                'note': f'Appeared in {hits} matched rule traces across leading crops.',
            }
        )
    rows.sort(key=lambda r: r['influence_score'], reverse=True)
    return rows


def build_field_adjustment_opportunities(consultation, what_if_scenarios, base_top_crop):
    opportunities = []
    season = consultation.get_season_display()
    water = consultation.get_water_availability_display()
    farm = consultation.get_farm_type_display()
    preference = consultation.get_crop_preference_display()

    for scenario in what_if_scenarios:
        if scenario.get('top_crop') == base_top_crop:
            continue
        change = scenario.get('change', '')
        if 'Water' in change:
            opportunities.append(
                f"If water availability shifts from {water}, ranking can change to {scenario['top_crop']}; prioritize irrigation planning and water scheduling."
            )
        elif 'Season' in change:
            opportunities.append(
                f"If season conditions move away from {season}, {scenario['top_crop']} can become more competitive; align planting window with seasonal transitions."
            )
        elif 'Farm type' in change or 'Farm Type' in change:
            opportunities.append(
                f"If farm setup changes from {farm}, {scenario['top_crop']} may improve; prepare alternate field management practices."
            )

    opportunities.append(
        f"If preference focus changes from {preference}, alternative crop families in the top-10 may become stronger options."
    )
    opportunities.append(
        "If water and soil constraints worsen, prioritize resilient lower-risk crops and avoid condition-sensitive options."
    )

    deduped = []
    for text in opportunities:
        if text not in deduped:
            deduped.append(text)
    return deduped[:4]


def build_crop_category_opportunity_chart(top10_rows):
    grouped = defaultdict(list)
    for row in top10_rows:
        grouped[row['category']].append(row['score'])

    max_avg = 1
    for scores in grouped.values():
        avg = sum(scores) / max(len(scores), 1)
        if avg > max_avg:
            max_avg = avg

    payload = []
    for category, scores in grouped.items():
        count = len(scores)
        total_score = sum(scores)
        avg_score = round(total_score / max(count, 1), 2)
        width = int(round((avg_score / max_avg) * 100)) if max_avg else 0
        payload.append(
            {
                'category': category,
                'count': count,
                'total_score': total_score,
                'avg_score': avg_score,
                'opportunity_width': width,
            }
        )
    payload.sort(key=lambda x: x['avg_score'], reverse=True)
    return payload


def build_condition_match_strength_by_factor(top_row):
    if not top_row:
        return []

    contributions = build_factor_contributions(top_row)
    payload = []
    for row in contributions:
        score = row['width']
        if score >= 70:
            label = 'Strong Support'
        elif score >= 35:
            label = 'Moderate Support'
        else:
            label = 'Low Support'
        payload.append(
            {
                'factor_label': row['factor_label'],
                'strength_score': score,
                'strength_label': label,
                'raw_value': row['value'],
            }
        )
    return payload


def _extract_top_factors_from_lines(lines):
    factor_scores = defaultdict(int)
    for line in lines:
        lower = line.lower()
        points = abs(extract_numeric_points(line))
        for factor, keywords in FACTOR_KEYWORDS.items():
            if any(keyword in lower for keyword in keywords):
                factor_scores[factor] += max(points, 1)
                break
    ranked = sorted(factor_scores.items(), key=lambda item: item[1], reverse=True)
    return [key for key, _ in ranked]


def _factor_to_driver_text(factor_key, consultation):
    mapping = {
        'season': f"{consultation.get_season_display()} season",
        'soil_type': f"{consultation.get_soil_type_display()} soil",
        'water_availability': f"{consultation.get_water_availability_display()} water",
        'farm_type': f"{consultation.get_farm_type_display()} farm setup",
        'soil_ph': f"{consultation.get_soil_ph_category_display()} soil pH",
        'budget': f"{consultation.get_budget_level_display()} budget fit",
        'crop_preference': f"{consultation.get_crop_preference_display()} preference",
    }
    return mapping.get(factor_key, factor_key.replace('_', ' '))


def build_top_recommendation_podium(top_rows, consultation):
    if not top_rows:
        return []

    leader_score = top_rows[0]['score']
    podium = []

    for idx, row in enumerate(top_rows[:3], start=1):
        gap = leader_score - row['score']
        factor_keys = _extract_top_factors_from_lines(row.get('explanation_lines', []))
        key_drivers = [_factor_to_driver_text(key, consultation) for key in factor_keys[:4]]
        if len(key_drivers) < 2:
            fallback = [
                f"{consultation.get_season_display()} season",
                f"{consultation.get_soil_type_display()} soil",
                f"{consultation.get_water_availability_display()} water",
            ]
            for item in fallback:
                if item not in key_drivers:
                    key_drivers.append(item)
                if len(key_drivers) >= 3:
                    break

        if idx == 1:
            decision_role = 'Primary Recommendation'
            relative_position = 'Current leader'
            planning_insight = 'Best immediate planting option under current conditions.'
            podium_height = 100
            visual_order = 2
        elif idx == 2:
            if gap == 0:
                decision_role = 'Co-Leading Alternative'
                relative_position = 'Tied with leader'
            elif gap <= 5:
                decision_role = 'Close Alternative'
                relative_position = 'Closely competitive'
            else:
                decision_role = 'Close Alternative'
                relative_position = f'{gap} points behind leader'
            planning_insight = 'Strong backup if the top crop is less feasible.'
            podium_height = 78
            visual_order = 1
        else:
            if gap == 0:
                relative_position = 'Tied with leader'
            elif gap <= 6:
                relative_position = 'Competitive third option'
            else:
                relative_position = f'{gap} points behind leader'
            decision_role = 'Secondary Option'
            planning_insight = 'Viable alternative for contingency planning.'
            podium_height = 62
            visual_order = 3

        podium.append(
            {
                'rank': row['rank'],
                'crop_name': row['crop_name'],
                'category': row['category'],
                'suitability_score': row['score'],
                'score_percent': row['score_percent'],
                'key_drivers': key_drivers[:4],
                'decision_role': decision_role,
                'relative_position': relative_position,
                'planning_insight': planning_insight,
                'podium_height': podium_height,
                'visual_order': visual_order,
            }
        )

    return sorted(podium, key=lambda row: row['visual_order'])
