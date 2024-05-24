// Expandir/fechar itens do menu lateral
var btnExp = document.querySelector('#btn-exp');
var menuSide = document.querySelector('.menu-lateral');

btnExp.addEventListener('click', function () {
    menuSide.classList.toggle('expandir');
});

// Função para obter a data formatada
function obterDataFormatada() {
    const diasDaSemana = ['Domingo', 'Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado'];
    const meses = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'];

    const dataAtual = new Date();
    const diaSemana = diasDaSemana[dataAtual.getDay()];
    const dia = dataAtual.getDate();
    const mes = meses[dataAtual.getMonth()];
    const ano = dataAtual.getFullYear();

    return `${diaSemana}, ${dia} ${mes}, ${ano}`;
}

// Função para atualizar a data no elemento span
function atualizarData() {
    const elementoData = document.getElementById('dataAtual');
    elementoData.textContent = obterDataFormatada();
}

// Atualizar a data quando a página carregar
window.addEventListener('load', function () {
    atualizarData();
});

// Atualizar a data a cada minuto (60 segundos)
setInterval(atualizarData, 60000);

// Mapeando cada item do menu lateral com sua respectiva função de abertura de formulário
/*
document.querySelectorAll('.item-menu').forEach(item => {
    item.addEventListener('click', function () {
        const target = this.getAttribute('data-target');
        openFormContainer(target);

        // Oculta a imagem de fundo quando uma opção do menu lateral é clicada
        document.body.classList.add('sem-imagem-fundo');
    });
});
*/
// Função para ocultar todos os formulários
function ocultarFormularios() {
    document.getElementById('AlteraSenhaForm').style.display = 'none';
    document.getElementById('tabelaPermissõesForm').style.display = 'none';
    document.getElementById('tabelausuariosForm').style.display = 'none';
    //document.getElementById('DocumentosApagadosForm').style.display = 'none';
    //document.getElementById('ApagarDocumentoForm').style.display = 'none';
    //document.getElementById('ErrosRHForm').style.display = 'none';
    //document.getElementById('ErrosDepartamentosForm').style.display = 'none';
    document.getElementById('tabelaOcupaçãoForm').style.display = 'none';
    document.getElementById('tabelaTiposDocumentosForm').style.display = 'none';
    document.getElementById('tabelaGruposDocumentosForm').style.display = 'none';
    //document.getElementById('tabelaSetorForm').style.display = 'none';
    document.getElementById('tabelaÁreasForm').style.display = 'none';
    document.getElementById('tabelaUnidadesForm').style.display = 'none';
    document.getElementById('tabelaRegionaisForm').style.display = 'none';
    //document.getElementById('tabelaEstabelecimentoForm').style.display = 'none';
    document.getElementById('tabelaFuncionariosForm').style.display = 'none';
    document.getElementById('tabelaEmpresaForm').style.display = 'none';
    document.getElementById('SincronizarDocumentosForm').style.display = 'none';
    document.getElementById('RessincronizarDocumentosForm').style.display = 'none';
    document.getElementById('AtualizarBancoForm').style.display = 'none';
}

// Função para mostrar um formulário específico por ID
function mostrarFormulario(id) {
    ocultarFormularios();
    var formulario = document.getElementById(id);
    formulario.style.display = 'block';
    formulario.style.zIndex = '1000'; // Define a propriedade z-index para garantir que o formulário fique na frente
}

// Função para abrir o formulário de cadastros de funcionários
function abrirAlteraSenha() {
    mostrarFormulario('AlteraSenhaForm');
}
// Função para abrir o formulário de cadastros de funcionários
function abrirPermissões() {
    mostrarFormulario('tabelaPermissõesForm');
}

// Função para abrir o formulário de cadastros de funcionários
function abrirusuarios() {
    mostrarFormulario('tabelausuariosForm');
}

/*/ Função para abrir o formulário de cadastros de funcionários
function abrirDocumentosApagados() {
    mostrarFormulario('DocumentosApagadosForm');
}
//Função para abrir o formulário de cadastros de funcionários
function abrirApagarDocumento() {
   mostrarFormulario('ApagarDocumentoForm');
}
/ Função para abrir o formulário de cadastros de funcionários
 function abrirErrosRH() {
   mostrarFormulario('ErrosRHForm');
}
Função para abrir o formulário de cadastros de funcionários
function abrirErrosDepartamentos() {
    mostrarFormulario('ErrosDepartamentosForm');
} */
// Função para abrir o formulário de cadastros de funcionários
function abrirOcupação() {
    mostrarFormulario('tabelaOcupaçãoForm');
}
// Função para abrir o formulário de cadastros de funcionários
function abrirTiposDocumentos() {
    mostrarFormulario('tabelaTiposDocumentosForm');
}
// Função para abrir o formulário de cadastros de funcionários
function abrirGruposDocumentos() {
    mostrarFormulario('tabelaGruposDocumentosForm');
}
// Função para abrir o formulário de cadastros de funcionários
/*function abrirSetor() {
    mostrarFormulario('tabelaSetorForm');
}*/
// Função para abrir o formulário de cadastros de funcionários
function abrirÁreas() {
    mostrarFormulario('tabelaÁreasForm');
}
// Função para abrir o formulário de cadastros de funcionários
function abrirUnidades() {
    mostrarFormulario('tabelaUnidadesForm');
}

