import sqlite3
import sys

from flask import Flask, jsonify, render_template, request

from dao import (
    CAMINHO_BANCO,
    RAIZ_PROJETO,
    DesafioDAO,
    InscricaoDAO,
    ModalidadeDAO,
    ParticipanteDAO,
    RegistroAtividadeDAO,
    data_valida,
    preparar_banco,
)
from demonstracao import preparar_demonstracao
from models import Desafio, Inscricao, Modalidade, Participante, RegistroAtividade


app = Flask(__name__)
MODO_DEMO = __name__ == "__main__" and "--demo" in sys.argv[1:]
BANCO = RAIZ_PROJETO / "ritmofit-demo.db" if MODO_DEMO else CAMINHO_BANCO
participante_dao = ParticipanteDAO(BANCO)
modalidade_dao = ModalidadeDAO(BANCO)
desafio_dao = DesafioDAO(BANCO)
inscricao_dao = InscricaoDAO(BANCO)
registro_dao = RegistroAtividadeDAO(BANCO)

LIMITE_INTEIRO_SQLITE = 9223372036854775807


def ler_dados():
    dados = request.get_json(silent=True)
    if type(dados) != dict:
        raise ValueError("Envie os dados em um objeto JSON.")
    return dados


def ler_texto(dados, campo, limite=None):
    valor = dados.get(campo)
    if type(valor) != str or not valor.strip():
        raise ValueError(f"Preencha o campo {campo} com texto.")
    valor = valor.strip()
    if limite and len(valor) > limite:
        raise ValueError(f"O campo {campo} aceita até {limite} caracteres.")
    return valor


def ler_inteiro(dados, campo):
    valor = dados.get(campo)
    if type(valor) != int or not 1 <= valor <= LIMITE_INTEIRO_SQLITE:
        raise ValueError(f"Informe um número inteiro positivo no campo {campo}.")
    return valor


def ler_data(dados, campo):
    valor = ler_texto(dados, campo)
    if not data_valida(valor, BANCO):
        raise ValueError(f"Informe uma data válida no formato AAAA-MM-DD em {campo}.")
    return valor


@app.route("/")
def inicio():
    return render_template("index.html", modo_demo=MODO_DEMO)


@app.route("/api")
def status_api():
    return jsonify({"projeto": "RitmoFit", "mensagem": "API em execução."})


def id_valido(id_registro):
    return 1 <= id_registro <= LIMITE_INTEIRO_SQLITE


def excluir(dao, id_registro, vinculo):
    if not id_valido(id_registro):
        return jsonify({"erro": "Registro não encontrado."}), 404
    try:
        if not dao.remover(id_registro):
            return jsonify({"erro": "Registro não encontrado."}), 404
    except sqlite3.IntegrityError:
        return jsonify({"erro": vinculo}), 409
    return jsonify({"mensagem": "Registro excluído."})


@app.route("/participantes", methods=["GET"])
def listar_participantes():
    participantes = participante_dao.buscar_todos()
    return jsonify([participante.to_dict() for participante in participantes])


@app.route("/participantes", methods=["POST"])
@app.route("/participantes/<int:id_participante>", methods=["PUT"])
def cadastrar_participante(id_participante=None):
    try:
        dados = ler_dados()
        nome = ler_texto(dados, "nome", 100)
        email = ler_texto(dados, "email", 100)
        participante = Participante(id_participante, nome, email)
        if id_participante is not None:
            if not id_valido(id_participante) or not participante_dao.atualizar(id_participante, participante):
                return jsonify({"erro": "Participante não encontrado."}), 404
            return jsonify({"id_participante": id_participante})
        id_participante = participante_dao.inserir(participante)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    except sqlite3.IntegrityError:
        return jsonify({"erro": "Já existe um participante com esse e-mail."}), 409
    return jsonify({"id_participante": id_participante}), 201


@app.route("/participantes/<int:id_participante>", methods=["DELETE"])
def excluir_participante(id_participante):
    return excluir(participante_dao, id_participante, "Exclua as inscrições deste participante primeiro.")


