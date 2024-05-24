from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission

class Command(BaseCommand):
    help = 'Cria o grupo de administradores e atribui permissões'

    def handle(self, *args, **options):
        grupo_admin = Group.objects.create(name='Administradores')
        permissoes = Permission.objects.filter(codename__in=[
            'add_empresa', 'view_empresa_list', 'add_regional', 'view_regional_list',
            'add_unidade', 'view_unidade_list', 'access_dashboard', 'access_dossie',
            'access_dados_pessoais', 'access_relatorios'
        ])
        grupo_admin.permissions.set(permissoes)
        grupo_admin.save()

        self.stdout.write(self.style.SUCCESS('Grupo de administradores criado e configurado com sucesso.'))

