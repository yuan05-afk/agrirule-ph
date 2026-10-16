from django.core.exceptions import ValidationError
from django.db import models


class ConsultationChoices:
    class Season(models.TextChoices):
        WET = 'wet', 'Wet'
        DRY = 'dry', 'Dry'

    class SoilType(models.TextChoices):
        CLAY = 'clay', 'Clay'
        LOAM = 'loam', 'Loam'
        SANDY = 'sandy', 'Sandy'
        SILT = 'silt', 'Silt'

    class WaterAvailability(models.TextChoices):
        LOW = 'low', 'Low'
        MODERATE = 'moderate', 'Moderate'
        HIGH = 'high', 'High'

    class FarmType(models.TextChoices):
        IRRIGATED = 'irrigated', 'Irrigated'
        RAINFED = 'rainfed', 'Rainfed'

    class SoilPH(models.TextChoices):
        ACIDIC = 'acidic', 'Acidic'
        NEUTRAL = 'neutral', 'Neutral'
        ALKALINE = 'alkaline', 'Alkaline'

    class BudgetLevel(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'

    class CropPreference(models.TextChoices):
        STAPLE = 'staple', 'Staple'
        VEGETABLE = 'vegetable', 'Vegetable'
        RESILIENT = 'resilient', 'Resilient Crop'


class Crop(models.Model):
    class Category(models.TextChoices):
        STAPLES_ROOT = 'staples_root', 'Staples, Legumes, and Root Crops'
        INDUSTRIAL_PERENNIAL = 'industrial_perennial', 'Industrial and Perennial Crops'
        FRUIT = 'fruit', 'Fruit Crops'
        VEGETABLE_SPICE = 'vegetable_spice', 'Vegetables and Spices'

    name = models.CharField(max_length=120, unique=True)
    category = models.CharField(max_length=40, choices=Category.choices)
    description = models.TextField(blank=True)
    planting_note = models.TextField(blank=True)
    avoid_note = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name


class Rule(models.Model):
    class RuleType(models.TextChoices):
        POSITIVE = 'positive', 'Positive'
        NEGATIVE = 'negative', 'Negative'
        AVOID = 'avoid', 'Avoid'

    name = models.CharField(max_length=200, unique=True)
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name='rules')

    # Blank condition means wildcard (ANY).
    season_condition = models.CharField(max_length=20, blank=True, choices=ConsultationChoices.Season.choices)
    soil_type_condition = models.CharField(max_length=20, blank=True, choices=ConsultationChoices.SoilType.choices)
    water_availability_condition = models.CharField(max_length=20, blank=True, choices=ConsultationChoices.WaterAvailability.choices)
    farm_type_condition = models.CharField(max_length=20, blank=True, choices=ConsultationChoices.FarmType.choices)
    soil_ph_condition = models.CharField(max_length=20, blank=True, choices=ConsultationChoices.SoilPH.choices)
    budget_level_condition = models.CharField(max_length=20, blank=True, choices=ConsultationChoices.BudgetLevel.choices)
    crop_preference_condition = models.CharField(max_length=20, blank=True, choices=ConsultationChoices.CropPreference.choices)

    score = models.IntegerField()
    rule_type = models.CharField(max_length=20, choices=RuleType.choices, default=RuleType.POSITIVE)
    explanation = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['crop__name', 'name']
        indexes = [
            models.Index(fields=['is_active', 'crop']),
        ]

    def clean(self):
        if self.score == 0:
            raise ValidationError({'score': 'Score cannot be zero.'})

    def __str__(self):
        return self.name


class Consultation(models.Model):
    season = models.CharField(max_length=20, choices=ConsultationChoices.Season.choices)
    soil_type = models.CharField(max_length=20, choices=ConsultationChoices.SoilType.choices)
    water_availability = models.CharField(max_length=20, choices=ConsultationChoices.WaterAvailability.choices)
    farm_type = models.CharField(max_length=20, choices=ConsultationChoices.FarmType.choices)
    soil_ph_category = models.CharField(max_length=20, choices=ConsultationChoices.SoilPH.choices)
    budget_level = models.CharField(max_length=20, choices=ConsultationChoices.BudgetLevel.choices)
    crop_preference = models.CharField(max_length=20, choices=ConsultationChoices.CropPreference.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'Consultation #{self.pk}'


class ConsultationResult(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='results')
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    explanation_text = models.TextField(blank=True)
    is_recommended = models.BooleanField(default=False)
    is_avoid = models.BooleanField(default=False)
    rank_order = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['rank_order', '-score', 'crop__name']
        unique_together = ('consultation', 'crop')
        indexes = [
            models.Index(fields=['consultation', 'is_recommended', 'rank_order']),
            models.Index(fields=['consultation', 'is_avoid', '-score']),
        ]

    def __str__(self):
        return f'{self.consultation_id} - {self.crop.name}'
