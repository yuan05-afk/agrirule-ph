from django import forms

from expert_system.forms import CropForm as BaseCropForm
from expert_system.forms import RuleForm as BaseRuleForm


class CropForm(BaseCropForm):
    pass


class RuleForm(BaseRuleForm):
    pass


TEXT_CLASS = (
    'w-full rounded-xl border border-stone-200 bg-stone-50/30 focus:bg-white '
    'focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 text-sm py-2.5 px-3 outline-none transition-all shadow-sm'
)


def apply_dashboard_classes(form):
    for field in form.fields.values():
        widget = field.widget
        if isinstance(widget, forms.CheckboxInput):
            continue
        current = widget.attrs.get('class', '')
        widget.attrs['class'] = f'{current} {TEXT_CLASS}'.strip()
