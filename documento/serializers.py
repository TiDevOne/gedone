# serializers.py
from rest_framework import serializers
from .models import Colaborador, DocumentoPendente, Hyperlinkpdf, PendenteASO, CartaoPontoInexistente, DomingosFeriados, DocumentoVencido

class ColaboradorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Colaborador
        fields = '__all__'


class DocumentoPendenteSerializer(serializers.ModelSerializer):
    nome = serializers.CharField(source='nome.nome')
    empresa = serializers.CharField(source='empresa.nome')
    regional = serializers.CharField(source='regional.nome')
    unidade = serializers.CharField(source='unidade.nome')
    cargo = serializers.CharField(source='cargo.nome')
    tipo_documento = serializers.CharField(source='tipo_documento.nome')

    class Meta:
        model = DocumentoPendente
        fields = ['id', 'nome', 'matricula', 'cpf', 'empresa', 'regional', 'unidade', 'cargo', 'admissao', 'desligamento', 'situacao', 'tipo_documento', 'obrigatorio']

class HyperlinkpdfSerializer(serializers.ModelSerializer):
    nome = serializers.CharField(source='colaborador.nome')
    empresa = serializers.CharField(source='empresa.nome')
    regional = serializers.CharField(source='regional.nome')
    unidade = serializers.CharField(source='unidade.nome')
    cargo = serializers.CharField(source='cargo.nome')
    admissao = serializers.DateField(source='colaborador.admissao', format='%d/%m/%Y', allow_null=True)
    desligamento = serializers.DateField(source='colaborador.desligamento', format='%d/%m/%Y', allow_null=True)
    situacao = serializers.CharField(source='colaborador.status.nome')
    documento = serializers.SerializerMethodField()
    obrigatorio = serializers.SerializerMethodField()

    class Meta:
        model = Hyperlinkpdf
        fields = ['nome', 'matricula', 'cpf', 'empresa', 'regional', 'unidade', 'cargo', 'admissao', 'desligamento', 'situacao', 'documento', 'obrigatorio']

    def get_documento(self, obj):
        return obj.documento.nome if obj.documento else ''

    def get_obrigatorio(self, obj):
        return obj.documento.obrigatorio if obj.documento else False


class PendenteASOSerializer(serializers.ModelSerializer):
    nome = serializers.CharField(source='nome.nome', default='N/A')
    empresa = serializers.CharField(source='empresa.nome', default='N/A')
    regional = serializers.CharField(source='regional.nome', default='N/A')
    unidade = serializers.CharField(source='unidade.nome', default='N/A')
    cargo = serializers.CharField(source='cargo.nome', default='N/A')
    status = serializers.CharField(source='status.nome', default='N/A')
    tipo_documento = serializers.CharField(source='tipo_aso.nome', default='N/A')
    admissao = serializers.DateField(format='%d/%m/%Y', default='N/A')
    desligamento = serializers.DateField(format='%d/%m/%Y', default='N/A')
    aso_existente = serializers.SerializerMethodField()

    def get_aso_existente(self, obj):
        return 'Sim' if obj.aso_admissional_existente else 'Não'

    class Meta:
        model = PendenteASO
        fields = [
            'id', 'nome', 'matricula', 'cpf', 'empresa', 'regional', 'unidade',
            'cargo', 'admissao', 'desligamento', 'status', 'tipo_documento', 'aso_existente'
        ]

class CartaoPontoInexistenteSerializer(serializers.ModelSerializer):
    empresa = serializers.CharField(source='empresa.nome', default='N/A')
    regional = serializers.CharField(source='regional.nome', default='N/A')
    unidade = serializers.CharField(source='unidade.nome', default='N/A')
    colaborador = serializers.CharField(source='colaborador.nome', default='N/A')
    matricula = serializers.CharField(source='colaborador.matricula', default='N/A')
    cpf = serializers.CharField(source='colaborador.cpf', default='N/A')
    admissao = serializers.DateField(format='%d/%m/%Y', default='N/A')
    desligamento = serializers.DateField(format='%d/%m/%Y', default='N/A')
    data = serializers.DateField(format='%d/%m/%Y', default='N/A')
    existente = serializers.SerializerMethodField()
    status = serializers.CharField(source='status.nome', default='N/A')

    def get_existente(self, obj):
        return 'Sim' if obj.existente else 'Não'

    class Meta:
        model = CartaoPontoInexistente
        fields = [
            'id', 'empresa', 'regional', 'unidade', 'colaborador', 'matricula', 'cpf',
            'admissao', 'desligamento', 'data', 'existente', 'status'
        ]

# documento/serializers.py
class UnidadePendenciasSerializer(serializers.Serializer):
    unidade__nome = serializers.CharField()
    total_pendencias = serializers.IntegerField()

class EmpresaPendenciasSerializer(serializers.Serializer):
    empresa__nome = serializers.CharField()
    total_pendencias = serializers.IntegerField()

class DomingosFeriadosSerializer(serializers.ModelSerializer):
    empresa = serializers.CharField(source='empresa.nome', allow_null=True)
    regional = serializers.CharField(source='regional.nome', allow_null=True)

    class Meta:
        model = DomingosFeriados
        fields = ['id', 'empresa', 'regional', 'loja', 'data_documento', 'nome_documento', 'link_documento', 'data_upload']

class DocumentoVencidoSerializer(serializers.ModelSerializer):
    empresa = serializers.SerializerMethodField()
    regional = serializers.SerializerMethodField()
    unidade = serializers.SerializerMethodField()
    colaborador = serializers.SerializerMethodField()
    cargo = serializers.SerializerMethodField()
    tipo_documento = serializers.SerializerMethodField()
    situacao = serializers.SerializerMethodField()
    admissao = serializers.SerializerMethodField()
    desligamento = serializers.SerializerMethodField()
    obrigatorio = serializers.SerializerMethodField()
    dta_documento = serializers.SerializerMethodField()
    data_vencimento = serializers.SerializerMethodField()

    class Meta:
        model = DocumentoVencido
        exclude = ['id']

    def get_empresa(self, obj):
        return obj.empresa.nome if obj.empresa else ''

    def get_regional(self, obj):
        return obj.regional.nome if obj.regional else ''

    def get_unidade(self, obj):
        return obj.unidade.nome if obj.unidade else ''

    def get_colaborador(self, obj):
        return obj.colaborador.nome if obj.colaborador else ''

    def get_cargo(self, obj):
        return obj.cargo.nome if obj.cargo else ''

    def get_tipo_documento(self, obj):
        return obj.tipo_documento.nome if obj.tipo_documento else ''

    def get_situacao(self, obj):
        return obj.situacao.descricao if hasattr(obj, 'situacao') and obj.situacao else 'Não Definido'

    def get_admissao(self, obj):
        return obj.colaborador.admissao.strftime('%d/%m/%Y') if obj.colaborador.admissao else 'Não Definido'

    def get_desligamento(self, obj):
        return obj.colaborador.desligamento.strftime('%d/%m/%Y') if obj.colaborador.desligamento else 'Não Definido'

    def get_obrigatorio(self, obj):
        return 'Sim' if obj.tipo_documento.obrigatorio else 'Não'

    def get_dta_documento(self, obj):
        return obj.dta_documento.strftime('%d/%m/%Y') if obj.dta_documento else 'Não Definido'

    def get_data_vencimento(self, obj):
        return obj.data_vencimento.strftime('%d/%m/%Y') if obj.data_vencimento else 'Não Definido'

