const API_URL = "";
const modoPages = document.body.classList.contains("modo-pages");

const colecoes = {
  desafios: { id: "id_desafio", nome: "desafio", novo: "Novo desafio" },
  participantes: { id: "id_participante", nome: "participante", novo: "Novo participante" },
  inscricoes: { id: "id_inscricao", nome: "inscrição", novo: "Nova inscrição" },
  atividades: { id: "id_registro", nome: "atividade", novo: "Registrar atividade" },
  modalidades: { id: "id_modalidade", nome: "modalidade", novo: "Nova modalidade" },
};

const rotulosPeriodo = {
  ativo: "Em andamento",
  agendado: "Agendado",
  encerrado: "Encerrado",
};

let registros = {};
let dadosDisponiveis = false;
let consultaProgresso = 0;
let temporizadorAviso;
let enviando = false;

const dialogo = document.querySelector("#dialogo");
const selecaoProgresso = document.querySelector("#selecao-progresso");
const filtroDesafios = document.querySelector("#filtro-desafios");
const salvar = document.querySelector("#salvar");

async function solicitar(caminho, metodo = "GET", dados = null) {
  const endereco = modoPages ? "./dados" + caminho + ".json" : API_URL + caminho;
  const opcoes = { method: metodo };
  if (dados !== null) {
    opcoes.headers = { "Content-Type": "application/json" };
    opcoes.body = JSON.stringify(dados);
  }

  let resposta;
  try {
    resposta = await fetch(endereco, opcoes);
  } catch (erro) {
    if (modoPages) throw new Error("Falha ao carregar os dados de demonstração. Tente novamente.");
    throw new Error("Falha na conexão. Confira se o RitmoFit está rodando e tente novamente.");
  }

  const conteudo = await resposta.json().catch(() => null);
  if (!resposta.ok || conteudo === null) {
    const mensagem = conteudo && conteudo.erro;
    throw new Error(mensagem || "Não foi possível concluir a operação. Tente novamente.");
  }
  return conteudo;
}

function criarElemento(tag, classe, texto) {
  const elemento = document.createElement(tag);
  if (classe) elemento.className = classe;
  if (texto !== undefined) elemento.textContent = texto;
  return elemento;
}

function criarBotao(texto, acao, classe = "") {
  const botao = criarElemento("button", "botao botao-compacto " + classe, texto);
  botao.type = "button";
  botao.addEventListener("click", acao);
  return botao;
}

function dataDeHoje() {
  const hoje = new Date();
  const mes = String(hoje.getMonth() + 1).padStart(2, "0");
  const dia = String(hoje.getDate()).padStart(2, "0");
  return hoje.getFullYear() + "-" + mes + "-" + dia;
}

function formatarData(data) {
  const partes = data.split("-");
  return partes[2] + "/" + partes[1] + "/" + partes[0];
}

function numero(valor) {
  return valor.toLocaleString("pt-BR");
}

function periodo(desafio) {
  return formatarData(desafio.data_inicio) + " a " + formatarData(desafio.data_fim);
}

function estadoDoDesafio(desafio, hoje) {
  if (desafio.data_inicio > hoje) return "agendado";
  if (desafio.data_fim < hoje) return "encerrado";
  return "ativo";
}

function buscar(tipo, id) {
  return registros[tipo].find((item) => item[colecoes[tipo].id] === Number(id));
}

function nomeParticipante(id) {
  const participante = buscar("participantes", id);
  return participante ? participante.nome : "Participante indisponível";
}

function nomeModalidade(id) {
  const modalidade = buscar("modalidades", id);
  return modalidade ? modalidade.nome : "Modalidade indisponível";
}

function tituloDesafio(id) {
  const desafio = buscar("desafios", id);
  return desafio ? desafio.titulo : "Desafio indisponível";
}

function rotuloInscricao(inscricao) {
  return nomeParticipante(inscricao.id_participante) + " · " + tituloDesafio(inscricao.id_desafio);
}

