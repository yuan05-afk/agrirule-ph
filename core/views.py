from time import perf_counter

from django.contrib import messages
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db import connection, transaction
from django.db.utils import InterfaceError, OperationalError
from django.db.models import Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import cache_page, never_cache

from core.forms import ConsultationForm, apply_tailwind_classes
from expert_system.models import Consultation, ConsultationResult, Crop
from expert_system.services.analytics_service import (
    build_condition_match_strength_by_factor,
    build_crop_category_opportunity_chart,
    build_field_adjustment_opportunities,
    build_ranked_rows,
    build_suitability_tiers,
    build_top_recommendation_podium,
    build_tradeoff_comparison,
    generate_what_if_scenarios,
)
from expert_system.services.inference_engine import run_inference
from expert_system.services.result_formatter import (
    build_action_recommendations,
    build_condition_assessment,
    build_decision_summary,
    confidence_label,
    confidence_legend_items,
)


def _set_timing(request, key, elapsed_ms):
    if not hasattr(request, '_server_timing'):
        request._server_timing = {}
    request._server_timing[key] = round(float(elapsed_ms), 2)


def _build_analytics_interpretations(
    analytics_top10,
    podium_rows,
    category_rows,
    factor_rows,
    tradeoff_rows,
    field_adjustments,
    suitability_tiers,
    what_if_scenarios,
    insights_rows,
):
    data = {}

    if len(analytics_top10) >= 3:
        top1, top2, top3 = analytics_top10[0], analytics_top10[1], analytics_top10[2]
        drop = top1['score'] - top3['score']
        data['top10_key_insight'] = (
            f"{top1['crop_name']} leads the ranking, with {top2['crop_name']} and {top3['crop_name']} close behind; "
            f"the top-3 spread is {drop} points."
        )
        data['top10_recommended_action'] = (
            f"Prioritize {top1['crop_name']} first, then validate {top2['crop_name']} and {top3['crop_name']} as practical backups before planting."
        )
    else:
        data['top10_key_insight'] = "Only a limited set of ranked crops is available, so recommendation depth is currently narrow."
        data['top10_recommended_action'] = "Run another consultation with verified field inputs to expand and stabilize the ranking set."

    by_rank = {row.get('rank'): row for row in podium_rows}
    p1 = by_rank.get(1)
    p2 = by_rank.get(2)
    p3 = by_rank.get(3)
    if p1 and p2 and p3:
        gap_12 = p1['suitability_score'] - p2['suitability_score']
        gap_13 = p1['suitability_score'] - p3['suitability_score']
        data['podium_key_insight'] = (
            f"{p1['crop_name']} is currently ahead, while {p2['crop_name']} and {p3['crop_name']} remain competitive with gaps of {gap_12} and {gap_13} points."
        )
        data['podium_recommended_action'] = (
            f"Use {p1['crop_name']} as the main plan and keep {p2['crop_name']} and {p3['crop_name']} prepared as fallback execution paths."
        )
    else:
        data['podium_key_insight'] = "Top-3 podium comparison is limited, so competitive separation among lead crops is incomplete."
        data['podium_recommended_action'] = "Review full ranking and rerun consultation if you need clearer top-3 strategic separation."

    if category_rows:
        lead = category_rows[0]
        data['category_key_insight'] = (
            f"{lead['category']} is the strongest category under current conditions, averaging {lead['avg_score']} across {lead['count']} top-ranked crops."
        )
        data['category_recommended_action'] = (
            f"Allocate most planning effort to {lead['category']} first, while retaining non-leading categories for diversification."
        )
    else:
        data['category_key_insight'] = "No clear category concentration is visible from current ranked outputs."
        data['category_recommended_action'] = "Prioritize field validation first, then rerun analytics to identify a leading crop category."

    if factor_rows:
        sorted_factors = sorted(factor_rows, key=lambda row: row['strength_score'], reverse=True)
        strong = sorted_factors[0]
        weak = sorted_factors[-1]
        data['factor_key_insight'] = (
            f"{strong['factor_label']} is the strongest support factor, while {weak['factor_label']} is the weakest support factor in the current profile."
        )
        data['factor_recommended_action'] = (
            f"Protect {strong['factor_label'].lower()} alignment and improve {weak['factor_label'].lower()} conditions where feasible before scaling planting decisions."
        )
    else:
        data['factor_key_insight'] = "Factor support strength could not be derived from current explanation traces."
        data['factor_recommended_action'] = "Collect clearer condition inputs and rerun consultation to improve factor-level guidance."

    if len(tradeoff_rows) >= 3:
        a, b, c = tradeoff_rows[0], tradeoff_rows[1], tradeoff_rows[2]
        data['tradeoff_key_insight'] = (
            f"{a['crop_name']}, {b['crop_name']}, and {c['crop_name']} present different balance points across planning fit, risk, and flexibility."
        )
        data['tradeoff_recommended_action'] = (
            f"Choose {a['crop_name']} for immediate alignment, but move to {b['crop_name']} or {c['crop_name']} if risk, inputs, or market constraints change."
        )
    else:
        data['tradeoff_key_insight'] = "Trade-off comparison is limited because fewer than three strong options are available."
        data['tradeoff_recommended_action'] = "Use available top options conservatively and validate constraints before final crop commitment."

    scenario_switches = sum(1 for row in what_if_scenarios if row.get('score_delta', 0) != 0)
    if field_adjustments:
        data['field_key_insight'] = (
            f"Small field-condition adjustments can alter ranking behavior, and {scenario_switches} nearby scenarios already show measurable recommendation shifts."
        )
    else:
        data['field_key_insight'] = "Current adjustment analysis shows limited movement, indicating rankings are relatively stable under nearby condition changes."

    tier_counts = {name: len(rows) for name, rows in suitability_tiers.items()}
    data['tier_key_insight'] = (
        f"Tier grouping currently separates into {tier_counts.get('Tier 1 - Best Match', 0)} best-match, "
        f"{tier_counts.get('Tier 2 - Strong Alternatives', 0)} strong-alternative, and "
        f"{tier_counts.get('Tier 3 - Lower Priority', 0)} lower-priority crops."
    )

    if what_if_scenarios:
        changed_top = [row for row in what_if_scenarios if row.get('top_crop') and analytics_top10 and row['top_crop'] != analytics_top10[0]['crop_name']]
        changed_count = len(changed_top)
        field_counter = {}
        for row in what_if_scenarios:
            for item in row.get('changed_fields', []):
                key = item.get('field')
                if not key:
                    continue
                field_counter[key] = field_counter.get(key, 0) + 1
        dominant_field = max(field_counter, key=field_counter.get) if field_counter else 'water_availability'
        readable = dominant_field.replace('_', ' ')
        data['what_if_key_insight'] = (
            f"Scenario analysis shows {changed_count} of {len(what_if_scenarios)} nearby condition shifts change the leading crop, indicating recommendation sensitivity."
        )
        data['what_if_recommended_action'] = (
            f"Stabilize {readable} first, because it is the most repeatedly changed controllable factor across what-if tests."
        )
    else:
        data['what_if_key_insight'] = "No scenario comparisons are available, so sensitivity to nearby condition changes is unknown."
        data['what_if_recommended_action'] = "Generate what-if runs before finalizing crop selection for a risk-aware decision."

    if insights_rows:
        strong_count = sum(1 for row in insights_rows if row.get('confidence_label') in ('Very Strong Match', 'Strong Match'))
        avoid_count = sum(1 for row in insights_rows if row.get('is_avoid'))
        avg_trace = round(sum(row.get('explanation_count', 0) for row in insights_rows) / max(len(insights_rows), 1), 1)
        data['table_key_insight'] = (
            f"The table shows {strong_count} high-confidence options, {avoid_count} avoid-flagged options, and an average explanation trace depth of {avg_trace} per crop."
        )
        data['table_recommended_action'] = (
            "Use score, confidence level, trace depth, and avoid flag together as the final screening criteria before crop commitment."
        )
    else:
        data['table_key_insight'] = "No tabular insight rows are available for final cross-checking."
        data['table_recommended_action'] = "Complete a consultation run first, then use the table as your final validation layer."

    return data


