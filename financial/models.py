from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class PaymentMethod(models.TextChoices):
    """
    Available payment methods.
    """

    CASH = "cash", "Dinheiro"
    PIX = "pix", "PIX"
    DEBIT_CARD = "debit_card", "Cartão de débito"
    CREDIT_CARD = "credit_card", "Cartão de crédito"
    BANK_TRANSFER = "bank_transfer", "Transferência bancária"
    OTHER = "other", "Outro"


class PaymentStatus(models.TextChoices):
    """
    Available payment statuses.
    """

    PENDING = "pending", "Pendente"
    PAID = "paid", "Pago"
    CANCELED = "canceled", "Cancelado"


class CashFlowType(models.TextChoices):
    """
    Cash flow entry types.
    """

    INCOME = "income", "Entrada"
    EXPENSE = "expense", "Saída"


class Receivable(models.Model):
    """
    Model that stores amounts to be received from service orders.
    """

    service_order = models.OneToOneField(
        "service_orders.ServiceOrder",
        on_delete=models.PROTECT,
        related_name="receivable",
        verbose_name="Ordem de serviço",
    )

    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="receivables",
        verbose_name="Cliente",
    )

    original_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Valor original",
    )

    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Desconto",
    )

    final_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Valor final",
    )

    paid_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Valor pago",
    )

    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name="Status",
    )

    due_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Data de vencimento",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_receivables",
        verbose_name="Criado por",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em",
    )

    class Meta:
        verbose_name = "Conta a receber"
        verbose_name_plural = "Contas a receber"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Receivable OS #{self.service_order_id} - {self.final_amount}"

    @property
    def remaining_amount(self):
        """
        Return remaining amount to be paid.
        """
        remaining = self.final_amount - self.paid_amount

        if remaining < Decimal("0.00"):
            return Decimal("0.00")

        return remaining

    @property
    def is_fully_paid(self):
        """
        Check if receivable is fully paid.
        """
        return self.paid_amount >= self.final_amount

    def clean(self):
        """
        Validate receivable financial rules.
        """
        super().clean()

        if self.discount_amount > self.original_amount:
            raise ValidationError(
                {
                    "discount_amount": "O desconto não pode ser maior que o valor original."
                }
            )

        expected_final_amount = self.original_amount - self.discount_amount

        if self.final_amount != expected_final_amount:
            raise ValidationError(
                {
                    "final_amount": "O valor final deve ser igual ao valor original menos o desconto."
                }
            )

        if self.paid_amount > self.final_amount:
            raise ValidationError(
                {"paid_amount": "O valor pago não pode ser maior que o valor final."}
            )


class Payment(models.Model):
    """
    Model that stores payments received for a receivable.
    """

    receivable = models.ForeignKey(
        Receivable,
        on_delete=models.PROTECT,
        related_name="payments",
        verbose_name="Conta a receber",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Valor",
    )

    method = models.CharField(
        max_length=30,
        choices=PaymentMethod.choices,
        verbose_name="Forma de pagamento",
    )

    paid_at = models.DateTimeField(
        verbose_name="Pago em",
    )

    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_payments",
        verbose_name="Criado por",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em",
    )

    class Meta:
        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"
        ordering = ["-paid_at"]

    def __str__(self):
        return f"Payment #{self.pk} - {self.amount}"

    def clean(self):
        """
        Validate payment rules.
        """
        super().clean()

        if self.receivable_id and self.amount > self.receivable.remaining_amount:
            raise ValidationError(
                {"amount": "O pagamento não pode ser maior que o valor restante."}
            )


class Expense(models.Model):
    """
    Model that stores workshop expenses.
    """

    description = models.CharField(
        max_length=180,
        verbose_name="Descrição",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Valor",
    )

    due_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Data de vencimento",
    )

    paid_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Pago em",
    )

    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name="Status",
    )

    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_expenses",
        verbose_name="Criado por",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em",
    )

    class Meta:
        verbose_name = "Despesa"
        verbose_name_plural = "Despesas"
        ordering = ["-created_at"]

    def __str__(self):
        return self.description


class CashFlowEntry(models.Model):
    """
    Model that stores auditable cash flow entries.
    """

    entry_type = models.CharField(
        max_length=20,
        choices=CashFlowType.choices,
        verbose_name="Tipo",
    )

    description = models.CharField(
        max_length=180,
        verbose_name="Descrição",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Valor",
    )

    payment = models.OneToOneField(
        Payment,
        on_delete=models.PROTECT,
        related_name="cash_flow_entry",
        blank=True,
        null=True,
        verbose_name="Pagamento",
    )

    expense = models.OneToOneField(
        Expense,
        on_delete=models.PROTECT,
        related_name="cash_flow_entry",
        blank=True,
        null=True,
        verbose_name="Despesa",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_cash_flow_entries",
        verbose_name="Criado por",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em",
    )

    class Meta:
        verbose_name = "Lançamento de caixa"
        verbose_name_plural = "Lançamentos de caixa"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_entry_type_display()} - {self.amount}"

    def clean(self):
        """
        Validate cash flow source consistency.
        """
        super().clean()

        if self.payment and self.expense:
            raise ValidationError(
                "Um lançamento de caixa não pode estar ligado a pagamento e despesa ao mesmo tempo."
            )

        if not self.payment and not self.expense:
            raise ValidationError(
                "Um lançamento de caixa precisa estar ligado a um pagamento ou despesa."
            )
