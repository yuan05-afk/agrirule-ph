from collections import defaultdict

from expert_system.models import Crop, Rule


RULE_FIELD_MAP = {
    'season_condition': 'season',
    'soil_type_condition': 'soil_type',
    'water_availability_condition': 'water_availability',
    'farm_type_condition': 'farm_type',
    'soil_ph_condition': 'soil_ph_category',
    'budget_level_condition': 'budget_level',
    'crop_preference_condition': 'crop_preference',
}


def _rule_matches(rule, facts):
    for rule_field, fact_field in RULE_FIELD_MAP.items():
        expected_value = getattr(rule, rule_field)
        if expected_value and facts.get(fact_field) != expected_value:
            return False
    return True


def run_inference(facts, top_n=3, crops=None, rules=None):
    crops = list(crops) if crops is not None else list(Crop.objects.filter(is_active=True).order_by('name'))
    rules = list(rules) if rules is not None else list(
        Rule.objects.filter(is_active=True, crop__is_active=True)
        .select_related('crop')
        .order_by('crop__name', 'name')
    )

    scores = {crop.id: 0 for crop in crops}
    traces = defaultdict(list)
    avoid_flags = defaultdict(bool)
    avoid_reasons = defaultdict(list)
    negative_hits = defaultdict(int)
    engine_notes = []

    for rule in rules:
        if not _rule_matches(rule, facts):
            continue

        crop_id = rule.crop_id
        score_value = abs(rule.score)

        if rule.rule_type == Rule.RuleType.POSITIVE:
            scores[crop_id] += score_value
        elif rule.rule_type == Rule.RuleType.NEGATIVE:
            scores[crop_id] -= score_value
            negative_hits[crop_id] += 1
        else:  # avoid
            scores[crop_id] -= max(score_value, 50)
            avoid_flags[crop_id] = True
            avoid_reasons[crop_id].append(rule.explanation)

        traces[crop_id].append(rule.explanation)

    for crop in crops:
        if scores[crop.id] <= -20 and negative_hits[crop.id] > 0:
            avoid_flags[crop.id] = True
            avoid_reasons[crop.id].append('Final score is strongly negative for current conditions.')

    ranked = sorted(crops, key=lambda c: (scores[c.id], c.name), reverse=True)
    non_avoid = [c for c in ranked if not avoid_flags[c.id]]

    if not non_avoid:
        non_avoid = ranked[:top_n]
        engine_notes.append('No strong non-avoid matches found. Showing best available fallback crops.')

    recommendations = non_avoid[:top_n]
    if len(recommendations) < top_n:
        needed = top_n - len(recommendations)
        extras = [c for c in ranked if c not in recommendations][:needed]
        recommendations.extend(extras)
        engine_notes.append('Insufficient high-confidence matches. Included fallback recommendations.')

    max_score = max([scores[c.id] for c in recommendations], default=0)
    normalizer = max(max_score, 1)

    recommendation_payload = []
    for index, crop in enumerate(recommendations, start=1):
        pct = int(max(0, min(100, round((scores[crop.id] / normalizer) * 100))))
        recommendation_payload.append(
            {
                'crop_id': crop.id,
                'crop_name': crop.name,
                'category': crop.get_category_display(),
                'score': scores[crop.id],
                'score_percent': pct,
                'planting_note': crop.planting_note,
                'explanations': traces[crop.id] or ['No direct matched rules. Fallback recommendation.'],
                'rank_order': index,
            }
        )

    avoid_list = []
    for crop in ranked:
        if avoid_flags[crop.id]:
            reason = '; '.join(dict.fromkeys(avoid_reasons[crop.id]))
            if not reason:
                reason = crop.avoid_note or 'Avoided due to low suitability under current conditions.'
            avoid_list.append({'crop_id': crop.id, 'crop_name': crop.name, 'reason': reason})

    return {
        'recommendations': recommendation_payload,
        'avoid_list': avoid_list,
        'all_scores': scores,
        'engine_notes': engine_notes,
        # Internal maps used by views when persisting results.
        'trace_map': {k: v for k, v in traces.items()},
        'avoid_flag_map': dict(avoid_flags),
    }
