from django.contrib import admin

from expert_system.models import Consultation, ConsultationResult, Crop, Rule


@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_active', 'updated_at')
    list_filter = ('category', 'is_active')
    search_fields = ('name',)


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'crop', 'rule_type', 'score', 'is_active', 'updated_at')
    list_filter = ('rule_type', 'is_active', 'crop__category')
    search_fields = ('name', 'crop__name', 'explanation')


class ConsultationResultInline(admin.TabularInline):
    model = ConsultationResult
    extra = 0
    readonly_fields = ('crop', 'score', 'is_recommended', 'is_avoid', 'rank_order')


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('id', 'season', 'soil_type', 'water_availability', 'crop_preference', 'created_at')
    list_filter = ('season', 'soil_type', 'water_availability', 'farm_type', 'crop_preference')
    inlines = [ConsultationResultInline]


@admin.register(ConsultationResult)
class ConsultationResultAdmin(admin.ModelAdmin):
    list_display = ('consultation', 'crop', 'score', 'is_recommended', 'is_avoid', 'rank_order')
    list_filter = ('is_recommended', 'is_avoid', 'crop__category')
