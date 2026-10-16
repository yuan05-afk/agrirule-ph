from django import forms

from expert_system.forms import ConsultationForm as BaseConsultationForm


class ConsultationForm(BaseConsultationForm):
    PLACEHOLDERS = {
        'season': 'Select season',
        'water_availability': 'Select water availability',
        'soil_type': 'Select soil type',
        'soil_ph_category': 'Select soil pH category',
        'farm_type': 'Select farm type',
        'budget_level': 'Select budget level',
        'crop_preference': 'Select crop preference',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, placeholder in self.PLACEHOLDERS.items():
            field = self.fields.get(field_name)
            if not field:
                continue
            choices = list(field.choices)
            non_empty_choices = [choice for choice in choices if choice[0] != '']
            field.choices = [('', placeholder)] + non_empty_choices


FIELD_CLASS = (
    'w-full rounded-xl border border-stone-200 bg-stone-50/30 focus:bg-white '
    'focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 text-sm py-2.5 px-3 outline-none transition-all shadow-sm'
)


def apply_tailwind_classes(form):
    for field in form.fields.values():
        widget = field.widget
        if isinstance(widget, forms.CheckboxInput):
            continue
        existing = widget.attrs.get('class', '')
        widget.attrs['class'] = f'{existing} {FIELD_CLASS}'.strip()
