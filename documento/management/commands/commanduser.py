
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):
    help = 'Cria o grupo de usuários comuns e atribui permissões'

    def handle(self, *args, **options):
        # Criando o grupo de usuários comuns
        grupo_comum = Group.objects.create(name='Usuarios')

        # Definindo as permissões que este grupo terá
        permissoes = Permission.objects.filter(codename__in=[
            'view_empresa_list', 'view_regional_list', 'view_unidade_list',
            'access_tela_login', 'access_dashboard', 'access_dossie',
            'access_dados_pessoais', 'access_relatorios'
        ])

        # Atribuindo as permissões ao grupo
        grupo_comum.permissions.set(permissoes)
        grupo_comum.save()

        self.stdout.write(self.style.SUCCESS('Grupo de usuários comuns criado e configurado com sucesso.'))

