import pandas as pd
from django.db.models import Q, Prefetch
from django.utils.decorators import method_decorator
from jsonschema import ValidationError
from loguru import logger
from openpyxl.utils import datetime
from django.db import IntegrityError
from .forms import ImportarUsuariosForm, PesquisaFuncionarioForm
import secrets
from .models import (Area, CartaoPontoInexistente, Regional, Unidade,
                     Cargo, TipoDocumentoCargo, Empresa)
from .models import DocumentoVencido, ColaboradorTipoDocumento, RelatorioGerencial
from django.views.generic import DetailView
from django.views.generic import ListView
from .models import PendenteASO
from .models import ImportUsuarioXLSX  # Importe o modelo ImportUsuarioXLSX
from .forms import PasswordResetForm
from .forms import ImportarDadosForm
from .queries import (importar_dados, ServicoPendenteASO, ObterDocumentosPendentes, CarregarASOAtivo, CarregarASOInativo, \
    calcular_porcentagens_documentos_obrigatorios_ativos, calcular_porcentagens_documentos_obrigatorios_inativos, \
    ServicoPonto, calcular_porcentagens_ponto_ativos, calcular_porcentagens_ponto_inativos,
    calcular_porcentagens_obrigatorios_unidade_ativos, DocumentoVencidoService, calcular_porcentagens_obrigatorios_unidade_inativos,
                      DocumentoPendenciaQuery)
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest
from django.urls import reverse
import json
import requests
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from .models import GrupoDocumento
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.views import PasswordResetDoneView
from .models import DocumentoPendente
from .forms import RelatoriosPendentesForm
from .models import Situacao
from django.views import View
from django.db.models import Count
from .models import Hyperlinkpdf, Colaborador, TipoDocumento
from django.views.decorators.http import require_GET
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from .models import Usuario
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import Group, Permission
from .models import DomingosFeriados
import logging
from django.http import JsonResponse
from django.forms.models import model_to_dict
from django.utils import timezone
from datetime import date, datetime
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from json import loads
from django.utils.dateparse import parse_date


#  ********* VIEWS para MENUS SUPERIORES  ************
# VIEW que INICIA o PROJETO

def index(request):
    """
    View para renderizar a página inicial.

    Args:
        request. Objeto HttpRequest contendo os dados da requisição.

    Returns:
        HttpResponse: Resposta HTTP renderizando a página 'documento/.html'.
    """
    return render(request, 'documento/import_xlsx.html')

@login_required
def dossie(request):
    return render(request, 'documento/dossie.html')

@login_required
def relatorios(request):
    return render(request, 'documento/relatorios.html')

@login_required
def configuracao(request):
    return render(request, 'documento/configuracao.html')




# @login_required
# def tela_login(request):
    # return render(request, 'documento/tela_login.html')

#  ************  Views Para Telas Referente a aba DOSSIE ***********

class PesquisaDossieView(DetailView):
    model = Colaborador
    template_name = 'documento/dossie.html'
    context_object_name = 'colaborador'
    pk_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['empresa'] = Empresa.objects.all()
        return context

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = PesquisaFuncionarioForm(instance=self.object)

        return self.render_to_response(self.get_context_data(form=form))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = PesquisaFuncionarioForm(request.POST, instance=self.object)
        if form.is_valid():
            query = {}
            for field in form.fields:
                value = form.cleaned_data[field]
                if value:
                    query[field] = value

            # Adicionando filtro de região
            if 'empresa' in query:
                empresa_id = query.pop('empresa')
                query['regional__empresa_id'] = empresa_id

            resultados = Colaborador.objects.filter(**query)
            serialized_resultados = [{'nome': resultado.nome, 'cpf': resultado.cpf} for resultado in resultados]
            return JsonResponse(serialized_resultados, safe=False)
        return self.render_to_response(self.get_context_data(form=form))


class CarregarEmpresaView(View):
    def get(self, request, *args, **kwargs):
        empresas = Empresa.objects.all()
        serialized_empresas = [{'id': empresa.id, 'nome': empresa.nome} for empresa in empresas]
        return JsonResponse(serialized_empresas, safe=False)


class CarregarRegionalView(View):
    def get(self, request, *args, **kwargs):
        regionais = Regional.objects.all()  # Corrigido para 'regionais' ao invés de 'regional'
        serialized_regionais = [{'id': regional.id, 'nome': regional.nome} for regional in regionais]
        return JsonResponse(serialized_regionais, safe=False)  # Corrigido para 'serialized_regionais'


class CarregarUnidadesView(View):
    def get(self, request, *args, **kwargs):
        unidades = Unidade.objects.all()
        # print(f"as unidades: {unidades}")
        serialized_unidades = [{'id': unidade.id, 'nome': unidade.nome} for unidade in
                               unidades]  # Corrigido para 'unidade'
        return JsonResponse(serialized_unidades, safe=False)


class CarregarDadosView(View):
    def get(self, request, *args, **kwargs):
        colaboradores = Colaborador.objects.select_related(
            'empresa', 'regional', 'unidade'
        ).all()

        serialized_colaboradores2 = []
        for colaborador in colaboradores:
            serialized_colaborador = {
                'id': colaborador.id,
                'nome': colaborador.nome,
                'empresa': colaborador.empresa.nome,
                'regional': colaborador.regional.nome,
                'unidade': colaborador.unidade.nome
            }
            serialized_colaboradores2.append(serialized_colaborador)

        return JsonResponse(serialized_colaboradores2, safe=False)



class CarregarColaboradorSimplesView(View):
    def get(self, request, *args, **kwargs):
        colaboradores = Colaborador.objects.select_related('empresa', 'regional', 'unidade', 'cargo', 'status').all().values(
            'empresa__nome', 'regional__nome', 'unidade__nome', 'cargo__nome', 'status__nome')

        serialized_colaboradores = [
            {
                'empresa': colaborador['empresa__nome'],
                'regional': colaborador['regional__nome'],
                'unidade': colaborador['unidade__nome'],
                'cargo': colaborador['cargo__nome'],
                'situacao': colaborador['status__nome']
            }
            for colaborador in colaboradores
        ]

        return JsonResponse(serialized_colaboradores, safe=False)


class CarregarColaboradorView(View):
    def get(self, request, *args, **kwargs):
        colaboradores = Colaborador.objects.select_related('empresa', 'regional', 'unidade', 'cargo', 'status').all().values(
            'id', 'nome', 'matricula', 'cpf', 'admissao', 'desligamento',
            'empresa__nome', 'regional__nome', 'unidade__nome', 'cargo__nome', 'status__nome')

        # Coletando os nomes das empresas
        empresas_nomes = set(colaborador['empresa__nome'] for colaborador in colaboradores)
        print(f"Empresas envolvidas: {', '.join(empresas_nomes)}")

        serialized_colaboradores = [
            {
                'id': colaborador['id'],
                'nome': colaborador['nome'],
                'matricula': colaborador['matricula'],
                'cpf': colaborador['cpf'],
                'admissao': colaborador['admissao'].strftime('%d/%m/%Y') if colaborador['admissao'] else '',
                'desligamento': colaborador['desligamento'].strftime('%d/%m/%Y') if colaborador['desligamento'] else '',
                'cargo': colaborador['cargo__nome'],
                'situacao': colaborador['status__nome'],
                'empresa': colaborador['empresa__nome'],
                'regional': colaborador['regional__nome'],
                'unidade': colaborador['unidade__nome']
            }
            for colaborador in colaboradores
        ]

        return JsonResponse(serialized_colaboradores, safe=False)


@method_decorator(csrf_protect, name='dispatch')
class CarregarCargoView(View):
    def get(self, request, *args, **kwargs):
        # logger.info("Recebido GET para carregar cargos")
        cargos = Cargo.objects.all()
        serialized_cargos = [{'id': cargo.id, 'nome': cargo.nome} for cargo in cargos]
        # logger.info(f"Dados serializados: {serialized_cargos}")
        return JsonResponse(serialized_cargos, safe=False)

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        nome = data.get('nome')
        if not nome:
            return HttpResponseBadRequest("Nome é obrigatório")
        cargo = Cargo.objects.create(nome=nome)
        # logger.info(f"Cargo criado: {cargo}")
        return JsonResponse({'id': cargo.id, 'nome': cargo.nome}, status=201)

    def put(self, request, *args, **kwargs):
        data = json.loads(request.body)
        cargo_id = data.get('id')
        nome = data.get('nome')
        if not cargo_id or not nome:
            return HttpResponseBadRequest("ID e Nome são obrigatórios")
        try:
            cargo = Cargo.objects.get(id=cargo_id)
            cargo.nome = nome
            cargo.save()
            # logger.info(f"Cargo editado: {cargo}")
            return JsonResponse({'id': cargo.id, 'nome': cargo.nome})
        except Cargo.DoesNotExist:
            # logger.error("Cargo não encontrado")
            return HttpResponseBadRequest("Cargo não encontrado")

    def delete(self, request, *args, **kwargs):
        data = json.loads(request.body)
        cargo_id = data.get('id')
        if not cargo_id:
            return HttpResponseBadRequest("ID é obrigatório")
        try:
            cargo = Cargo.objects.get(id=cargo_id)
            cargo.delete()
            # logger.info(f"Cargo removido: {cargo_id}")
            return JsonResponse({'id': cargo_id})
        except Cargo.DoesNotExist:
            # logger.error("Cargo não encontrado")
            return HttpResponseBadRequest("Cargo não encontrado")

class CarregarSituacoesView(View):
    def get(self, request, *args, **kwargs):
        situacoes = Situacao.objects.all()
        serialized_situacoes = [{'id': situacao.id, 'nome': situacao.nome} for situacao in situacoes]

        return JsonResponse(serialized_situacoes, safe=False)


class ListarResultadoDossieView(View):
    """
    Exibe uma lista com todos os resultados dos dossiês dos colaboradores.
    """

    def get(self, request, *args, **kwargs):
        colaboradores = Colaborador.objects.select_related('status', 'empresa', 'regional', 'unidade', 'cargo').all()
        situacoes = Situacao.objects.all()

        serialized_colaboradores = []
        for colaborador in colaboradores:
            serialized_colaborador = {
                'nome': colaborador.nome,
                'cpf': colaborador.cpf,
                'matricula': colaborador.matricula,
                'situacao': colaborador.status.nome,
                'cargo': colaborador.cargo.nome if colaborador.cargo else '',  # Adicionando o campo cargo
                'admissao': colaborador.admissao.strftime('%d/%m/%Y') if colaborador.admissao else '',
                'desligamento': colaborador.desligamento.strftime('%d/%m/%Y') if colaborador.desligamento else '',
                'empresa': colaborador.empresa.nome if colaborador.empresa else '',
                'regional': colaborador.regional.nome if colaborador.regional else '',
                'unidade': colaborador.unidade.nome if colaborador.unidade else '',
            }
            serialized_colaboradores.append(serialized_colaborador)

        serialized_situacoes = [{'id': situacao.id, 'nome': situacao.nome} for situacao in situacoes]

        data = {
            'situacoes': serialized_situacoes,
            'colaboradores': serialized_colaboradores
        }

        return JsonResponse(data, safe=False)

    def post(self, request, *args, **kwargs):
        form = PesquisaFuncionarioForm(request.POST)
        if form.is_valid():
            query = {field: value for field, value in form.cleaned_data.items() if value}

            colaboradores = Colaborador.objects.select_related('status', 'empresa', 'regional', 'unidade',
                                                               'cargo').filter(**query)
            situacoes = Situacao.objects.filter(**query)

            serialized_colaboradores = []
            for colaborador in colaboradores:
                serialized_colaborador = {
                    'nome': colaborador.nome,
                    'cpf': colaborador.cpf,
                    'matricula': colaborador.matricula,
                    'situacao': colaborador.status.nome,
                    'cargo': colaborador.cargo.nome if colaborador.cargo else '',  # Adicionando o campo cargo
                    'admissao': colaborador.admissao.strftime('%d/%m/%Y') if colaborador.admissao else '',
                    'desligamento': colaborador.desligamento.strftime('%d/%m/%Y') if colaborador.desligamento else '',
                    'empresa': colaborador.empresa.nome if colaborador.empresa else '',
                    'regional': colaborador.regional.nome if colaborador.regional else '',
                    'unidade': colaborador.unidade.nome if colaborador.unidade else '',
                }
                serialized_colaboradores.append(serialized_colaborador)

            serialized_situacoes = [{'id': situacao.id, 'nome': situacao.nome} for situacao in situacoes]

            return JsonResponse({'resultados': serialized_colaboradores, 'situacoes': serialized_situacoes}, status=200)
        else:
            return JsonResponse({'error': form.errors}, status=400)

def dados_pessoais(request):
    # Lógica da view, se necessário
    return render(request, 'documento/dados_pessoais.html')


def visualizar_documentos(request):
    # Obter todos os documentos da tabela Hyperlinkpdf
    documentos = Hyperlinkpdf.objects.all()

    # Preparar contexto para o template
    contexto = {
        'documentos': documentos,
        'campos': [field.name for field in Hyperlinkpdf._meta.get_fields()],  # Obter todos os nomes dos campos do modelo
    }

    # Renderizar o template HTML
    return render(request, 'documento/dados_pessoais.html', contexto)


def get_hyperlinkpdf_data(request):
    hyperlinkpdf_data = []
    hyperlinkpdf_objects = Hyperlinkpdf.objects.all()

    for hyperlinkpdf_obj in hyperlinkpdf_objects:
        data = {
            'id': hyperlinkpdf_obj.id,
            'data_upload': hyperlinkpdf_obj.data_upload,
            'caminho': hyperlinkpdf_obj.caminho,
            'documento': hyperlinkpdf_obj.documento.nome,  # Supondo que 'nome' seja um campo relevante do modelo TipoDocumento
            'matricula': hyperlinkpdf_obj.matricula,
            'cpf': hyperlinkpdf_obj.cpf,
            'nome_arquivo': hyperlinkpdf_obj.nome_arquivo,
            'dta_documento': hyperlinkpdf_obj.dta_documento,
            'codigo_documento': hyperlinkpdf_obj.codigo_documento,
        }
        hyperlinkpdf_data.append(data)

    return JsonResponse({'hyperlinkpdf_data': hyperlinkpdf_data})