def _grouped_crops():
    cache_key = 'grouped-crops-v1'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    groups = {}
    for value, label in Crop.Category.choices:
        groups[label] = list(Crop.objects.filter(is_active=True, category=value).values_list('name', flat=True))
    cache.set(cache_key, groups, 600)
    return groups


def _serialize_ranked_row(row):
    return {
        key: value
        for key, value in row.items()
        if key != 'crop_obj'
    }


def _build_analytics_payload(consultation):
    db_fetch_start = perf_counter()
    all_result_rows = list(consultation.results.select_related('crop').order_by('-score', 'crop__name'))
    db_fetch_ms = (perf_counter() - db_fetch_start) * 1000

    scored_non_avoid = [row for row in all_result_rows if not row.is_avoid]
    avoid_results = [row for row in all_result_rows if row.is_avoid]

    inference_start = perf_counter()
    ranked_non_avoid = build_ranked_rows(scored_non_avoid)
    analytics_top10 = ranked_non_avoid[:10]
    top_recommendation = analytics_top10[0] if analytics_top10 else None
    top_recommendation_podium = build_top_recommendation_podium(analytics_top10, consultation)
    category_opportunity_chart = build_crop_category_opportunity_chart(analytics_top10)
    condition_match_strength = build_condition_match_strength_by_factor(top_recommendation)
    what_if_scenarios = generate_what_if_scenarios(consultation)
    suitability_tiers = build_suitability_tiers(analytics_top10)
    tradeoff_comparison = build_tradeoff_comparison(analytics_top10, avoid_results)
    field_adjustments = build_field_adjustment_opportunities(
        consultation,
        what_if_scenarios,
        top_recommendation.get('crop_name') if top_recommendation else None,
    )
    top3_preview = analytics_top10[:3]
    top_crop_trace_count = top_recommendation.get('explanation_count', 0) if top_recommendation else 0
    avoid_names = [item.crop.name for item in avoid_results[:3]]
    has_high_confidence = bool(top_recommendation and top_recommendation.get('score_percent', 0) >= 85)
    decision_status = 'High Confidence Recommendation' if has_high_confidence else 'Needs Local Validation'

    quick_next_step = (
        f"Proceed with a pilot plot for {top_recommendation['crop_name']} and monitor water and soil response weekly."
        if top_recommendation
        else 'Review consultation inputs and run another scenario before final crop selection.'
    )

    interpretations = _build_analytics_interpretations(
        analytics_top10=analytics_top10,
        podium_rows=top_recommendation_podium,
        category_rows=category_opportunity_chart,
        factor_rows=condition_match_strength,
        tradeoff_rows=tradeoff_comparison,
        field_adjustments=field_adjustments,
        suitability_tiers=suitability_tiers,
        what_if_scenarios=what_if_scenarios,
        insights_rows=analytics_top10,
    )
    inference_ms = (perf_counter() - inference_start) * 1000

    payload = {
        'summary': {
            'top_recommendation': _serialize_ranked_row(top_recommendation) if top_recommendation else None,
            'top3_preview': [_serialize_ranked_row(row) for row in top3_preview],
            'top_crop_trace_count': top_crop_trace_count,
            'avoid_names': avoid_names,
            'avoid_count': len(avoid_results),
            'decision_status': decision_status,
            'quick_next_step': quick_next_step,
        },
        'top_recommendation_podium': top_recommendation_podium,
        'category_opportunity_chart': category_opportunity_chart,
        'condition_match_strength': condition_match_strength,
        'what_if_scenarios': what_if_scenarios,
        'suitability_tiers': {
            tier_name: [_serialize_ranked_row(row) for row in rows]
            for tier_name, rows in suitability_tiers.items()
        },
        'tradeoff_comparison': tradeoff_comparison,
        'field_adjustments': field_adjustments,
        'insights_rows': [_serialize_ranked_row(row) for row in analytics_top10],
        'interpretations': interpretations,
        '_timing': {
            'db_fetch_ms': round(db_fetch_ms, 2),
            'inference_ms': round(inference_ms, 2),
        },
    }
    return payload


