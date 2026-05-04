from auditoria.context import reset_current_request, set_current_request


class AuditRequestMiddleware:
    """
    Disponibiliza a request atual para services de auditoria.

    O middleware não grava logs sozinho para evitar ruído. Ele apenas permite
    que auditoria.services capture IP, user-agent e path quando um serviço de
    negócio registrar um evento crítico.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = set_current_request(request)
        try:
            return self.get_response(request)
        finally:
            reset_current_request(token)