def get_documentos_info(request):
    # Recuperando todos os tipos de documentos e ordenando pelo campo 'codigo'
    tipos_documentos = TipoDocumento.objects.all().select_related('grupo_documento', 'hiperlink_documento').order_by('codigo')

    # Prefetch relacionado aos documentos para otimizar consultas
    documentos_prefetch = Prefetch('hyperlinkpdf_set', queryset=Hyperlinkpdf.objects.select_related('colaborador', 'documento'))

    tipos_documentos = tipos_documentos.prefetch_related(documentos_prefetch)

    data = []

    for tipo in tipos_documentos:
        documentos = tipo.hyperlinkpdf_set.all()

        # Verificar se o Kit Admissional está presente para o colaborador
        kit_admissional_presente = Hyperlinkpdf.objects.filter(
            colaborador__in=documentos.values_list('colaborador', flat=True),
            documento__codigo='146'
        ).exists()

        documentos_data = [{
            'documento_nome': doc.documento.nome if doc.documento else 'Documento não especificado',
            'colaborador_nome': doc.colaborador.nome if doc.colaborador else 'N/A',
            'colaborador_id': doc.colaborador.id if doc.colaborador else 'N/A',
            'caminho': doc.caminho,
            'cpf': doc.cpf,
            'matricula': doc.matricula,
            # Aplica a regra do Kit Admissional
            'obrigatorio': False if kit_admissional_presente else tipo.obrigatorio
        } for doc in documentos]

        data.append({
            'tipo_documento_id': tipo.id,
            'codigo': tipo.codigo,
            'nome': tipo.nome,
            'grupo_documento': tipo.grupo_documento.nome if tipo.grupo_documento else 'N/A',
            'pcd': tipo.pcd,
            'obrigatorio': tipo.obrigatorio,
            'valor_legal': tipo.valor_legal,
            'verifica_assinatura': tipo.verifica_assinatura,
            'auditoria': tipo.auditoria,
            'validade': tipo.validade,
            'tipo_validade': tipo.tipo_validade,
            'exibe_relatorio': tipo.exibe_relatorio,
            'lista_situacao': tipo.lista_situacao,
            'prioridade': tipo.prioridade,
            'hiperlink_documento_id': tipo.hiperlink_documento.id if tipo.hiperlink_documento else 'N/A',
            'documentos': documentos_data
        })

    return JsonResponse(data, safe=False)

# *************  Views Para Telas Referente ao DASHBOARD **************

class TotalColaboradoresView(View):
    def get(self, request):
        # Conta o total de colaboradores ativos
        total_ativos = Colaborador.objects.filter(status__nome='Ativo').count()

        # Conta o total de colaboradores inativos
        total_inativos = Colaborador.objects.filter(status__nome='Inativo').count()

        # Formata os números para incluir o separador de milhares
        formatted_total_ativos = f"{total_ativos:,}".replace(',', '.')
        formatted_total_inativos = f"{total_inativos:,}".replace(',', '.')

        # Prepara os dados para o JSON de resposta
        data = {
            'total_ativos': formatted_total_ativos,
            'total_inativos': formatted_total_inativos
        }

        return JsonResponse(data)


@method_decorator(csrf_exempt, name='dispatch')
class ASOPercentualAtivoView(View):
    def get(self, request, *args, **kwargs):
        percentuais = CarregarASOAtivo.calcular_porcentagens_aso_admissional()
        return JsonResponse(percentuais)


@method_decorator(csrf_exempt, name='dispatch')
class ASOPercentualInativoView(View):
    def get(self, request, *args, **kwargs):
        percentuais = CarregarASOInativo.calcular_porcentagens_aso_demissional()
        return JsonResponse(percentuais)


@method_decorator(csrf_exempt, name='dispatch')
class DocumentosObrigatoriosAtivosView(View):
    def get(self, request, *args, **kwargs):
        percentuais = calcular_porcentagens_documentos_obrigatorios_ativos()
        return JsonResponse(percentuais)

@method_decorator(csrf_exempt, name='dispatch')
class DocumentosObrigatoriosInativosView(View):
    def get(self, request, *args, **kwargs):
        percentuais = calcular_porcentagens_documentos_obrigatorios_inativos()
        return JsonResponse(percentuais)


@method_decorator(csrf_exempt, name='dispatch')
class DocumentosPontoAtivoView(View):
    def get(self, request, *args, **kwargs):
        percentuais = calcular_porcentagens_ponto_ativos()
        print("Dados em DocumentosPontoAtivoView:", percentuais)  # Adicionando o print dos dados
        return JsonResponse(percentuais)


@method_decorator(csrf_exempt, name='dispatch')
class DocumentosPontoInativoView(View):
    def get(self, request, *args, **kwargs):
        percentuais = calcular_porcentagens_ponto_inativos()
        return JsonResponse(percentuais)

@method_decorator(csrf_exempt, name='dispatch')
class ObrigatoriosUnidadesAtivoView(View):
    def get(self, request, *args, **kwargs):
        percentuais = calcular_porcentagens_obrigatorios_unidade_ativos()
        return JsonResponse(percentuais, safe=False)  # Adicione safe=False aqui

@method_decorator(csrf_exempt, name='dispatch')
class ObrigatoriosUnidadesInativoView(View):
    def get(self, request, *args, **kwargs):
        percentuais = calcular_porcentagens_obrigatorios_unidade_inativos()
        return JsonResponse(percentuais, safe=False)  # Adicione safe=False aqui

@method_decorator(require_GET, name='dispatch')
class AtualizarDocumentosPendentesView(View):
    def get(self, request, *args, **kwargs):
        ObterDocumentosPendentes.atualizar_tabela_documentos_pendentes()
        return JsonResponse({'status': 'Atualização concluída com sucesso!'})


"""class ObrigatoriosPorUnidadeAtivo(View):
    def get(self, request):
        documentos_obrigatorios = (
            DocumentoPendente.objects
            .filter(obrigatorio=True, desligamento__isnull=True)  # Filtra apenas colaboradores ativos
            .select_related('unidade', 'tipo_documento', 'nome', 'unidade__regional', 'cargo')
            .values(
                'unidade__nome',
                'unidade__regional__nome',
                'tipo_documento__nome',
                'nome__nome',
                'nome__matricula',
                'nome__cpf',
                'cargo__nome',
                'admissao'
            )
            .annotate(quantidade=Count('id'))
            .order_by('unidade__nome', 'tipo_documento__nome')
        )

        # logger.info("Documentos obrigatórios carregados.")

        obrigatorios_por_unidade = {}
        for documento in documentos_obrigatorios:
            unidade_nome = documento['unidade__nome']
            regional_nome = documento['unidade__regional__nome']
            tipo_documento_nome = documento['tipo_documento__nome']
            # logger.info(f"Processando documento: Unidade={unidade_nome}, Regional={regional_nome}, Tipo de Documento={tipo_documento_nome}")

            if unidade_nome not in obrigatorios_por_unidade:
                obrigatorios_por_unidade[unidade_nome] = {
                    'regional': regional_nome,
                    'documentos': {},
                }
                # logger.info(f"Adicionado nova unidade: {unidade_nome} com regional {regional_nome}")

            if tipo_documento_nome not in obrigatorios_por_unidade[unidade_nome]['documentos']:
                obrigatorios_por_unidade[unidade_nome]['documentos'][tipo_documento_nome] = {
                    'quantidade': 0,
                    'colaboradores': []
                }
                # logger.info(f"Adicionado novo tipo de documento: {tipo_documento_nome} em {unidade_nome}")

            documento_info = obrigatorios_por_unidade[unidade_nome]['documentos'][tipo_documento_nome]
            documento_info['quantidade'] += documento['quantidade']
            documento_info['colaboradores'].append({
                'regional': documento['unidade__regional__nome'],
                'unidade': documento['unidade__nome'],
                'cargo': documento['cargo__nome'],
                'nome': documento['nome__nome'],
                'matricula': documento['nome__matricula'],
                'cpf': documento['nome__cpf'],
                'admissao': documento['admissao']
            })

        # Calcula o total de pendências por unidade
        for unidade_info in obrigatorios_por_unidade.values():
            total_pendentes = sum(doc_info['quantidade'] for doc_info in unidade_info['documentos'].values())
            unidade_info['total_pendentes'] = total_pendentes
            # logger.info(f"Total pendentes em {unidade_info['regional']}: {unidade_info['total_pendentes']}")

        # Prepara a lista de unidades para resposta JSON
        lista_unidades = []
        for unidade, info in obrigatorios_por_unidade.items():
            # logger.info(f"Montando lista para: Unidade={unidade}, Regional={info['regional']}")
            unidade_dict = {
                'regional': info['regional'],
                'unidade': unidade,
                'total_pendentes': info['total_pendentes'],
                'documentos': [
                    {
                        'tipo_documento': doc_tipo,
                        'quantidade': doc_info['quantidade'],
                        'colaboradores': doc_info['colaboradores']
                    }
                    for doc_tipo, doc_info in info['documentos'].items()
                ]
            }
            lista_unidades.append(unidade_dict)

        logger.info(f"Lista final de unidades e pendências: {lista_unidades}")

        return JsonResponse(lista_unidades, safe=False)

"""
class ObrigatoriosPorUnidadeAtivo(View):
    def get(self, request):
        # Filtra os colaboradores ativos
        colaboradores_ativos = Colaborador.objects.filter(status__nome='Ativo')

        # Calcula o número total de colaboradores ativos por unidade
        total_colaboradores_por_unidade = colaboradores_ativos.values('unidade__nome').annotate(total=Count('id'))

        # Cria um dicionário para fácil acesso ao total de colaboradores por unidade
        total_colaboradores_dict = {item['unidade__nome']: item['total'] for item in total_colaboradores_por_unidade}

        # Filtra os documentos pendentes obrigatórios de colaboradores ativos
        documentos_obrigatorios = (
    DocumentoPendente.objects
    .filter(obrigatorio=True, situacao="Ativo")
    .select_related('unidade', 'tipo_documento', 'nome', 'regional', 'cargo')
    .values(
        'unidade__nome',
        'regional__nome',
        'tipo_documento__nome',
        'nome__nome',
        'nome__matricula',
        'nome__cpf',
        'cargo__nome',
        'admissao'
    )
    .annotate(quantidade=Count('nome'))
    .order_by('unidade__nome', 'tipo_documento__nome')
)

        obrigatorios_por_unidade = {}
        total_documentos = 0

        for documento in documentos_obrigatorios:
            unidade_nome = documento['unidade__nome']
            regional_nome = documento['regional__nome']
            tipo_documento_nome = documento['tipo_documento__nome']
            quantidade = documento['quantidade']
            total_documentos += quantidade

            if unidade_nome not in obrigatorios_por_unidade:
                obrigatorios_por_unidade[unidade_nome] = {
                    'regional': regional_nome,
                    'documentos': {},
                    'total_pendentes': 0,
                    'quantidade': 0  # Total de pendências por unidade
                }

            if tipo_documento_nome not in obrigatorios_por_unidade[unidade_nome]['documentos']:
                obrigatorios_por_unidade[unidade_nome]['documentos'][tipo_documento_nome] = {
                    'quantidade': 0,
                    'colaboradores': []
                }

            documento_info = obrigatorios_por_unidade[unidade_nome]['documentos'][tipo_documento_nome]
            documento_info['quantidade'] += quantidade
            documento_info['colaboradores'].append({
                'regional': documento['regional__nome'],
                'unidade': documento['unidade__nome'],
                'cargo': documento['cargo__nome'],
                'nome': documento['nome__nome'],
                'matricula': documento['nome__matricula'],
                'cpf': documento['nome__cpf'],
                'admissao': documento['admissao']
            })
            obrigatorios_por_unidade[unidade_nome]['quantidade'] += quantidade

        # Calcula o total de pendências por unidade e a porcentagem
        for unidade, unidade_info in obrigatorios_por_unidade.items():
            total_pendentes = sum(doc_info['quantidade'] for doc_info in unidade_info['documentos'].values())
            unidade_info['total_pendentes'] = total_pendentes

            total_colaboradores = total_colaboradores_dict.get(unidade, 0)
            if total_colaboradores > 0:
                percentual_pendencias = (total_pendentes / (total_colaboradores * len(unidade_info['documentos']))) * 100
                unidade_info['percentual_pendencias'] = min(percentual_pendencias, 100)
            else:
                unidade_info['percentual_pendencias'] = 0

            # Adicionando print para exibir a porcentagem de pendências por unidade
            print(f"Unidade: {unidade}, Percentual de Pendências: {unidade_info['percentual_pendencias']:.1f}%")

        # Prepara a lista de unidades para resposta JSON
        lista_unidades = []
        for unidade, info in obrigatorios_por_unidade.items():
            unidade_dict = {
                'regional': info['regional'],
                'unidade': unidade,
                'total_pendentes': info['total_pendentes'],
                'percentual_pendencias': f"{info['percentual_pendencias']:.1f}%",
                'documentos': [
                    {
                        'tipo_documento': doc_tipo,
                        'quantidade': doc_info['quantidade'],
                        'colaboradores': doc_info['colaboradores']
                    }
                    for doc_tipo, doc_info in info['documentos'].items()
                ]
            }
            lista_unidades.append(unidade_dict)

        return JsonResponse(lista_unidades, safe=False)




