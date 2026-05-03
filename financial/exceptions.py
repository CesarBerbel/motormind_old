class FinancialError(Exception):
    """Erro base do módulo financeiro"""

    pass


class InvalidAmountError(FinancialError):
    """Valor inválido para operação financeira"""

    pass


class PaymentExceedsBalanceError(FinancialError):
    """Pagamento maior que saldo disponível"""

    pass