// Função para abrir o formulário de cadastros de funcionários
function abrirRegionais() {
    mostrarFormulario('tabelaRegionaisForm');
}
/*/ Função para abrir o formulário de cadastros de funcionários
function abrirEstabelecimento() {
    mostrarFormulario('tabelaEstabelecimentoForm');
}*/
// Função para abrir o formulário de cadastros de funcionários
function abrirEmpresa() {
    mostrarFormulario('tabelaEmpresaForm');
}
// Função para abrir o formulário de cadastros de funcionários
function abrirCadastrosFuncionarios() {
    mostrarFormulario('tabelaFuncionariosForm');
}

// Função para abrir o formulário de sincronização de documentos
function abrirSincronizarDocumentos() {
    mostrarFormulario('SincronizarDocumentosForm');
}

// Função para abrir o formulário de ressincronização de documentos
function abrirRessincronizarDocumentos() {
    mostrarFormulario('RessincronizarDocumentosForm');
}

// Função para abrir o formulário de atualização do banco de dados
function abrirAtualizarBanco() {
    mostrarFormulario('AtualizarBancoForm');
}

// Adiciona eventos de clique para as opções de formulário
document.querySelector('[data-target="AlteraSenhaForm"]').addEventListener('click', abrirAlteraSenha);
document.querySelector('[data-target="PermissõesForm"]').addEventListener('click', abrirPermissões);
document.querySelector('[data-target="usuariosForm"]').addEventListener('click', abrirusuarios);
//document.querySelector('[data-target="DocumentosApagadosForm"]').addEventListener('click', abrirDocumentosApagados);
//document.querySelector('[data-target="ApagarDocumentoForm"]').addEventListener('click', abrirApagarDocumento);
//document.querySelector('[data-target="ErrosRHForm"]').addEventListener('click', abrirErrosRH);
//document.querySelector('[data-target="ErrosDepartamentosForm"]').addEventListener('click', abrirErrosDepartamentos);
document.querySelector('[data-target="OcupaçãoForm"]').addEventListener('click', abrirOcupação);
document.querySelector('[data-target="TiposDocumentosForm"]').addEventListener('click', abrirTiposDocumentos);
document.querySelector('[data-target="GruposDocumentosForm"]').addEventListener('click', abrirGruposDocumentos);
//document.querySelector('[data-target="SetorForm"]').addEventListener('click', abrirSetor);
document.querySelector('[data-target="ÁreasForm"]').addEventListener('click', abrirÁreas);
document.querySelector('[data-target="UnidadesForm"]').addEventListener('click', abrirUnidades);
document.querySelector('[data-target="RegionaisForm"]').addEventListener('click', abrirRegionais);
//document.querySelector('[data-target="EstabelecimentoForm"]').addEventListener('click', abrirEstabelecimento);
document.querySelector('[data-target="EmpresaForm"]').addEventListener('click', abrirEmpresa);
document.querySelector('[data-target="CadastrosFuncionariosForm"]').addEventListener('click', abrirCadastrosFuncionarios);
document.querySelector('[data-target="SincronizarDocumentosForm"]').addEventListener('click', abrirSincronizarDocumentos);
document.querySelector('[data-target="RessincronizarForm"]').addEventListener('click', abrirRessincronizarDocumentos);
document.querySelector('[data-target="AtualizarBancoForm"]').addEventListener('click', abrirAtualizarBanco);


/*
// Função para abrir o formulário de cadastro de funcionários
function abrirFormularioCrud() {
    var formulario = document.getElementById('formularioCrud');
    formulario.style.display = 'block';
    formulario.style.zIndex = '1000'; // Define a propriedade z-index para garantir que o formulário fique na frente
    // Adiciona a classe 'modal-open' ao body para aplicar o efeito de fundo desfocado
    document.body.classList.add('modal-open');
}

// Função para fechar o formulário de cadastro de funcionários
function fecharFormularioCrud() {
    var formulario = document.getElementById('formularioCrud');
    formulario.style.display = 'none';
    // Remove a classe 'modal-open' do body
    document.body.classList.remove('modal-open');
}

// Adiciona evento de clique para abrir o formulário
document.getElementById('abrirFormulario').addEventListener('click', abrirFormularioCrud);

// Adiciona evento de clique para fechar o formulário ao clicar no 'x'
document.getElementById('fecharFormulario').addEventListener('click', fecharFormularioCrud);

// Adiciona evento de clique para o botão de cancelar
document.getElementById('cancelar').addEventListener('click', fecharFormularioCrud);

// Manipule o envio do formulário conforme necessário
document.getElementById('formFuncionario').addEventListener('submit', function (event) {
    // Evite o envio padrão do formulário
    event.preventDefault();

    // Lógica para enviar os dados do formulário
    // Por exemplo, você pode usar AJAX para enviar os dados para o servidor e manipular a resposta aqui
    // Após o envio bem-sucedido, você pode fechar o formulário

    // Fechar o formulário após o envio
    fecharFormularioCrud();
});

*/
