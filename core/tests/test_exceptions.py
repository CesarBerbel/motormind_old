from core.exceptions import (
    DomainError,
    FinancialAmountError,
    InsufficientStockError,
    InvalidStatusTransition,
    ObjectAlreadyExistsError,
    ObjectNotFoundError,
    OperationNotAllowedError,
    PermissionDeniedError,
    ValidationDomainError,
)


def test_domain_error_uses_default_message():
    error = DomainError()

    assert str(error) == "Ocorreu um erro de regra de negócio."


def test_domain_error_accepts_custom_message():
    error = DomainError("Mensagem personalizada.")

    assert str(error) == "Mensagem personalizada."


def test_permission_denied_error_default_message():
    assert (
        str(PermissionDeniedError())
        == "Você não tem permissão para executar esta ação."
    )


def test_invalid_status_transition_default_message():
    assert str(InvalidStatusTransition()) == "Transição de status inválida."


def test_insufficient_stock_error_default_message():
    assert str(InsufficientStockError()) == "Estoque insuficiente para esta operação."


def test_financial_amount_error_default_message():
    assert str(FinancialAmountError()) == "Valor financeiro inválido."


def test_object_already_exists_error_default_message():
    assert str(ObjectAlreadyExistsError()) == "O registro informado já existe."


def test_object_not_found_error_default_message():
    assert str(ObjectNotFoundError()) == "Registro não encontrado."


def test_operation_not_allowed_error_default_message():
    assert str(OperationNotAllowedError()) == "Esta operação não é permitida."


def test_validation_domain_error_default_message():
    assert str(ValidationDomainError()) == "Dados inválidos para esta operação."
