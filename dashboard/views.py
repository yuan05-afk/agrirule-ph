from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from dashboard.forms import CropForm, RuleForm, apply_dashboard_classes
from expert_system.models import Consultation, ConsultationResult, Crop, Rule


def staff_required(view_func):
    @login_required
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'Staff access required.')
            return redirect('home')
        return view_func(request, *args, **kwargs)

    return _wrapped


@staff_required
def dashboard_index(request):
    context = {
        'crop_count': Crop.objects.count(),
        'rule_count': Rule.objects.filter(is_active=True).count(),
        'consultation_count': Consultation.objects.count(),
        'recent_consultations': Consultation.objects.order_by('-created_at')[:10],
        'category_breakdown': Crop.objects.values('category').annotate(total=Count('id')).order_by('category'),
    }
    return render(request, 'dashboard/index.html', context)


@staff_required
def crops_list(request):
    if request.method == 'POST' and request.POST.get('delete_id'):
        crop = get_object_or_404(Crop, pk=request.POST.get('delete_id'))
        crop.delete()
        messages.success(request, 'Crop deleted successfully.')
        return redirect('dashboard_crops_list')

    crops = Crop.objects.all().order_by('name')
    return render(request, 'dashboard/crops_list.html', {'crops': crops})


@staff_required
def crop_add(request):
    if request.method == 'POST':
        form = CropForm(request.POST)
        apply_dashboard_classes(form)
        if form.is_valid():
            form.save()
            messages.success(request, 'Crop created successfully.')
            return redirect('dashboard_crops_list')
    else:
        form = CropForm()
        apply_dashboard_classes(form)
    return render(request, 'dashboard/crop_form.html', {'form': form, 'is_edit': False})


@staff_required
def crop_edit(request, crop_id):
    crop = get_object_or_404(Crop, pk=crop_id)
    if request.method == 'POST':
        form = CropForm(request.POST, instance=crop)
        apply_dashboard_classes(form)
        if form.is_valid():
            form.save()
            messages.success(request, 'Crop updated successfully.')
            return redirect('dashboard_crops_list')
    else:
        form = CropForm(instance=crop)
        apply_dashboard_classes(form)
    return render(request, 'dashboard/crop_form.html', {'form': form, 'is_edit': True, 'crop': crop})


@staff_required
def rules_list(request):
    if request.method == 'POST' and request.POST.get('delete_id'):
        rule = get_object_or_404(Rule, pk=request.POST.get('delete_id'))
        rule.delete()
        messages.success(request, 'Rule deleted successfully.')
        return redirect('dashboard_rules_list')

    rules = Rule.objects.select_related('crop').all().order_by('crop__name', 'name')
    return render(request, 'dashboard/rules_list.html', {'rules': rules})


@staff_required
def rule_add(request):
    if request.method == 'POST':
        form = RuleForm(request.POST)
        apply_dashboard_classes(form)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rule created successfully.')
            return redirect('dashboard_rules_list')
    else:
        form = RuleForm()
        apply_dashboard_classes(form)
    return render(request, 'dashboard/rule_form.html', {'form': form, 'is_edit': False})


@staff_required
def rule_edit(request, rule_id):
    rule = get_object_or_404(Rule, pk=rule_id)
    if request.method == 'POST':
        form = RuleForm(request.POST, instance=rule)
        apply_dashboard_classes(form)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rule updated successfully.')
            return redirect('dashboard_rules_list')
    else:
        form = RuleForm(instance=rule)
        apply_dashboard_classes(form)
    return render(request, 'dashboard/rule_form.html', {'form': form, 'is_edit': True, 'rule': rule})


@staff_required
def consultations_list(request):
    top_prefetch = Prefetch(
        'results',
        queryset=ConsultationResult.objects.filter(is_recommended=True)
        .select_related('crop')
        .order_by('rank_order', '-score', 'crop__name'),
    )
    consultations = Consultation.objects.prefetch_related(top_prefetch).order_by('-created_at')
    paginator = Paginator(consultations, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    rows = []
    for item in page_obj.object_list:
        prefetched_results = list(item.results.all())
        top = prefetched_results[0] if prefetched_results else None
        rows.append({'consultation': item, 'top_result': top})
    return render(request, 'dashboard/consultations.html', {'rows': rows, 'page_obj': page_obj})