def home(request):
    db_fetch_start = perf_counter()
    context = {'grouped_crops': _grouped_crops()}
    _set_timing(request, 'db_fetch_ms', (perf_counter() - db_fetch_start) * 1000)
    render_start = perf_counter()
    response = render(request, 'core/home.html', context)
    _set_timing(request, 'render_ms', (perf_counter() - render_start) * 1000)
    return response


@cache_page(600)
def about(request):
    render_start = perf_counter()
    response = render(request, 'core/about.html')
    _set_timing(request, 'render_ms', (perf_counter() - render_start) * 1000)
    return response


def consult(request):
    if request.method == 'POST':
        form = ConsultationForm(request.POST)
        apply_tailwind_classes(form)
        if form.is_valid():
            db_fetch_start = perf_counter()
            active_crops = list(Crop.objects.filter(is_active=True).order_by('name'))
            _set_timing(request, 'db_fetch_ms', (perf_counter() - db_fetch_start) * 1000)

            inference_start = perf_counter()
            inference = run_inference(form.cleaned_data, top_n=3, crops=active_crops)
            _set_timing(request, 'inference_ms', (perf_counter() - inference_start) * 1000)

            recommendations_by_crop = {
                item['crop_id']: item for item in inference['recommendations']
            }
            avoid_crop_ids = {item['crop_id'] for item in inference['avoid_list']}
            result_rows = []

            with transaction.atomic():
                consultation = form.save()
                for crop in active_crops:
                    rec_item = recommendations_by_crop.get(crop.id)
                    score = inference['all_scores'].get(crop.id, 0)
                    trace_lines = inference.get('trace_map', {}).get(crop.id, [])
                    result_rows.append(
                        ConsultationResult(
                            consultation=consultation,
                            crop=crop,
                            score=score,
                            explanation_text='\n'.join(trace_lines),
                            is_recommended=bool(rec_item),
                            is_avoid=(crop.id in avoid_crop_ids),
                            rank_order=rec_item['rank_order'] if rec_item else None,
                        )
                    )
                ConsultationResult.objects.bulk_create(result_rows, batch_size=100)

            messages.success(request, 'Consultation completed successfully.')
            return redirect('results', consultation_id=consultation.id)
    else:
        form = ConsultationForm()
        apply_tailwind_classes(form)

    render_start = perf_counter()
    response = render(request, 'core/consult.html', {'form': form})
    _set_timing(request, 'render_ms', (perf_counter() - render_start) * 1000)
    return response


