class DomainError(Exception):
    """
    Base exception for business rule violations.

    Services should raise DomainError or one of its subclasses when a business
    rule is violated. Views should catch these exceptions and convert them into
    friendly messages for the user.
    """

    default_message = "Ocorreu um erro de regra de negócio."

    def __init__(self, message=None):
        self.message = message or self.default_message
        super().__init__(self.message)


class PermissionDeniedError(DomainError):
    default_message = "Você não tem permissão para executar esta ação."


class InvalidStatusTransition(DomainError):
    default_message = "Transição de status inválida."


class InsufficientStockError(DomainError):
    default_message = "Estoque insuficiente para esta operação."


class FinancialAmountError(DomainError):
    default_message = "Valor financeiro inválido."


class ObjectAlreadyExistsError(DomainError):
    default_message = "O registro informado já existe."


class ObjectNotFoundError(DomainError):
    default_message = "Registro não encontrado."


class OperationNotAllowedError(DomainError):
    default_message = "Esta operação não é permitida."


class ValidationDomainError(DomainError):
    default_message = "Dados inválidos para esta operação."
