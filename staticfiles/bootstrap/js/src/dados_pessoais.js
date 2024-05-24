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
  




   document.addEventListener("DOMContentLoaded", function() {
          // Extrai os parâmetros da URL
          var params = new URLSearchParams(window.location.search);
          
          // Preenche os dados nos respectivos campos
          document.querySelector('.regional').textContent = params.get('regional');
          document.querySelector('.unidade').textContent = params.get('unidade');
          document.querySelector('.admissao').textContent = params.get('admissao');
          document.querySelector('.desligamento').textContent = params.get('desligamento');
          document.querySelector('.cargo').textContent = params.get('cargo');
          document.querySelector('.matricula').textContent = params.get('matricula');
          document.querySelector('.colaborador').textContent = params.get('colaborador');
          document.querySelector('.cpf').textContent = params.get('cpf');
          document.querySelector('.situacao').textContent = params.get('situacao');
      });
      document.addEventListener("DOMContentLoaded", function() {
  // Extrai os parâmetros da URL
  var params = new URLSearchParams(window.location.search);
  
  // Verifica se os parâmetros estão sendo passados corretamente
  console.log(params.get('colaborador')); // Verifique se isso retorna o nome do colaborador
  
  // Preenche os dados nos respectivos campos
  document.querySelector('.colaborador').textContent = params.get('colaborador');
});
document.addEventListener("DOMContentLoaded", function() {
  // Extrai os parâmetros da URL
  var params = new URLSearchParams(window.location.search);
  
  // Verifica se os parâmetros estão sendo passados corretamente
  console.log(params.get('colaborador')); // Esta linha irá imprimir o valor do parâmetro 'colaborador' no console
  
  // Preenche os dados nos respectivos campos
  document.querySelector('.colaborador').textContent = params.get('colaborador');
});


