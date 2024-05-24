# queries.py
import csv
import codecs
from datetime import datetime, timezone, timedelta
from django.db import transaction
from dateutil.relativedelta import relativedelta
from documento.models import CartaoPontoInexistente, DocumentoVencido, ColaboradorTipoDocumento
from documento.utils import validar_dados_csv, validar_cabecalho_csv
from .models import Hyperlinkpdf, DocumentoPendente, TipoDocumento, PendenteASO, HyperlinkDadosNull
from django.db.models import Count
from django.utils import timezone
from .models import Empresa, Regional, Unidade, Cargo, Situacao, Colaborador
from django.db.models import OuterRef, Subquery
from django.db.models import Q


def importar_dados(arquivo_csv):
    try:
        leitor_csv = csv.DictReader(codecs.iterdecode(arquivo_csv, 'utf-8-sig'), delimiter=';')
        if not leitor_csv.fieldnames or not validar_cabecalho_csv(leitor_csv.fieldnames):
            return False, "Problema no cabeçalho do CSV"

        empresas_encontradas = set()
        bloco = []  # Lista para armazenar linhas a serem processadas
        for i, linha in enumerate(leitor_csv, start=1):
            if not validar_dados_csv(linha, leitor_csv.fieldnames):
                print(f"Linha {i} inválida e será ignorada.")
                continue

            empresas_encontradas.add(linha['EMPRESA'])

            bloco.append(linha)
            if len(bloco) == 300:  # Processa em blocos de 300
                processar_bloco(bloco, i)
                bloco = []  # Reseta o bloco após o processamento

        if bloco:  # Processa qualquer linha restante
            processar_bloco(bloco, i)


        return True, "Dados importados com sucesso."
    except Exception as e:
        return False, f"Erro ao importar dados: {str(e)}"

def processar_bloco(bloco, start_index):
    with transaction.atomic():  # Inicia uma transação
        unique_keys = set()  # Para armazenar chaves únicas processadas

        for index, linha in enumerate(bloco, start=start_index):
            sid = transaction.savepoint()  # Cria um ponto de salvamento

            # Construir chave única com base nos campos que definem a unicidade
            key = (
                linha['EMPRESA'], linha['REGIONAL'], linha['UNIDADE'], linha['CARGO'],
                linha['STATUS'], linha['CPF'], linha['MATRICULA'], linha['ADMISSAO'], linha['DESLIGAMENTO']
            )
            if key in unique_keys:

                continue  # Ignora esta linha duplicada
            unique_keys.add(key)

            try:


                empresa, created_empresa = Empresa.objects.get_or_create(nome=linha['EMPRESA'])
                # logger.info(f"Empresa {'criada' if created_empresa else 'recuperada'}: {empresa.nome} (ID: {empresa.id})")

                regional, created_regional = Regional.objects.get_or_create(nome=linha['REGIONAL'], empresa=empresa)
                # logger.info(f"Regional {'criada' if created_regional else 'recuperada'}: {regional.nome} (ID: {regional.id}, Empresa ID: {regional.empresa.id})")

                unidade, created_unidade = Unidade.objects.get_or_create(nome=linha['UNIDADE'], regional=regional)
                # logger.info(f"Unidade {'criada' if created_unidade else 'recuperada'}: {unidade.nome} (ID: {unidade.id}, Regional ID: {unidade.regional.id})")

                cargo, created_cargo = Cargo.objects.get_or_create(nome=linha['CARGO'], unidade=unidade)
                # logger.info(f"Cargo {'criado' if created_cargo else 'recuperado'}: {cargo.nome} (ID: {cargo.id}, Unidade ID: {cargo.unidade.id})")

                situacao, created_situacao = Situacao.objects.get_or_create(nome=linha['STATUS'], cargo=cargo)
                # logger.info(f"Situacao {'criada' if created_situacao else 'recuperada'}: {situacao.nome} (ID: {situacao.id}, Cargo ID: {situacao.cargo.id})")

                try:
                    colaborador = Colaborador.objects.get(unidade=unidade, matricula=linha['MATRICULA'])
                    # Se o colaborador existir, atualiza as informações
                    colaborador.empresa = empresa
                    colaborador.nome = linha['NOME']
                    colaborador.cpf = linha['CPF']
                    colaborador.cargo = cargo
                    colaborador.status = situacao
                    colaborador.admissao = converter_data(linha['ADMISSAO'], index)
                    colaborador.desligamento = converter_data(linha['DESLIGAMENTO'], index)
                    colaborador.email = linha['EMAIL']
                    colaborador.pcd = linha.get('PCD', 'Não')
                    colaborador.save()
                    # logger.info(f"Atualizado: {index} - {colaborador.matricula} (Empresa ID: {colaborador.empresa.id})")
                except Colaborador.DoesNotExist:
                    # Se o colaborador não existir, cria um novo
                    colaborador = Colaborador.objects.create(
                        empresa=empresa,
                        unidade=unidade,
                        matricula=linha['MATRICULA'],
                        nome=linha['NOME'],
                        cpf=linha['CPF'],
                        cargo=cargo,
                        status=situacao,
                        admissao=converter_data(linha['ADMISSAO'], index),
                        desligamento=converter_data(linha['DESLIGAMENTO'], index),
                        email=linha['EMAIL'],
                        pcd=linha.get('PCD', 'Não')
                    )
                    # logger.info(f"Criado: {index} - {colaborador.matricula} (Empresa ID: {colaborador.empresa.id})")

            except Exception as e:
                print(f"Erro ao processar a linha {index}: {e}")
                transaction.savepoint_rollback(sid)  # Reverte para o ponto de salvamento
            else:
                transaction.savepoint_commit(sid)  # Commit do ponto de salvamento se tudo correu bem

