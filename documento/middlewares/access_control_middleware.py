from django.http import HttpResponseForbidden
from django.contrib.auth.models import Permission
from documento.models import AcessoEmpresa, AcessoUnidade

class AcessoControleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        empresa_id = request.GET.get('empresa_id')
        unidade_id = request.GET.get('unidade_id')
        tipo_documento_id = request.GET.get('tipo_documento_id')  # Supondo que este seja um parâmetro

        if empresa_id and not self.tem_acesso_empresa(request.user, empresa_id):
            return HttpResponseForbidden("Acesso negado à empresa.")
        if unidade_id and not self.tem_acesso_unidade(request.user, unidade_id):
            return HttpResponseForbidden("Acesso negado à unidade.")
        if tipo_documento_id and not self.tem_acesso_documento(request.user, tipo_documento_id):
            return HttpResponseForbidden("Acesso negado ao tipo de documento.")

        return self.get_response(request)

    def tem_acesso_empresa(self, user, empresa_id):
        return AcessoEmpresa.objects.filter(usuario=user, empresa_id=empresa_id, pode_acessar=True).exists()

    def tem_acesso_unidade(self, user, unidade_id):
        return AcessoUnidade.objects.filter(usuario=user, unidade_id=unidade_id, pode_acessar=True).exists()

    def tem_acesso_documento(self, user, tipo_documento_id):
        # Esta função precisaria ser implementada para verificar permissões específicas de documentos
        perm_codename = f"documento.view_tipodocumento_{tipo_documento_id}"
        return user.has_perm(perm_codename)