class ObrigatoriosPorUnidadeInativo(View):
    def get(self, request):
        colaboradores_inativos = Colaborador.objects.filter(status__nome='Inativo')
        total_colaboradores_por_unidade = colaboradores_inativos.values('unidade__nome').annotate(total=Count('id'))
        total_colaboradores_dict = {item['unidade__nome']: item['total'] for item in total_colaboradores_por_unidade}

        documentos_obrigatorios = (
            DocumentoPendente.objects
            .filter(obrigatorio=True, situacao="Inativo")
            .select_related('unidade', 'tipo_documento', 'nome', 'regional', 'cargo')
            .values(
                'unidade__nome',
                'regional__nome',
                'tipo_documento__nome',
                'nome__nome',
                'nome__matricula',
                'nome__cpf',
                'cargo__nome',
                'admissao'
            )
            .annotate(quantidade=Count('id'))
            .order_by('unidade__nome', 'tipo_documento__nome')
        )

        obrigatorios_por_unidade = {}
        total_documentos = 0

        for documento in documentos_obrigatorios:
            unidade_nome = documento['unidade__nome']
            regional_nome = documento['regional__nome']
            tipo_documento_nome = documento['tipo_documento__nome']
            quantidade = documento['quantidade']
            total_documentos += quantidade

            if unidade_nome not in obrigatorios_por_unidade:
                obrigatorios_por_unidade[unidade_nome] = {
                    'regional': regional_nome,
                    'documentos': {},
                    'total_pendentes': 0,
                    'quantidade': 0
                }

            if tipo_documento_nome not in obrigatorios_por_unidade[unidade_nome]['documentos']:
                obrigatorios_por_unidade[unidade_nome]['documentos'][tipo_documento_nome] = {
                    'quantidade': 0,
                    'colaboradores': []
                }

            documento_info = obrigatorios_por_unidade[unidade_nome]['documentos'][tipo_documento_nome]
            documento_info['quantidade'] += quantidade
            documento_info['colaboradores'].append({
                'regional': documento['regional__nome'],
                'unidade': documento['unidade__nome'],
                'cargo': documento['cargo__nome'],
                'nome': documento['nome__nome'],
                'matricula': documento['nome__matricula'],
                'cpf': documento['nome__cpf'],
                'admissao': documento['admissao']
            })
            obrigatorios_por_unidade[unidade_nome]['quantidade'] += quantidade

        for unidade, unidade_info in obrigatorios_por_unidade.items():
            total_pendentes = sum(doc_info['quantidade'] for doc_info in unidade_info['documentos'].values())
            unidade_info['total_pendentes'] = total_pendentes

            total_colaboradores = total_colaboradores_dict.get(unidade, 0)
            if total_colaboradores > 0:
                percentual_pendencias = (total_pendentes / (total_colaboradores * len(unidade_info['documentos']))) * 100
                unidade_info['percentual_pendencias'] = min(percentual_pendencias, 100)
            else:
                unidade_info['percentual_pendencias'] = 0

            print(f"Unidade INATIVO: {unidade}, Percentual de Pendências: {unidade_info['percentual_pendencias']:.1f}%")

        lista_unidades = []
        for unidade, info in obrigatorios_por_unidade.items():
            unidade_dict = {
                'regional': info['regional'],
                'unidade': unidade,
                'total_pendentes': info['total_pendentes'],
                'percentual_pendencias': f"{info['percentual_pendencias']:.1f}%",
                'documentos': [
                    {
                        'tipo_documento': doc_tipo,
                        'quantidade': doc_info['quantidade'],
                        'colaboradores': doc_info['colaboradores']
                    }
                    for doc_tipo, doc_info in info['documentos'].items()
                ]
            }
            lista_unidades.append(unidade_dict)

        return JsonResponse(lista_unidades, safe=False)


class DocumentosExistentesView(ListView):
    model = Hyperlinkpdf
    paginate_by = 100  # Ajuste conforme necessário para o volume de dados
    template_name = 'documento/relatorios.html'  # Insira o caminho para o seu template

    def get_queryset(self):
        queryset = super().get_queryset()

        empresa = self.request.GET.get('empresa')
        regional = self.request.GET.get('regional')
        unidade = self.request.GET.get('unidade')
        nome = self.request.GET.get('nome')
        matricula = self.request.GET.get('matricula')
        cpf = self.request.GET.get('cpf')
        cargo = self.request.GET.get('cargo')
        admissao = self.request.GET.get('admissao')
        desligamento = self.request.GET.get('admissao')

        # Filtrar por campos de texto
        if empresa:
            queryset = queryset.filter(empresa__nome__icontains=empresa)
        if regional:
            queryset = queryset.filter(regional__nome__icontains=regional)
        if unidade:
            queryset = queryset.filter(unidade__nome__icontains=unidade)
        if nome:
            queryset = queryset.filter(colaborador__nome__icontains=nome)
        if matricula:
            queryset = queryset.filter(matricula__icontains=matricula)
        if cpf:
            queryset = queryset.filter(cpf__icontains=cpf)
        if cargo:
            queryset = queryset.filter(cargo__nome__icontains=cargo)

        # Filtrar por datas de admissão
        if admissao:
            try:
                admissao_inicio_date = datetime.datetime.strptime(admissao, '%Y-%m-%d').date()
                queryset = queryset.filter(colaborador__admissao__gte=admissao_inicio_date)
            except ValueError:
                raise ValidationError("Formato de data de admissão inicial inválido.")
        if desligamento:
            try:
                desligamento = datetime.datetime.strptime(desligamento, '%Y-%m-%d').date()
                queryset = queryset.filter(colaborador__admissao__lte=desligamento)
            except ValueError:
                raise ValidationError("Formato de data de admissão final inválido.")

        return queryset


@method_decorator(csrf_exempt, name='dispatch')
class CarregarDocumentosVencidosView(View):
    def get(self, request, *args, **kwargs):
        documentos = DocumentoVencidoService.copiar_documentos_relevantes()
        # logger.info('Os documentos: %s', documentos)
        return JsonResponse(documentos, safe=False)



class ListarDocumentosSimplesView(View):
    def get(self, request):
        try:
            # Coletando apenas os documentos cuja data de vencimento já passou
            documentos = DocumentoVencido.objects.filter(
                data_vencimento__lte=timezone.now()  # Filtra para incluir apenas documentos vencidos
            ).select_related(
                'empresa',
                'regional',
                'unidade',
                'cargo',
                'tipo_documento'
            )

            # Convertendo documentos para JSON
            data = []
            for doc in documentos:
                doc_dict = {
                    'empresa': doc.empresa.nome if doc.empresa else '',
                    'regional': doc.regional.nome if doc.regional else '',
                    'unidade': doc.unidade.nome if doc.unidade else '',
                    'cargo': doc.cargo.nome if doc.cargo else '',
                    'tipo_documento': doc.tipo_documento.nome if doc.tipo_documento else ''
                }
                data.append(doc_dict)
                # Logando detalhes do documento
                # logger.info(f'Documento processado: {doc_dict}')

            return JsonResponse(data, safe=False)
        except Exception as e:
           #  logger.error('Erro ao listar documentos vencidos: %s', e)
            return JsonResponse({'error': 'Não foi possível recuperar os documentos vencidos'}, status=500)




class ListarDocumentosVencidosView(View):
    def get(self, request):
        try:
            # Coletando os parâmetros de filtro
            empresa = request.GET.get('empresa', None)
            regional = request.GET.get('regional', None)
            unidade = request.GET.get('unidade', None)
            nome_colaborador = request.GET.get('nomeColaborador', None)
            matricula = request.GET.get('matricula', None)
            cpf = request.GET.get('cpf', None)
            cargo = request.GET.get('cargo', None)
            admissao = request.GET.get('admissao', None)
            desligamento = request.GET.get('desligamento', None)
            tipo_documento = request.GET.get('tipoDocumento', None)

            # Coletando apenas os documentos cuja data de vencimento já passou
            documentos = DocumentoVencido.objects.filter(
                data_vencimento__lte=timezone.now()
            ).select_related(
                'empresa', 'regional', 'unidade', 'colaborador', 'cargo', 'tipo_documento'
            )

            # Aplicando os filtros
            if empresa:
                documentos = documentos.filter(empresa__nome=empresa)
            if regional:
                documentos = documentos.filter(regional__nome=regional)
            if unidade:
                documentos = documentos.filter(unidade__nome=unidade)
            if nome_colaborador:
                documentos = documentos.filter(colaborador__nome__icontains=nome_colaborador)
            if matricula:
                documentos = documentos.filter(colaborador__matricula=matricula)
            if cpf:
                documentos = documentos.filter(colaborador__cpf=cpf)
            if cargo:
                documentos = documentos.filter(cargo__nome=cargo)
            if admissao:
                documentos = documentos.filter(colaborador__admissao=parse_date(admissao))
            if desligamento:
                documentos = documentos.filter(colaborador__desligamento=parse_date(desligamento))
            if tipo_documento:
                documentos = documentos.filter(tipo_documento__nome=tipo_documento)

            # Paginação
            page = request.GET.get('page', 1)
            per_page = request.GET.get('per_page', 10)
            paginator = Paginator(documentos, per_page)

            try:
                documentos_paginados = paginator.page(page)
            except PageNotAnInteger:
                documentos_paginados = paginator.page(1)
            except EmptyPage:
                documentos_paginados = paginator.page(paginator.num_pages)

            # Convertendo documentos para JSON
            data = []
            for doc in documentos_paginados:
                doc_dict = model_to_dict(doc, exclude=['id'])
                doc_dict.update({
                    'empresa': doc.empresa.nome if doc.empresa else '',
                    'regional': doc.regional.nome if doc.regional else '',
                    'unidade': doc.unidade.nome if doc.unidade else '',
                    'colaborador': doc.colaborador.nome if doc.colaborador else '',
                    'cargo': doc.cargo.nome if doc.cargo else '',
                    'tipo_documento': doc.tipo_documento.nome if doc.tipo_documento else '',
                    'situacao': doc.situacao.descricao if hasattr(doc, 'situacao') and doc.situacao else 'Não Definido',
                    'admissao': doc.colaborador.admissao.strftime('%d/%m/%Y') if doc.colaborador.admissao else 'Não Definido',
                    'desligamento': doc.colaborador.desligamento.strftime('%d/%m/%Y') if doc.colaborador.desligamento else 'Não Definido',
                    'obrigatorio': 'Sim' if doc.tipo_documento.obrigatorio else 'Não',
                    'dta_documento': doc.dta_documento.strftime('%d/%m/%Y') if doc.dta_documento else 'Não Definido',
                    'data_vencimento': doc.data_vencimento.strftime('%d/%m/%Y') if doc.data_vencimento else 'Não Definido'
                })
                data.append(doc_dict)

            response = {
                'data': data,
                'page': documentos_paginados.number,
                'num_pages': paginator.num_pages,
                'total_documents': paginator.count
            }

            return JsonResponse(response, safe=False)
        except Exception as e:
            return JsonResponse({'error': 'Não foi possível recuperar os documentos vencidos'}, status=500)


class ListarDocumentosVencerSimplesView(View):
    def get(self, request):
        try:
            documentos = DocumentoVencido.objects.select_related(
                'empresa', 'regional', 'unidade', 'cargo', 'tipo_documento'
            ).filter(data_vencimento__gt=timezone.now())  # Filtra para incluir apenas documentos que ainda não venceram

            data = []
            for doc in documentos:
                doc_dict = {
                    'empresa': doc.empresa.nome if doc.empresa else '',
                    'regional': doc.regional.nome if doc.regional else '',
                    'unidade': doc.unidade.nome if doc.unidade else '',
                    'cargo': doc.cargo.nome if doc.cargo else '',
                    'tipo_documento': doc.tipo_documento.nome if doc.tipo_documento else '',
                }
                data.append(doc_dict)

            return JsonResponse(data, safe=False)
        except Exception as e:
            #logger.error('Erro ao listar documentos a vencer: %s', e)
            return JsonResponse({'error': 'Não foi possível recuperar os documentos a vencer'}, status=500)


class ListarDocumentosaVencerView(View):
    def get(self, request):
        try:
            # Obtém o número da página da query string, padrão para 1 se não estiver presente
            page_number = int(request.GET.get('page', 1))

            documentos = DocumentoVencido.objects.select_related(
                'empresa', 'regional', 'unidade', 'colaborador', 'cargo', 'tipo_documento'
            ).filter(data_vencimento__gt=timezone.now())  # Filtra para incluir apenas documentos que ainda não venceram

            # Paginação dos resultados
            paginator = Paginator(documentos, per_page=10)  # 10 documentos por página
            page_obj = paginator.get_page(page_number)

            data = []
            for doc in page_obj:
                dias_para_vencer = (doc.data_vencimento - timezone.now().date()).days

                doc_dict = model_to_dict(doc, exclude=['id'])
                doc_dict.update({
                    'empresa': doc.empresa.nome if doc.empresa else '',
                    'regional': doc.regional.nome if doc.regional else '',
                    'unidade': doc.unidade.nome if doc.unidade else '',
                    'colaborador': doc.colaborador.nome if doc.colaborador else '',
                    'cargo': doc.cargo.nome if doc.cargo else '',
                    'tipo_documento': doc.tipo_documento.nome if doc.tipo_documento else '',
                    'situacao': doc.situacao.descricao if hasattr(doc, 'situacao') and doc.situacao else 'Não Definido',
                    'admissao': doc.colaborador.admissao.strftime('%d/%m/%Y') if doc.colaborador.admissao else 'Não Definido',
                    'desligamento': doc.colaborador.desligamento.strftime('%d/%m/%Y') if doc.colaborador.desligamento else 'Não Definido',
                    'obrigatorio': 'Sim' if doc.tipo_documento.obrigatorio else 'Não',
                    'dta_documento': doc.dta_documento.strftime('%d/%m/%Y') if doc.dta_documento else 'Não Definido',
                    'data_vencimento': doc.data_vencimento.strftime('%d/%m/%Y') if doc.data_vencimento else 'Não Definido',
                    'dias_para_vencer': dias_para_vencer  # Adiciona os dias para vencer
                })
                data.append(doc_dict)

            return JsonResponse({
                'data': data,
                'has_next': page_obj.has_next(),
                'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None
            }, safe=False)
        except Exception as e:
            #logger.error('Erro ao listar documentos a vencer: %s', e)
            return JsonResponse({'error': 'Não foi possível recuperar os documentos a vencer'}, status=500)