def converter_data(data_str, linha):
    import re
    from datetime import datetime
    if data_str.strip():
        data_limpa = re.sub(r"[^0-9/]", "", data_str.strip())
        try:
            return datetime.strptime(data_limpa, '%d/%m/%Y').date()
        except ValueError:
            print(f"Data inválida na linha {linha}: {data_limpa}")
            return None


# import logging

# logger = logging.getLogger('documento')


class ObterDocumentosPendentes:
    @staticmethod
    def calcular_documentos_pendentes():
        # Buscar todos os colaboradores ativos e inativos
        todos_colaboradores = Colaborador.objects.filter(status__nome__in=['Ativo', 'Inativo'])

        # Buscar tipos de documentos obrigatórios
        tipos_de_documentos_obrigatorios = TipoDocumento.objects.filter(obrigatorio=True)

        documentos_a_atualizar = []

        # Verificar para cada colaborador e cada tipo de documento obrigatório
        for colaborador in todos_colaboradores:
            for tipo_documento in tipos_de_documentos_obrigatorios:
                # Verificar se o documento existe no Hyperlinkpdf
                documento_existe = Hyperlinkpdf.objects.filter(
                    colaborador=colaborador,
                    documento=tipo_documento
                ).exists()

                if documento_existe:
                    # Se o documento existir, remova a pendência se existir
                    # logger.debug(f"Documento existente encontrado para {colaborador.nome} - {tipo_documento.nome}. Removendo pendência se existir.")
                    DocumentoPendente.objects.filter(
                        nome=colaborador,
                        tipo_documento=tipo_documento
                    ).delete()
                else:
                    # Se o documento não existir, crie ou atualize a pendência
                    documento_pendente, created = DocumentoPendente.objects.get_or_create(
                        nome=colaborador,
                        tipo_documento=tipo_documento,
                        defaults={
                            'empresa': colaborador.empresa,
                            'regional': colaborador.regional,
                            'unidade': colaborador.unidade,
                            'matricula': colaborador.matricula,
                            'cpf': colaborador.cpf,
                            'cargo': colaborador.cargo,
                            'admissao': colaborador.admissao,
                            'desligamento': colaborador.desligamento,
                            'situacao': colaborador.status.nome,
                            'obrigatorio': tipo_documento.obrigatorio
                        }
                    )
                    if not created:
                        documentos_a_atualizar.append(documento_pendente)

    @staticmethod
    def atualizar_tabela_documentos_pendentes():
        ObterDocumentosPendentes.calcular_documentos_pendentes()


"""
class ObterDocumentosPendentes:
    @staticmethod
    def calcular_documentos_pendentes():
        # Buscar colaboradores ativos
        colaboradores_ativos = Colaborador.objects.filter(status__nome='Ativo')

        # Buscar colaboradores inativos por status
        colaboradores_inativos = Colaborador.objects.filter(status__nome='Inativo')

        # Combinar ambos os QuerySets
        todos_colaboradores = colaboradores_ativos | colaboradores_inativos

        # Buscar tipos de documentos obrigatórios
        tipos_de_documentos_obrigatorios = TipoDocumento.objects.filter(obrigatorio=True)
        documentos_a_atualizar = []

        for colaborador in todos_colaboradores:
            for tipo_documento in tipos_de_documentos_obrigatorios:
                documento_pendente, created = DocumentoPendente.objects.get_or_create(
                    nome=colaborador,
                    tipo_documento=tipo_documento,
                    defaults={
                        'empresa': colaborador.empresa,
                        'regional': colaborador.regional,
                        'unidade': colaborador.unidade,
                        'matricula': colaborador.matricula,
                        'cpf': colaborador.cpf,
                        'cargo': colaborador.cargo,
                        'admissao': colaborador.admissao,
                        'desligamento': colaborador.desligamento,
                        'situacao': colaborador.status.nome,  # Usar status.nome em vez de situacao
                        'obrigatorio': tipo_documento.obrigatorio
                    }
                )
                if not created:
                    documentos_a_atualizar.append(documento_pendente)

    @staticmethod
    def atualizar_tabela_documentos_pendentes():
        ObterDocumentosPendentes.calcular_documentos_pendentes()
"""
class ServicoPendenteASO:
    @staticmethod
    def inicializar_pendencias():
        colaboradores = Colaborador.objects.all()
        tipos_de_documentos_aso = TipoDocumento.objects.filter(codigo__in=[401, 402, 403])

        for colaborador in colaboradores:
            for tipo_documento in tipos_de_documentos_aso:
                documentos = Hyperlinkpdf.objects.filter(colaborador_id=colaborador.id, documento_id=tipo_documento.id)
                documento_existe = documentos.exists()

                PendenteASO.objects.update_or_create(
                    nome=colaborador,
                    tipo_aso=tipo_documento,
                    defaults={
                        'empresa': colaborador.empresa,
                        'regional': colaborador.regional,
                        'unidade': colaborador.unidade,
                        'matricula': colaborador.matricula,
                        'cpf': colaborador.cpf,
                        'cargo': colaborador.cargo,
                        'admissao': colaborador.admissao,
                        'desligamento': colaborador.desligamento,
                        'status': colaborador.status,
                        'aso_admissional_existente': True if tipo_documento.nome == "ASO Admissional" and documento_existe else False,
                        'aso_demissional_existente': True if tipo_documento.nome == "ASO Demissional" and documento_existe else False,
                        'aso_periodico_existente': True if tipo_documento.nome == "ASO Periódico/ Retorno ao Trabalho" and documento_existe else False,
                    }
                )

    @staticmethod
    def atualizar_pendencias():
        pendencias = PendenteASO.objects.all()
        for pendencia in pendencias:
            documentos = Hyperlinkpdf.objects.filter(colaborador_id=pendencia.nome.id, documento_id=pendencia.tipo_aso.id)
            documento_existe = documentos.exists()

            if documento_existe:
                # Remove a pendência se o documento existir
                pendencia.delete()
            else:
                # Atualiza campos booleanos de acordo com a inexistência dos documentos
                pendencia.aso_admissional_existente = False
                pendencia.aso_demissional_existente = False
                pendencia.aso_periodico_existente = False

                pendencia.save()

