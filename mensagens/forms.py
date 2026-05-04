import json
import re

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from customers.models import Customer

from .models import (
    MessageChannel,
    MessageStatus,
    MessageTemplate,
    MessageType,
)

PLACEHOLDER_PATTERN = re.compile(r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*}}")


class BootstrapFormMixin:
    """Apply Bootstrap-friendly widgets without requiring template-specific code."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")
            if field.required:
                widget.attrs.setdefault("required", "required")
            if field.help_text:
                widget.attrs.setdefault("aria-describedby", f"id_{field_name}_helptext")


class MessageTemplateForm(BootstrapFormMixin, forms.ModelForm):
    available_variables = forms.CharField(
        label="Variáveis disponíveis",
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": '["cliente_nome", "os_numero", "portal_url"] ou uma variável por linha',
            }
        ),
        help_text="Informe JSON, uma variável por linha ou variáveis separadas por vírgula. Use somente letras, números e underline.",
    )

    class Meta:
        model = MessageTemplate
        fields = [
            "name",
            "code",
            "channel",
            "message_type",
            "subject",
            "body",
            "available_variables",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={"placeholder": "Ex.: Abertura de OS por e-mail"}
            ),
            "code": forms.TextInput(attrs={"placeholder": "Ex.: abertura_os_email"}),
            "subject": forms.TextInput(
                attrs={"placeholder": "Ex.: Ordem de serviço {{ os_numero }} aberta"}
            ),
            "body": forms.Textarea(
                attrs={
                    "rows": 10,
                    "placeholder": "Digite o texto usando variáveis como {{ cliente_nome }}.",
                }
            ),
        }
        help_texts = {
            "code": "Código técnico único usado pelos services. Use minúsculas, números, hífen ou underline.",
            "subject": "Obrigatório para e-mail. Opcional para WhatsApp.",
            "body": "Corpo oficial do template. O texto enviado ficará salvo como snapshot no log.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if (
            self.instance
            and self.instance.pk
            and isinstance(self.instance.available_variables, list)
        ):
            self.initial["available_variables"] = json.dumps(
                self.instance.available_variables, ensure_ascii=False, indent=2
            )

    def clean_code(self):
        code = (self.cleaned_data.get("code") or "").strip().lower().replace("-", "_")
        if not re.fullmatch(r"[a-z0-9_]+", code):
            raise ValidationError(
                "Use apenas letras minúsculas, números e underline no código."
            )
        return code

    def clean_available_variables(self):
        raw_value = (self.cleaned_data.get("available_variables") or "").strip()
        if not raw_value:
            return []

        if raw_value.startswith("["):
            try:
                variables = json.loads(raw_value)
            except json.JSONDecodeError as exc:
                raise ValidationError(
                    "JSON inválido nas variáveis disponíveis."
                ) from exc
            if not isinstance(variables, list):
                raise ValidationError(
                    "As variáveis disponíveis devem formar uma lista."
                )
        else:
            variables = [
                item.strip() for item in re.split(r"[,\n]", raw_value) if item.strip()
            ]

        normalized = []
        for variable in variables:
            if not isinstance(variable, str):
                raise ValidationError("Cada variável deve ser texto.")
            variable = variable.strip().strip("{} ")
            if not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*", variable):
                raise ValidationError(f"Variável inválida: {variable}")
            if variable not in normalized:
                normalized.append(variable)
        return normalized

    def clean(self):
        cleaned_data = super().clean()
        channel = cleaned_data.get("channel")
        subject = (cleaned_data.get("subject") or "").strip()
        body = cleaned_data.get("body") or ""
        available_variables = cleaned_data.get("available_variables") or []

        if channel == MessageChannel.EMAIL and not subject:
            self.add_error("subject", "Templates de e-mail precisam de assunto.")

        used_variables = set(PLACEHOLDER_PATTERN.findall(f"{subject}\n{body}"))
        missing_variables = sorted(used_variables - set(available_variables))
        if missing_variables:
            self.add_error(
                "available_variables",
                "Inclua nas variáveis disponíveis: " + ", ".join(missing_variables),
            )
        return cleaned_data


class ManualMessageForm(BootstrapFormMixin, forms.Form):
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.filter(is_active=True).order_by("name"),
        label="Cliente",
        required=False,
        help_text="Selecione um cliente para o sistema preencher o destinatário pelo cadastro quando possível.",
    )
    template = forms.ModelChoiceField(
        queryset=MessageTemplate.objects.none(),
        label="Template",
        required=False,
        help_text="Opcional. Ao selecionar um template, canal e tipo serão validados contra ele.",
    )
    channel = forms.ChoiceField(choices=MessageChannel.choices, label="Canal")
    message_type = forms.ChoiceField(choices=MessageType.choices, label="Tipo")
    recipient = forms.CharField(
        label="Destinatário",
        max_length=180,
        required=False,
        help_text="Obrigatório se nenhum cliente for selecionado ou se o cliente não tiver contato no canal escolhido.",
    )
    subject = forms.CharField(label="Assunto", max_length=180, required=False)
    body = forms.CharField(
        label="Mensagem",
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 8,
                "placeholder": "Digite a mensagem manual ou use um template.",
            }
        ),
    )
    variables = forms.CharField(
        label="Variáveis do template",
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": '{"cliente_nome": "João", "os_numero": "123"}',
            }
        ),
        help_text="Use JSON quando o template tiver variáveis. Mensagens manuais sem template podem deixar este campo vazio.",
    )
    scheduled_at = forms.DateTimeField(
        label="Agendar para",
        required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        input_formats=["%Y-%m-%dT%H:%M"],
        help_text="Deixe vazio para enviar assim que a fila for processada.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["template"].queryset = MessageTemplate.objects.filter(
            is_active=True
        ).order_by("channel", "name")
        self.fields["recipient"].widget.attrs.setdefault(
            "placeholder", "email@exemplo.com ou telefone com DDD"
        )
        self.fields["subject"].widget.attrs.setdefault(
            "placeholder", "Obrigatório para e-mail sem template"
        )

    def clean_variables(self):
        raw_value = (self.cleaned_data.get("variables") or "").strip()
        if not raw_value:
            return {}
        try:
            variables = json.loads(raw_value)
        except json.JSONDecodeError as exc:
            raise ValidationError("As variáveis devem estar em JSON válido.") from exc
        if not isinstance(variables, dict):
            raise ValidationError(
                'As variáveis devem formar um objeto JSON, por exemplo: {"cliente_nome": "João"}.'
            )
        return variables

    def clean_scheduled_at(self):
        scheduled_at = self.cleaned_data.get("scheduled_at")
        if scheduled_at and timezone.is_naive(scheduled_at):
            scheduled_at = timezone.make_aware(
                scheduled_at, timezone.get_current_timezone()
            )
        return scheduled_at

    def clean(self):
        cleaned_data = super().clean()
        customer = cleaned_data.get("customer")
        template = cleaned_data.get("template")
        channel = cleaned_data.get("channel")
        message_type = cleaned_data.get("message_type")
        recipient = (cleaned_data.get("recipient") or "").strip()
        subject = (cleaned_data.get("subject") or "").strip()
        body = (cleaned_data.get("body") or "").strip()
        variables = cleaned_data.get("variables") or {}

        if template:
            if template.channel != channel:
                self.add_error(
                    "channel", "O canal deve ser o mesmo do template selecionado."
                )
            if template.message_type != message_type:
                self.add_error(
                    "message_type", "O tipo deve ser o mesmo do template selecionado."
                )
            missing_variables = sorted(
                set(template.available_variables or []) - set(variables.keys())
            )
            if missing_variables:
                self.add_error(
                    "variables",
                    "Informe as variáveis obrigatórias do template: "
                    + ", ".join(missing_variables),
                )
        elif not body:
            self.add_error("body", "Digite a mensagem ou selecione um template ativo.")

        if channel == MessageChannel.EMAIL and not template and not subject:
            self.add_error(
                "subject", "Mensagens de e-mail sem template precisam de assunto."
            )

        if not customer and not recipient:
            self.add_error(
                "recipient", "Informe o destinatário ou selecione um cliente."
            )

        cleaned_data["recipient"] = recipient
        cleaned_data["subject"] = subject
        cleaned_data["body"] = body
        return cleaned_data


class QueueFilterForm(BootstrapFormMixin, forms.Form):
    status = forms.ChoiceField(
        choices=[("", "Todos")] + list(MessageStatus.choices),
        required=False,
        label="Status",
    )
    channel = forms.ChoiceField(
        choices=[("", "Todos")] + list(MessageChannel.choices),
        required=False,
        label="Canal",
    )
