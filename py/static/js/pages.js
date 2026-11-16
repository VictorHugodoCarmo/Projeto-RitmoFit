const CHAVE_PAGES = "Projeto-RitmoFit:demonstracao:v2";
const CHAVE_PAGES_ANTERIOR = "Projeto-RitmoFit:demonstracao:v1";

const vinculosPages = {
  participantes: ["inscricoes", "id_participante", "Exclua as inscrições deste participante primeiro."],
  modalidades: ["desafios", "id_modalidade", "Há desafios usando esta modalidade."],
  desafios: ["inscricoes", "id_desafio", "Exclua as inscrições deste desafio primeiro."],
  inscricoes: ["atividades", "id_inscricao", "Exclua as atividades desta inscrição primeiro."],
};

function lerBancoPages(chave = CHAVE_PAGES) {
  try {
    return JSON.parse(localStorage.getItem(chave));
  } catch {
    throw new Error("Não foi possível ler os cadastros neste navegador.");
  }
}

function salvarBancoPages(banco) {
  try {
    localStorage.setItem(CHAVE_PAGES, JSON.stringify(banco));
  } catch {
    throw new Error("Não foi possível salvar. Verifique o armazenamento do navegador.");
  }
}

function dataUTC(data) {
  return new Date(data + "T00:00:00Z");
}

function registrosDoDesafioPages(listas, idDesafio) {
  const desafio = listas.desafios.find((item) => item.id_desafio === idDesafio);
  const inscricoes = listas.inscricoes.filter((item) => item.id_desafio === idDesafio);
  const idsInscricoes = new Set(inscricoes.map((item) => item.id_inscricao));
  const atividades = listas.atividades.filter((item) => idsInscricoes.has(item.id_inscricao));
  return { desafio, inscricoes, atividades };
}

function ajustarDatasExemplosPages(banco, hoje) {
  const exemplos = banco.exemplos;
  if (exemplos.data === hoje || !exemplos.desafios.length) return false;

  const diferenca = dataUTC(hoje) - dataUTC(exemplos.data);
  function deslocar(data) {
    return new Date(dataUTC(data).getTime() + diferenca).toISOString().slice(0, 10);
  }

  for (const idDesafio of exemplos.desafios) {
    const { desafio, inscricoes, atividades } = registrosDoDesafioPages(banco.listas, idDesafio);
    desafio.data_inicio = deslocar(desafio.data_inicio);
    desafio.data_fim = deslocar(desafio.data_fim);
    for (const inscricao of inscricoes) inscricao.data_inscricao = deslocar(inscricao.data_inscricao);
    for (const atividade of atividades) atividade.data_atividade = deslocar(atividade.data_atividade);
  }
  exemplos.data = hoje;
  return true;
}

async function iniciarBancoPages() {
  const atual = lerBancoPages();
  if (atual) {
    if (ajustarDatasExemplosPages(atual, dataDeHoje())) salvarBancoPages(atual);
    return;
  }
  const banco = { listas: {}, ultimosIds: {} };

  for (const tipo of Object.keys(colecoes)) {
    const resposta = await fetch("./dados/" + tipo + ".json");
    if (!resposta.ok) throw new Error("Não foi possível carregar os exemplos.");
    const lista = await resposta.json();
    const chave = colecoes[tipo].id;
    banco.listas[tipo] = lista;
    banco.ultimosIds[tipo] = lista.reduce((maior, item) => Math.max(maior, item[chave]), 0);
  }

  if (lerBancoPages()) return;

  const anterior = lerBancoPages(CHAVE_PAGES_ANTERIOR);
  const destino = anterior || banco;
  // Um desafio editado ou com novos registros conserva todas as suas datas.
  const desafios = banco.listas.desafios.map((item) => item.id_desafio).filter((id) =>
    JSON.stringify(registrosDoDesafioPages(destino.listas, id))
    === JSON.stringify(registrosDoDesafioPages(banco.listas, id))
  );
  const data = banco.listas.atividades.reduce((ultima, item) =>
    item.data_atividade > ultima ? item.data_atividade : ultima, ""
  );
  destino.exemplos = { data, desafios };
  ajustarDatasExemplosPages(destino, dataDeHoje());
  salvarBancoPages(destino);
}

function fixarDatasPages(banco, tipo, registro) {
  if (!registro) return;
  let idDesafio = registro.id_desafio;
  if (tipo === "atividades") {
    const inscricao = banco.listas.inscricoes.find((item) => item.id_inscricao === registro.id_inscricao);
    idDesafio = inscricao.id_desafio;
  }
  if (idDesafio === undefined) return;
  banco.exemplos.desafios = banco.exemplos.desafios.filter((id) => id !== idDesafio);
}

function buscarNoBancoPages(listas, tipo, id, erro) {
  const chave = colecoes[tipo].id;
  const registro = listas[tipo].find((item) => item[chave] === id);
  if (!registro) throw new Error(erro);
  return registro;
}

