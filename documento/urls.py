from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import PasswordResetDoneView

from .views import CarregarColaboradorSimplesView, CarregarRelatorioExistenteSimplesView, CarregarRelatorioPendenteASOSimplesView, CarregarRelatorioPendenteSimplesView, ListarCartaoPontoInexistenteSimplesView, ListarDocumentosSimplesView, ListarDocumentosVencerSimplesView, dashboard, get_tipo_documentos, index,  dossie, relatorios, configuracao
from .views import (LoginView, visualizar_documentos, TotalColaboradoresView, get_documentos_info,
                    AtualizarDocumentosPendentesView, DocumentosExistentesAtivosView,
                    ObrigatoriosPorUnidadeAtivo, ObrigatoriosPorUnidadeInativo, AtualizarASOView,
                    ASOPercentualAtivoView, AtualizarCartaoPontoView, DocumentosPontoAtivoView,
                    DocumentosPontoInativoView, DomingosFeriadosExistenteView,
                    CarregarRelatorioPendenteView, CarregarRelatorioExistenteView, CarregarRelatorioPendenteASOView,
                    ListarCartaoPontoInexistenteView, CarregarDocumentosVencidosView, ObrigatoriosUnidadesInativoView,
                    ASOPercentualInativoView, DocumentosObrigatoriosAtivosView, DocumentosObrigatoriosInativosView,
                    ObrigatoriosUnidadesAtivoView, ListarDocumentosVencidosView, ListarDocumentosaVencerView, GerarRelatorioGerencialView,
                    get_hyperlinkpdf_data, DocumentosPendentesAtivosPorUnidadeView,
                    DocumentosPendentesInativosPorUnidadeView, DocumentoExistenteListView, buscar_pendencias)
from .views import (
    importar_usuarios,  CadastrarFuncionarioView, gerenciar_empresa, gerenciar_regional, gerenciar_unidade, GerenciarUsuarioView,
    CarregarDadosView, PesquisaDossieView, ListarResultadoDossieView, CarregarEmpresaView, CarregarCargoView,
    CarregarRegionalView, CarregarUnidadesView, CarregarSituacoesView, CarregarColaboradorView, dados_pessoais,
    cadastrar_area, cadastrar_grupo_documento, inserir_tipodocumento_cargo, CarregarRelatoriosGerenciaisView,
    inserir_tipodocumento_colaborador, RelatorioPendenteView,
    DocumentosExistentesView, DocumentoVencidoListView, DocumentoAVencerListView,
    PendenteASOListView, RelatorioGerencialListView, criar_funcionario,
    lista_funcionarios, cadastrar_tipodocumento, AuthenticationViews, ImportarDadosView, CustomLogoutView)



