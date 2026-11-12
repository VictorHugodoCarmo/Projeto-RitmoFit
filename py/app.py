import sqlite3

from flask import Flask, jsonify, request

from dao import (
    DesafioDAO,
    InscricaoDAO,
    ModalidadeDAO,
    ParticipanteDAO,
    RegistroAtividadeDAO,
    data_valida,
    preparar_banco,
)
from models import Desafio, Inscricao, Modalidade, Participante, RegistroAtividade


app = Flask(__name__)
participante_dao = ParticipanteDAO()
modalidade_dao = ModalidadeDAO()
desafio_dao = DesafioDAO()
inscricao_dao = InscricaoDAO()
registro_dao = RegistroAtividadeDAO()

LIMITE_INTEIRO_SQLITE = 9223372036854775807


def ler_dados():
    dados = request.json
    if type(dados) != dict:
        raise ValueError("Envie os dados em um objeto JSON.")
    return dados


def ler_texto(dados, campo):
    valor = dados.get(campo)
    if type(valor) != str or not valor.strip():
        raise ValueError(f"Preencha o campo {campo} com texto.")
    return valor.strip()


def ler_inteiro(dados, campo):
    valor = dados.get(campo)
    if type(valor) != int or not 1 <= valor <= LIMITE_INTEIRO_SQLITE:
        raise ValueError(f"Informe um número inteiro positivo no campo {campo}.")
    return valor


def ler_data(dados, campo):
    valor = ler_texto(dados, campo)
    if not data_valida(valor):
        raise ValueError(f"Informe uma data válida no formato AAAA-MM-DD em {campo}.")
    return valor


@app.route("/")
def inicio():
    return jsonify({"projeto": "RitmoFit", "mensagem": "API em execução."})


@app.route("/participantes", methods=["GET"])
def listar_participantes():
    participantes = participante_dao.buscar_todos()
    return jsonify([participante.to_dict() for participante in participantes])


@app.route("/participantes", methods=["POST"])
def cadastrar_participante():
    try:
        dados = ler_dados()
        nome = ler_texto(dados, "nome")
        email = ler_texto(dados, "email")
        participante = Participante(None, nome, email)
        id_participante = participante_dao.inserir(participante)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    except sqlite3.IntegrityError:
        return jsonify({"erro": "Já existe um participante com esse e-mail."}), 409
    return jsonify({"id_participante": id_participante}), 201


@app.route("/modalidades", methods=["GET"])
def listar_modalidades():
    modalidades = modalidade_dao.buscar_todos()
    return jsonify([modalidade.to_dict() for modalidade in modalidades])


@app.route("/modalidades", methods=["POST"])
def cadastrar_modalidade():
    try:
        dados = ler_dados()
        modalidade = Modalidade(None, ler_texto(dados, "nome"))
        id_modalidade = modalidade_dao.inserir(modalidade)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    except sqlite3.IntegrityError:
        return jsonify({"erro": "Essa modalidade já está cadastrada."}), 409
    return jsonify({"id_modalidade": id_modalidade}), 201


@app.route("/desafios", methods=["GET"])
def listar_desafios():
    desafios = desafio_dao.buscar_todos()
    return jsonify([desafio.to_dict() for desafio in desafios])


@app.route("/desafios", methods=["POST"])
def cadastrar_desafio():
    try:
        dados = ler_dados()
        id_modalidade = ler_inteiro(dados, "id_modalidade")
        titulo = ler_texto(dados, "titulo")
        data_inicio = ler_data(dados, "data_inicio")
        data_fim = ler_data(dados, "data_fim")
        meta_minutos = ler_inteiro(dados, "meta_minutos")

        if data_fim < data_inicio:
            raise ValueError("A data de fim deve ser igual ou posterior à data de início.")
        if modalidade_dao.buscar_por_id(id_modalidade) is None:
            return jsonify({"erro": "Modalidade não encontrada."}), 404

        desafio = Desafio(None, id_modalidade, titulo, data_inicio, data_fim, meta_minutos)
        id_desafio = desafio_dao.inserir(desafio)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    except sqlite3.IntegrityError:
        return jsonify({"erro": "Confira a modalidade e os dados do desafio."}), 400
    return jsonify({"id_desafio": id_desafio}), 201


@app.route("/inscricoes", methods=["GET"])
def listar_inscricoes():
    inscricoes = inscricao_dao.buscar_todos()
    return jsonify([inscricao.to_dict() for inscricao in inscricoes])


@app.route("/inscricoes", methods=["POST"])
def cadastrar_inscricao():
    try:
        dados = ler_dados()
        id_participante = ler_inteiro(dados, "id_participante")
        id_desafio = ler_inteiro(dados, "id_desafio")
        data_inscricao = ler_data(dados, "data_inscricao")

        if participante_dao.buscar_por_id(id_participante) is None:
            return jsonify({"erro": "Participante não encontrado."}), 404
        if desafio_dao.buscar_por_id(id_desafio) is None:
            return jsonify({"erro": "Desafio não encontrado."}), 404

        inscricao = Inscricao(None, id_participante, id_desafio, data_inscricao)
        id_inscricao = inscricao_dao.inserir(inscricao)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    except sqlite3.IntegrityError:
        return jsonify({"erro": "O participante já está inscrito nesse desafio."}), 409
    return jsonify({"id_inscricao": id_inscricao}), 201


@app.route("/atividades", methods=["GET"])
def listar_atividades():
    registros = registro_dao.buscar_todos()
    return jsonify([registro.to_dict() for registro in registros])


@app.route("/atividades", methods=["POST"])
def cadastrar_atividade():
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

        registro = RegistroAtividade(None, id_inscricao, data_atividade, duracao_minutos)
        id_registro = registro_dao.inserir(registro)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    except sqlite3.IntegrityError:
        return jsonify({"erro": "Confira a inscrição e os dados da atividade."}), 400
    return jsonify({"id_registro": id_registro}), 201


@app.route("/inscricoes/<int:id_inscricao>/progresso", methods=["GET"])
def consultar_progresso(id_inscricao):
    inscricao = None
    if 1 <= id_inscricao <= LIMITE_INTEIRO_SQLITE:
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
    preparar_banco()
    app.run()
