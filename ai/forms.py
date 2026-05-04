from django import forms

from .models import AIPromptTemplate, AIReviewStatus


class AIAssistantForm(forms.Form):
    prompt_template = forms.ModelChoiceField(
        label="Template de prompt",
        queryset=AIPromptTemplate.objects.none(),
        empty_label="Selecione um template ativo",
        help_text="A lista mostra apenas templates ativos. Se um caso de uso não aparecer, rode o seed ou ative o template no Admin.",
    )
    content = forms.CharField(
        label="Texto base",
        widget=forms.Textarea(attrs={"rows": 8}),
        help_text="Informe o relato, diagnóstico, mensagem ou contexto que a IA deve organizar.",
    )
    customer_name = forms.CharField(label="Cliente", required=False)
    vehicle = forms.CharField(label="Veículo", required=False)
    service_order_number = forms.CharField(label="Número da OS", required=False)
    tone = forms.CharField(
        label="Tom desejado",
        required=False,
        initial="profissional, claro e objetivo",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["prompt_template"].queryset = AIPromptTemplate.objects.filter(
            is_active=True
        ).order_by("use_case", "code", "-version")

    def clean_prompt_template(self):
        prompt_template = self.cleaned_data["prompt_template"]
        if not prompt_template.is_active:
            raise forms.ValidationError("Este template de prompt está inativo.")
        return prompt_template

    def get_input_data(self):
        return {
            "conteudo": self.cleaned_data["content"],
            "cliente_nome": self.cleaned_data.get("customer_name", ""),
            "veiculo": self.cleaned_data.get("vehicle", ""),
            "os_numero": self.cleaned_data.get("service_order_number", ""),
            "tom": self.cleaned_data.get("tone", ""),
        }


class AIReviewForm(forms.Form):
    status = forms.ChoiceField(
        label="Decisão da revisão", choices=AIReviewStatus.choices
    )
    edited_output_text = forms.CharField(
        label="Texto editado",
        required=False,
        widget=forms.Textarea(attrs={"rows": 8}),
    )
    notes = forms.CharField(
        label="Observações",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )
