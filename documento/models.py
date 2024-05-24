from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .validators import CustomPasswordValidator
from django.contrib.auth import get_user_model


# **************** BASE GERAL DO SISTEMA **********************

class Empresa(models.Model):
    """
    Modelo que representa uma empresa.
    """
    nome = models.CharField(max_length=255)

    class Meta:
        db_table = 'empresa'  # Especifica o nome da tabela no banco de dados
        ordering = ['id']  # Isso garante que as empresas sejam ordenadas pelo ID por padrão

    def str(self):
        return self.nome

    @staticmethod
    def get_default_empresa_id():
        primeira_empresa = Empresa.objects.first()
        if primeira_empresa:
            return primeira_empresa.id
        return None


class Regional(models.Model):
    """
    Modelo que representa uma regional.
    """
    nome = models.CharField(max_length=255)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)

    class Meta:
        db_table = 'regional'  # Especifica o nome da tabela no banco de dados
        ordering = ['id']  # Isso garante que as regionais sejam ordenadas pelo ID por padrão

    def str(self):
        return self.nome

    @staticmethod
    def get_default_regional_id():
        primeira_regional = Regional.objects.first()
        if primeira_regional:
            return primeira_regional.id
        return None


class Unidade(models.Model):
    """
    Modelo que representa uma unidade.
    """
    nome = models.CharField(max_length=255)
    regional = models.ForeignKey(Regional, on_delete=models.CASCADE)

    class Meta:
        db_table = 'unidade'  # Especifica o nome da tabela no banco de dados
        ordering = ['id']  # Isso garante que as unidades sejam ordenadas pelo ID por padrão

    def str(self):
        return self.nome

    @staticmethod
    def get_default_unidade_id():
        primeira_unidade = Unidade.objects.first()
        if primeira_unidade:
            return primeira_unidade.id
        return None


class Cargo(models.Model):
    """
    Modelo que representa um cargo.
    """
    nome = models.CharField(max_length=255)
    unidade = models.ForeignKey(Unidade, on_delete=models.CASCADE, null=False)

    class Meta:
        db_table = 'cargo'  # Especifica o nome da tabela no banco de dados
        ordering = ['id']  # Isso garante que os cargos sejam ordenados pelo ID por padrão

    def str(self):
        return self.nome

    @staticmethod
    def get_default_cargo_id():
        primeiro_cargo = Cargo.objects.first()
        if primeiro_cargo:
            return primeiro_cargo.id
        return None

class Situacao(models.Model):
    """
    Modelo que representa uma situação.
    """

    nome = models.CharField(max_length=255)
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE, null=False)

    class Meta:
        db_table = 'situacao'  # Especifica o nome da tabela no banco de dados
        ordering = ['id']  # Isso garante que as empresas sejam ordenadas pelo ID por padrão

    def str(self):
        return self.nome

    @staticmethod
    def get_default_situacao_id():
        primeiro_situacao = Situacao.objects.first()
        if primeiro_situacao:
            return primeiro_situacao.id
        return None


class Colaborador(models.Model):
    """
    Modelo para representar um colaborador.

    Atributos:
        regional (CharField): Regional do colaborador.
        unidade (CharField): Unidade do colaborador.
        nome_colaborador (CharField): Nome do colaborador.
        matricula (CharField): Matrícula do colaborador.
        cpf (CharField): CPF do colaborador.
        cargo (CharField): Cargo do colaborador.
        situacao (CharField): Situação do colaborador.
        admissao (DateField): Data de admissão do colaborador.
        desligamento (DateField): Data de desligamento do colaborador.
    """
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, default=Empresa.get_default_empresa_id)
    regional = models.ForeignKey(Regional, on_delete=models.CASCADE, default=Regional.get_default_regional_id)
    unidade = models.ForeignKey(Unidade, on_delete=models.CASCADE, default=Unidade.get_default_unidade_id)
    nome = models.CharField(max_length=255)
    matricula = models.CharField(max_length=20)
    cpf = models.CharField(max_length=14)
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE, default=Cargo.get_default_cargo_id)
    modo_ponto = models.CharField(max_length=255)
    status = models.ForeignKey(Situacao, on_delete=models.CASCADE, default=Situacao.get_default_situacao_id)
    admissao = models.DateField()
    desligamento = models.DateField(null=True, blank=True)
    email = models.CharField(max_length=255, null=True)
    pcd = models.CharField(max_length=3)

    class Meta:
        db_table = 'colaborador'  # Especifica o nome da tabela no banco de dados
        # unique_together = ('matricula', 'unidade')  # Isso cria uma chave única composta por 'matricula' e 'unidade'

    def str(self):
        return self.nome


