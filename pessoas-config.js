/*
  PESSOAS CONFIG
  --------------
  Liste aqui todas as personas disponíveis na sidebar.

  Cada objeto precisa de:
    id         → identificador único (usado como chave no localStorage etc.)
    configVar  → nome da variável global definida pelo arquivo de config
                 (ex: "PERSONA_JULIA" vira window.PERSONA_JULIA)
    configFile → arquivo JS a carregar (relativo à raiz do projeto)

  Para adicionar uma nova persona:
    1. Crie assets/nome.png
    2. Crie nome-config.js com  window.PERSONA_NOME = { ... }
    3. Adicione um item aqui embaixo
*/

window.PERSONAS_LIST = [
  {
    id: "julia",
    configVar: "PERSONA_JULIA",
    configFile: "julia-config.js"
  }
  // Exemplo de nova persona:
  // {
  //   id: "pessoa2",
  //   configVar: "PERSONA_PESSOA2",
  //   configFile: "pessoa2-config.js"
  // }
];