"""class ServicoPendenteASO:
    @staticmethod
    def inicializar_pendencias():
        colaboradores = Colaborador.objects.all()
        # Filtra apenas os tipos de documentos que correspondem aos IDs dos ASOs
        tipos_de_documentos_aso = TipoDocumento.objects.filter(codigo__in=[401, 402, 403])


        for colaborador in colaboradores:
            for tipo_documento in tipos_de_documentos_aso:
                documentos = Hyperlinkpdf.objects.filter(colaborador_id=colaborador.id, documento_id=tipo_documento.id)

                documento_existe = documentos.exists()

                pendencia, created = PendenteASO.objects.update_or_create(
                    nome=colaborador,
                    tipo_aso=tipo_documento,
                    defaults={
                        'empresa': colaborador.empresa,
                        'regional': colaborador.regional,
                        'unidade': colaborador.unidade,
                        'matricula': colaborador.matricula,
                        'cpf': colaborador.cpf,
                        'cargo': colaborador.cargo,
                        'admissao': colaborador.admissao,
                        'desligamento': colaborador.desligamento,
                        'status': colaborador.status,
                        'aso_admissional_existente': True if tipo_documento.nome == "ASO Admissional" and documento_existe else False,
                        'aso_demissional_existente': True if tipo_documento.nome == "ASO Demissional" and documento_existe else False,
                        'aso_periodico_existente': True if tipo_documento.nome == "ASO Periódico/ Retorno ao Trabalho" and documento_existe else False,
                    }
                )

    @staticmethod
    def atualizar_pendencias():
        pendencias = PendenteASO.objects.all()
        for pendencia in pendencias:
            documentos = Hyperlinkpdf.objects.filter(nome=pendencia.nome, tipo_documento=pendencia.tipo_aso)
            documento_existe = documentos.exists()
            # print(f'os tipos encontrados: {documentos}')
            # Adiciona um print para os ASOs demissionais encontrados
            if pendencia.tipo_aso.nome == "ASO Demissional" and documento_existe:
                print(f"ASO Demissional encontrado para {pendencia.nome} no Hyperlinkpdf.")

            # Atualiza campos booleanos de acordo com a existência dos documentos
            pendencia.aso_admissional_existente = True if pendencia.tipo_aso.nome == "ASO Admissional" and documento_existe else False
            pendencia.aso_demissional_existente = True if pendencia.tipo_aso.nome == "ASO Demissional" and documento_existe else False
            pendencia.aso_periodico_existente = True if pendencia.tipo_aso.nome == "ASO Periódico/ Retorno ao Trabalho" and documento_existe else False

            pendencia.save()"""

"""class ServicoPendenteASO:
    @staticmethod
    def inicializar_pendencias():

        colaboradores = Colaborador.objects.all()
        # Filtra apenas os tipos de documentos que correspondem aos IDs dos ASOs
        tipos_de_documentos_aso = TipoDocumento.objects.filter(codigo__in=[401, 402, 403])

        for colaborador in colaboradores:
            for tipo_documento in tipos_de_documentos_aso:
                documentos = Hyperlinkpdf.objects.filter(colaborador_id=colaborador.id, documento_id=tipo_documento.id)

                documento_existe = documentos.exists()

                pendencia, created = PendenteASO.objects.update_or_create(
                    nome=colaborador,
                    tipo_aso=tipo_documento,
                    defaults={
                        'empresa': colaborador.empresa,
                        'regional': colaborador.regional,
                        'unidade': colaborador.unidade,
                        'matricula': colaborador.matricula,
                        'cpf': colaborador.cpf,
                        'cargo': colaborador.cargo,
                        'admissao': colaborador.admissao,
                        'desligamento': colaborador.desligamento,
                        'status': colaborador.status,
                        'aso_admissional_existente': True if tipo_documento.nome == "ASO Admissional" and documento_existe else False,
                        'aso_demissional_existente': True if tipo_documento.nome == "ASO Demissional" and documento_existe else False,
                        'aso_periodico_existente': True if tipo_documento.nome == "ASO Periódico/ Retorno ao Trabalho" and documento_existe else False,
                    }
                )

    @staticmethod
    def atualizar_pendencias():
        pendencias = PendenteASO.objects.all()
        for pendencia in pendencias:
            documentos = Hyperlinkpdf.objects.filter(nome=pendencia.nome, tipo_documento=pendencia.tipo_aso)
            documento_existe = documentos.exists()

            # Atualiza campos booleanos de acordo com a existência dos documentos
            pendencia.aso_admissional_existente = True if pendencia.tipo_aso.nome == "ASO Admissional" and documento_existe else False
            pendencia.aso_demissional_existente = True if pendencia.tipo_aso.nome == "ASO Demissional" and documento_existe else False
            pendencia.aso_periodico_existente = True if pendencia.tipo_aso.nome == "ASO Periódico/ Retorno ao Trabalho" and documento_existe else False

            pendencia.save()"""


