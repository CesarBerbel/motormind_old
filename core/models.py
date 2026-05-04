import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """
    Abstract model for created_at and updated_at fields.
    """

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em",
    )

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """
    Abstract model with public UUID.

    The regular database ID remains available, but UUID can be used later in
    URLs, APIs or external references without exposing sequential IDs.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
        verbose_name="UUID",
    )

    class Meta:
        abstract = True


class ActiveModel(models.Model):
    """
    Abstract model with active/inactive flag.
    """

    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativo",
    )

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """
    Abstract soft delete behavior.

    This does not physically remove the record. It marks deleted_at and
    deactivates the record when the model also has is_active.
    """

    deleted_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Excluído em",
    )

    class Meta:
        abstract = True

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def soft_delete(self, save=True):
        self.deleted_at = timezone.now()

        if hasattr(self, "is_active"):
            self.is_active = False

        if save:
            self.save()

    def restore(self, save=True):
        self.deleted_at = None

        if hasattr(self, "is_active"):
            self.is_active = True

        if save:
            self.save()


class BaseModel(UUIDModel, TimeStampedModel, ActiveModel, SoftDeleteModel):
    """
    Recommended base model for future MotorMind entities.

    Use this in new models when the entity needs:
    - UUID;
    - created_at;
    - updated_at;
    - is_active;
    - deleted_at;
    - soft delete behavior.

    Existing models do not need to be changed immediately to avoid unnecessary
    migrations during the current refactoring phase.
    """

    class Meta:
        abstract = True


class CompanySettings(TimeStampedModel):
    """
    Stores the official workshop/company data used by the administrative area.

    This model is intentionally singleton-like. The system must have at most one
    active configuration record because the current MotorMind scope is a single
    workshop, not a multi-tenant SaaS.
    """

    name = models.CharField(
        max_length=150,
        verbose_name="Nome da oficina",
    )

    legal_name = models.CharField(
        max_length=180,
        blank=True,
        verbose_name="Razão social",
    )

    document = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="CPF/CNPJ",
    )

    state_registration = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Inscrição estadual",
    )

    municipal_registration = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Inscrição municipal",
    )

    phone = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Telefone principal",
    )

    whatsapp = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="WhatsApp",
    )

    email = models.EmailField(
        blank=True,
        verbose_name="Email principal",
    )

    website = models.URLField(
        blank=True,
        verbose_name="Site",
    )

    address_line = models.CharField(
        max_length=180,
        blank=True,
        verbose_name="Endereço",
    )

    number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Número",
    )

    complement = models.CharField(
        max_length=80,
        blank=True,
        verbose_name="Complemento",
    )

    neighborhood = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Bairro",
    )

    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Cidade",
    )

    state = models.CharField(
        max_length=2,
        blank=True,
        verbose_name="UF",
    )

    zip_code = models.CharField(
        max_length=12,
        blank=True,
        verbose_name="CEP",
    )

    opening_hours = models.TextField(
        blank=True,
        verbose_name="Horário de funcionamento",
    )

    service_terms = models.TextField(
        blank=True,
        verbose_name="Termos de serviço e observações padrão",
    )

    is_configured = models.BooleanField(
        default=False,
        verbose_name="Configuração concluída",
    )

    class Meta:
        verbose_name = "Dados da oficina"
        verbose_name_plural = "Dados da oficina"

    def __str__(self):
        return self.name or "Dados da oficina"

    @classmethod
    def get_solo(cls):
        """
        Return the single company settings row, creating it when necessary.
        """
        settings, _created = cls.objects.get_or_create(
            pk=1,
            defaults={
                "name": "Oficina",
            },
        )
        return settings

    def clean(self):
        super().clean()

        if self.pk and self.pk != 1:
            raise ValidationError("O sistema permite apenas um cadastro de dados da oficina.")

        if self.state:
            self.state = self.state.upper()

        if self.state and len(self.state) != 2:
            raise ValidationError({"state": "Informe a UF com 2 letras."})

    def save(self, *args, **kwargs):
        self.pk = 1
        self.full_clean()
        return super().save(*args, **kwargs)
