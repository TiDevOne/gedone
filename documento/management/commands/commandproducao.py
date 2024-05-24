from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):
    help = 'Cria o grupo de Produção e atribui permissões'

    def handle(self, *args, **options):
        grupo_producao = Group.objects.create(name='Producao')
        permissoes = Permission.objects.filter(codename__in=[
            'add_empresa', 'view_empresa_list', 'add_regional', 'view_regional_list',
            'add_unidade', 'view_unidade_list', 'access_dashboard', 'access_dossie',
            'access_dados_pessoais', 'access_relatorios', 'access_configuracao'
        ])
        grupo_producao.permissions.set(permissoes)
        grupo_producao.save()

        self.stdout.write(self.style.SUCCESS('Grupo de Producão criado e configurado com sucesso.'))