function preencherOpcoes(campo, itens, chave, rotulo, placeholder) {
  const opcaoVazia = criarElemento("option", "", placeholder);
  opcaoVazia.value = "";
  campo.replaceChildren(opcaoVazia);

  itens.forEach((item) => {
    const opcao = criarElemento("option", "", rotulo(item));
    opcao.value = item[chave];
    campo.append(opcao);
  });
}

function mostrarTela(focar) {
  const hash = window.location.hash.slice(1);
  if (hash === "conteudo") return;
  const chave = Object.keys(colecoes).includes(hash) ? hash : "inicio";

  document.querySelectorAll(".tela").forEach((tela) => {
    tela.hidden = tela.id !== "tela-" + chave;
  });

  document.querySelectorAll("[data-tela]").forEach((link) => {
    if (link.dataset.tela === chave) {
      link.setAttribute("aria-current", "page");
    } else {
      link.removeAttribute("aria-current");
    }
  });

  if (focar && hash === "progresso") {
    document.querySelector("#progresso").scrollIntoView({ block: "start" });
    selecaoProgresso.focus({ preventScroll: true });
  } else if (focar) {
    window.scrollTo(0, 0);
    document.querySelector("#tela-" + chave + " h1").focus({ preventScroll: true });
  }
}

function notificar(texto) {
  window.clearTimeout(temporizadorAviso);
  document.querySelector("#notificacao").hidden = false;
  document.querySelector("#texto-notificacao").textContent = texto;
  temporizadorAviso = window.setTimeout(() => {
    document.querySelector("#notificacao").hidden = true;
  }, 6200);
}

function atualizarConexao(texto, erro = "") {
  const conexao = document.querySelector("#conexao");
  conexao.textContent = texto;
  conexao.classList.toggle("offline", Boolean(erro));
  document.querySelector("#falha").hidden = !erro;
  document.querySelector("#texto-falha").textContent = erro;
}

async function carregarDados(preferenciaProgresso) {
  dadosDisponiveis = false;
  atualizarConexao("Carregando");
  document.querySelectorAll("[data-novo]").forEach((botao) => {
    botao.disabled = true;
  });

  try {
    const listas = {};
    for (const tipo of Object.keys(colecoes)) {
      listas[tipo] = await solicitar("/" + tipo);
    }
    registros = listas;
    dadosDisponiveis = true;
    renderizarVisaoGeral(preferenciaProgresso);
    renderizarDesafios();
    renderizarTabelas();
    atualizarConexao(modoPages ? "Dados de exemplo" : "Conectado");
  } catch (erro) {
    atualizarConexao("Erro ao carregar", erro.message);
  } finally {
    document.querySelectorAll("[data-novo]").forEach((botao) => {
      botao.disabled = !dadosDisponiveis;
    });
  }
}

function seloPeriodo(desafio, hoje) {
  const estado = estadoDoDesafio(desafio, hoje);
  return criarElemento("span", "selo " + estado, rotulosPeriodo[estado]);
}

function renderizarVisaoGeral(preferenciaProgresso) {
  const hoje = dataDeHoje();
  const ativos = registros.desafios.filter((desafio) => estadoDoDesafio(desafio, hoje) === "ativo");
  const minutos = registros.atividades.reduce((total, atividade) => total + atividade.duracao_minutos, 0);
  document.querySelector("#metrica-desafios").textContent = numero(ativos.length);
  document.querySelector("#metrica-participantes").textContent = numero(registros.participantes.length);
  document.querySelector("#metrica-atividades").textContent = numero(registros.atividades.length);
  document.querySelector("#metrica-minutos").textContent = numero(minutos);

  const recentes = document.querySelector("#desafios-recentes");
  recentes.replaceChildren();
  if (registros.desafios.length === 0) {
    const vazio = criarElemento("li", "lista-vazia", "Nenhum desafio cadastrado.");
    vazio.append(" ", criarBotao("Criar desafio", () => abrirFormulario("desafios")));
    recentes.append(vazio);
  } else {
    registros.desafios.slice(-3).reverse().forEach((desafio) => {
      const item = criarElemento("li", "resumo-item");
      const detalhe = criarElemento("div");
      detalhe.append(
        criarElemento("strong", "", desafio.titulo),
        criarElemento("small", "", nomeModalidade(desafio.id_modalidade) + " · " + numero(desafio.meta_minutos) + " min por pessoa")
      );
      item.append(detalhe, seloPeriodo(desafio, hoje));
      recentes.append(item);
    });
  }

  const id = preferenciaProgresso || Number(selecaoProgresso.value);
  preencherOpcoes(selecaoProgresso, registros.inscricoes, "id_inscricao", rotuloInscricao, "Selecione uma inscrição");
  selecaoProgresso.disabled = registros.inscricoes.length === 0;
  if (buscar("inscricoes", id)) {
    selecaoProgresso.value = id;
  } else if (registros.inscricoes.length) {
    selecaoProgresso.value = registros.inscricoes[0].id_inscricao;
  }
  atualizarProgresso();
}

