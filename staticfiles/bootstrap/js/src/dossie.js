

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