class CarregarASOAtivo:
    @staticmethod
    def calcular_porcentagens_aso_admissional():
        total_asos = PendenteASO.objects.filter(tipo_aso__codigo=401).count()
        if total_asos == 0:
            return {"Existente": "0%", "Pendente": "0%"}  # Evita divisão por zero

        asos_existentes = PendenteASO.objects.filter(tipo_aso__codigo=401, aso_admissional_existente=True).count()

        percentual_existente = (asos_existentes / total_asos) * 100
        percentual_pendente = 100 - percentual_existente


        return {
            "Existente": f"{percentual_existente:.1f}%",
            "Pendente": f"{percentual_pendente:.1f}%"
        }


class CarregarASOInativo:
    @staticmethod
    def calcular_porcentagens_aso_demissional():
        total_asos = PendenteASO.objects.filter(tipo_aso__codigo=402).count()
        if total_asos == 0:
            return {"Existente": "0%", "Pendente": "0%"}  # Evita divisão por zero

        asos_existentes = PendenteASO.objects.filter(tipo_aso__codigo=402, aso_demissional_existente=True).count()

      #  print(f"Total de ASOs Demissional: {total_asos}")
       # print(f"ASOs Demissional Existentes: {asos_existentes}")

        percentual_existente = (asos_existentes / total_asos) * 1000
        percentual_pendente = 100 - percentual_existente

        # Adicionando o print para mostrar o resultado do cálculo das porcentagens sem arredondamento
       # print(f"Percentual Existente DEMISSIONAL (sem arredondamento): {percentual_existente}")
       # print(f"Percentual Pendente DEMISSIONAL (sem arredondamento): {percentual_pendente}")

        # Adicionando o print para mostrar o resultado do cálculo das porcentagens com uma casa decimal
      #  print(f"Percentual Existente DEMISSIONAL (com arredondamento): {percentual_existente:.1f}%")
       # print(f"Percentual Pendente DEMISSIONAL (com arredondamento): {percentual_pendente:.1f}%")

        return {
            "Existente": f"{percentual_existente:.1f}%",
            "Pendente": f"{percentual_pendente:.1f}%"
        }


"""@staticmethod
def calcular_porcentagens_documentos_obrigatorios_ativos():
    total_tipos_obrigatorios = TipoDocumento.objects.filter(obrigatorio=True).count()
    documentos_existentes = Hyperlinkpdf.objects.filter(
        documento__obrigatorio=True,
        colaborador__status__nome='Ativo'  # Corrige para acessar o nome da situação
    ).distinct('documento').count()

    if total_tipos_obrigatorios == 0:
        return {"Existente": "0%", "Pendente": "0%"}  # Evita divisão por zero

    percentual_existente = (documentos_existentes / total_tipos_obrigatorios) * 100
    percentual_pendente = 100 - percentual_existente

    return {
        "Existente": f"{percentual_existente:.0f}%",
        "Pendente": f"{percentual_pendente:.0f}%"
    }"""


"""def calcular_porcentagens_documentos_obrigatorios_ativos():
    # Consulta para contar o total de documentos obrigatórios ativos por unidade
    total_documentos_por_unidade = (
        DocumentoPendente.objects
        .filter(obrigatorio=True, situacao="Ativo")
        .values('unidade__nome')
        .annotate(total_documentos=Count('id'))
        .order_by('unidade__nome')
    )

    # Consulta para contar o total de documentos pendentes por unidade
    documentos_pendentes_por_unidade = (
        DocumentoPendente.objects
        .filter(obrigatorio=True, situacao="Ativo")
        .values('unidade__nome')
        .annotate(total_pendentes=Count('id'))
        .order_by('unidade__nome')
    )

    # Consulta para contar o total de documentos existentes no Hyperlinkpdf por unidade
    documentos_existentes_por_unidade = (
        Hyperlinkpdf.objects
        .values('unidade__nome')
        .annotate(total_existentes=Count('id'))
        .order_by('unidade__nome')
    )

    # Cálculo das porcentagens de documentos pendentes
    porcentagens_por_unidade = []
    for total_doc in total_documentos_por_unidade:
        unidade_nome = total_doc['unidade__nome']
        total_documentos = total_doc['total_documentos']

        # Encontra o total de documentos pendentes para a unidade
        documentos_pendentes = next((item['total_pendentes'] for item in documentos_pendentes_por_unidade if
                                     item['unidade__nome'] == unidade_nome), 0)

        # Encontra o total de documentos existentes para a unidade
        documentos_existentes = next((item['total_existentes'] for item in documentos_existentes_por_unidade if
                                      item['unidade__nome'] == unidade_nome), 0)

        # Calcula a porcentagem de documentos pendentes
        total_obrigatorios_pendentes = total_documentos - documentos_existentes
        porcentagem_pendentes = (total_obrigatorios_pendentes / total_documentos) * 100 if total_documentos > 0 else 0

        porcentagens_por_unidade.append({
            'unidade': unidade_nome,
            'total_documentos': total_documentos,
            'documentos_pendentes': total_obrigatorios_pendentes,
            'porcentagem_pendentes': porcentagem_pendentes
        })

    return porcentagens_por_unidade"""