@app.route("/modalidades", methods=["GET"])
def listar_modalidades():
    modalidades = modalidade_dao.buscar_todos()
    return jsonify([modalidade.to_dict() for modalidade in modalidades])


@app.route("/modalidades", methods=["POST"])
@app.route("/modalidades/<int:id_modalidade>", methods=["PUT"])
def cadastrar_modalidade(id_modalidade=None):
    try:
        dados = ler_dados()
        modalidade = Modalidade(id_modalidade, ler_texto(dados, "nome", 50))
        if id_modalidade is not None:
            if not id_valido(id_modalidade) or not modalidade_dao.atualizar(id_modalidade, modalidade):
                return jsonify({"erro": "Modalidade não encontrada."}), 404
            return jsonify({"id_modalidade": id_modalidade})
        id_modalidade = modalidade_dao.inserir(modalidade)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    except sqlite3.IntegrityError:
        return jsonify({"erro": "Essa modalidade já está cadastrada."}), 409
    return jsonify({"id_modalidade": id_modalidade}), 201


@app.route("/modalidades/<int:id_modalidade>", methods=["DELETE"])
def excluir_modalidade(id_modalidade):
    return excluir(modalidade_dao, id_modalidade, "Há desafios usando esta modalidade.")


@app.route("/desafios", methods=["GET"])
def listar_desafios():
    desafios = desafio_dao.buscar_todos()
    return jsonify([desafio.to_dict() for desafio in desafios])


@app.route("/desafios", methods=["POST"])
@app.route("/desafios/<int:id_desafio>", methods=["PUT"])
def cadastrar_desafio(id_desafio=None):
    try:
        dados = ler_dados()
        id_modalidade = ler_inteiro(dados, "id_modalidade")
        titulo = ler_texto(dados, "titulo", 100)
        data_inicio = ler_data(dados, "data_inicio")
        data_fim = ler_data(dados, "data_fim")
        meta_minutos = ler_inteiro(dados, "meta_minutos")

        if data_fim < data_inicio:
            raise ValueError("A data de fim deve ser igual ou posterior à data de início.")
        if modalidade_dao.buscar_por_id(id_modalidade) is None:
            return jsonify({"erro": "Modalidade não encontrada."}), 404

        desafio = Desafio(id_desafio, id_modalidade, titulo, data_inicio, data_fim, meta_minutos)
        if id_desafio is not None:
            if not id_valido(id_desafio) or desafio_dao.buscar_por_id(id_desafio) is None:
                return jsonify({"erro": "Desafio não encontrado."}), 404
            if not desafio_dao.atualizar(id_desafio, desafio):
                return jsonify({"erro": "O período precisa incluir as atividades já registradas."}), 409
            return jsonify({"id_desafio": id_desafio})
        id_desafio = desafio_dao.inserir(desafio)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    except sqlite3.IntegrityError:
        return jsonify({"erro": "Confira a modalidade e os dados do desafio."}), 400
    return jsonify({"id_desafio": id_desafio}), 201


@app.route("/desafios/<int:id_desafio>", methods=["DELETE"])
def excluir_desafio(id_desafio):
    return excluir(desafio_dao, id_desafio, "Exclua as inscrições deste desafio primeiro.")


@app.route("/inscricoes", methods=["GET"])
def listar_inscricoes():
    inscricoes = inscricao_dao.buscar_todos()
    return jsonify([inscricao.to_dict() for inscricao in inscricoes])


