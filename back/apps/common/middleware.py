from apps.common.tenancy import attach_tenant_context


class TenantContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        attach_tenant_context(request)
        return self.get_response(request)