"""def calcular_porcentagens_documentos_obrigatorios_ativos():
    # Filtrar colaboradores na situação "Ativo"
    colaboradores_ativos_ids = Colaborador.objects.filter(status__nome='Ativo').values_list('id', flat=True)

    # Filtrar documentos obrigatórios dos colaboradores ativos
    documentos_obrigatorios_ids = DocumentoPendente.objects.filter(
        obrigatorio=True,
        nome_id__in=colaboradores_ativos_ids
    ).values_list('tipo_documento_id', flat=True)

    # Subquery para obter os códigos dos documentos obrigatórios
    tipo_documento_subquery = TipoDocumento.objects.filter(
        id=OuterRef('tipo_documento_id')
    ).values('codigo')[:1]

    # Consulta para contar o total de documentos obrigatórios para colaboradores ativos
    total_documentos = DocumentoPendente.objects.filter(
        obrigatorio=True,
        nome_id__in=colaboradores_ativos_ids
    ).count()

    # Consulta para contar o total de documentos existentes no Hyperlinkpdf
    total_documentos_existentes = Hyperlinkpdf.objects.filter(
        codigo_documento__in=Subquery(
            DocumentoPendente.objects.filter(
                obrigatorio=True,
                nome_id__in=colaboradores_ativos_ids
            ).annotate(
                tipo_documento_codigo=Subquery(tipo_documento_subquery)
            ).values('tipo_documento_codigo')
        )
    ).count()

    # Lista os documentos obrigatórios no Hyperlinkpdf para verificação
    documentos_obrigatorios_existentes = Hyperlinkpdf.objects.filter(
        codigo_documento__in=Subquery(
            DocumentoPendente.objects.filter(
                obrigatorio=True,
                nome_id__in=colaboradores_ativos_ids
            ).annotate(
                tipo_documento_codigo=Subquery(tipo_documento_subquery)
            ).values('tipo_documento_codigo')
        )
    ).values_list('codigo_documento', flat=True)

    # Calcula a quantidade de documentos pendentes
    total_documentos_pendentes = total_documentos - total_documentos_existentes

    # Calcula as porcentagens
    porcentagem_existente = (total_documentos_existentes / total_documentos) * 100 if total_documentos > 0 else 0
    porcentagem_pendente = (total_documentos_pendentes / total_documentos) * 100 if total_documentos > 0 else 0

    # Retorna um dicionário com as porcentagens
    return {
        'Existente': f"{porcentagem_existente:.2f}%",
        'Pendente': f"{porcentagem_pendente:.2f}%"
    }"""

from django.db.models import OuterRef, Subquery

def calcular_porcentagens_documentos_obrigatorios_ativos():
    # Filtrar colaboradores na situação "Ativo"
    colaboradores_ativos_ids = Colaborador.objects.filter(status__nome='Ativo').values_list('id', flat=True)

    # Filtrar documentos obrigatórios dos colaboradores ativos
    documentos_obrigatorios_ids = DocumentoPendente.objects.filter(
        obrigatorio=True,
        nome_id__in=colaboradores_ativos_ids
    ).values_list('tipo_documento_id', flat=True)

    # Subquery para obter os códigos dos documentos obrigatórios
    tipo_documento_subquery = TipoDocumento.objects.filter(
        id=OuterRef('tipo_documento_id')
    ).values('codigo')[:1]

    # Consulta para contar o total de documentos obrigatórios para colaboradores ativos
    total_documentos = DocumentoPendente.objects.filter(
        obrigatorio=True,
        nome_id__in=colaboradores_ativos_ids
    ).count()

    # Consulta para contar o total de documentos existentes no Hyperlinkpdf
    total_documentos_existentes = Hyperlinkpdf.objects.filter(
        codigo_documento__in=Subquery(
            DocumentoPendente.objects.filter(
                obrigatorio=True,
                nome_id__in=colaboradores_ativos_ids
            ).annotate(
                tipo_documento_codigo=Subquery(tipo_documento_subquery)
            ).values('tipo_documento_codigo')
        )
    ).count()

    # Calcula a quantidade de documentos pendentes
    total_documentos_pendentes = total_documentos_existentes - total_documentos

    # Calcula as porcentagens, garantindo que não haja divisões por zero
    porcentagem_existente = (total_documentos / total_documentos_existentes) * 100 if total_documentos > 0 else 0
    porcentagem_pendente = (total_documentos_pendentes / total_documentos) * 100 if total_documentos > 0 else 0

    # Retorna um dicionário com as porcentagens
    return {
        'Existente': f"{porcentagem_existente:.2f}%",
        'Pendente': f"{porcentagem_pendente:.2f}%"
    }

# Chamar a função e imprimir os resultados
resultados = calcular_porcentagens_documentos_obrigatorios_ativos()
print(resultados)