def results(request, consultation_id):
    db_fetch_start = perf_counter()
    consultation = get_object_or_404(Consultation, pk=consultation_id)
    all_results = list(
        consultation.results.select_related('crop').order_by('-score', 'crop__name')
    )
    _set_timing(request, 'db_fetch_ms', (perf_counter() - db_fetch_start) * 1000)
    scored_non_avoid = [result for result in all_results if not result.is_avoid]
    avoid_results = sorted([result for result in all_results if result.is_avoid], key=lambda row: row.crop.name)

    def _clean_reason(text):
        cleaned = text.strip()
        for prefix in ('Avoid note:', 'Avoid:', 'Rule:', '+', '-'):
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()
        return cleaned

    def _short_reason(text):
        normalized = _clean_reason(text)
        lower = normalized.lower()

        if 'dry season' in lower:
            return 'Unsuitable in dry season'
        if 'wet season' in lower:
            return 'Unsuitable in wet season'
        if 'water' in lower and ('low' in lower or 'limited' in lower):
            return 'Sensitive to low water conditions'
        if 'water' in lower and ('high' in lower or 'excess' in lower):
            return 'Performs poorly under excess water'
        if 'soil' in lower:
            return 'Current soil setup is less favorable'
        if 'farm' in lower:
            return 'Current farm setup is less favorable'
        if 'ph' in lower:
            return 'Current soil pH is less favorable'
        if 'budget' in lower:
            return 'Budget level is less suitable for this crop'
        if 'heat' in lower:
            return 'Sensitive to heat stress'
        if 'negative' in lower or 'below' in lower:
            return 'Overall suitability is currently low'

        shortened = normalized.split('.')[0].strip()
        return shortened if shortened else 'Current condition profile is unfavorable'

    def _build_avoid_payload(result_item):
        raw_lines = [line.strip() for line in result_item.explanation_text.splitlines() if line.strip()]
        negative_lines = []
        for line in raw_lines:
            lower = line.lower()
            if lower.startswith('-') or 'avoid' in lower or 'unsuitable' in lower or 'strongly negative' in lower:
                negative_lines.append(_clean_reason(line))

        if result_item.crop.avoid_note:
            negative_lines.append(_clean_reason(result_item.crop.avoid_note))

        negative_lines = list(dict.fromkeys(negative_lines))
        short_reasons = list(dict.fromkeys([_short_reason(line) for line in negative_lines if line]))[:3]

        c = result_item.consultation
        fallback_short = [
            f'Unsuitable in {c.get_season_display().lower()} season',
            f'{c.get_water_availability_display()} water profile is less favorable',
            'Current soil/farm setup is less favorable',
        ]
        while len(short_reasons) < 3:
            short_reasons.append(fallback_short[len(short_reasons)])

        badge = 'Avoid'
        if result_item.score <= -50:
            badge = 'High Risk'
        elif result_item.score <= -20:
            badge = 'Not Recommended'

        return {
            'summary': short_reasons[0],
            'short_reasons': short_reasons[:3],
            'full_reasons': negative_lines[:8],
            'badge': badge,
        }

    ranked_rows = build_ranked_rows(scored_non_avoid)
    top3_rows = ranked_rows[:3]
    top10_extended = ranked_rows[3:10]

    top10_status_rows = []
    if all_results:
        top_score_all = max(item.score for item in all_results)
        denom_all = max(top_score_all, 1)
        for idx, item in enumerate(all_results[:10], start=1):
            lines = [line.strip() for line in item.explanation_text.splitlines() if line.strip()]
            score_percent = int(max(0, min(100, round((item.score / denom_all) * 100))))
            top10_status_rows.append(
                {
                    'rank': idx,
                    'display_rank': idx,
                    'crop_name': item.crop.name,
                    'category': item.crop.get_category_display(),
                    'score': item.score,
                    'score_percent': score_percent,
                    'confidence_label': confidence_label(score_percent),
                    'short_reason': lines[0] if lines else 'Included by overall score ranking.',
                    'status': 'Avoid' if item.is_avoid else ('Recommended' if idx <= 3 else 'Secondary'),
                    'explanation_lines': lines,
                }
            )

    for item in avoid_results:
        payload = _build_avoid_payload(item)
        item.avoid_summary = payload['summary']
        item.avoid_lines = payload['short_reasons']
        item.avoid_full_reasons = payload['full_reasons']
        item.avoid_badge = payload['badge']

    decision_summary = build_decision_summary(
        consultation=consultation,
        top3=top3_rows,
        avoid_results=avoid_results,
    )
    condition_assessment = build_condition_assessment(consultation)
    action_recommendations = build_action_recommendations(
        consultation=consultation,
        top3=top3_rows,
        avoid_results=avoid_results,
    )

    context = {
        'consultation': consultation,
        'decision_summary': decision_summary,
        'confidence_legend': confidence_legend_items(),
        'condition_assessment': condition_assessment,
        'action_recommendations': action_recommendations,
        'top3_recommendations': top3_rows,
        'top10_extended': top10_extended,
        'top10_status_rows': top10_status_rows,
        'avoid_results': avoid_results,
    }
    render_start = perf_counter()
    response = render(request, 'core/results.html', context)
    _set_timing(request, 'render_ms', (perf_counter() - render_start) * 1000)
    return response