function foraDoPeriodo(desafio, data) {
  return data < desafio.data_inicio || data > desafio.data_fim;
}

function validarRegistroPages(listas, tipo, dados, atual) {
  if (tipo === "participantes") {
    if (listas.participantes.some((p) => p !== atual && p.email === dados.email)) {
      throw new Error("Já existe um participante com esse e-mail.");
    }
  } else if (tipo === "modalidades") {
    if (listas.modalidades.some((m) => m !== atual && m.nome === dados.nome)) {
      throw new Error("Essa modalidade já está cadastrada.");
    }
  } else if (tipo === "desafios") {
    buscarNoBancoPages(listas, "modalidades", dados.id_modalidade, "Modalidade não encontrada.");
    if (atual) {
      const inscricoes = listas.inscricoes.filter((i) => i.id_desafio === atual.id_desafio);
      const fora = listas.atividades.some((atividade) =>
        foraDoPeriodo(dados, atividade.data_atividade)
        && inscricoes.some((i) => i.id_inscricao === atividade.id_inscricao)
      );
      if (fora) throw new Error("O período precisa incluir as atividades já registradas.");
    }
  } else if (tipo === "inscricoes") {
    buscarNoBancoPages(listas, "participantes", dados.id_participante, "Participante não encontrado.");
    buscarNoBancoPages(listas, "desafios", dados.id_desafio, "Desafio não encontrado.");
    const repetida = listas.inscricoes.some((i) =>
      i !== atual && i.id_participante === dados.id_participante && i.id_desafio === dados.id_desafio
    );
    if (repetida) throw new Error("O participante já está inscrito nesse desafio.");
    if (atual && (atual.id_participante !== dados.id_participante || atual.id_desafio !== dados.id_desafio)
      && listas.atividades.some((r) => r.id_inscricao === atual.id_inscricao)) {
      throw new Error("Inscrições com atividades podem ter apenas a data editada.");
    }
  } else if (tipo === "atividades") {
    const inscricao = buscarNoBancoPages(listas, "inscricoes", dados.id_inscricao, "Inscrição não encontrada.");
    const desafio = buscarNoBancoPages(listas, "desafios", inscricao.id_desafio, "Desafio não encontrado.");
    if (foraDoPeriodo(desafio, dados.data_atividade)) {
      throw new Error("A atividade deve ocorrer dentro do período do desafio.");
    }
  }
}

function progressoPages(listas, id) {
  const inscricao = buscarNoBancoPages(listas, "inscricoes", id, "Inscrição não encontrada.");
  const desafio = buscarNoBancoPages(listas, "desafios", inscricao.id_desafio, "Desafio não encontrado.");
  const total = listas.atividades
    .filter((atividade) => atividade.id_inscricao === id)
    .reduce((minutos, atividade) => minutos + atividade.duracao_minutos, 0);
  return {
    id_inscricao: id,
    total_minutos: total,
    meta_minutos: desafio.meta_minutos,
    minutos_restantes: Math.max(0, desafio.meta_minutos - total),
    meta_atingida: total >= desafio.meta_minutos,
  };
}

async function solicitarPages(caminho, metodo, dados) {
  try {
    await iniciarBancoPages();
  } catch (erro) {
    if (erro instanceof TypeError || erro instanceof SyntaxError) {
      throw new Error("Não foi possível carregar os dados de demonstração. Tente novamente.");
    }
    throw erro;
  }
  const banco = lerBancoPages();
  const [tipo, numeroId, acao] = caminho.slice(1).split("/");
  const lista = banco.listas[tipo];
  const chave = colecoes[tipo].id;
  const id = Number(numeroId);

  if (metodo === "GET") {
    return acao === "progresso" ? progressoPages(banco.listas, id) : lista;
  }

  const posicao = lista.findIndex((item) => item[chave] === id);
  if (metodo !== "POST" && posicao === -1) throw new Error("Registro não encontrado.");

  if (metodo === "DELETE") {
    const vinculo = vinculosPages[tipo];
    if (vinculo && banco.listas[vinculo[0]].some((item) => item[vinculo[1]] === id)) {
      throw new Error(vinculo[2]);
    }
    fixarDatasPages(banco, tipo, lista[posicao]);
    lista.splice(posicao, 1);
    salvarBancoPages(banco);
    return { mensagem: "Registro excluído." };
  }

  validarRegistroPages(banco.listas, tipo, dados, lista[posicao]);
  fixarDatasPages(banco, tipo, lista[posicao]);
  fixarDatasPages(banco, tipo, dados);
  if (metodo === "POST") {
    const novoId = banco.ultimosIds[tipo] + 1;
    banco.ultimosIds[tipo] = novoId;
    lista.push({ ...dados, [chave]: novoId });
    salvarBancoPages(banco);
    return { [chave]: novoId };
  }

  lista[posicao] = { ...dados, [chave]: id };
  salvarBancoPages(banco);
  return { [chave]: id };
}