async function atualizarProgresso() {
  const consulta = ++consultaProgresso;
  const id = Number(selecaoProgresso.value);
  const medidor = document.querySelector("#medidor");
  const mensagem = document.querySelector("#mensagem-progresso");
  document.querySelector("#registrar-progresso").hidden = !id || modoPages;
  medidor.hidden = true;
  mensagem.hidden = false;

  if (!id) {
    mensagem.textContent = registros.inscricoes.length
      ? "Escolha uma inscrição para consultar a meta."
      : "Crie uma inscrição para acompanhar o progresso.";
    return;
  }

  mensagem.textContent = "Consultando progresso…";
  try {
    const progresso = await solicitar("/inscricoes/" + id + "/progresso");
    if (consulta !== consultaProgresso) return;

    const percentual = Math.min(100, Math.floor(100 * progresso.total_minutos / progresso.meta_minutos));
    const anel = document.querySelector("#anel-progresso");
    anel.style.setProperty("--percentual", percentual + "%");
    anel.setAttribute("aria-valuenow", percentual);
    document.querySelector("#percentual").textContent = percentual + "%";
    document.querySelector("#total-progresso").textContent = numero(progresso.total_minutos);
    document.querySelector("#meta-progresso").textContent = "/ " + numero(progresso.meta_minutos) + " min";
    document.querySelector("#resumo-progresso").textContent = progresso.meta_atingida
      ? "Meta atingida"
      : numero(progresso.minutos_restantes) + " min para atingir a meta";
    medidor.hidden = false;
    mensagem.hidden = true;
  } catch (erro) {
    if (consulta === consultaProgresso) mensagem.textContent = erro.message;
  }
}

function verProgresso(id) {
  selecaoProgresso.value = id;
  if (window.location.hash === "#progresso") {
    mostrarTela(true);
  } else {
    window.location.hash = "progresso";
  }
  atualizarProgresso();
}

function acoesRegistro(tipo, registro) {
  const acoes = criarElemento("div", "acoes-registro");
  if (modoPages) return acoes;
  acoes.append(
    criarBotao("Editar", () => abrirFormulario(tipo, registro)),
    criarBotao("Excluir", () => abrirExclusao(tipo, registro), "botao-excluir")
  );
  return acoes;
}

