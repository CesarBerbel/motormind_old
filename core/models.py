import uuid

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
