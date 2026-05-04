from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from customers.models import Customer, Vehicle
from service_orders.models import ServiceOrder

from .models import (
    Campaign,
    CampaignAudience,
    CustomerInteraction,
    CustomerOpportunity,
    CustomerReminder,
)


class CRMBaseModelForm(forms.ModelForm):
    """
    Base visual e operacional para formulários do CRM.

    Mantém Bootstrap 5 sem depender de alteração em settings.py e centraliza
    classes, placeholders e mensagens para evitar formulários crus/inconsistentes.
    """

    required_css_class = "required"
    error_css_class = "is-invalid"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._configure_common_querysets()
        self._apply_bootstrap_widgets()

    def _configure_common_querysets(self):
        if "customer" in self.fields:
            self.fields["customer"].queryset = Customer.objects.filter(
                is_active=True
            ).order_by("name")
            self.fields["customer"].empty_label = "Selecione o cliente"

        if "vehicle" in self.fields:
            self.fields["vehicle"].queryset = (
                Vehicle.objects.filter(is_active=True)
                .select_related("customer")
                .order_by("plate")
            )
            self.fields["vehicle"].empty_label = "Selecione o veículo, se aplicável"
            self.fields["vehicle"].required = False

        if "service_order" in self.fields:
            self.fields["service_order"].queryset = (
                ServiceOrder.objects.select_related("customer", "vehicle")
                .exclude(status=ServiceOrder.Status.CANCELED)
                .order_by("-created_at")
            )
            self.fields["service_order"].empty_label = "Selecione a OS, se aplicável"
            self.fields["service_order"].required = False

    def _apply_bootstrap_widgets(self):
        for field in self.fields.items():
            widget = field.widget
            css_class = (
                "form-check-input"
                if isinstance(widget, forms.CheckboxInput)
                else "form-control"
            )

            if isinstance(widget, (forms.Select, forms.SelectMultiple)):
                css_class = "form-select"

            existing_class = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing_class} {css_class}".strip()

            if field.required and not isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("required", "required")

            if isinstance(widget, forms.TextInput):
                widget.attrs.setdefault("placeholder", field.label)

    def clean(self):
        cleaned_data = super().clean()
        customer = cleaned_data.get("customer")
        vehicle = cleaned_data.get("vehicle")
        service_order = cleaned_data.get("service_order")

        if vehicle and customer and vehicle.customer_id != customer.id:
            self.add_error(
                "vehicle", "O veículo selecionado não pertence ao cliente informado."
            )

        if service_order and customer and service_order.customer_id != customer.id:
            self.add_error(
                "service_order", "A OS selecionada não pertence ao cliente informado."
            )

        if service_order and vehicle and service_order.vehicle_id != vehicle.id:
            self.add_error(
                "service_order", "A OS selecionada não pertence ao veículo informado."
            )

        return cleaned_data


class CustomerInteractionForm(CRMBaseModelForm):
    class Meta:
        model = CustomerInteraction
        fields = [
            "customer",
            "vehicle",
            "service_order",
            "interaction_type",
            "channel",
            "subject",
            "description",
            "next_follow_up_date",
        ]
        labels = {
            "customer": "Cliente",
            "vehicle": "Veículo relacionado",
            "service_order": "OS relacionada",
            "interaction_type": "Tipo de interação",
            "channel": "Canal",
            "subject": "Assunto",
            "description": "Descrição da interação",
            "next_follow_up_date": "Próximo follow-up",
        }
        help_texts = {
            "vehicle": "Opcional. Use quando a interação estiver ligada a um veículo específico.",
            "service_order": "Opcional. Use quando a interação estiver ligada a uma ordem de serviço.",
            "next_follow_up_date": "Opcional. Preencha se esta interação exigir retorno futuro.",
        }
        widgets = {
            "description": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "Descreva o contato, combinado, reclamação, retorno ou observação comercial.",
                }
            ),
            "next_follow_up_date": forms.DateInput(attrs={"type": "date"}),
        }

    def clean_subject(self):
        subject = self.cleaned_data["subject"].strip()
        if len(subject) < 3:
            raise ValidationError("Informe um assunto com pelo menos 3 caracteres.")
        return subject

    def clean_description(self):
        description = self.cleaned_data["description"].strip()
        if len(description) < 5:
            raise ValidationError("Descreva a interação com pelo menos 5 caracteres.")
        return description