@staticmethod
def calcular_porcentagens_documentos_obrigatorios_inativos():
    # Filtrar colaboradores na situação "Inativo"
    colaboradores_inativos_ids = Colaborador.objects.filter(status__nome='Inativo').values_list('id', flat=True)

    # Filtrar documentos obrigatórios dos colaboradores inativos
    documentos_obrigatorios_ids = DocumentoPendente.objects.filter(
        obrigatorio=True,
        nome_id__in=colaboradores_inativos_ids
    ).values_list('tipo_documento_id', flat=True)

    # Subquery para obter os códigos dos documentos obrigatórios
    tipo_documento_subquery = TipoDocumento.objects.filter(
        id=OuterRef('tipo_documento_id')
    ).values('codigo')[:1]

    # Consulta para contar o total de documentos obrigatórios para colaboradores inativos
    total_documentos = DocumentoPendente.objects.filter(
        obrigatorio=True,
        nome_id__in=colaboradores_inativos_ids
    ).count()

    # Consulta para contar o total de documentos existentes no Hyperlinkpdf
    total_documentos_existentes = Hyperlinkpdf.objects.filter(
        codigo_documento__in=Subquery(
            DocumentoPendente.objects.filter(
                obrigatorio=True,
                nome_id__in=colaboradores_inativos_ids
            ).annotate(
                tipo_documento_codigo=Subquery(tipo_documento_subquery)
            ).values('tipo_documento_codigo')
        )
    ).count()

    # Lista os documentos obrigatórios no Hyperlinkpdf para verificação
    documentos_obrigatorios_existentes = Hyperlinkpdf.objects.filter(
        codigo_documento__in=Subquery(
            DocumentoPendente.objects.filter(
                obrigatorio=True,
                nome_id__in=colaboradores_inativos_ids
            ).annotate(
                tipo_documento_codigo=Subquery(tipo_documento_subquery)
            ).values('tipo_documento_codigo')
        )
    ).values_list('codigo_documento', flat=True)

    # Calcula a quantidade de documentos pendentes
    total_documentos_pendentes = total_documentos - total_documentos_existentes

    # Calcula as porcentagens
    porcentagem_existente = (total_documentos_existentes / total_documentos) * 100 if total_documentos > 0 else 0
    porcentagem_pendente = (total_documentos_pendentes / total_documentos) * 100 if total_documentos > 0 else 0

    # Retorna um dicionário com as porcentagens
    return {
        'Existente': f"{porcentagem_existente:.2f}%",
        'Pendente': f"{porcentagem_pendente:.2f}%"
    }

class ServicoPonto:
    @staticmethod
    def inicializar_pendencias():
        colaboradores = Colaborador.objects.all()
        tipos_de_documentos_ponto = TipoDocumento.objects.filter(codigo__in=[601])

        for colaborador in colaboradores:
            for tipo_documento in tipos_de_documentos_ponto:
                documento_existe = Hyperlinkpdf.objects.filter(colaborador_id=colaborador.id, documento_id=tipo_documento.id).exists()

                if documento_existe:
                    # Remove a pendência se o documento existir
                    CartaoPontoInexistente.objects.filter(colaborador=colaborador).delete()
                else:
                    # Cria ou atualiza a pendência se o documento não existir
                    CartaoPontoInexistente.objects.update_or_create(
                        colaborador=colaborador,
                        defaults={
                            'empresa': colaborador.empresa,
                            'regional': colaborador.regional,
                            'unidade': colaborador.unidade,
                            'status': colaborador.status,  # Assumindo que 'status' reflete o status do colaborador
                            'existente': documento_existe,  # Variável booleana indicando se o documento existe
                        }
                    )

    @staticmethod
    def atualizar_pendencias():
        pendencias = CartaoPontoInexistente.objects.all()
        for pendencia in pendencias:
            documento_existe = Hyperlinkpdf.objects.filter(colaborador_id=pendencia.colaborador.id, documento_id=601).exists()

            if documento_existe:
                # Remove a pendência se o documento existir
                pendencia.delete()
            else:
                # Atualiza o campo booleano 'existente' para False se o documento não existir
                pendencia.existente = False
                pendencia.save()



def calcular_porcentagens_ponto_ativos():
    # Conta total de colaboradores com pendências de ponto
    total_ponto = CartaoPontoInexistente.objects.filter(colaborador__status__nome='Ativo').count()

    # Conta quantos desses têm o documento de ponto existente
    documentos_existentes = CartaoPontoInexistente.objects.filter(
        colaborador__status__nome='Ativo',
        existente=True  # Considerando que 'existente' é o campo booleano que indica se o documento existe
    ).count()

    if total_ponto == 0:
        return {"Existente": "0%", "Pendente": "0%"}  # Evita divisão por zero

    percentual_existente = (documentos_existentes / total_ponto) * 100
    percentual_pendente = 100 - percentual_existente

    return {
        "Existente": f"{percentual_existente:.0f}%",
        "Pendente": f"{percentual_pendente:.0f}%"
    }

def calcular_porcentagens_ponto_inativos():
    # Conta total de colaboradores inativos com pendências de ponto
    total_ponto = CartaoPontoInexistente.objects.filter(colaborador__status__nome='Inativo').count()

    # Conta quantos desses têm o documento de ponto existente
    documentos_existentes = CartaoPontoInexistente.objects.filter(
        colaborador__status__nome='Inativo',
        existente=True  # Considerando que 'existente' é o campo booleano que indica se o documento existe
    ).count()

    if total_ponto == 0:
        return {"Existente": "0%", "Pendente": "0%"}  # Evita divisão por zero

    percentual_existente = (documentos_existentes / total_ponto) * 100
    percentual_pendente = 100 - percentual_existente

    return {
        "Existente": f"{percentual_existente:.0f}%",
        "Pendente": f"{percentual_pendente:.0f}%"
    }