class GerarRelatorioGerencialView(View):

    def get(self, request, *args, **kwargs):
        # Listar as 10 unidades com menos pendências
        unidades_com_menos_pendencias = (
            DocumentoPendente.objects.values('unidade__nome')
            .annotate(total_pendencias=Count('id'))
            .order_by('total_pendencias')[:10]
        )

        # Listar as 10 empresas com menos pendências
        empresas_com_menos_pendencias = (
            DocumentoPendente.objects.values('empresa__nome')
            .annotate(total_pendencias=Count('id'))
            .order_by('total_pendencias')[:10]
        )

        # Converter as listas em JSON
        response_data = {
            'unidades_com_menos_pendencias': list(unidades_com_menos_pendencias),
            'empresas_com_menos_pendencias': list(empresas_com_menos_pendencias)
        }

        return JsonResponse(response_data)

# ************* Views que carregam os dados dos relatórios ************

class CarregarRelatorioPendenteView(View):
    def get(self, request, *args, **kwargs):
        # Capturar os parâmetros de filtro da requisição
        empresa = request.GET.get('empresa', '')
        regional = request.GET.get('regional', '')
        unidade = request.GET.get('unidade', '')
        nome = request.GET.get('nome', '').lower()
        matricula = request.GET.get('matricula', '').lower()
        cpf = request.GET.get('cpf', '').lower()
        cargo = request.GET.get('cargo', '')
        admissao = request.GET.get('admissao', '')
        desligamento = request.GET.get('desligamento', '')
        situacao = request.GET.get('situacao', '')
        tipo_documento = request.GET.get('tipo_documento', '')

        pendentes = DocumentoPendente.objects.select_related(
            'empresa', 'regional', 'unidade', 'nome', 'cargo', 'tipo_documento'
        )

        # Aplicar os filtros
        if empresa:
            pendentes = pendentes.filter(empresa__nome=empresa)
        if regional:
            pendentes = pendentes.filter(regional__nome=regional)
        if unidade:
            pendentes = pendentes.filter(unidade__nome=unidade)
        if nome:
            pendentes = pendentes.filter(nome__nome__icontains=nome)
        if matricula:
            pendentes = pendentes.filter(matricula__icontains=matricula)
        if cpf:
            pendentes = pendentes.filter(cpf__icontains=cpf)
        if cargo:
            pendentes = pendentes.filter(cargo__nome=cargo)
        if admissao:
            pendentes = pendentes.filter(admissao=admissao)
        if desligamento:
            pendentes = pendentes.filter(desligamento=desligamento)
        if situacao:
            pendentes = pendentes.filter(situacao=situacao)
        if tipo_documento:
            pendentes = pendentes.filter(tipo_documento__nome=tipo_documento)

        page = request.GET.get('page', 1)
        items_per_page = request.GET.get('items_per_page', 8)

        paginator = Paginator(pendentes, items_per_page)
        current_page = paginator.get_page(page)

        serialized_pendentes = []
        for pendente in current_page:
            serialized_pendente = {
                'id': pendente.id,
                'nome': pendente.nome.nome,  # assumindo que Colaborador tem um campo 'nome'
                'matricula': pendente.matricula,
                'cpf': pendente.cpf,
                'empresa': pendente.empresa.nome,
                'regional': pendente.regional.nome,
                'unidade': pendente.unidade.nome,
                'cargo': pendente.cargo.nome,  # assumindo que Cargo tem um campo 'nome'
                'admissao': pendente.admissao.strftime('%d/%m/%Y') if pendente.admissao else '',
                'desligamento': pendente.desligamento.strftime('%d/%m/%Y') if pendente.desligamento else '',
                'situacao': pendente.situacao,
                'tipo_documento': pendente.tipo_documento.nome,  # Verifique se este campo está sendo acessado corretamente
                'obrigatorio': pendente.obrigatorio
            }
            serialized_pendentes.append(serialized_pendente)

        response_data = {
            'pendentes': serialized_pendentes,
            'current_page': current_page.number,
            'total_pages': paginator.num_pages,
            'total_items': paginator.count
        }

        return JsonResponse(response_data, safe=False)


class CarregarRelatorioPendenteSimplesView(View):
    def get(self, request, situacao=None, *args, **kwargs):
        # Filtrando documentos com base na situação passada na URL, se fornecida
        if situacao:
            pendentes = DocumentoPendente.objects.select_related(
                'empresa', 'regional', 'unidade', 'cargo', 'tipo_documento'
            ).filter(situacao=situacao)
        else:
            pendentes = DocumentoPendente.objects.select_related(
                'empresa', 'regional', 'unidade', 'cargo', 'tipo_documento'
            ).all()  # Se a situação não for fornecida, retornar todos os documentos pendentes

        serialized_pendentes = []
        for pendente in pendentes:
            serialized_pendente = {
                'empresa': pendente.empresa.nome,
                'regional': pendente.regional.nome,
                'unidade': pendente.unidade.nome,
                'cargo': pendente.cargo.nome,  # assumindo que Cargo tem um campo 'nome'
                'situacao': pendente.situacao,
                'tipo_documento': pendente.tipo_documento.nome,  # Verifique se este campo está sendo acessado corretamente
            }
            serialized_pendentes.append(serialized_pendente)

        return JsonResponse(serialized_pendentes, safe=False)

class CarregarRelatorioExistenteSimplesView(View):
    def get(self, request, *args, **kwargs):
        # Consulta otimizada com prefetch_related para carregar todos os dados relacionados
        pendentes = Hyperlinkpdf.objects.select_related(
            'empresa', 'regional', 'unidade', 'cargo', 'documento'
        ).prefetch_related(
            'colaborador__status'  # Corrigido para refletir o relacionamento correto
        )

        data = {'Ativo': [], 'Inativo': [], 'Afastado': []}
        for pendente in pendentes:
            situacao = pendente.colaborador.status.nome  # Acessando o nome da situação através do colaborador
            pendente_data = {
                'empresa': pendente.empresa.nome,
                'regional': pendente.regional.nome,
                'unidade': pendente.unidade.nome,
                'cargo': pendente.cargo.nome,
                'situacao': situacao,
                'tipo_documento': pendente.documento.nome if pendente.documento else 'N/A'  # Verificação de None
            }
            if situacao in data:
                data[situacao].append(pendente_data)

        return JsonResponse(data, safe=False)


class CarregarRelatorioExistenteView(View):
    def get(self, request, *args, **kwargs):
        # Obtenha os parâmetros de filtro da solicitação GET
        selected_empresa = request.GET.get('empresa')
        selected_regional = request.GET.get('regional')
        # Obtenha outros parâmetros de filtro, se necessário

        # Consulte todos os registros com base nos parâmetros de filtro
        pendentes = Hyperlinkpdf.objects.select_related(
            'empresa', 'regional', 'unidade', 'cargo', 'documento'
        ).prefetch_related(
            'colaborador__status'  # Corrigido para refletir o relacionamento correto
        )

        if selected_empresa:
            pendentes = pendentes.filter(empresa__nome=selected_empresa)
        if selected_regional:
            pendentes = pendentes.filter(regional__nome=selected_regional)
        # Adicione outras condições de filtro, se necessário

        # Paginação dos resultados
        paginator = Paginator(pendentes, 10)  # Divida em páginas, 10 itens por página
        page_number = request.GET.get('page')
        try:
            pendentes_paginados = paginator.page(page_number)
        except PageNotAnInteger:
            pendentes_paginados = paginator.page(1)  # Se 'page' não é um número, retorne a primeira página
        except EmptyPage:
            pendentes_paginados = paginator.page(paginator.num_pages)  # Se a página estiver fora do intervalo, retorne a última página

        # Construa a resposta JSON
        data = {'results': []}
        for pendente in pendentes_paginados:
            situacao = pendente.colaborador.status.nome  # Acessando o nome da situação através do colaborador
            pendente_data = {
                'nome': pendente.colaborador.nome,
                'matricula': pendente.matricula,
                'cpf': pendente.cpf,
                'empresa': pendente.empresa.nome,
                'regional': pendente.regional.nome,
                'unidade': pendente.unidade.nome,
                'cargo': pendente.cargo.nome,
                'admissao': pendente.colaborador.admissao.strftime('%d/%m/%Y') if pendente.colaborador.admissao else '',
                'desligamento': pendente.colaborador.desligamento.strftime('%d/%m/%Y') if pendente.colaborador.desligamento else '',
                'situacao': situacao,  # Situação ao invés de status
                'documento': pendente.documento.nome,
                'obrigatorio': pendente.documento.obrigatorio
            }
            data['results'].append(pendente_data)

        return JsonResponse(data, safe=False)


class DomingosFeriadosExistenteView(View):
    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            return JsonResponse({'error': 'Request must be AJAX and GET'}, status=400)

        empresa_id = request.GET.get('empresa_id')
        regional_id = request.GET.get('regional_id')
        loja = request.GET.get('loja')
        data_str = request.GET.get('data')

        query = DomingosFeriados.objects.all()
        if empresa_id:
            query = query.filter(empresa_id=empresa_id)
        if regional_id:
            query = query.filter(regional_id=regional_id)
        if loja:
            query = query.filter(loja__icontains=loja)
        if data_str:
            data = parse_date(data_str) # type: ignore
            if data:
                query = query.filter(data_documento=data)
            else:
                # logger.error('Data fornecida é inválida: %s', data_str)
                return JsonResponse({'error': 'Invalid date format'}, status=400)

        query = query.select_related('empresa', 'regional')

        data = [{
            'id': item.id,
            'empresa': item.empresa.nome if item.empresa else '',
            'regional': item.regional.nome if item.regional else '',
            'loja': item.loja,
            'data': item.data_documento or '',
            'nome_documento': item.nome_documento or '',
            'link_documento': item.link_documento or '',
            'data_upload': item.data_upload.strftime('%Y-%m-%d') if item.data_upload else ''
        } for item in query]

        # logger.info('Os dados dos Domingos e feriados: %s', data)

        return JsonResponse(data, safe=False)

class CarregarRelatorioPendenteASOSimplesView(View):
    def get(self, request, *args, **kwargs):
        pendentes = PendenteASO.objects.select_related(
            'empresa', 'regional', 'unidade', 'cargo', 'tipo_aso', 'status'
        )
        serialized_pendentes = []
        for pendente in pendentes:
            serialized_pendente = {
                'empresa': pendente.empresa.nome if pendente.empresa else 'N/A',
                'regional': pendente.regional.nome if pendente.regional else 'N/A',
                'unidade': pendente.unidade.nome if pendente.unidade else 'N/A',
                'cargo': pendente.cargo.nome if pendente.cargo else 'N/A',
                'situacao': pendente.status.nome if pendente.status else 'N/A',
                'tipo_documento': pendente.tipo_aso.nome if pendente.tipo_aso else 'N/A',
            }
            serialized_pendentes.append(serialized_pendente)

        return JsonResponse(serialized_pendentes, safe=False)


class CarregarRelatorioPendenteASOView(View):
    def get(self, request, *args, **kwargs):
        # Obtendo parâmetros de filtro da requisição
        empresa = request.GET.get('empresa', '')
        regional = request.GET.get('regional', '')
        unidade = request.GET.get('unidade', '')
        cargo = request.GET.get('cargo', '')
        status = request.GET.get('status', '')
        tipo_documento = request.GET.get('tipo_documento', '')
        nome = request.GET.get('nome', '').lower()
        matricula = request.GET.get('matricula', '').lower()
        cpf = request.GET.get('cpf', '').lower()
        admissao = request.GET.get('admissao', '')
        desligamento = request.GET.get('desligamento', '')

        pendentes = PendenteASO.objects.select_related(
            'empresa', 'regional', 'unidade', 'nome', 'cargo', 'tipo_aso', 'status'
        ).all()

        # Aplicando filtros
        if empresa:
            pendentes = pendentes.filter(empresa__nome=empresa)
        if regional:
            pendentes = pendentes.filter(regional__nome=regional)
        if unidade:
            pendentes = pendentes.filter(unidade__nome=unidade)
        if cargo:
            pendentes = pendentes.filter(cargo__nome=cargo)
        if status:
            pendentes = pendentes.filter(status__nome=status)
        if tipo_documento:
            pendentes = pendentes.filter(tipo_aso__nome=tipo_documento)
        if nome:
            pendentes = pendentes.filter(nome__nome__icontains=nome)
        if matricula:
            pendentes = pendentes.filter(matricula__icontains=matricula)
        if cpf:
            pendentes = pendentes.filter(cpf__icontains=cpf)
        if admissao:
            pendentes = pendentes.filter(admissao=admissao)
        if desligamento:
            pendentes = pendentes.filter(desligamento=desligamento)

        # Paginação
        page_number = request.GET.get('page', 1)
        paginator = Paginator(pendentes, 10)  # 10 itens por página
        page_obj = paginator.get_page(page_number)

        serialized_pendentes = []
        for pendente in page_obj:
            serialized_pendente = {
                'id': pendente.id,
                'nome': pendente.nome.nome if pendente.nome else 'N/A',
                'matricula': pendente.matricula,
                'cpf': pendente.cpf,
                'empresa': pendente.empresa.nome if pendente.empresa else 'N/A',
                'regional': pendente.regional.nome if pendente.regional else 'N/A',
                'unidade': pendente.unidade.nome if pendente.unidade else 'N/A',
                'cargo': pendente.cargo.nome if pendente.cargo else 'N/A',
                'admissao': pendente.admissao.strftime('%d/%m/%Y') if pendente.admissao else 'N/A',
                'desligamento': pendente.desligamento.strftime('%d/%m/%Y') if pendente.desligamento else 'N/A',
                'status': pendente.status.nome if pendente.status else 'N/A',
                'tipo_documento': pendente.tipo_aso.nome if pendente.tipo_aso else 'N/A',
                'aso_existente': 'Sim' if pendente.aso_admissional_existente else 'Não'
            }
            serialized_pendentes.append(serialized_pendente)

        response = {
            'pendentes': serialized_pendentes,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'page_number': page_obj.number,
            'num_pages': paginator.num_pages,
        }

        return JsonResponse(response)