urlpatterns = [
    # Urls tela inicial e Login
    path('index/', index, name='index'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),

    path('forgot_password/', AuthenticationViews.as_view, name='forgot_password'),
    path('password_reset_done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('documento/importar_dados/', ImportarDadosView.as_view(), name='importar-dados'),


    # Urls tela DOSSIE
    path('dossie/<int:pk>/', PesquisaDossieView.as_view(), name='detalhe_dossie'),
    path('carregar_empresa/', CarregarEmpresaView.as_view(), name='carregar_empresa'),
    path('carregar_regionais/', CarregarRegionalView.as_view(), name='carregar_regionais'),
    path('carregar_unidades/', CarregarUnidadesView.as_view(), name='carregar_unidades'),
    path('carregar_colaborador/', CarregarColaboradorView.as_view(), name='carregar_colaborador'),
    path('carregar_cargos/', CarregarCargoView.as_view(), name='carregar_cargos'),
    path('carregar_situacoes/', CarregarSituacoesView.as_view(), name='carregar_situacoes'),
    path('dossie/<int:pk>/resultados/', ListarResultadoDossieView.as_view(), name='listar_resultado_dossie'),
    path('dados-pessoais/', dados_pessoais, name='dados_pessoais'),
    path('api/carregar_dados/', CarregarDadosView.as_view(), name='carregar_dados'),
    path('visualizar_documentos/', visualizar_documentos, name='visualizar_documentos'),
    # path('atualizar-documentos-pendentes/', AtualizarDocumentosPendentesView.as_view(), name='atualizar_documentos_pendentes'),
    path('hyperlinkpdf/', get_hyperlinkpdf_data, name='hyperlinkpdf'),
    path('get_documentos_info/', get_documentos_info, name='get_documentos_info'),



    # URLS tela DASHBOARD
    path('aso_percentual_ativo/', ASOPercentualAtivoView.as_view(), name='aso_percentual_ativo'),
    path('aso/percentual-inativo/', ASOPercentualInativoView.as_view(), name='aso_percentual_inativo'),
    path('documentos/obrigatorios-ativos/', DocumentosObrigatoriosAtivosView.as_view(),
         name='documentos_obrigatorios_ativos'),
    path('documentos/obrigatorios-inativos/', DocumentosObrigatoriosInativosView.as_view(),
         name='documentos_obrigatorios_inativos'),
    path('documentos/ponto-ativos/', DocumentosPontoAtivoView.as_view(), name='documentos_ponto_ativos'),
    path('documentos/ponto-inativos/', DocumentosPontoInativoView.as_view(), name='documentos_ponto_inativos'),

    path('obr_unidade_ativo_inativos/', ObrigatoriosUnidadesAtivoView.as_view(), name='obr_unidade_ativo_inativos'),
    path('obr_unidade_ativo_inativos/', ObrigatoriosUnidadesInativoView.as_view(), name='obr_unidade_ativo_inativos'),

    path('get_documentos_info/', get_documentos_info, name='get_documentos_info'),

    path('carregar-relatorio-pendente/<str:situacao>/', CarregarRelatorioPendenteView.as_view(), name='carregar_relatorio_pendente'),
    path('relatorio-pendente/', CarregarRelatorioPendenteView.as_view(), name='carregar_relatorio_pendente_sem_situacao'),

    path('relatorio_existente_todo/<str:status>/', CarregarRelatorioExistenteView.as_view(), name='relatorio_existente_todos'),
    path('relatorio_existente_todo/', CarregarRelatorioExistenteView.as_view(), name='relatorio_existente_todos_sem_situacao'),

    path('relatorio/asos/', CarregarRelatorioPendenteASOView.as_view(), name='carregar_relatorio_pendente_asos'),
    path('listar-cartoes/', ListarCartaoPontoInexistenteView.as_view(), name='listar_cartoes_ponto_inexistentes'),


    path('documentos_vencidos/', CarregarDocumentosVencidosView.as_view(), name='documentos_vencidos'),
    path('lista_documentos_vencidos/', ListarDocumentosVencidosView.as_view(), name='lista_vencidos'),
    path('lista_a_vence/', ListarDocumentosaVencerView.as_view(), name='lista_a_vencer'),

    path('relatorio_gerencia/', CarregarRelatoriosGerenciaisView.as_view(), name='relatorio_gerencias'),
    # path('documentos_auditoria/', CarregarDocumentosAuditoriaView.as_view(), name='documentos_auditorias'),
    path('documentos_existentes/', DocumentosExistentesView.as_view(), name='documentos_existentes'),
    path('atualizar-documentos-pendentes/', AtualizarDocumentosPendentesView.as_view(), name='atualizar_documentos_pendentes'),
    path('pendente_aso/', AtualizarASOView.as_view(), name='atualizar-aso'),
    path('atualizar_controle_ponto/', AtualizarCartaoPontoView.as_view(), name="atualizar_controle_ponto"),



    # Urls tela Relatorios
    path('doc_pendentes_unidade_ativo/', DocumentosPendentesAtivosPorUnidadeView.as_view(),
         name='doc_pendentes_unidade_ativo'),
    path('obrigatorios-por-unidade/', ObrigatoriosPorUnidadeAtivo.as_view(), name='obrigatorios_por_unidade'),
    path('doc_pendentes_unidade_inativo/', DocumentosPendentesInativosPorUnidadeView.as_view(),
         name='doc_pendentes_unidade_inativo'),
    path('doc_existentes_unidades/<str:unidade_nome>/<str:status>/', DocumentosExistentesAtivosView.as_view(),
         name='doc_existentes_unidades_ativos'),
    path('relatorio_pendente/', RelatorioPendenteView.as_view(), name='relatorio_pendente'),
    path('documentos_existentes/', DocumentoExistenteListView.as_view(), name='documentos_existentes'),
    path("documentos_vencidos/", DocumentoVencidoListView.as_view(), name="documentos_vencidos"),
    path("documentos_a_vencer/", DocumentoAVencerListView.as_view(), name="documentos_a_vencer"),
    # path("controle_ponto/", ControlePontoListView.as_view(), name="controle_ponto"),
    path("pendentes_aso/", PendenteASOListView.as_view(), name="pendentes_aso"),
    # path("documentos_existentes_auditoria/", DocumentoExistenteAuditoriaListView.as_view(), name="documentos_existentes_auditoria"),
    path("relatorios_gerenciais/", RelatorioGerencialListView.as_view(), name="relatorios_gerenciais"),
    path('total_colaboradores/', TotalColaboradoresView.as_view(), name='total_colaboradores'),
    path('obrigatorios-inativos-unidade/', ObrigatoriosPorUnidadeInativo.as_view(), name='obrigatorios_inativos_unid'),

    path('pesquisa-documentos/', DomingosFeriadosExistenteView.as_view(), name='domingos_feriados'),

    path('pendencias/', buscar_pendencias, name='buscar_pendencias'),


    # Urls Tela Configurações
    path('importar_dados/', ImportarDadosView.as_view(), name='importar_dados'),
    path('importar-usuarios/', importar_usuarios, name='importar_usuarios'),
    path('criar-funcionario/', criar_funcionario, name='criar_funcionario'),
    path('lista-funcionarios/', lista_funcionarios, name='lista_funcionarios'),
    path('listar_resultados_dossie/', ListarResultadoDossieView.as_view(), name='listar_resultados_dossie'),
    path('cadastrar_area/', cadastrar_area, name='cadastrar_area'),
    path('cadastrar_grupo_documento/', cadastrar_grupo_documento, name='cadastrar_grupo_documento'),
    path('cadastrar_tipodocumento/', cadastrar_tipodocumento, name='cadastrar_tipodocumento'),
    path('inserir_tipodocumento_cargo/', inserir_tipodocumento_cargo, name='inserir_tipodocumento_cargo'),
    path('inserir_tipodocumento_colaborador/', inserir_tipodocumento_colaborador, name='inserir_tipodocumento_colaborador'),

    path('cadastrar_funcionario/', CadastrarFuncionarioView.as_view(), name='cadastrar_funcionario'),
    # path('cadastro_colaborador/', gerenciar_colaborador, name='cadastrar_colaboradores'),

    path('cadastro_empresa/', gerenciar_empresa, name='cadastrar_empresas'),
    path('cadastro_regional/', gerenciar_regional, name='cadastrar_regionais'),
    path('cadastro_uniade/', gerenciar_unidade, name='cadastrar_unidades'),
    path('cadastro_usuario/', GerenciarUsuarioView.as_view(), name='cadastro_usuarios'),
     path('get_tipo_documentos/', get_tipo_documentos, name='get_tipo_documentos'),
    path('dossie/', dossie, name='dossie'),
    path('relatorios/', relatorios, name='relatorios'),
    path('configuracao/', configuracao, name='configuracao'),
    path('dashboard/', dashboard, name='dashboard'),
    #  path('login_tela/', tela_login, name='tela_login'),
    
    
    #URLs de Relatorios com estrategias 
    path('relatorio-pendente-simples/', CarregarRelatorioPendenteSimplesView.as_view(), name='relatorio_pendente_simples'),
     path('carregar-relatorio-existente-simples/', CarregarRelatorioExistenteSimplesView.as_view(), name='carregar_relatorio_existente_simples'),
     path('relatorio_aso_simples/', CarregarRelatorioPendenteASOSimplesView.as_view(), name='relatorio_aso_simples'),
     path('relatorio_cartao_simples/', ListarCartaoPontoInexistenteSimplesView.as_view(), name='relatorio_cartao_simples'),
     path('relatorio_vencidos_simples/', ListarDocumentosSimplesView.as_view(), name='relatorio_vencidos_simples'),
     path('relatorio_vencer_simples/', ListarDocumentosVencerSimplesView.as_view(), name='relatorio_vencer_simples'),
     path('relatorio_colaborador_simples/', CarregarColaboradorSimplesView.as_view(), name='relatorio_colaborador_simples'),

]



    





# No final do seu arquivo urls.py
if settings.DEBUG:
    from django.conf.urls.static import static
    from django.conf import settings
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