def calcular_porcentagens_obrigatorios_unidade_ativos():
    # Conta total de tipos de documentos obrigatórios
    total_tipos_obrigatorios = TipoDocumento.objects.filter(obrigatorio=True).count()

    if total_tipos_obrigatorios == 0:
        return []

    # Conta total de documentos obrigatórios por unidade para colaboradores ativos
    documentos_por_unidade = ColaboradorTipoDocumento.objects.filter(
        colaborador__status__nome='Ativo',
        tipo_documento__obrigatorio=True
    ).values('colaborador__unidade__nome').annotate(
        total_colaboradores=Count('colaborador', distinct=True),
        documentos_existentes=Count('tipo_documento', distinct=True)
    ).order_by('colaborador__unidade__nome')

    porcentagens_por_unidade = []
    for item in documentos_por_unidade:
        unidade_nome = item['colaborador__unidade__nome']
        total_colaboradores = item['total_colaboradores']
        documentos_existentes = item['documentos_existentes']

        # Calcula as porcentagens baseado nos documentos existentes e total de tipos obrigatórios por colaborador
        percentual_existente = (documentos_existentes / (total_colaboradores * total_tipos_obrigatorios)) * 100
        percentual_pendente = 100 - percentual_existente

        porcentagens_por_unidade.append({
            'unidade_nome': unidade_nome,
            'percentual_existente': f"{percentual_existente:.0f}%",
            'percentual_pendente': f"{percentual_pendente:.0f}%"
        })

    return porcentagens_por_unidade


def calcular_porcentagens_obrigatorios_unidade_inativos():
        total_tipos_obrigatorios = TipoDocumento.objects.filter(obrigatorio=True).count()

        if total_tipos_obrigatorios == 0:
            return []

        # Conta total de documentos obrigatórios por unidade para colaboradores ativos
        documentos_por_unidade = ColaboradorTipoDocumento.objects.filter(
            colaborador__status__nome='Inativo',
            tipo_documento__obrigatorio=True
        ).values('colaborador__unidade__nome').annotate(
            total_colaboradores=Count('colaborador', distinct=True),
            documentos_existentes=Count('tipo_documento', distinct=True)
        ).order_by('colaborador__unidade__nome')

        porcentagens_por_unidade = []
        for item in documentos_por_unidade:
            unidade_nome = item['colaborador__unidade__nome']
            total_colaboradores = item['total_colaboradores']
            documentos_existentes = item['documentos_existentes']

            # Calcula as porcentagens baseado nos documentos existentes e total de tipos obrigatórios por colaborador
            percentual_existente = (documentos_existentes / (total_colaboradores * total_tipos_obrigatorios)) * 100
            percentual_pendente = 100 - percentual_existente

            porcentagens_por_unidade.append({
                'unidade_nome': unidade_nome,
                'percentual_existente': f"{percentual_existente:.0f}%",
                'percentual_pendente': f"{percentual_pendente:.0f}%"
            })

        return porcentagens_por_unidade


class DocumentoVencidoService:
    @staticmethod
    def copiar_documentos_relevantes():
        documentos_processados = 0

        codigos_relevantes = [401, 403, 501, 502]
        tipos_documentos_relevantes = TipoDocumento.objects.filter(codigo__in=codigos_relevantes)

        for documento in Hyperlinkpdf.objects.filter(documento__in=tipos_documentos_relevantes):
            _, created = DocumentoVencidoService.criar_a_partir_de_hyperlinkpdf(documento)
            if created:
                documentos_processados += 1

        return {'documentos_processados': documentos_processados}

    @staticmethod
    def criar_a_partir_de_hyperlinkpdf(hyperlinkpdf):
        tipo_doc_id = str(hyperlinkpdf.codigo_documento)
        precisa_renovar = tipo_doc_id in ['403', '501', '502']
        novo_documento, created = DocumentoVencido.objects.update_or_create(
            matricula=hyperlinkpdf.matricula,
            tipo_documento=hyperlinkpdf.documento,
            defaults={
                'empresa': hyperlinkpdf.empresa,
                'regional': hyperlinkpdf.regional,
                'unidade': hyperlinkpdf.unidade,
                'colaborador': hyperlinkpdf.colaborador,
                'cpf': hyperlinkpdf.cpf,
                'cargo': hyperlinkpdf.cargo,
                'dta_documento': hyperlinkpdf.dta_documento,
                'precisa_renovar': precisa_renovar
            }
        )
        return novo_documento, created