class ListarCartaoPontoInexistenteSimplesView(View):
    def get(self, request, *args, **kwargs):
        cartoes = CartaoPontoInexistente.objects.select_related(
            'empresa', 'regional', 'unidade', 'status'
        ).all()
        serialized_cartoes = []
        for cartao in cartoes:
            serialized_cartao = {
                'empresa': cartao.empresa.nome if cartao.empresa else 'N/A',
                'regional': cartao.regional.nome if cartao.regional else 'N/A',
                'unidade': cartao.unidade.nome if cartao.unidade else 'N/A',
                'status': cartao.status.nome if cartao.status else 'N/A'
            }
            serialized_cartoes.append(serialized_cartao)

        return JsonResponse(serialized_cartoes, safe=False)


class ListarCartaoPontoInexistenteView(View):
    def get(self, request, *args, **kwargs):
        cartoes = CartaoPontoInexistente.objects.select_related(
            'empresa', 'regional', 'unidade', 'colaborador', 'status'
        ).all()
        
        # Adicionar paginação
        page_number = request.GET.get('page', 1)
        paginator = Paginator(cartoes, 10)  # 10 itens por página
        page_obj = paginator.get_page(page_number)
        
        serialized_cartoes = []
        for cartao in page_obj:
            serialized_cartao = {
                'id': cartao.id,
                'empresa': cartao.empresa.nome if cartao.empresa else 'N/A',
                'regional': cartao.regional.nome if cartao.regional else 'N/A',
                'unidade': cartao.unidade.nome if cartao.unidade else 'N/A',
                'colaborador': cartao.colaborador.nome if cartao.colaborador else 'N/A',
                'matricula': cartao.colaborador.matricula if cartao.colaborador else 'N/A',
                'cpf': cartao.colaborador.cpf if cartao.colaborador else 'N/A',
                'admissao': cartao.colaborador.admissao.strftime('%d/%m/%Y') if cartao.colaborador and cartao.colaborador.admissao else 'N/A',
                'desligamento': cartao.colaborador.desligamento.strftime('%d/%m/%Y') if cartao.colaborador and cartao.colaborador.desligamento else 'N/A',
                'data': cartao.data.strftime('%d/%m/%Y') if cartao.data else 'N/A',
                'existente': 'Sim' if cartao.existente else 'Não',
                'status': cartao.status.nome if cartao.status else 'N/A'
            }
            serialized_cartoes.append(serialized_cartao)

        response = {
            'cartoes': serialized_cartoes,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'page_number': page_obj.number,
            'num_pages': paginator.num_pages
        }

        return JsonResponse(response, safe=False)

def buscar_pendencias(request):
    data_escolhida = request.GET.get('data', None)
    if data_escolhida:
        resultado = DocumentoPendenciaQuery.buscar_pendencias_por_data(data_escolhida)
        return JsonResponse(resultado)
    else:
        return JsonResponse({'error': 'Data não especificada'}, status=400)

class CarregarRelatoriosGerenciaisView(View):
    @staticmethod
    def unidades_com_menos_pendencias():
        unidades = (DocumentoPendente.objects
                    .values('unidade__nome')
                    .annotate(total_pendencias=Count('id'))
                    .order_by('total_pendencias')[:10])

        detalhes = {}
        for unidade in unidades:
            documentos = (DocumentoPendente.objects
                          .filter(unidade__nome=unidade['unidade__nome'])
                          .values('tipo_documento__nome')
                          .annotate(total=Count('id'))
                          .order_by('tipo_documento__nome'))
            detalhes[unidade['unidade__nome']] = list(documentos)

        return unidades, detalhes

    @staticmethod
    def empresas_com_menos_pendencias():
        empresas = (DocumentoPendente.objects
                    .values('empresa__nome')
                    .annotate(total_pendencias=Count('id'))
                    .order_by('total_pendencias')[:10])

        detalhes = {}
        for empresa in empresas:
            documentos = (DocumentoPendente.objects
                          .filter(empresa__nome=empresa['empresa__nome'])
                          .values('tipo_documento__nome')
                          .annotate(total=Count('id'))
                          .order_by('tipo_documento__nome'))
            detalhes[empresa['empresa__nome']] = list(documentos)

        return empresas, detalhes

    def get(self, request, *args, **kwargs):
        unidades, detalhes_unidades = self.unidades_com_menos_pendencias()
        empresas, detalhes_empresas = self.empresas_com_menos_pendencias()

        data = {
            'unidades': [{'nome': u['unidade__nome'], 'total_pendencias': u['total_pendencias']} for u in unidades],
            'detalhes_unidades': detalhes_unidades,
            'empresas': [{'nome': e['empresa__nome'], 'total_pendencias': e['total_pendencias']} for e in empresas],
            'detalhes_empresas': detalhes_empresas
        }
        return JsonResponse(data)

    def data_atual(request):
        context = {
            'data_atual': date.today().isoformat()
        }
        return render(request, 'documento/relatorios.html', context)

# ***************       Views que apresentam o html do relatório ++++++++++++++++++++++++


class DocumentosPendentesAtivosPorUnidadeView(View):
    def get(self, request):
        # A parte original do seu método get fica intacta aqui
        dados_resumo = []
        documentos_por_unidade = DocumentoPendente.objects.filter(
            obrigatorio=True,
            nome_desligamento_isnull=True
        ).values('unidade__nome').annotate(total_pendentes=Count('id')).order_by('unidade')
        for doc_unidade in documentos_por_unidade:
            dados_resumo.append({
                'unidade': doc_unidade['unidade__nome'],
                'documentos_pendentes': doc_unidade['total_pendentes']
            })
        response_data = {'dados_resumo': dados_resumo}
        return JsonResponse(response_data, safe=False)


class DocumentosPendentesInativosPorUnidadeView(View):
    def get(self, request):

        # Preparar os dados de resumo por unidade
        dados_resumo = []

        documentos_por_unidade = DocumentoPendente.objects.filter(
            obrigatorio=True,
            nome_desligamento_isnull=False  # Considerar apenas colaboradores inativos
        ).values('unidade__nome').annotate(total_pendentes=Count('id')).order_by('unidade')

        # Processar cada unidade e o seu total de documentos pendentes
        for doc_unidade in documentos_por_unidade:
            dados_resumo.append({
                'unidade': doc_unidade['unidade__nome'],
                'documentos_pendentes': doc_unidade['total_pendentes']
            })

        response_data = {'dados_resumo': dados_resumo}
        return JsonResponse(response_data, safe=False)

    def documentos_pendentes_por_unidade(self, request, unidade_nome):
        # Este método pode ser chamado de outra view ou URL que passe 'unidade_nome' como parâmetro
        documentos_pendentes = DocumentoPendente.objects.filter(
            obrigatorio=True,
            nome_unidade_nome=unidade_nome,
            nome_desligamento_isnull=False
        ).values('tipo_documento_nome', 'nomenome', 'nome_matricula').distinct()
        dados = list(documentos_pendentes)
        return JsonResponse({'dados': dados})


class RelatorioPendenteView(View):
    def get(self, request):
        form = RelatoriosPendentesForm()
        return render(request, 'documento/relatorios.html', {'form': form})

    def post(self, request):
        form = RelatoriosPendentesForm(request.POST)
        if form.is_valid():

            # Mapeando o nome do formulário para o nome do campo do modelo
            query = {}
            for field, value in form.cleaned_data.items():
                if value:
                    if field == 'nome':
                        query['nome'] = value
                    else:
                        query[field] = value

            documentos = DocumentoPendente.objects.filter(**query)

            return render(request, 'documento/relatorios.html', {
                'form': form,
                'documentos_pendentes': documentos
            })

        return render(request, 'documento/relatorios.html', {'form': form})


class DocumentosExistentesAtivosView(View):
    def get(self, request, unidade_nome, status):
        # Filtrar colaboradores com base no status (ativos/inativos)
        if status == 'ativos':
            colaboradores_filtro = Colaborador.objects.filter(desligamento__isnull=True)
        # elif status == 'inativos':
            # colaboradores_filtro = Colaborador.objects.filter(desligamento__isnull=False)
        else:
            return JsonResponse({'erro': 'Status inválido'}, status=400)

        # Obter CPFs e/ou matrículas dos colaboradores filtrados
        cpf_matricula_filtrados = colaboradores_filtro.values_list('cpf', 'matricula')

        # Construir uma lista de Q objects para busca no modelo Hyperlinkpdf
        q_objects = Q()
        for cpf, matricula in cpf_matricula_filtrados:
            q_objects |= (Q(cpf=cpf) & Q(matricula=matricula))

        # Filtrar documentos existentes que correspondam aos CPFs e/ou matrículas dos colaboradores
        documentos = Hyperlinkpdf.objects.filter(
            q_objects,
            colaborador__unidade__nome=unidade_nome  # Ajuste esse campo conforme a relação no seu modelo
        ).values('categoria').annotate(total=Count('id')).order_by('categoria')

        dados_resumo = [{'categoria': doc['categoria'], 'total': doc['total']} for doc in documentos]

        return JsonResponse({'dados_resumo': dados_resumo})


class DocumentosExistentesInativosView(View):
    def get(self, request, unidade_nome, status):
        # Filtrar colaboradores inativos
        if status == 'inativos':
            colaboradores_filtro = Colaborador.objects.filter(desligamento__isnull=False)
        else:
            return JsonResponse({'erro': 'Status inválido'}, status=400)

        # Obter CPFs e/ou matrículas dos colaboradores filtrados
        cpf_matricula_filtrados = colaboradores_filtro.values_list('cpf', 'matricula')

        if not cpf_matricula_filtrados:
            return JsonResponse({'dados_resumo': []})

        # Construir uma lista de Q objects para busca no modelo Hyperlinkpdf
        q_objects = Q()
        for cpf, matricula in cpf_matricula_filtrados:
            q_objects |= (Q(cpf=cpf) & Q(matricula=matricula))

        # Filtrar documentos existentes que correspondam aos CPFs e/ou matrículas dos colaboradores
        documentos = Hyperlinkpdf.objects.filter(
            q_objects,
            colaborador__unidade__nome=unidade_nome
        ).values('categoria').annotate(total=Count('id')).order_by('categoria')

        dados_resumo = [{'categoria': doc['categoria'], 'total': doc['total']} for doc in documentos]

        return JsonResponse({'dados_resumo': dados_resumo})


class DocumentoExistenteListView(ListView):
    """
    Exibe a lista de documentos existentes.

    Atributos:
        model (Model): Modelo que será usado para carregar os dados (DocumentoExistente).
        template_name (str): Caminho para o template HTML que será usado para renderizar a view.
        context_object_name (str): Nome do objeto que será passado para o template.

    Métodos:
        get_queryset (request): Retorna um QuerySet que será usado para carregar os dados.
    """

    model = Hyperlinkpdf
    template_name = "documento/relatorios.html"
    context_object_name = "documentos_existentes"

    def get_queryset(self, request):
        """
        Filtra os documentos existentes por regional, unidade, colaborador, matrícula, CPF, cargo, data de admissão, situação, tipo de documento, número do documento e data do documento.

        Argumentos:
            request: O objeto HttpRequest que contém informações sobre a requisição.

        Retorno:
            QuerySet: QuerySet filtrado com os documentos existentes.
        """

        queryset = super().get_queryset(request)

        regional = request.GET.get("regional")
        unidade = request.GET.get("unidade")
        colaborador = request.GET.get("colaborador")
        matricula = request.GET.get("matricula")
        cpf = request.GET.get("cpf")
        cargo = request.GET.get("cargo")
        data_admissao_inicial = request.GET.get("data_admissao_inicial")
        data_admissao_final = request.GET.get("data_admissao_final")
        situacao = request.GET.get("situacao")
        tipo_documento = request.GET.get("tipo_documento")
        numero_documento = request.GET.get("numero_documento")
        data_documento = request.GET.get("data_documento")

        if regional:
            queryset = queryset.filter(regional__icontains=regional)

        if unidade:
            queryset = queryset.filter(unidade__icontains=unidade)

        if colaborador:
            queryset = queryset.filter(colaborador__icontains=colaborador)

        if matricula:
            queryset = queryset.filter(matricula__icontains=matricula)

        if cpf:
            queryset = queryset.filter(cpf__icontains=cpf)

        if cargo:
            queryset = queryset.filter(cargo__icontains=cargo)

        if data_admissao_inicial:
            queryset = queryset.filter(data_admissao_inicial__gte=data_admissao_inicial)

        if data_admissao_final:
            queryset = queryset.filter(data_admissao_final__lte=data_admissao_final)

        if situacao:
            queryset = queryset.filter(situacao__icontains=situacao)

        if tipo_documento:
            queryset = queryset.filter(tipo_documento__icontains=tipo_documento)

        if numero_documento:
            queryset = queryset.filter(numero_documento__icontains=numero_documento)

        if data_documento:
            queryset = queryset.filter(data_documento__gte=data_documento)

        return queryset

class PendenteASOListView(ListView):
    """
    Exibe a lista de pendências ASO.

    Atributos:
        model (Model): Modelo que será usado para carregar os dados (PendenteASO).
        template_name (str): Caminho para o template HTML que será usado para renderizar a view.
        context_object_name (str): Nome do objeto que será passado para o template.

    Métodos:
        get_queryset (request): Retorna um QuerySet que será usado para carregar os dados.
    """

    model = PendenteASO
    template_name = "documento/relatorios.html"
    context_object_name = "pendentes_aso"

    def get_queryset(self, request):
        """
        Filtra as pendências ASO por regional, unidade, nome do colaborador, matrícula, título, descrição, data de criação, data limite, status e prioridade.

        Argumentos:
            request: Objeto HttpRequest que contém informações sobre a requisição.

        Retorno:
            QuerySet: QuerySet filtrado com as pendências ASO.
        """

        queryset = super().get_queryset(request)

        regional = request.GET.get("regional")
        unidade = request.GET.get("unidade")
        nome_colaborador = request.GET.get("nome_colaborador")
        matricula = request.GET.get("matricula")
        titulo = request.GET.get("titulo")
        descricao = request.GET.get("descricao")
        data_criacao = request.GET.get("data_criacao")
        status = request.GET.get("status")
        prioridade = request.GET.get("prioridade")

        if regional:
            queryset = queryset.filter(regional=regional)

        if unidade:
            queryset = queryset.filter(unidade=unidade)

        if nome_colaborador:
            queryset = queryset.filter(nome_colaborador__icontains=nome_colaborador)

        if matricula:
            queryset = queryset.filter(matricula=matricula)

        if titulo:
            queryset = queryset.filter(titulo__icontains=titulo)

        if descricao:
            queryset = queryset.filter(descricao__icontains=descricao)

        if data_criacao:
            queryset = queryset.filter(data_criacao__gte=data_criacao)