function renderizarDesafios() {
  const hoje = dataDeHoje();
  const filtro = filtroDesafios.value;
  const desafios = registros.desafios.filter((desafio) => filtro === "todos" || estadoDoDesafio(desafio, hoje) === filtro);
  const lista = document.querySelector("#lista-desafios");
  const contagem = desafios.length === 1 ? "1 desafio" : numero(desafios.length) + " desafios";
  document.querySelector("#contagem-desafios").textContent = contagem;
  lista.replaceChildren();

  if (!desafios.length) {
    const texto = registros.desafios.length
      ? "Nenhum desafio nesse período."
      : "Crie o primeiro desafio e convide os participantes a se inscrever.";
    lista.append(criarElemento("p", "estado-vazio", texto));
  }

  desafios.slice().reverse().forEach((desafio) => {
    const cartao = criarElemento("article", "cartao-desafio");
    const topo = criarElemento("div", "cartao-topo");
    topo.append(criarElemento("span", "", nomeModalidade(desafio.id_modalidade)), seloPeriodo(desafio, hoje));
    const meta = criarElemento("p", "cartao-meta", numero(desafio.meta_minutos) + " ");
    meta.append(criarElemento("small", "", "min por pessoa"));
    cartao.append(
      topo,
      criarElemento("h2", "", desafio.titulo),
      criarElemento("p", "cartao-periodo", periodo(desafio)),
      meta
    );
    if (!modoPages) {
      const acoes = acoesRegistro("desafios", desafio);
      acoes.prepend(criarBotao("Inscrever", () => abrirFormulario("inscricoes", null, { id_desafio: desafio.id_desafio }), "botao-primario"));
      cartao.append(acoes);
    }
    lista.append(cartao);
  });
}

function renderizarTabela(tipo, colunas, montarLinha, textoVazio) {
  const lista = document.querySelector("#lista-" + tipo);
  const cabecalhos = lista.parentElement.querySelectorAll("th");
  lista.replaceChildren();
  if (!registros[tipo].length) {
    const linha = criarElemento("tr", "linha-vazia");
    const celula = criarElemento("td", "", textoVazio);
    celula.colSpan = colunas;
    linha.append(celula);
    lista.append(linha);
    return;
  }

  registros[tipo].slice().reverse().forEach((registro) => {
    const linha = criarElemento("tr");
    montarLinha(registro).forEach((valor, indice) => {
      const celula = criarElemento("td", "", valor);
      celula.dataset.rotulo = cabecalhos[indice].textContent;
      linha.append(celula);
    });
    if (!modoPages || tipo === "inscricoes") {
      const acoes = acoesRegistro(tipo, registro);
      if (tipo === "inscricoes") {
        acoes.prepend(criarBotao("Ver progresso", () => verProgresso(registro.id_inscricao)));
      }
      const ultima = criarElemento("td");
      ultima.append(acoes);
      linha.append(ultima);
    }
    lista.append(linha);
  });
}

function renderizarTabelas() {
  renderizarTabela("participantes", 4, (p) => [
    p.nome, p.email,
    numero(registros.inscricoes.filter((inscricao) => inscricao.id_participante === p.id_participante).length),
  ], "Nenhum participante cadastrado.");

  renderizarTabela("modalidades", 3, (m) => [
    m.nome,
    numero(registros.desafios.filter((desafio) => desafio.id_modalidade === m.id_modalidade).length),
  ], "Nenhuma modalidade cadastrada.");

  renderizarTabela("inscricoes", 4, (i) => [
    nomeParticipante(i.id_participante), tituloDesafio(i.id_desafio), formatarData(i.data_inscricao),
  ], "Nenhuma inscrição cadastrada.");

  renderizarTabela("atividades", 5, (r) => {
    const inscricao = buscar("inscricoes", r.id_inscricao);
    return [
      inscricao ? nomeParticipante(inscricao.id_participante) : "—",
      inscricao ? tituloDesafio(inscricao.id_desafio) : "—",
      formatarData(r.data_atividade),
      numero(r.duracao_minutos) + " min",
    ];
  }, "Nenhuma atividade registrada.");
}

function prepararFormulario(titulo, apoio, botao, perigo = false) {
  document.querySelector("#titulo-dialogo").textContent = titulo;
  document.querySelector("#apoio-dialogo").textContent = apoio;
  document.querySelector("#erro-dialogo").hidden = true;
  salvar.textContent = botao;
  salvar.classList.toggle("botao-perigo", perigo);
  salvar.classList.toggle("botao-primario", !perigo);

  const formulario = criarElemento("form", "formulario");
  formulario.id = "formulario-registro";
  document.querySelector("#campos-dialogo").replaceChildren(formulario);
  return formulario;
}

