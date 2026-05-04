from django import forms

from mensagens.models import MessageTemplate
from mensagens.template_renderer import parse_variables_payload


class MessagePreviewForm(forms.Form):
    template = forms.ModelChoiceField(
        queryset=MessageTemplate.objects.filter(is_active=True).order_by("name"),
        label="Template",
        empty_label="Selecione um template",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    variables = forms.CharField(
        label="Variáveis reais",
        required=False,
        help_text=(
            "Informe JSON ou linhas no formato chave=valor. "
            'Exemplo JSON: {"cliente_nome": "João", "os_numero": "123"}'
        ),
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 10,
                "placeholder": (
                    "{\n"
                    '  "cliente_nome": "João Silva",\n'
                    '  "os_numero": "1234",\n'
                    '  "valor_total": "R$ 500,00"\n'
                    "}"
                ),
            }
        ),
    )

    def clean_variables(self):
        raw_variables = self.cleaned_data.get("variables")

        try:
            return parse_variables_payload(raw_variables)
        except ValueError as exc:
            raise forms.ValidationError(str(exc)) from exc
