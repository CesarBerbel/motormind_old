# Auditoria MotorMind

## Objetivo

Centralizar o registro de eventos críticos do sistema sem acoplar os módulos de negócio entre si.

## Eventos cobertos

- login realizado;
- falha de login;
- logout;
- abertura, alteração e cancelamento de OS;
- movimentação de estoque;
- criação de conta a receber;
- registro de pagamento;
- registro e quitação de despesa.

## Regra de permissão

A trilha global de auditoria é visível apenas para usuários do grupo `Administrador`.

## Como registrar um evento em outro módulo

Use sempre o serviço público:

```python
from auditoria.models import AuditLog
from auditoria.services import log_event, serialize_instance

log_event(
    action=AuditLog.Action.UPDATE,
    user=request.user,
    obj=objeto,
    old_data=dados_antigos,
    new_data=serialize_instance(objeto),
)
```

Nunca grave diretamente em `AuditLog.objects.create()` dentro dos módulos de negócio.
