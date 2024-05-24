// Ação dos formulários
function openFormContainer(target, openForm = true) {
    document.querySelectorAll('.form-container').forEach(container => {
        container.style.display = 'none';
    });

    if (openForm) {
        document.getElementById(target).style.display = 'block';
    }
}

document.querySelectorAll('.item-menu').forEach(item => {
    item.addEventListener('click', function () {
        const target = this.getAttribute('data-target');
        openFormContainer(target);
    });
});

// Fixar seleção do menu lateral
var menuItem = document.querySelectorAll('.item-menu');

function selectlink() {
    menuItem.forEach((item) =>
        item.classList.remove('ativo')
    )
    this.classList.add('ativo')
}

menuItem.forEach((item) =>
    item.addEventListener('click', selectlink)
)

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

function carregarRegioes() {
    const arquivoExcel = 'C:/Users/andre/OneDrive/Documentos/dados/BASE AEGEA 23022023.xlsx';

    fetch(arquivoExcel)
        .then(response => response.arrayBuffer())
        .then(data => {
            console.log('Dados do arquivo Excel:', data); // Verificar se os dados do arquivo foram corretamente recebidos
            const workbook = XLSX.read(data, { type: 'array' });
            console.log('Workbook:', workbook); // Verificar se o workbook foi corretamente criado
            const sheet = workbook.Sheets[workbook.SheetNames[0]];
            console.log('Planilha:', sheet); // Verificar se a planilha foi corretamente selecionada

            const dataObjects = XLSX.utils.sheet_to_json(sheet, { header: ['REGIAO'], range: 1 });
            console.log('Dados extraídos:', dataObjects); // Verificar se os dados foram corretamente extraídos

            // Restante do código para adicionar opções ao select
        })
        .catch(error => console.error('Erro ao carregar o arquivo Excel:', error));
}



document.querySelectorAll('.item-menu').forEach(item => {
    item.addEventListener('click', function () {
        const target = this.getAttribute('data-target');
        openFormContainer(target);

        // Oculta a imagem de fundo quando uma opção do menu lateral é clicada
        document.body.classList.add('sem-imagem-fundo');
    });
});