def result_analytics(request, consultation_id):
    consultation = get_object_or_404(Consultation, pk=consultation_id)
    render_start = perf_counter()
    response = render(
        request,
        'core/result_analytics.html',
        {
            'consultation': consultation,
            'analytics_data_url': reverse('result_analytics_data', args=[consultation.id]),
        },
    )
    _set_timing(request, 'render_ms', (perf_counter() - render_start) * 1000)
    return response


def result_analytics_data(request, consultation_id):
    consultation = get_object_or_404(Consultation, pk=consultation_id)
    cache_key = f"analytics-data-v1:{consultation_id}"
    cached = cache.get(cache_key)
    if cached:
        _set_timing(request, 'db_fetch_ms', cached.get('_timing', {}).get('db_fetch_ms', 0))
        _set_timing(request, 'inference_ms', cached.get('_timing', {}).get('inference_ms', 0))
        return JsonResponse(cached)

    payload = _build_analytics_payload(consultation)
    cache.set(cache_key, payload, 60)
    _set_timing(request, 'db_fetch_ms', payload.get('_timing', {}).get('db_fetch_ms', 0))
    _set_timing(request, 'inference_ms', payload.get('_timing', {}).get('inference_ms', 0))
    return JsonResponse(payload)


def history(request):
    db_fetch_start = perf_counter()
    result_prefetch = Prefetch(
        'results',
        queryset=ConsultationResult.objects.select_related('crop').order_by('-score', 'crop__name'),
    )
    consultations_qs = Consultation.objects.prefetch_related(result_prefetch).order_by('-created_at')
    paginator = Paginator(consultations_qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    _set_timing(request, 'db_fetch_ms', (perf_counter() - db_fetch_start) * 1000)

    rows = []
    for item in page_obj.object_list:
        prefetched_results = list(item.results.all())
        top = next((result for result in prefetched_results if not result.is_avoid), None)
        if not top and prefetched_results:
            top = prefetched_results[0]
        rows.append({'consultation': item, 'top_result': top})

    render_start = perf_counter()
    response = render(request, 'core/history.html', {'rows': rows, 'page_obj': page_obj})
    _set_timing(request, 'render_ms', (perf_counter() - render_start) * 1000)
    return response


@never_cache
def healthz(request):
    """Liveness and database readiness probe for uptime monitors."""
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
    except (OperationalError, InterfaceError):
        return JsonResponse({'status': 'degraded', 'database': 'unavailable'}, status=503)
    return JsonResponse({'status': 'ok', 'database': 'ok'})
