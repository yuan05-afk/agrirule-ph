from django import forms

from expert_system.models import Consultation, Crop, Rule


class ConsultationForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = [
            'season',
            'soil_type',
            'water_availability',
            'farm_type',
            'soil_ph_category',
            'budget_level',
            'crop_preference',
        ]


class CropForm(forms.ModelForm):
    class Meta:
        model = Crop
        fields = ['name', 'category', 'description', 'planting_note', 'avoid_note', 'is_active']


class RuleForm(forms.ModelForm):
    class Meta:
        model = Rule
        fields = [
            'name',
            'crop',
            'season_condition',
            'soil_type_condition',
            'water_availability_condition',
            'farm_type_condition',
            'soil_ph_condition',
            'budget_level_condition',
            'crop_preference_condition',
            'rule_type',
            'score',
            'explanation',
            'is_active',
        ]