@app.route("/inscricoes", methods=["POST"])
@app.route("/inscricoes/<int:id_inscricao>", methods=["PUT"])
def cadastrar_inscricao(id_inscricao=None):
    try:
        dados = ler_dados()
        id_participante = ler_inteiro(dados, "id_participante")
        id_desafio = ler_inteiro(dados, "id_desafio")
        data_inscricao = ler_data(dados, "data_inscricao")

        if participante_dao.buscar_por_id(id_participante) is None:
            return jsonify({"erro": "Participante não encontrado."}), 404
        if desafio_dao.buscar_por_id(id_desafio) is None:
            return jsonify({"erro": "Desafio não encontrado."}), 404

        inscricao = Inscricao(id_inscricao, id_participante, id_desafio, data_inscricao)
        if id_inscricao is not None:
            if not id_valido(id_inscricao) or inscricao_dao.buscar_por_id(id_inscricao) is None:
                return jsonify({"erro": "Inscrição não encontrada."}), 404
            if not inscricao_dao.atualizar(id_inscricao, inscricao):
                return jsonify({"erro": "Inscrições com atividades podem ter apenas a data editada."}), 409
            return jsonify({"id_inscricao": id_inscricao})
        id_inscricao = inscricao_dao.inserir(inscricao)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    except sqlite3.IntegrityError:
        return jsonify({"erro": "O participante já está inscrito nesse desafio."}), 409
    return jsonify({"id_inscricao": id_inscricao}), 201


@app.route("/inscricoes/<int:id_inscricao>", methods=["DELETE"])
def excluir_inscricao(id_inscricao):
    return excluir(inscricao_dao, id_inscricao, "Exclua as atividades desta inscrição primeiro.")


@app.route("/atividades", methods=["GET"])
def listar_atividades():
    registros = registro_dao.buscar_todos()
    return jsonify([registro.to_dict() for registro in registros])


@app.route("/atividades", methods=["POST"])
@app.route("/atividades/<int:id_registro>", methods=["PUT"])
def cadastrar_atividade(id_registro=None):
    try:
        dados = ler_dados()
        id_inscricao = ler_inteiro(dados, "id_inscricao")
        data_atividade = ler_data(dados, "data_atividade")
        duracao_minutos = ler_inteiro(dados, "duracao_minutos")

        inscricao = inscricao_dao.buscar_por_id(id_inscricao)
        if inscricao is None:
            return jsonify({"erro": "Inscrição não encontrada."}), 404
        desafio = desafio_dao.buscar_por_id(inscricao.id_desafio)
        if desafio is None:
            return jsonify({"erro": "Desafio da inscrição não encontrado."}), 404
        if not desafio.aceita_data(data_atividade):
            raise ValueError("A atividade deve ocorrer dentro do período do desafio.")

        registro = RegistroAtividade(id_registro, id_inscricao, data_atividade, duracao_minutos)
        if id_registro is not None:
            if not id_valido(id_registro) or registro_dao.buscar_por_id(id_registro) is None:
                return jsonify({"erro": "Atividade não encontrada."}), 404
            if not registro_dao.atualizar(id_registro, registro):
                return jsonify({"erro": "A atividade deve ocorrer dentro do período do desafio."}), 409
            return jsonify({"id_registro": id_registro})
        id_registro = registro_dao.inserir(registro)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    except sqlite3.IntegrityError:
        return jsonify({"erro": "Confira a inscrição e os dados da atividade."}), 400
    return jsonify({"id_registro": id_registro}), 201


@app.route("/atividades/<int:id_registro>", methods=["DELETE"])
def excluir_atividade(id_registro):
    return excluir(registro_dao, id_registro, "A atividade está vinculada a outro cadastro.")


@app.route("/inscricoes/<int:id_inscricao>/progresso", methods=["GET"])
def consultar_progresso(id_inscricao):
    inscricao = None
    if id_valido(id_inscricao):
        inscricao = inscricao_dao.buscar_por_id(id_inscricao)
    if inscricao is None:
        return jsonify({"erro": "Inscrição não encontrada."}), 404
    desafio = desafio_dao.buscar_por_id(inscricao.id_desafio)
    if desafio is None:
        return jsonify({"erro": "Desafio da inscrição não encontrado."}), 404

    registros = registro_dao.buscar_por_inscricao(id_inscricao)
    total = inscricao.total_minutos(registros)
    return jsonify({
        "id_inscricao": id_inscricao,
        "total_minutos": total,
        "meta_minutos": desafio.meta_minutos,
        "minutos_restantes": max(0, desafio.meta_minutos - total),
        "meta_atingida": inscricao.meta_atingida(desafio, registros),
    })


if __name__ == "__main__":
    preparar_banco(BANCO)
    if MODO_DEMO:
        preparar_demonstracao(BANCO)
    app.run()