class Area(models.Model):
    nome = models.CharField(max_length=255)
    codigo = models.CharField(max_length=255)


    class Meta:
        db_table = 'area'  # Especifica o nome da tabela no banco de dados
        # Você pode adicionar outras opções da classe Meta conforme necessário

    def str(self):
        return self.area

    def get_default_area_id(self):
        primeira_area = Area.objects.first()
        if primeira_area:
            return primeira_area.id
        return None



#   ************** CONFIGURAÇÔES *****************


class GrupoDocumento(models.Model):
    nome = models.CharField(max_length=255)
    codigo = models.CharField(max_length=255)  # Corrigido aqui
    area = models.ForeignKey('Area', on_delete=models.CASCADE, default=Area.get_default_area_id)

    # tipo_documento = models.ForeignKey('TipoDocumento', on_delete=models.CASCADE, default=TipoDocumento.get_default_tipodocumento_id)
    class Meta:
        db_table = 'grupodocumento'


    def str(self):
        return self.nome  # Parece que aqui deveria ser self.nome

    def get_default_grupodocumento_id(self):
        primeira_grupodocumento = GrupoDocumento.objects.first()
        if primeira_grupodocumento:
            return primeira_grupodocumento.id
        return None


class TipoDocumento(models.Model):
    codigo = models.CharField(max_length=255)
    grupo_documento = models.ForeignKey(GrupoDocumento, on_delete=models.CASCADE, default=GrupoDocumento.get_default_grupodocumento_id)
    nome = models.CharField(max_length=255)
    # colaboradordoc = models.ForeignKey(ColaboradorTipoDocumento, on_delete=models.CASCADE, default=None)  # Remova o default
    pcd = models.CharField(max_length=255, default=False)
    obrigatorio = models.BooleanField(default=False, null=True)
    valor_legal = models.BooleanField(default=False)
    verifica_assinatura = models.BooleanField(default=False)
    auditoria = models.CharField(max_length=255, null=True)  # Corrigido aqui
    validade = models.CharField(max_length=255)
    tipo_validade = models.CharField(max_length=255)
    exibe_relatorio = models.BooleanField(default=False)
    lista_situacao = models.CharField(max_length=255)
    prioridade = models.CharField(max_length=255, null=True)
    # cargo = models.ForeignKey(TipoDocumentoCargo, on_delete=models.CASCADE, default=None, null=True)  # Remova o default
    hiperlink_documento = models.ForeignKey('Hyperlinkpdf', on_delete=models.CASCADE, null=True)  # Remova o default

    class Meta:
        db_table = 'tipodocumento'


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # Corrigindo a chamada para desempacotar args e kwargs
        self.hiperlink_documento_id = None

    def __str__(self):
        return self.tipo_documento

   #  @classmethod
    # def get_default_colaborador_id(cls):
        # primeiro_colaborador = Colaborador.objects.first()
        # if primeiro_colaborador:
           #  return primeiro_colaborador.id
        # return None

    @classmethod
    def get_default_hiperlink_documento_id(cls):
        primeiro_hiperlink_documento = Hyperlinkpdf.objects.first()
        if primeiro_hiperlink_documento:
            return primeiro_hiperlink_documento.id
        return None

    def save(self, *args, **kwargs):
        # if not self.colaborador_id:
            # self.colaborador_id = self.get_default_colaborador_id()
        if not self.hiperlink_documento_id:
            self.hiperlink_documento_id = self.get_default_hiperlink_documento_id()
        super().save(*args, **kwargs)


