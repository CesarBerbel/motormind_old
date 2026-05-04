from django import forms

from auditoria.models import AuditLog


class AuditLogFilterForm(forms.Form):
    action = forms.ChoiceField(
        label="Ação",
        required=False,
        choices=[("", "Todas")] + list(AuditLog.Action.choices),
    )
    app_label = forms.CharField(
        label="App",
        required=False,
        max_length=100,
    )
    model_name = forms.CharField(
        label="Modelo",
        required=False,
        max_length=100,
    )