@method_decorator(csrf_exempt, name='dispatch')
class AtualizarASOView(View):
    def get(self, request, *args, **kwargs):
        parametro = request.GET.get('parametro')

        if parametro:
            # Realiza alguma lógica com base no parâmetro
            resposta = f"Recebido o parâmetro {parametro}"
            return JsonResponse({"status": resposta}, status=200)
        else:
            # Retorna uma mensagem dizendo que o método GET não é suportado
            return JsonResponse({"status": "Método GET não suportado"}, status=405)

    def post(self, request, *args, **kwargs):
        def iniciar_atualizacao():
            ServicoPendenteASO.inicializar_pendencias()

        def realizar_atualizacao():
            ServicoPendenteASO.atualizar_pendencias()

        iniciar_atualizacao()
        realizar_atualizacao()

        return JsonResponse({"status": "Atualização iniciada"}, status=202)

@method_decorator(csrf_exempt, name='dispatch')
class AtualizarCartaoPontoView(View):
    def get(self, request, *args, **kwargs):
        parametro = request.GET.get('parametro')

        if parametro:
            # Realiza alguma lógica com base no parâmetro
            resposta = f"Recebido o parâmetro {parametro}"
            return JsonResponse({"status": resposta}, status=200)
        else:
            # Retorna uma mensagem dizendo que o método GET não é suportado
            return JsonResponse({"status": "Método GET não suportado"}, status=405)

    def post(self, request, *args, **kwargs):
        def iniciar_atualizacao():
            ServicoPonto.inicializar_pendencias()

        def realizar_atualizacao():
            ServicoPonto.atualizar_pendencias()


        iniciar_atualizacao()
        realizar_atualizacao()

        return JsonResponse({"status": "Atualização iniciada"}, status=202)

class CartaoPontoInexistenteListView(ListView):
    """
    Exibe a lista de cartões de ponto inexistentes.

    Atributos:
        model (Model): Modelo que será usado para carregar os dados (CartaoPontoInexistente).
        template_name (str): Caminho para o template HTML que será usado para renderizar a view.
        context_object_name (str): Nome do objeto que será passado para o template.

    Métodos:
        get_queryset (request): Retorna um QuerySet que será usado para carregar os dados.
    """

    model = CartaoPontoInexistente
    template_name = "documento/relatorios.html"
    context_object_name = "cartoes_ponto_inexistentes"

    def get_queryset(self, request):
        """
        Filtra os cartões de ponto inexistentes por data, regional, unidade, nome do colaborador e situação.

        Argumentos:
            request: Objeto HttpRequest que contém informações sobre a requisição.

        Retorno:
            QuerySet: QuerySet filtrado com os cartões de ponto inexistentes.
        """

        queryset = super().get_queryset(request)

        data = request.GET.get("data")
        regional = request.GET.get("regional")
        unidade = request.GET.get("unidade")
        nome_colaborador = request.GET.get("nome_colaborador")
        situacao = request.GET.get("situacao")

        if data:
            queryset = queryset.filter(data=data)

        if regional:
            queryset = queryset.filter(regional=regional)

        if unidade:
            queryset = queryset.filter(unidade=unidade)

        if nome_colaborador:
            queryset = queryset.filter(nome_colaborador__icontains=nome_colaborador)

        if situacao:
            queryset = queryset.filter(situacao=situacao)

        return queryset


class DocumentoVencidoListView(ListView):
    """
    Exibe a lista de documentos vencidos.

    Atributos:
        model (Model): Modelo que será usado para carregar os dados (DocumentoVencido).
        template_name (str): Caminho para o template HTML que será usado para renderizar a view.
        context_object_name (str): Nome do objeto que será passado para o template.

    Métodos:
        get_queryset (request): Retorna um QuerySet que será usado para carregar os dados.
    """

    model = DocumentoVencido
    template_name = "documento/relatorios.html"
    context_object_name = "documentos_vencidos"

    def get_queryset(self, request):
        """
        Filtra os documentos vencidos por regional, unidade, nome do colaborador, matrícula, CPF, cargo, data de admissão inicial,
        data de admissão final, mês, ano e tipo de documento.

        Argumentos:
            request: Objeto HttpRequest que contém informações sobre a requisição.

        Retorno:
            QuerySet: QuerySet filtrado com os documentos vencidos.
        """

        queryset = super().get_queryset(request)

        regional = request.GET.get("regional")
        unidade = request.GET.get("unidade")
        nome_colaborador = request.GET.get("nome_colaborador")
        matricula = request.GET.get("matricula")
        cpf = request.GET.get("cpf")
        cargo = request.GET.get("cargo")
        data_admissao_inicial = request.GET.get("data_admissao_inicial")
        data_admissao_final = request.GET.get("data_admissao_final")
        mes = request.GET.get("mes")
        ano = request.GET.get("ano")
        tipo_documento = request.GET.get("tipo_documento")

        if regional:
            queryset = queryset.filter(regional=regional)

        if unidade:
            queryset = queryset.filter(unidade=unidade)

        if nome_colaborador:
            queryset = queryset.filter(nome_colaborador__icontains=nome_colaborador)

        if matricula:
            queryset = queryset.filter(matricula=matricula)

        if cpf:
            queryset = queryset.filter(cpf=cpf)

        if cargo:
            queryset = queryset.filter(cargo=cargo)

        if data_admissao_inicial:
            queryset = queryset.filter(data_admissao_inicial__gte=data_admissao_inicial)

        if data_admissao_final:
            queryset = queryset.filter(data_admissao_final__lte=data_admissao_final)

        if mes:
            queryset = queryset.filter(mes=mes)

        if ano:
            queryset = queryset.filter(ano=ano)

        if tipo_documento:
            queryset = queryset.filter(tipo_documento=tipo_documento)

        return queryset


class DocumentoAVencerListView(ListView):
    """
    Exibe a lista de documentos a vencer.

    Atributos:
        model (Model): Modelo que será usado para carregar os dados (DocumentoAVencer).
        template_name (str): Caminho para o template HTML que será usado para renderizar a view.
        context_object_name (str): Nome do objeto que será passado para o template.

    Métodos:
        get_queryset (request): Retorna um QuerySet que será usado para carregar os dados.
    """

    model = DocumentoVencido
    template_name = "documento/relatorios.html"
    context_object_name = "documentos_a_vencer"

    def get_queryset(self, request):
        """
        Filtra os documentos a vencer por regional, unidade, nome do colaborador, matrícula, CPF, cargo, data de admissão inicial, data de admissão final, dias de antecedência e tipo de documento.

        Argumentos:
            request: Objeto HttpRequest que contém informações sobre a requisição.

        Retorno:
            QuerySet: QuerySet filtrado com os documentos a vencer.
        """

        queryset = super().get_queryset(request)

        regional = request.GET.get("regional")
        unidade = request.GET.get("unidade")
        nome_colaborador = request.GET.get("nome_colaborador")
        matricula = request.GET.get("matricula")
        cpf = request.GET.get("cpf")
        cargo = request.GET.get("cargo")
        data_admissao_inicial = request.GET.get("data_admissao_inicial")
        data_admissao_final = request.GET.get("data_admissao_final")
        dias_antecedencia = request.GET.get("dias_antecedencia")
        tipo_documento = request.GET.get("tipo_documento")

        if regional:
            queryset = queryset.filter(regional=regional)

        if unidade:
            queryset = queryset.filter(unidade=unidade)

        if nome_colaborador:
            queryset = queryset.filter(nome_colaborador__icontains=nome_colaborador)

        if matricula:
            queryset = queryset.filter(matricula=matricula)

        if cpf:
            queryset = queryset.filter(cpf=cpf)

        if cargo:
            queryset = queryset.filter(cargo=cargo)

        if data_admissao_inicial:
            queryset = queryset.filter(data_admissao_inicial__gte=data_admissao_inicial)

        if data_admissao_final:
            queryset = queryset.filter(data_admissao_final__lte=data_admissao_final)

        if dias_antecedencia:
            queryset = queryset.filter(dias_antecedencia=dias_antecedencia)

        if tipo_documento:
            queryset = queryset.filter(tipo_documento=tipo_documento)

        return queryset


class RelatorioGerencialListView(ListView):
    """
    Exibe a lista de documentos pendentes.

    Atributos:
        model (Model): Modelo que será usado para carregar os dados (DocumentoPendente).
        template_name (str): Caminho para o template HTML que será usado para renderizar a view.
        context_object_name (str): Nome do objeto que será passado para o template.

    Métodos:
        get_queryset (request): Retorna um QuerySet que será usado para carregar os dados.
    """

    model = DocumentoPendente
    template_name = "documento/relatorios.html"
    context_object_name = "relatorios_gerenciais"

    def get_queryset(self):
        """
        Filtra os documentos pendentes por empresa, regional, unidade, nome do colaborador, matrícula, CPF, cargo, admissão, desligamento, situação e tipo de documento.

        Argumentos:
            request: Objeto HttpRequest que contém informações sobre a requisição.

        Retorno:
            QuerySet: QuerySet filtrado com os documentos pendentes.
        """

        queryset = super().get_queryset()

        # Filtrando por campos que podem ser comuns para buscas
        matricula = self.request.GET.get('matricula')
        cpf = self.request.GET.get('cpf')
        nome = self.request.GET.get('nome')
        situacao = self.request.GET.get('situacao')

        if matricula:
            queryset = queryset.filter(matricula__icontains=matricula)
        if cpf:
            queryset = queryset.filter(cpf__icontains=cpf)
        if nome:
            queryset = queryset.filter(nome__nome__icontains=nome)
        if situacao:
            queryset = queryset.filter(situacao__icontains=situacao)

        return queryset



# **********   Views para a aba de Configurações **********


class CadastrarFuncionarioView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        # Exclusão de um colaborador existente
        if 'excluir' in data:
            try:
                colaborador_id = data.get('id')
                colaborador = Colaborador.objects.get(id=colaborador_id)
                colaborador.delete()
                return JsonResponse({'mensagem': 'Colaborador excluído com sucesso!'}, status=204)
            except Colaborador.DoesNotExist:
                return JsonResponse({'mensagem': 'Colaborador não encontrado.'}, status=404)

        # Atualização de um colaborador existente
        colaborador_id = data.get('id', None)
        if colaborador_id:
            try:
                colaborador = Colaborador.objects.get(id=colaborador_id)
                for field in ['nome', 'matricula', 'cpf', 'cargo', 'status', 'admissao', 'desligamento', 'email', 'pcd']:
                    if field in data:
                        setattr(colaborador, field, data[field])
                colaborador.save()
                return JsonResponse({'mensagem': 'Colaborador atualizado com sucesso!'})
            except Colaborador.DoesNotExist:
                return JsonResponse({'mensagem': 'Colaborador não encontrado.'}, status=404)

        # Criação de novo colaborador
        empresa_nome = data.get('empresa')
        empresa, _ = Empresa.objects.get_or_create(nome=empresa_nome)

        regional_nome = data.get('regional')
        regional, _ = Regional.objects.get_or_create(nome=regional_nome, empresa=empresa)

        unidade_nome = data.get('unidade')
        unidade, _ = Unidade.objects.get_or_create(nome=unidade_nome, regional=regional)

        cargo_nome = data.get('cargo')
        if not cargo_nome:
            return JsonResponse({'mensagem': 'Nome do cargo é obrigatório!'}, status=400)
        cargo, _ = Cargo.objects.get_or_create(nome=cargo_nome, unidade=unidade)

        status_nome = data.get('situacao')
        if not status_nome:
            return JsonResponse({'mensagem': 'Situação é obrigatória!'}, status=400)
        status, _ = Situacao.objects.get_or_create(nome=status_nome, cargo=cargo)

        data_admissao = data.get('admissao')
        if not data_admissao:
            return JsonResponse({'mensagem': 'A data de admissão é obrigatória!'}, status=400)
        try:
            data_admissao = datetime.strptime(data_admissao, '%Y-%m-%d')
        except ValueError:
            return JsonResponse({'mensagem': 'Formato de data de admissão inválido. Use YYYY-MM-DD.'}, status=400)

        data_desligamento = data.get('desligamento')
        if status_nome == 'Inativo':
            if not data_desligamento:
                return JsonResponse({'mensagem': 'Para status Inativo, a data de desligamento é obrigatória!'}, status=400)
            try:
                data_desligamento = datetime.strptime(data_desligamento, '%Y-%m-%d')
            except ValueError:
                return JsonResponse({'mensagem': 'Formato de data de desligamento inválido. Use YYYY-MM-DD.'}, status=400)
        else:
            data_desligamento = None  # Garantir que será nulo se não for Inativo

        novo_colaborador = Colaborador(
            empresa=empresa,
            regional=regional,
            unidade=unidade,
            matricula=data['matricula'],
            nome=data['nome'],
            cargo=cargo,
            admissao=data_admissao,
            cpf=data['cpf'],
            pcd=data['pcd'],
            status=status,
            modo_ponto=data.get('modoponto'),
            desligamento=data_desligamento,
            email=data.get('email', None)
        )
        novo_colaborador.save()

        return JsonResponse({'mensagem': 'Funcionário cadastrado com sucesso!'})

    def get(self, request, *args, **kwargs):
        colaboradores_list = Colaborador.objects.all().select_related('empresa', 'regional', 'unidade', 'cargo', 'status')
        paginator = Paginator(colaboradores_list, 100)  # Paginando em lotes de 100

        # Obtendo o número da página do parâmetro GET (querystring)
        page_number = request.GET.get('page', 1)
        colaboradores = paginator.get_page(page_number)

        data = [
            {
                'id': colaborador.id,
                'nome': colaborador.nome,
                'matricula': colaborador.matricula,
                'cpf': colaborador.cpf,
                'cargo': colaborador.cargo.nome if colaborador.cargo else '',
                'status': colaborador.status.nome if colaborador.status else '',
                'admissao': colaborador.admissao.strftime('%d/%m/%Y') if colaborador.admissao else 'Não Definido',
                'desligamento': colaborador.desligamento.strftime(
                    '%d/%m/%Y') if colaborador.desligamento else 'Não Definido',
                'email': colaborador.email,
                'empresa': colaborador.empresa.nome if colaborador.empresa else '',
                'regional': colaborador.regional.nome if colaborador.regional else '',
                'unidade': colaborador.unidade.nome if colaborador.unidade else ''
            }
            for colaborador in colaboradores
        ]
        return JsonResponse({'data': data, 'has_next': colaboradores.has_next(), 'has_previous': colaboradores.has_previous(),
                             'num_pages': paginator.num_pages}, safe=False)