class ColaboradorTipoDocumento(models.Model):
    colaborador = models.ForeignKey(Colaborador, on_delete=models.CASCADE)
    tipo_documento = models.ForeignKey(TipoDocumento, on_delete=models.CASCADE)

    class Meta:
        db_table = 'colaborador_tipodocumento'
        constraints = [
            models.UniqueConstraint(fields=['colaborador', 'tipo_documento'], name='unique_colaborador_tipodocumento'),
        ]

    def str(self):
        return f"{self.colaborador} - {self.tipo_documento}"


class TipoDocumentoCargo(models.Model):
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE)
    tipo_documento = models.ForeignKey(TipoDocumento, on_delete=models.CASCADE, db_column='tipodocumento_id')

    class Meta:
        db_table = 'tipodocumento_cargo'
        constraints = [
            models.UniqueConstraint(fields=['cargo', 'tipo_documento'], name='unique_tipodocumento_cargo'),
        ]

    def __str__(self):
        return f"{self.cargo} - {self.tipo_documento}"


# FAZ PARTE DA CLASS HYPERLINKPDF *********
def default_empresa_id():
    default = Empresa.objects.first()
    return default.id if default else None

def default_regional_id():
    default = Regional.objects.first()
    return default.id if default else None

def default_unidade_id():
    default = Unidade.objects.first()
    return default.id if default else None

def default_colaborador_id():
    default = Colaborador.objects.first()
    return default.id if default else None

def default_cargo_id():
    default = Cargo.objects.first()
    return default.id if default else None

# Modelo Hyperlinkpdf
class Hyperlinkpdf(models.Model):
    data_upload = models.DateField()
    caminho = models.CharField(max_length=255)
    documento = models.ForeignKey('TipoDocumento', on_delete=models.CASCADE, null=True)
    matricula = models.CharField(max_length=255)
    cpf = models.CharField(max_length=255)
    nome_arquivo = models.CharField(max_length=255)
    dta_documento = models.DateField(null=True)
    codigo_documento = models.CharField(max_length=255)
    empresa = models.ForeignKey('Empresa', on_delete=models.CASCADE, default=default_empresa_id, null=True)
    regional = models.ForeignKey('Regional', on_delete=models.CASCADE, default=default_regional_id, null=True)
    unidade = models.ForeignKey('Unidade', on_delete=models.CASCADE, default=default_unidade_id, null=True)
    colaborador = models.ForeignKey('Colaborador', on_delete=models.CASCADE, default=default_colaborador_id, null=True)
    cargo = models.ForeignKey('Cargo', on_delete=models.CASCADE, default=default_cargo_id, null=True)


    class Meta:
        db_table = 'hyperlinkdocpdf'

    def __str__(self):
        return self.nome_arquivo


class HyperlinkDadosNull(models.Model):
    data_upload = models.DateField()
    caminho = models.CharField(max_length=255)
    documento = models.ForeignKey('TipoDocumento', on_delete=models.CASCADE, null=True)
    matricula = models.CharField(max_length=255)
    cpf = models.CharField(max_length=255)
    nome_arquivo = models.CharField(max_length=255)
    dta_documento = models.DateField(null=True)
    codigo_documento = models.CharField(max_length=255)
    empresa = models.ForeignKey('Empresa', on_delete=models.CASCADE, null=True)
    regional = models.ForeignKey('Regional', on_delete=models.CASCADE, null=True)
    unidade = models.ForeignKey('Unidade', on_delete=models.CASCADE, null=True)
    colaborador = models.ForeignKey('Colaborador', on_delete=models.CASCADE, null=True)
    cargo = models.ForeignKey('Cargo', on_delete=models.CASCADE, null=True)

    class Meta:
        db_table = 'hyperlink_dados_null'

    def __str__(self):
        return self.nome_arquivo


