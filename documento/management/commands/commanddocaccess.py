from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):
    help = 'Cria o grupo de acesso a documentos e atribui permissões'

    def handle(self, *args, **options):
        grupo_documentos = Group.objects.create(name='Acesso a Documentos')
        permissoes = Permission.objects.filter(codename__in=[
            'view_tipodocumento', 'edit_tipodocumento', 'delete_tipodocumento', 'create_tipodocumento',
            'view_grupodocumento', 'edit_grupodocumento', 'delete_grupodocumento', 'create_grupodocumento'
        ])
        grupo_documentos.permissions.set(permissoes)
        grupo_documentos.save()

        self.stdout.write(self.style.SUCCESS('Grupo de acesso a documentos criado e configurado com sucesso.'))