function exibirJanela(formulario) {
  if (!dialogo.open) dialogo.showModal();
  const primeiroCampo = formulario.querySelector("input, select");
  if (primeiroCampo) {
    primeiroCampo.focus();
  } else {
    dialogo.querySelector(".janela-acoes [data-fechar]").focus();
  }
}

function requisito(tipo) {
  if (tipo === "desafios" && !registros.modalidades.length) return "modalidades";
  if (tipo === "inscricoes" && !registros.participantes.length) return "participantes";
  if (tipo === "inscricoes" && !registros.desafios.length) return "desafios";
  if (tipo === "atividades" && !registros.inscricoes.length) return "inscricoes";
  return "";
}

function ajustarPeriodoAtividade(formulario) {
  const campoInscricao = formulario.elements.id_inscricao;
  const data = formulario.elements.data_atividade;
  const inscricao = buscar("inscricoes", campoInscricao.value);
  const desafio = inscricao && buscar("desafios", inscricao.id_desafio);
  data.min = desafio ? desafio.data_inicio : "";
  data.max = desafio ? desafio.data_fim : "";
  formulario.querySelector("#periodo-atividade").textContent = desafio ? "Período permitido de " + periodo(desafio) : "";
  if (desafio && !data.value) {
    const hoje = dataDeHoje();
    if (hoje < data.min) {
      data.value = data.min;
    } else if (hoje > data.max) {
      data.value = data.max;
    } else {
      data.value = hoje;
    }
  }
}

function preencherFormulario(formulario, tipo, valores) {
  if (tipo === "desafios") {
    preencherOpcoes(formulario.elements.id_modalidade, registros.modalidades, "id_modalidade", (m) => m.nome, "Selecione uma modalidade");
    formulario.elements.data_inicio.value = dataDeHoje();
  } else if (tipo === "inscricoes") {
    preencherOpcoes(formulario.elements.id_participante, registros.participantes, "id_participante", (p) => p.nome + " · " + p.email, "Selecione um participante");
    preencherOpcoes(formulario.elements.id_desafio, registros.desafios, "id_desafio", (d) => d.titulo + " · " + periodo(d), "Selecione um desafio");
    formulario.elements.data_inscricao.value = dataDeHoje();
  } else if (tipo === "atividades") {
    preencherOpcoes(formulario.elements.id_inscricao, registros.inscricoes, "id_inscricao", rotuloInscricao, "Selecione uma inscrição");
    formulario.elements.id_inscricao.addEventListener("change", () => ajustarPeriodoAtividade(formulario));
  }

  formulario.querySelectorAll("[name]").forEach((campo) => {
    if (valores[campo.name] !== undefined) campo.value = valores[campo.name];
  });

  if (tipo === "atividades") ajustarPeriodoAtividade(formulario);
}

function lerFormulario(formulario) {
  const dados = {};
  for (const campo of formulario.querySelectorAll("[name]")) {
    const texto = campo.value.trim();
    if (!texto) throw new Error("Preencha todos os campos.");
    if (campo.type === "number" || campo.tagName === "SELECT") {
      const valor = Number(texto);
      if (!Number.isSafeInteger(valor) || valor < 1) throw new Error("Informe um número inteiro positivo válido.");
      dados[campo.name] = valor;
    } else {
      dados[campo.name] = texto;
    }
  }
  if (dados.data_inicio && dados.data_fim < dados.data_inicio) {
    throw new Error("A data de fim deve ser igual ou posterior à data de início.");
  }
  return dados;
}