@csrf_exempt
def gerenciar_empresa(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        empresa_id = data.get('id', None)
        nome_empresa = data.get('nome', '')

        if 'excluir' in data and empresa_id:
            # Processa a exclusão da empresa
            try:
                empresa = Empresa.objects.get(id=empresa_id)
                empresa.delete()
                return HttpResponse(status=204)
            except Empresa.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Empresa não encontrada'}, status=404)

        if empresa_id:
            # Edita uma empresa existente
            try:
                empresa = Empresa.objects.get(id=empresa_id)
                empresa.nome = nome_empresa
                empresa.save()
                return JsonResponse({'status': 'success', 'message': 'Empresa atualizada com sucesso'})
            except Empresa.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Empresa não encontrada'}, status=404)
        else:
            # Cria uma nova empresa
            try:
                if Empresa.objects.filter(nome=nome_empresa).exists():
                    return JsonResponse({'status': 'error', 'message': 'Uma empresa com esse nome já existe'}, status=400)
                nova_empresa = Empresa(nome=nome_empresa)
                nova_empresa.save()
                return JsonResponse({'status': 'success', 'message': 'Empresa cadastrada com sucesso'})
            except IntegrityError as e:
                return JsonResponse({'status': 'error', 'message': f'Erro de integridade ao salvar a empresa: {str(e)}'}, status=500)
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': f'Erro ao cadastrar empresa: {str(e)}'}, status=500)

    elif request.method == 'GET':
        empresas = Empresa.objects.all().values('id', 'nome')
        return JsonResponse(list(empresas), safe=False)

    elif request.method == 'DELETE':
        # Tratamento específico para DELETE
        data = json.loads(request.body)
        empresa_id = data.get('id', None)
        if empresa_id:
            try:
                empresa = Empresa.objects.get(id=empresa_id)
                empresa.delete()
                return HttpResponse(status=204)
            except Empresa.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Empresa não encontrada'}, status=404)
        else:
            return JsonResponse({'status': 'error', 'message': 'ID de empresa não fornecido'}, status=400)

    else:
        return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)


@csrf_exempt
def gerenciar_regional(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        regional_id = data.get('id', None)
        nome_regional = data.get('nome', '')
        empresa_id = data.get('empresa_id', None)

        if 'excluir' in data and regional_id:
            # Processa a exclusão da regional
            try:
                regional = Regional.objects.get(id=regional_id)
                regional.delete()
                return HttpResponse(status=204)
            except Regional.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Regional não encontrada'}, status=404)

        if regional_id:
            # Edita uma regional existente
            try:
                regional = Regional.objects.get(id=regional_id)
                regional.nome = nome_regional
                if empresa_id:
                    regional.empresa_id = empresa_id
                regional.save()
                return JsonResponse({'status': 'success', 'message': 'Regional atualizada com sucesso'})
            except Regional.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Regional não encontrada'}, status=404)
            except Empresa.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Empresa não encontrada'}, status=404)
        else:
            # Cria uma nova regional
            try:
                if empresa_id is None or not Empresa.objects.filter(id=empresa_id).exists():
                    return JsonResponse({'status': 'error', 'message': 'Empresa fornecida não existe'}, status=400)
                if Regional.objects.filter(nome=nome_regional, empresa_id=empresa_id).exists():
                    return JsonResponse({'status': 'error', 'message': 'Uma regional com esse nome já existe nesta empresa'}, status=400)
                nova_regional = Regional(nome=nome_regional, empresa_id=empresa_id)
                nova_regional.save()
                return JsonResponse({'status': 'success', 'message': 'Regional cadastrada com sucesso'})
            except IntegrityError as e:
                return JsonResponse({'status': 'error', 'message': f'Erro de integridade ao salvar a regional: {str(e)}'}, status=500)
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': f'Erro ao cadastrar regional: {str(e)}'}, status=500)
    elif request.method == 'GET':
        regionais = Regional.objects.select_related('empresa').all().values(
            'id', 'nome', 'empresa__nome'
        )
        return JsonResponse(list(regionais), safe=False)
    elif request.method == 'DELETE':
        data = json.loads(request.body)
        regional_id = data.get('id', None)
        if regional_id:
            try:
                regional = Regional.objects.get(id=regional_id)
                regional.delete()
                return HttpResponse(status=204)
            except Regional.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Regional não encontrada'}, status=404)
        else:
            return JsonResponse({'status': 'error', 'message': 'ID da regional não fornecido'}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)

@csrf_exempt
def gerenciar_unidade(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        unidade_id = data.get('id', None)
        nome_unidade = data.get('nome', '')
        regional_id = data.get('regional_id', None)

        if 'excluir' in data and unidade_id:
            # Processa a exclusão da unidade
            try:
                unidade = Unidade.objects.get(id=unidade_id)
                unidade.delete()
                return HttpResponse(status=204)
            except Unidade.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Unidade não encontrada'}, status=404)

        if unidade_id:
            # Edita uma unidade existente
            try:
                unidade = Unidade.objects.get(id=unidade_id)
                unidade.nome = nome_unidade
                if regional_id:
                    unidade.regional_id = regional_id
                unidade.save()
                return JsonResponse({'status': 'success', 'message': 'Unidade atualizada com sucesso'})
            except Unidade.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Unidade não encontrada'}, status=404)
            except Regional.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Regional não encontrada'}, status=404)
        else:
            # Cria uma nova unidade
            try:
                if regional_id is None or not Regional.objects.filter(id=regional_id).exists():
                    return JsonResponse({'status': 'error', 'message': 'Regional fornecida não existe'}, status=400)
                if Unidade.objects.filter(nome=nome_unidade, regional_id=regional_id).exists():
                    return JsonResponse({'status': 'error', 'message': 'Uma unidade com esse nome já existe nesta regional'}, status=400)
                nova_unidade = Unidade(nome=nome_unidade, regional_id=regional_id)
                nova_unidade.save()
                return JsonResponse({'status': 'success', 'message': 'Unidade cadastrada com sucesso'})
            except IntegrityError as e:
                return JsonResponse({'status': 'error', 'message': f'Erro de integridade ao salvar a unidade: {str(e)}'}, status=500)
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': f'Erro ao cadastrar unidade: {str(e)}'}, status=500)
    elif request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            unidade_id = data.get('id')
            unidade = Unidade.objects.get(id=unidade_id)
            unidade.delete()
            return HttpResponse(status=204)
        except Unidade.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Unidade não encontrada'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Erro ao excluir unidade: {str(e)}'}, status=500)
    elif request.method == 'GET':
        if 'regionais' in request.GET:
            regionais = Regional.objects.all().values('id', 'nome')
            return JsonResponse(list(regionais), safe=False)
        else:
            unidades = Unidade.objects.select_related('regional').all().values(
                'id', 'nome', 'regional__nome'
            )
            return JsonResponse(list(unidades), safe=False)
    else:
        return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)

def get_tipo_documentos(request):
    tipos_documentos = TipoDocumento.objects.all().select_related('grupo_documento').order_by('codigo')

    data = []
    for tipo in tipos_documentos:
        data.append({
            'tipo_documento_id': tipo.id,
            'codigo': tipo.codigo,
            'nome': tipo.nome,
            'grupo_documento': tipo.grupo_documento.nome if tipo.grupo_documento else 'N/A',
            'pcd': tipo.pcd,
            'obrigatorio': tipo.obrigatorio,
            'valor_legal': tipo.valor_legal,
            'verifica_assinatura': tipo.verifica_assinatura,
            'auditoria': tipo.auditoria,
            'validade': tipo.validade,
            'tipo_validade': tipo.tipo_validade,
            'exibe_relatorio': tipo.exibe_relatorio,
            'lista_situacao': tipo.lista_situacao,
            'prioridade': tipo.prioridade,
            'hiperlink_documento_id': tipo.hiperlink_documento.id if tipo.hiperlink_documento else 'N/A'
        })

    return JsonResponse(data, safe=False)

def get_hyperlinkpdfs(request):
    hyperlinkpdfs = Hyperlinkpdf.objects.select_related('colaborador', 'documento').all()

    data = []
    for doc in hyperlinkpdfs:
        data.append({
            'documento_nome': doc.documento.nome if doc.documento else 'Documento não especificado',
            'colaborador_nome': doc.colaborador.nome if doc.colaborador else 'N/A',
            'colaborador_id': doc.colaborador.id if doc.colaborador else 'N/A',
            'caminho': doc.caminho,
            'cpf': doc.cpf,
            'matricula': doc.matricula,
            'documento_codigo': doc.documento.codigo if doc.documento else 'N/A',
            'colaborador_status': doc.colaborador.status if doc.colaborador else 'N/A'
        })

    return JsonResponse(data, safe=False)
@csrf_exempt
def cadastrar_tipodocumento(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Se os dados recebidos contiverem uma chave "excluir", indica que é uma solicitação de exclusão
            if 'excluir' in data:
                tipo_documento_id = data.get('id')
                tipo_documento = TipoDocumento.objects.get(id=tipo_documento_id)
                tipo_documento.delete()
                return HttpResponse(status=204)  # Resposta de sucesso sem conteúdo
            else:
                # Verificar se é uma solicitação de edição
                if 'id' in data:
                    tipo_documento_id = data.get('id')
                    tipo_documento = TipoDocumento.objects.get(id=tipo_documento_id)

                    # Restante do código para editar o tipo de documento

                    # Atualizar os campos do tipo de documento com os novos valores
                    tipo_documento.codigo = data.get('codigo')
                    tipo_documento.nome = data.get('nome')
                    tipo_documento.grupo_documento_id = data.get('grupo_id')
                    tipo_documento.pcd = sim_nao_to_boolean(data.get('pcd'))
                    tipo_documento.valor_legal = sim_nao_to_boolean(data.get('valor_legal'))
                    tipo_documento.verifica_assinatura = sim_nao_to_boolean(data.get('verifica_assinatura'))
                    tipo_documento.auditoria = data.get('auditoria')
                    tipo_documento.validade = data.get('validade')
                    tipo_documento.tipo_validade = data.get('tipo_validade')
                    tipo_documento.exibe_relatorio = sim_nao_to_boolean(data.get('exibe_relatorio'))
                    tipo_documento.lista_situacao = data.get('lista_situacao')
                    tipo_documento.prioridade = data.get('prioridade')
                    tipo_documento.save()

                    return JsonResponse({'status': 'success', 'message': 'Tipo de documento editado com sucesso'})
                else:
                    # Restante do código para criar um tipo de documento
                    # Função para converter valores "sim" e "nao" em True e False
                    def sim_nao_to_boolean(value):
                        return value.lower() == 'sim'

                    codigo = data.get('codigo')
                    nome = data.get('nome')
                    grupo_id = data.get('grupo_id')
                    pcd = sim_nao_to_boolean(data.get('pcd'))
                    valor_legal = sim_nao_to_boolean(data.get('valor_legal'))
                    verifica_assinatura = sim_nao_to_boolean(data.get('verifica_assinatura'))
                    auditoria = data.get('auditoria')
                    validade = data.get('validade')
                    tipo_validade = data.get('tipo_validade')
                    exibe_relatorio = sim_nao_to_boolean(data.get('exibe_relatorio'))
                    lista_situacao = data.get('lista_situacao')
                    prioridade = data.get('prioridade')
                    cargos_selecionados = data.get('cargos_selecionados')

                    tipo_documento = TipoDocumento.objects.create(
                        codigo=codigo,
                        nome=nome,
                        grupo_documento_id=grupo_id,
                        pcd=pcd,
                        valor_legal=valor_legal,
                        verifica_assinatura=verifica_assinatura,
                        auditoria=auditoria,
                        validade=validade,
                        tipo_validade=tipo_validade,
                        exibe_relatorio=exibe_relatorio,
                        lista_situacao=lista_situacao,
                        prioridade=prioridade
                    )

                    # Adicionar os cargos selecionados ao TipoDocumento
                    for cargo_id in cargos_selecionados:
                        cargo = Cargo.objects.get(id=int(cargo_id))
                        tipo_documento.cargo = cargo
                        tipo_documento.obrigatorio = True
                        tipo_documento.save()

                        # Construir URL completa para inserir_tipodocumento_cargo
                        url_cargo = request.build_absolute_uri(reverse('inserir_tipodocumento_cargo'))

                        # Enviar IDs para inserir_tipodocumento_cargo
                        response_cargo = requests.post(
                            url_cargo,
                            data={'cargo_id': cargo_id, 'tipodocumento_id': tipo_documento.id}
                        )


                    # Adicione os 'IDs' dos cargos selecionados aos dados enviados na solicitação POST
                    url_colaborador = request.build_absolute_uri(reverse('inserir_tipodocumento_colaborador'))
                    for cargo_id in cargos_selecionados:
                        response_colaborador = requests.post(
                            url_colaborador,
                            data={'tipodocumento_id': tipo_documento.id, 'cargo_id': cargo_id}
                        )

                    return JsonResponse({'status': 'success', 'message': 'Tipo de documento criado com sucesso'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    elif request.method == 'GET':
        # Se a solicitação for do tipo GET, retornar os tipos de documento existentes
        tipos_documento = TipoDocumento.objects.all().order_by('codigo')
        data = [{
            'id': tipo.id,
            'codigo': tipo.codigo,
            'grupo_documento': tipo.grupo_documento.nome if tipo.grupo_documento else '',
            'nome': tipo.nome,
            'obrigatorio': tipo.obrigatorio,
            'valor_legal': tipo.valor_legal,
            'validade': tipo.validade,
            'tipo_validade': tipo.tipo_validade,
            'verifica_assinatura': tipo.verifica_assinatura,
            'exibe_relatorio': tipo.exibe_relatorio,
            'lista_situacao': tipo.lista_situacao
        } for tipo in tipos_documento]
        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)


@csrf_exempt
def inserir_tipodocumento_cargo(request):
    if request.method == 'POST':
        cargo_id = request.POST.get('cargo_id')
        tipodocumento_id = request.POST.get('tipodocumento_id')

        try:
            cargo = Cargo.objects.get(pk=cargo_id)
            tipodocumento = TipoDocumento.objects.get(pk=tipodocumento_id)

            # Verifica se já existe uma relação com esses IDs
            if TipoDocumentoCargo.objects.filter(cargo=cargo, tipo_documento=tipodocumento).exists():
                return JsonResponse({'message': 'Essa relação já existe.'}, status=400)

            # Corrigindo o problema aqui:
            nova_relacao = TipoDocumentoCargo(cargo=cargo, tipo_documento=tipodocumento)
            nova_relacao.save()

            return JsonResponse({'message': 'Relação inserida com sucesso.'}, status=201)
        except Cargo.DoesNotExist:
            return JsonResponse({'message': 'Cargo não encontrado.'}, status=404)
        except TipoDocumento.DoesNotExist:
            return JsonResponse({'message': 'Tipo de documento não encontrado.'}, status=404)
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)

    return JsonResponse({'message': 'Método não permitido.'}, status=405)

@csrf_exempt
def inserir_tipodocumento_colaborador(request):
    if request.method == 'POST':
        tipodocumento_id = request.POST.get('tipodocumento_id')
        cargo_id = request.POST.get('cargo_id')

        try:
            tipodocumento = TipoDocumento.objects.get(pk=tipodocumento_id)
            cargo = Cargo.objects.get(pk=cargo_id)

            # Buscar colaboradores com o mesmo cargo
            colaboradores = Colaborador.objects.filter(cargo=cargo)

            # Salvar relação entre tipo de documento e colaborador
            for colaborador in colaboradores:
                colaborador_tipodocumento = ColaboradorTipoDocumento.objects.create(
                    tipo_documento=tipodocumento,
                    colaborador=colaborador
                )
                colaborador_tipodocumento.save()

            return JsonResponse({'message': 'Relações inseridas com sucesso.'}, status=201)
        except TipoDocumento.DoesNotExist:
            return JsonResponse({'message': 'Tipo de documento não encontrado.'}, status=404)
        except Cargo.DoesNotExist:
            return JsonResponse({'message': 'Cargo não encontrado.'}, status=404)
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)

    return JsonResponse({'message': 'Método não permitido.'}, status=405)