class CustomerOpportunityForm(CRMBaseModelForm):
    class Meta:
        model = CustomerOpportunity
        fields = [
            "customer",
            "vehicle",
            "service_order",
            "title",
            "description",
            "estimated_value",
            "probability",
            "status",
            "expected_close_date",
        ]
        labels = {
            "customer": "Cliente",
            "vehicle": "Veículo relacionado",
            "service_order": "OS relacionada",
            "title": "Título da oportunidade",
            "description": "Descrição",
            "estimated_value": "Valor estimado",
            "probability": "Probabilidade de fechamento (%)",
            "status": "Status",
            "expected_close_date": "Previsão de fechamento",
        }
        help_texts = {
            "estimated_value": "Use 0,00 quando ainda não houver valor estimado.",
            "probability": "Informe um número de 0 a 100.",
            "expected_close_date": "Opcional. Ajuda no acompanhamento comercial.",
        }
        widgets = {
            "description": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "Explique a oportunidade, necessidade do cliente e próximo passo recomendado.",
                }
            ),
            "expected_close_date": forms.DateInput(attrs={"type": "date"}),
            "estimated_value": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "probability": forms.NumberInput(attrs={"min": "0", "max": "100"}),
        }

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if len(title) < 3:
            raise ValidationError("Informe um título com pelo menos 3 caracteres.")
        return title

    def clean_estimated_value(self):
        value = self.cleaned_data.get("estimated_value") or Decimal("0.00")
        if value < 0:
            raise ValidationError("O valor estimado não pode ser negativo.")
        return value

    def clean_probability(self):
        probability = self.cleaned_data.get("probability")
        if probability is None:
            raise ValidationError("Informe a probabilidade.")
        if probability < 0 or probability > 100:
            raise ValidationError("A probabilidade deve estar entre 0 e 100.")
        return probability


class CustomerReminderForm(CRMBaseModelForm):
    class Meta:
        model = CustomerReminder
        fields = [
            "customer",
            "vehicle",
            "service_order",
            "title",
            "notes",
            "due_date",
            "status",
        ]
        labels = {
            "customer": "Cliente",
            "vehicle": "Veículo relacionado",
            "service_order": "OS relacionada",
            "title": "Título do lembrete",
            "notes": "Observações",
            "due_date": "Data de vencimento",
            "status": "Status",
        }
        help_texts = {
            "due_date": "Data em que o follow-up deve aparecer como pendência.",
            "notes": "Opcional. Inclua contexto para quem fará o contato.",
        }
        widgets = {
            "notes": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Ex.: ligar para confirmar satisfação, lembrar revisão preventiva, cobrar retorno de orçamento.",
                }
            ),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if len(title) < 3:
            raise ValidationError("Informe um título com pelo menos 3 caracteres.")
        return title

    def clean_due_date(self):
        due_date = self.cleaned_data.get("due_date")
        if not due_date:
            raise ValidationError("Informe a data de vencimento do lembrete.")
        return due_date


class CampaignForm(CRMBaseModelForm):
    class Meta:
        model = Campaign
        fields = [
            "name",
            "campaign_type",
            "channel",
            "subject",
            "message",
            "status",
            "scheduled_at",
        ]
        labels = {
            "name": "Nome da campanha",
            "campaign_type": "Tipo de campanha",
            "channel": "Canal",
            "subject": "Assunto",
            "message": "Mensagem",
            "status": "Status",
            "scheduled_at": "Agendada para",
        }
        help_texts = {
            "message": "Mensagens comerciais devem respeitar o consentimento do cliente antes do envio.",
            "scheduled_at": "Obrigatório quando o status for Agendada.",
        }
        widgets = {
            "message": forms.Textarea(
                attrs={
                    "rows": 8,
                    "placeholder": "Escreva a mensagem da campanha. Ex.: revisão preventiva, retorno de cliente inativo ou promoção.",
                }
            ),
            "scheduled_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["scheduled_at"].input_formats = ["%Y-%m-%dT%H:%M"]

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if len(name) < 3:
            raise ValidationError("Informe um nome com pelo menos 3 caracteres.")
        return name

    def clean_subject(self):
        subject = self.cleaned_data["subject"].strip()
        if len(subject) < 3:
            raise ValidationError("Informe um assunto com pelo menos 3 caracteres.")
        return subject

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if len(message) < 10:
            raise ValidationError(
                "A mensagem da campanha deve ter pelo menos 10 caracteres."
            )
        return message

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        scheduled_at = cleaned_data.get("scheduled_at")

        if status == Campaign.Status.SCHEDULED and not scheduled_at:
            self.add_error(
                "scheduled_at",
                "Informe a data e hora quando a campanha estiver agendada.",
            )

        if scheduled_at and scheduled_at < timezone.now():
            self.add_error(
                "scheduled_at", "A data de agendamento não pode estar no passado."
            )

        return cleaned_data


class CampaignAudienceForm(CRMBaseModelForm):
    class Meta:
        model = CampaignAudience
        fields = ["customer"]
        labels = {"customer": "Cliente"}
        help_texts = {
            "customer": "Selecione um cliente ativo para incluir no público da campanha."
        }