class ImportUsuarioXLSX(models.Model):
    nome = models.CharField(max_length=100)
    login = models.CharField(max_length=50)
    regional = models.CharField(max_length=50)
    unidade = models.CharField(max_length=50)
    ativo = models.BooleanField(default=True)
    senha = models.CharField(max_length=128)  # Ou outro tamanho adequado para sua aplicação

    def str(self):
        return self.nome  # Ou outro campo que você deseja que apareça quando você imprime um objeto ImportUsuarioXLSX


class UsuarioManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        """
        Cria e salva um Usuário com o username, e-mail e senha fornecidos.
        """
        if not email:
            raise ValueError('O email é obrigatório')
        if not username:
            raise ValueError('O username é obrigatório')

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        """
        Cria e salva um superusuário com o username, email e senha fornecidos.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)

class Usuario(AbstractUser):
    telefone = models.CharField(max_length=15, null=True, blank=True)
    objects = UsuarioManager()

    def set_password(self, raw_password):
        """
        Sobrescreve o método set_password para incluir validação de senha personalizada.
        """
        validator = CustomPasswordValidator()
        try:
            validator.validate(raw_password, self)
        except ValidationError as e:
            raise e
        super().set_password(raw_password)

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='documento_usuarios_groups',
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='documento_usuarios_permissions',
    )

    class Meta:
        db_table = 'auth_user'
        permissions = (
            ("add_empresa", "Pode adicionar empresas"),
            ("view_empresa_list", "Pode ver a lista de empresas"),
            ("add_regional", "Pode adicionar regionais"),
            ("view_regional_list", "Pode ver a lista de regionais"),
            ("add_unidade", "Pode adicionar unidades"),
            ("view_unidade_list", "Pode ver a lista de unidades"),
            ("access_tela_login", "Pode acessar a tela de login"),
            ("access_dashboard", "Pode acessar o dashboard"),
            ("access_dossie", "Pode acessar o dossiê"),
            ("access_dados_pessoais", "Pode acessar os dados pessoais"),
            ("access_relatorios", "Pode acessar relatórios"),
            ("access_configuracao", "Pode acessar configurações"),
            # Permissões para acessar menus específicos
            ("access_menu_dashboard", "Pode acessar o menu do Dashboard"),
            ("access_menu_dossie", "Pode acessar o menu do Dossiê"),
            ("access_menu_relatorios", "Pode acessar o menu de Relatórios"),
            ("access_menu_configuracoes", "Pode acessar o menu de Configurações"),
            # Adicione outras permissões conforme necessário
        )

class PasswordResetRequest(models.Model):
    email = models.EmailField()
    token = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)


#   ************** Relatórios *****************

class DocumentoPendente(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    regional = models.ForeignKey(Regional, on_delete=models.CASCADE)
    unidade = models.ForeignKey(Unidade, on_delete=models.CASCADE)
    nome = models.ForeignKey(Colaborador, on_delete=models.CASCADE)
    matricula = models.CharField(max_length=20)
    cpf = models.CharField(max_length=14)
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE)
    admissao = models.DateField()
    desligamento = models.DateField(null=True, blank=True)
    situacao = models.CharField(max_length=255, null=True, blank=True)
    tipo_documento = models.ForeignKey(TipoDocumento, on_delete=models.CASCADE)
    obrigatorio = models.BooleanField(default=False)

    class Meta:
        db_table = 'relatoriodocpendente'

    def __str__(self):
        return f"{self.nome} - {self.tipo_documento}"


class PendenteASO(models.Model):
    """
    Modelo para armazenar informações sobre as pendências ASO.

    Atributos:
        id (AutoField): Chave primária do modelo.
        empresa (ForeignKey): Referência à empresa do colaborador.
        regional (ForeignKey): Referência à regional do colaborador.
        unidade (ForeignKey): Referência à unidade do colaborador.
        nome (ForeignKey): Referência ao nome do colaborador.
        matricula (CharField): Matrícula do colaborador.
        cpf (CharField): CPF do colaborador, opcional.
        cargo (ForeignKey): Referência ao cargo do colaborador.
        admissao (DateField): Data de admissão do colaborador.
        desligamento (DateField): Data de desligamento do colaborador, opcional.
        status (ForeignKey): Status atual do colaborador.
        tipo_aso (ForeignKey): Tipo de ASO relacionado à pendência.
        aso_admissional_existente (BooleanField): Indica se o ASO Admissional está presente.
        aso_demissional_existente (BooleanField): Indica se o ASO Demissional está presente.
        aso_periodico_existente (BooleanField): Indica se o ASO Periódico/Retorno ao Trabalho está presente.
    """

    empresa = models.ForeignKey('Empresa', on_delete=models.CASCADE, null=True)
    regional = models.ForeignKey('Regional', on_delete=models.CASCADE, null=True)
    unidade = models.ForeignKey('Unidade', on_delete=models.CASCADE, null=True)
    nome = models.ForeignKey('Colaborador', on_delete=models.CASCADE, null=True)
    matricula = models.CharField(max_length=20)
    cpf = models.CharField(max_length=14, null=True)
    cargo = models.ForeignKey('Cargo', on_delete=models.CASCADE, null=True)
    admissao = models.DateField(null=True)
    desligamento = models.DateField(null=True, blank=True)
    status = models.ForeignKey('Situacao', on_delete=models.CASCADE, null=True)
    tipo_aso = models.ForeignKey('TipoDocumento', on_delete=models.CASCADE, null=True)
    aso_admissional_existente = models.BooleanField(default=False)
    aso_demissional_existente = models.BooleanField(default=False)
    aso_periodico_existente = models.BooleanField(default=False)

    def __str__(self):
        return f"Pendente ASO - {self.tipo_aso.nome if self.tipo_aso else 'Desconhecido'} - {self.nome.nome if self.nome else 'Desconhecido'}"

class DomingosFeriados(models.Model):
    loja = models.CharField(max_length=255)
    empresa = models.ForeignKey('Empresa', on_delete=models.CASCADE, null=True)
    regional = models.ForeignKey('Regional', on_delete=models.CASCADE, null=True)
    data_documento = models.CharField(max_length=255, null=True, blank=True)
    nome_documento = models.CharField(max_length=255)
    link_documento = models.CharField(max_length=255)
    data_upload = models.DateField()


    class Meta:
        db_table = 'domingosferiados'


    def __str__(self):
        return self.nome_arquivo

class CartaoPontoInexistente(models.Model):
    """
    Modelo para armazenar informações sobre os cartões de ponto inexistentes.
    """

    empresa = models.ForeignKey('Empresa', on_delete=models.CASCADE, null=True)
    regional = models.ForeignKey('Regional', on_delete=models.CASCADE, null=True)
    unidade = models.ForeignKey('Unidade', on_delete=models.CASCADE, null=True)
    colaborador = models.ForeignKey('Colaborador', on_delete=models.CASCADE, null=True)  # Renomeado de "nome" para "colaborador"
    data = models.DateField(null=True, blank=True)
    existente = models.BooleanField(default=False)
    status = models.ForeignKey('Situacao', on_delete=models.CASCADE, null=True)


    def __str__(self):
        return f"Cartão de Ponto Inexistente - {self.data.strftime('%Y-%m-%d') if self.data else 'Data Não Definida'} - {self.colaborador.nome if self.colaborador else 'Colaborador Não Definido'}"

class DocumentoVencido(models.Model):
    empresa = models.ForeignKey('Empresa', on_delete=models.CASCADE, null=True)
    regional = models.ForeignKey('Regional', on_delete=models.CASCADE, null=True)
    unidade = models.ForeignKey('Unidade', on_delete=models.CASCADE, null=True)
    colaborador = models.ForeignKey('Colaborador', on_delete=models.CASCADE, null=True)
    matricula = models.CharField(max_length=255)
    cpf = models.CharField(max_length=255)
    cargo = models.ForeignKey('Cargo', on_delete=models.CASCADE, null=True)
    dta_documento = models.DateField(null=True)
    tipo_documento = models.ForeignKey('TipoDocumento', on_delete=models.CASCADE, null=True)
    precisa_renovar = models.BooleanField(default=False)
    data_vencimento = models.DateField(null=True, blank=True)  # Campo para armazenar a data de vencimento

    def save(self, *args, **kwargs):
        try:
            if self.dta_documento and self.tipo_documento and self.tipo_documento.validade:
                # Tentativa de converter validade para inteiro
                validade_meses = int(self.tipo_documento.validade)
                self.data_vencimento = self.dta_documento + relativedelta(months=validade_meses)
        except ValueError:
            # Trata o caso onde a conversão falha
            print("Erro ao converter a validade para inteiro.")
            # Você pode escolher logar o erro, enviar para um sistema de monitoramento, ou mesmo definir um valor padrão
            self.data_vencimento = None  # Define um valor padrão ou mantém o anterior
        except Exception as e:
            # Trata qualquer outro tipo de erro que possa ocorrer
            print(f"Erro desconhecido ao salvar DocumentoVencido: {str(e)}")
            self.data_vencimento = None  # Segurança para garantir que não fiquemos com um estado inconsistente

        super(DocumentoVencido, self).save(*args, **kwargs)

    @classmethod
    def criar_a_partir_de_hyperlinkpdf(cls, hyperlinkpdf):
        tipo_doc_id = str(hyperlinkpdf.documento.codigo_documento)
        precisa_renovar = tipo_doc_id in ['403', '501', '502']
        return cls(
            empresa=hyperlinkpdf.empresa,
            regional=hyperlinkpdf.regional,
            unidade=hyperlinkpdf.unidade,
            colaborador=hyperlinkpdf.colaborador,
            matricula=hyperlinkpdf.matricula,
            cpf=hyperlinkpdf.cpf,
            cargo=hyperlinkpdf.cargo,
            dta_documento=hyperlinkpdf.dta_documento,
            tipo_documento=hyperlinkpdf.documento,
            precisa_renovar=precisa_renovar
        )

    class Meta:
        db_table = 'documentos_vencidos'

    def __str__(self):
        return f"{self.colaborador.nome if self.colaborador else 'Desconhecido'} - {self.tipo_documento.nome if self.tipo_documento else 'Documento Desconhecido'}"


class RelatorioGerencial(models.Model):
    """
    Modelo para armazenar informações sobre os relatórios gerenciais.

    Atributos:
        id (AutoField): Chave primária do modelo.
        titulo (CharField): Título do relatório.
        descricao (TextField): Descrição do relatório.
        data_criacao (DateField): Data de criação do relatório.
        data_atualizacao (DateField): Data de atualização do relatório.
        arquivo (FileField): Arquivo do relatório.
    """

    id = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=255)
    descricao = models.TextField()
    data_criacao = models.DateField()
    data_atualizacao = models.DateField()
    arquivo = models.FileField()

    def str(self):
        return f"Relatório Gerencial - {self.titulo}"

# ***************** PREMISSÕES DE USUÁRIOS ********************


User = get_user_model()

class AcessoEmpresa(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    pode_acessar = models.BooleanField(default=True)

    class Meta:
        unique_together = ('usuario', 'empresa')

class AcessoUnidade(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    unidade = models.ForeignKey(Unidade, on_delete=models.CASCADE)
    pode_acessar = models.BooleanField(default=True)

    class Meta:
        unique_together = ('usuario', 'unidade')