function abrirFormulario(tipo, registro = null, valores = {}) {
  if (!dadosDisponiveis) {
    notificar("Aguarde o carregamento ou tente conectar novamente.");
    return;
  }

  const pendencia = requisito(tipo);
  if (pendencia) {
    const config = colecoes[pendencia];
    const formulario = prepararFormulario(
      "Antes de continuar",
      "Este cadastro precisa de " + config.nome + ". Faça o cadastro necessário primeiro.",
      config.novo
    );
    formulario.addEventListener("submit", (evento) => {
      evento.preventDefault();
      abrirFormulario(pendencia);
    });
    exibirJanela(formulario);
    return;
  }

  const config = colecoes[tipo];
  const id = registro ? registro[config.id] : null;
  const temAtividades = tipo === "inscricoes" && registro
    && registros.atividades.some((atividade) => atividade.id_inscricao === id);
  const apoio = temAtividades
    ? "Com atividades registradas, apenas a data da inscrição pode ser editada."
    : "Todos os campos são obrigatórios.";
  const formulario = prepararFormulario(id ? "Editar " + config.nome : config.novo, apoio, "Salvar");
  formulario.append(document.querySelector("#campos-" + tipo).content.cloneNode(true));
  preencherFormulario(formulario, tipo, registro || valores);
  if (temAtividades) {
    formulario.elements.id_participante.disabled = true;
    formulario.elements.id_desafio.disabled = true;
  }
  formulario.addEventListener("submit", (evento) => {
    evento.preventDefault();
    executarOperacao(async () => {
      const dados = lerFormulario(formulario);
      const caminho = "/" + tipo + (id ? "/" + id : "");
      const resultado = await solicitar(caminho, id ? "PUT" : "POST", dados);
      if (tipo === "atividades") return dados.id_inscricao;
      if (tipo === "inscricoes") return resultado.id_inscricao;
    }, id ? "Alterações salvas." : "Cadastro concluído.");
  });
  exibirJanela(formulario);
}

function abrirExclusao(tipo, registro) {
  if (!dadosDisponiveis) {
    notificar("Atualize as listas antes de excluir um registro.");
    return;
  }

  const config = colecoes[tipo];
  const formulario = prepararFormulario(
    "Excluir " + config.nome + "?",
    "O registro será removido do banco. Confirme para continuar.",
    "Excluir",
    true
  );
  formulario.addEventListener("submit", (evento) => {
    evento.preventDefault();
    executarOperacao(async () => {
      await solicitar("/" + tipo + "/" + registro[config.id], "DELETE");
    }, "Registro excluído.");
  });
  exibirJanela(formulario);
}

async function executarOperacao(operacao, sucesso) {
  if (enviando) return;
  enviando = true;
  const erroDialogo = document.querySelector("#erro-dialogo");
  const botoesFechar = dialogo.querySelectorAll("[data-fechar]");
  const texto = salvar.textContent;
  erroDialogo.hidden = true;
  salvar.disabled = true;
  salvar.textContent = "Aguarde…";
  botoesFechar.forEach((botao) => { botao.disabled = true; });

  try {
    const idInscricao = await operacao();
    dialogo.close();
    await carregarDados(idInscricao);
    notificar(sucesso);
  } catch (erro) {
    erroDialogo.textContent = erro.message;
    erroDialogo.hidden = false;
  } finally {
    enviando = false;
    salvar.disabled = false;
    salvar.textContent = texto;
    botoesFechar.forEach((botao) => { botao.disabled = false; });
  }
}

document.querySelectorAll("[data-novo]").forEach((botao) => {
  botao.addEventListener("click", () => abrirFormulario(botao.dataset.novo));
});

dialogo.querySelectorAll("[data-fechar]").forEach((botao) => {
  botao.addEventListener("click", () => dialogo.close());
});

dialogo.addEventListener("cancel", (evento) => {
  if (enviando) evento.preventDefault();
});

filtroDesafios.addEventListener("change", () => {
  if (dadosDisponiveis) renderizarDesafios();
});
selecaoProgresso.addEventListener("change", atualizarProgresso);
document.querySelector("#registrar-progresso").addEventListener("click", () => {
  abrirFormulario("atividades", null, { id_inscricao: Number(selecaoProgresso.value) });
});
document.querySelector("#recarregar").addEventListener("click", () => carregarDados());
document.querySelector("#fechar-notificacao").addEventListener("click", () => {
  document.querySelector("#notificacao").hidden = true;
});
window.addEventListener("hashchange", () => mostrarTela(true));

mostrarTela(false);
carregarDados();