@csrf_exempt
def cadastrar_grupo_documento(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        grupo_documento_id = data.get('id')
        if grupo_documento_id:
            # Verifica se a solicitação é para editar ou excluir um grupo de documento
            try:
                grupo_documento = get_object_or_404(GrupoDocumento, pk=grupo_documento_id)
                if 'excluir' in data and data['excluir']:
                    grupo_documento.delete()
                    return JsonResponse({'status': 'success', 'message': 'Grupo de documento excluído com sucesso'})
                else:
                    # Atualiza apenas os campos de interesse (nome e código)
                    grupo_documento.nome = data.get('nome', grupo_documento.nome)
                    grupo_documento.codigo = data.get('codigo', grupo_documento.codigo)
                    grupo_documento.save()
                    return JsonResponse({'status': 'success', 'message': 'Grupo de documento editado com sucesso'})
            except Exception as e:
                # print("Erro ao editar/excluir grupo de documento:", e)  # Adicionando log para o erro
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        else:
            # Adicionar um novo grupo de documento
            nome = data.get('nome')
            codigo = data.get('codigo')
            area_id = data.get('area_id')  # Obtendo o campo 'area_id'

            if not nome or not codigo or not area_id:
                return JsonResponse({'status': 'error', 'message': 'Nome, código e área são obrigatórios'}, status=400)
            try:
                novo_grupo_documento = GrupoDocumento.objects.create(nome=nome, codigo=codigo, area_id=area_id)
                return JsonResponse({'status': 'success', 'message': 'Grupo de documento criado com sucesso'})
            except Exception as e:
               #  print("Erro ao criar novo grupo de documento:", e)  # Adicionando log para o erro
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    elif request.method == 'GET':
        # Consultando todos os grupos de documentos no banco de dados
        # Correto uso do order_by aqui para ordenar os resultados quando todos os objetos estão sendo listados
        grupo_documentos = GrupoDocumento.objects.all().order_by('codigo').values('id', 'nome', 'codigo', 'area_id')
        grupo_documentos_list = list(grupo_documentos)
        return JsonResponse({'grupo_documentos': grupo_documentos_list})
    else:
        return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)


@csrf_exempt
def cadastrar_area(request):

    if request.method == 'POST':
        try:
            data = json.loads(request.body)

        except json.JSONDecodeError as e:

            return JsonResponse({'status': 'error', 'message': 'Dados inválidos'}, status=400)

        area_id = data.get('id')
        if area_id:
            try:
                area = get_object_or_404(Area, pk=area_id)
                if 'excluir' in data and data['excluir']:
                    area.delete()
                    return JsonResponse({'status': 'success', 'message': 'Área excluída com sucesso'})
                else:
                    area.codigo = data.get('codigo', area.codigo)
                    area.nome = data.get('nome', area.nome)
                    area.save()
                    return JsonResponse({'status': 'success', 'message': 'Área editada com sucesso'})
            except Exception as e:

                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        else:
            codigo = data.get('codigo')
            nome = data.get('nome')
            if not codigo or not nome:
                return JsonResponse({'status': 'error', 'message': 'Código e nome são obrigatórios'}, status=400)
            try:
                nova_area = Area.objects.create(codigo=codigo, nome=nome)
                return JsonResponse({'status': 'success', 'message': 'Área criada com sucesso'})
            except Exception as e:

                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    elif request.method == 'GET':
        areas = Area.objects.all().values('id', 'codigo', 'nome')
        areas_list = list(areas)
        return JsonResponse({'areas': areas_list})
    else:

        return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)


class ImportarDadosView(View):
    template_name = 'documento/import_xlsx.html'

    def get(self, request):
        form = ImportarDadosForm()  # Cria uma instância do formulário
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = ImportarDadosForm(request.POST, request.FILES)
        if form.is_valid():
            arquivo_csv = form.cleaned_data.get('arquivo_csv')
            sucesso, mensagem = importar_dados(arquivo_csv)
            if sucesso:
                messages.success(request, "Dados importados com sucesso.")
                # Considerar um redirecionamento após o sucesso para evitar reenvio do formulário
                # return redirect('documento/import_xlsx.html')
            else:
                messages.error(request, mensagem)
        else:
            messages.error(request, "Erro no formulário.")

        # Sempre retorne o formulário no contexto, independente se é uma submissão válida ou não
        return render(request, self.template_name, {'form': form})

def importar_usuarios(request):
    if request.method == 'POST':
        form = ImportarUsuariosForm(request.POST, request.FILES)
        if form.is_valid():
            arquivo_excel = request.FILES['arquivo_excel']
            try:
                df = pd.read_excel(arquivo_excel, engine='openpyxl')

                for index, row in df.iterrows():
                    senha_aleatoria = secrets.token_urlsafe(12)  # Gera senha aleatória
                    # Crie um objeto ImportUsuarioXLSX com os dados do DataFrame
                    ImportUsuarioXLSX.objects.create(
                        nome=row['usuario'],
                        login=row['Login'],
                        regional=row['Regional'],
                        unidade=row['Unidade'],
                        ativo=row['Ativo'],
                        senha=senha_aleatoria,
                    )

                messages.success(request, 'Usuários importados com sucesso.')
            except Exception as e:
                messages.error(request, f'Ocorreu um erro ao importar os usuários: {str(e)}')
            return redirect('importar_usuarios')
    else:
        form = ImportarUsuariosForm()

    return render(request, 'documento/import_usuario.html', {'form': form})


def criar_funcionario(request):
    form = PesquisaFuncionarioForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('documento/configuracao.html')


def lista_funcionarios(request):
    funcionarios = Colaborador.objects.all()
    return render(request, 'documento/configuracao.html', {'funcionarios': funcionarios})


# ******* 'Login', autenticação com Banco de dados, Logut e criação de 'login' ***********

@method_decorator(csrf_protect, name='dispatch')
class LoginView(View):
    def get(self, request):
        return render(request, 'documento/tela_login.html')

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            return JsonResponse({'error': 'Faltam credenciais'}, status=400)

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')  # Redireciona para o dashboard após login bem-sucedido
        else:
            return render(request, 'documento/tela_login.html', {'error': 'Credenciais inválidas'})

@login_required
def dashboard(request):
    return render(request, 'documento/dashboard.html')


class AuthenticationViews(View):
    def forgot_password(request):
        if request.method == 'POST':
            form = PasswordResetForm(request.POST)
            if form.is_valid():
                email = form.cleaned_data['email']
                form.save(
                    request=request,
                    from_email='from@example.com',
                    email_template_name='documento/tela_login.html',
                    subject_template_name='documento/password_reset_subject.txt',
                    html_email_template_name='documento/password_reset_email.html',
                )
                return redirect('password_reset_done')
        else:
            form = PasswordResetForm()
        return render(request, 'documento/tela_login.html', {'form': form})

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'documento/tela_login.html'


class CustomLogoutView(View):
    def get(self, request, *args, **kwargs):
        # logger.info('GET request received for CustomLogoutView')
        # Realize o logout do usuário (se necessário)
        # logout(request)  # Se desejar realizar o logout

        # Redirecione o usuário para a tela de login
        return redirect('documento/tela_login.html')  # Corrigido para usar o nome da URL

    def post(self, request, *args, **kwargs):
        # logger.info('POST request received for CustomLogoutView')
        # Realize o logout do usuário (se necessário)
        # logout(request)  # Se desejar realizar o logout

        # Redirecione o usuário para a tela de login
        return redirect('documento/tela_login.html')  # Corrigido para usar o nome da URL


class CheckUserLoggedOutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.session.get('user_logged_out'):
            # Se o usuário tentar acessar uma página protegida após ter saído, redirecione para o 'login'
            del request.session['user_logged_out']  # Remova o sinalizador
            return redirect(reverse('login'))

        response = self.get_response(request)
        return response


# User = get_user_model()

@method_decorator(csrf_exempt, name='dispatch')
class GerenciarUsuarioView(View):
    def post(self, request):
        data = loads(request.body)
        user_id = data.get('id')

        if 'excluir' in data and user_id:
            try:
                usuario = Usuario.objects.get(id=user_id)
                usuario.delete()
                return JsonResponse({'status': 'success', 'message': 'Usuário excluído com sucesso'})
            except Usuario.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Usuário não encontrado'}, status=404)

        username = data.get('username')
        first_name = data.get('first_name')
        password = data.get('password')
        is_superuser = data.get('is_superuser', True)
        is_active = data.get('is_active', False)

        if user_id:
            try:
                usuario = Usuario.objects.get(id=user_id)
                usuario.username = username
                usuario.first_name = first_name
                usuario.is_active = is_active
                if password:
                    usuario.set_password(password)
                usuario.is_superuser = is_superuser
                usuario.save()
                return JsonResponse({'status': 'success', 'message': 'Usuário atualizado com sucesso'})
            except Usuario.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Usuário não encontrado'}, status=404)
        else:
            if Usuario.objects.filter(username=username).exists():
                return JsonResponse({'status': 'error', 'message': 'Este nome de usuário já está em uso'}, status=400)
            usuario = Usuario.objects.create_user(username=username, first_name=first_name, password=password, is_superuser=is_superuser)
            return JsonResponse({'status': 'success', 'message': 'Usuário criado com sucesso'})

    def get(self, request):
        usuarios = Usuario.objects.all().values('id', 'username', 'first_name', 'is_superuser')
        return JsonResponse(list(usuarios), safe=False)

    def dispatch(self, request, *args, **kwargs):
        if request.method not in ['GET', 'POST']:
            return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)
        return super().dispatch(request, *args, **kwargs)

# Constantes para menus
MENUS = [
    {'nome': 'Dossiê', 'url': 'dossie'},
    {'nome': 'Relatórios', 'url': 'relatorios'},
    {'nome': 'Configuração', 'url': 'configuracao'},
    {'nome': 'Dashboard', 'url': 'dashboard'},
]

@require_http_methods(["POST"])
def criar_grupo_permissoes(request):
    data = json.loads(request.body)
    nome_grupo = data.get('nome_grupo')
    codigo_grupo = data.get('codigo_grupo')  # Certifique-se de usar este campo conforme necessário
    permissoes_ids = data.get('permissoes_ids', [])

    grupo, created = Group.objects.get_or_create(name=nome_grupo)
    if created:
        grupo.permissions.set(Permission.objects.filter(id__in=permissoes_ids))
        grupo.save()
        return JsonResponse({'status': 'success', 'message': 'Grupo criado com sucesso!'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Grupo já existe'})

def listar_empresas(request):
    empresas = list(Empresa.objects.values('id', 'nome'))
    return JsonResponse(empresas, safe=False)

def listar_regionais(request):
    regionais = list(Regional.objects.values('id', 'nome'))
    return JsonResponse(regionais, safe=False)

def listar_unidades(request):
    unidades = list(Unidade.objects.values('id', 'nome'))
    return JsonResponse(unidades, safe=False)

def listar_permissoes(request):
    permissoes = list(Permission.objects.all().values('id', 'name'))
    return JsonResponse(permissoes, safe=False)