class ServicoValidadeDocumento:
    @staticmethod
    def documentos_vencidos():
        hoje = timezone.now().date()
        documentos_vencidos = []

        # Usando select_related para pegar as informações do cargo junto com cada colaborador
        documentos = DocumentoVencido.objects.select_related(
            'empresa',
            'regional',
            'unidade',
            'colaborador',
            'colaborador__cargo',  # Esta linha assume que o modelo 'Colaborador' tem uma ForeignKey para 'Cargo'
            'tipo_documento'
        ).all()

        for documento in documentos:
            try:
                validade = int(documento.tipo_documento.validade)
                data_competencia = documento.dta_documento + timedelta(days=validade * 30)
                if data_competencia < hoje:
                    doc_info = {
                        'id': documento.id,
                        'matricula': documento.matricula,
                        'nome': documento.colaborador.nome,
                        'cpf': documento.cpf,
                        'cargo': documento.colaborador.cargo.nome,  # Acessando um atributo específico do objeto Cargo
                        'unidade': documento.colaborador.unidade.nome,
                        'regional': documento.colaborador.unidade.regional.nome,
                        'empresa': documento.colaborador.unidade.regional.empresa.nome,
                        'dta_documento': data_competencia.strftime('%Y-%m-%d')  # Formatar a data para string
                    }
                    documentos_vencidos.append(doc_info)
            except ValueError:
                continue

        return documentos_vencidos


def documentos_a_vencer(documentos):
    hoje = timezone.now().date()

    vencimentos = {'15_dias': [], '30_dias': [], '45_dias': [], '60_dias': [], '70_dias': [], '90_dias': [], '365_dias': []}

    for documento in documentos:
        try:
            validade = int(documento.tipo_documento.validade.strip())
            data_vencimento = documento.dta_documento + relativedelta(months=validade)
            dias_para_vencer = (data_vencimento - hoje).days


            # Continua apenas se o documento ainda não venceu
            if dias_para_vencer >= 0:
                categorize_document(dias_para_vencer, documento, vencimentos)


        except Exception as e:
            print(f"Erro ao processar documento {documento.id}: {e}")

    return convert_to_dict(vencimentos)

def categorize_document(dias_para_vencer, documento, vencimentos):
    for prazo, lista in vencimentos.items():
        limite = int(prazo.split('_')[0])
        if dias_para_vencer <= limite:
            lista.append(documento)
            break  # Não precisa verificar os outros limites após categorizar

def convert_to_dict(vencimentos):
    dict_format = {}
    for prazo, documentos in vencimentos.items():
        dict_format[prazo] = [{
            'id': doc.id,
            'nome': doc.colaborador.nome,
            'cpf': doc.cpf,
            'cargo': doc.colaborador.cargo.nome if doc.colaborador.cargo else '',
            'unidade': doc.unidade.nome if doc.unidade else '',
            'regional': doc.regional.nome if doc.regional else '',
            'empresa': doc.empresa.nome if doc.empresa else '',
            'data_vencimento': doc.dta_documento.strftime('%Y-%m-%d'),
            'dias_para_vencer': (doc.dta_documento + relativedelta(months=int(doc.tipo_documento.validade)) - timezone.now().date()).days
        } for doc in documentos]

    return dict_format


class DocumentoPendenciaQuery:
    @staticmethod
    def buscar_pendencias_por_data(data_escolhida):
        # Converter a data escolhida para o formato de data do Python
        data_formatada = datetime.strptime(data_escolhida, '%d/%m/%Y').date()

        # Buscar pendências no modelo DocumentoPendente pela data de upload
        pendencias = DocumentoPendente.objects.filter(data_upload__date=data_formatada)

        # Buscar hyperlinks que foram carregados na data escolhida
        uploads = Hyperlinkpdf.objects.filter(data_upload__date=data_formatada)

        # Combinar os resultados em um dicionário para retorno
        resultado = {
            'pendencias': list(pendencias.values()),
            'uploads': list(uploads.values())
        }

        return resultado


def mover_registros_incompletos():
    registros_incompletos = Hyperlinkpdf.objects.filter(
        Q(empresa__isnull=True) |
        Q(regional__isnull=True) |
        Q(unidade__isnull=True) |
        Q(colaborador__isnull=True) |
        Q(cargo__isnull=True)
    )

    print(f'Encontrados {registros_incompletos.count()} registros incompletos.')

    for registro in registros_incompletos:
        print(f'Movendo registro {registro.id} para HyperlinkDadosNull.')
        HyperlinkDadosNull.objects.create(
            data_upload=registro.data_upload,
            caminho=registro.caminho,
            documento=registro.documento,
            matricula=registro.matricula,
            cpf=registro.cpf,
            nome_arquivo=registro.nome_arquivo,
            dta_documento=registro.dta_documento,
            codigo_documento=registro.codigo_documento,
            empresa=registro.empresa,
            regional=registro.regional,
            unidade=registro.unidade,
            colaborador=registro.colaborador,
            cargo=registro.cargo
        )
        registro.delete()




def get_documentos_pendentes(situacao=None):
    if situacao:
        pendentes = DocumentoPendente.objects.select_related(
            'empresa', 'regional', 'unidade', 'nome', 'cargo', 'tipo_documento'
        ).filter(situacao=situacao).only(
            'id', 'nome__nome', 'matricula', 'cpf', 'empresa__nome', 'regional__nome',
            'unidade__nome', 'cargo__nome', 'admissao', 'desligamento', 'situacao', 'tipo_documento__nome', 'obrigatorio'
        )
    else:
        pendentes = DocumentoPendente.objects.select_related(
            'empresa', 'regional', 'unidade', 'nome', 'cargo', 'tipo_documento'
        ).only(
            'id', 'nome__nome', 'matricula', 'cpf', 'empresa__nome', 'regional__nome',
            'unidade__nome', 'cargo__nome', 'admissao', 'desligamento', 'situacao', 'tipo_documento__nome', 'obrigatorio'
        )

    return pendentes
