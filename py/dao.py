import sqlite3

from models import Desafio, Inscricao, Modalidade, Participante, RegistroAtividade


CAMINHO_BANCO = "ritmofit.db"


def abrir_conexao(caminho_banco):
    conexao = sqlite3.connect(caminho_banco)
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def preparar_banco(caminho_banco=CAMINHO_BANCO):
    conexao = abrir_conexao(caminho_banco)
    try:
        tabelas = conexao.execute(
            """
            SELECT name FROM sqlite_schema
            WHERE type = 'table'
              AND name IN ('participante', 'modalidade', 'desafio',
                           'inscricao', 'registro_atividade')
            """
        ).fetchall()
        if len(tabelas) == 5:
            return
        if tabelas:
            raise ValueError("O banco do RitmoFit está incompleto. Confira o arquivo ritmofit.db.")

        with open("banco/ritmofit.sql", encoding="utf-8-sig") as arquivo:
            esquema = arquivo.read()
        conexao.executescript(esquema)
    finally:
        conexao.close()


def consultar(caminho_banco, comando, parametros=()):
    conexao = abrir_conexao(caminho_banco)
    try:
        cursor = conexao.cursor()
        cursor.execute(comando, parametros)
        return cursor.fetchall()
    finally:
        conexao.close()


def inserir_no_banco(caminho_banco, comando, parametros):
    conexao = abrir_conexao(caminho_banco)
    try:
        cursor = conexao.cursor()
        cursor.execute(comando, parametros)
        conexao.commit()
        return cursor.lastrowid
    finally:
        conexao.close()


def data_valida(data):
    linhas = consultar(CAMINHO_BANCO, "SELECT date(?, '+0 days')", (data,))
    return linhas[0][0] == data


class ParticipanteDAO:
    def __init__(self, caminho_banco=CAMINHO_BANCO):
        self.caminho_banco = caminho_banco

    def inserir(self, participante):
        dados = participante.to_dict()
        return inserir_no_banco(
            self.caminho_banco,
            "INSERT INTO participante (nome, email) VALUES (?, ?)",
            (dados["nome"], dados["email"]),
        )

    def buscar_todos(self):
        linhas = consultar(
            self.caminho_banco,
            "SELECT id_participante, nome, email FROM participante ORDER BY id_participante",
        )
        return [Participante(*linha) for linha in linhas]

    def buscar_por_id(self, id_participante):
        linhas = consultar(
            self.caminho_banco,
            "SELECT id_participante, nome, email FROM participante WHERE id_participante = ?",
            (id_participante,),
        )
        if linhas:
            return Participante(*linhas[0])
        return None


class ModalidadeDAO:
    def __init__(self, caminho_banco=CAMINHO_BANCO):
        self.caminho_banco = caminho_banco

    def inserir(self, modalidade):
        dados = modalidade.to_dict()
        return inserir_no_banco(
            self.caminho_banco,
            "INSERT INTO modalidade (nome) VALUES (?)",
            (dados["nome"],),
        )

    def buscar_todos(self):
        linhas = consultar(
            self.caminho_banco,
            "SELECT id_modalidade, nome FROM modalidade ORDER BY id_modalidade",
        )
        return [Modalidade(*linha) for linha in linhas]

    def buscar_por_id(self, id_modalidade):
        linhas = consultar(
            self.caminho_banco,
            "SELECT id_modalidade, nome FROM modalidade WHERE id_modalidade = ?",
            (id_modalidade,),
        )
        if linhas:
            return Modalidade(*linhas[0])
        return None


class DesafioDAO:
    def __init__(self, caminho_banco=CAMINHO_BANCO):
        self.caminho_banco = caminho_banco

    def inserir(self, desafio):
        dados = desafio.to_dict()
        return inserir_no_banco(
            self.caminho_banco,
            """
            INSERT INTO desafio (id_modalidade, titulo, data_inicio, data_fim, meta_minutos)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                dados["id_modalidade"],
                dados["titulo"],
                dados["data_inicio"],
                dados["data_fim"],
                dados["meta_minutos"],
            ),
        )

    def buscar_todos(self):
        linhas = consultar(
            self.caminho_banco,
            """
            SELECT id_desafio, id_modalidade, titulo, data_inicio, data_fim, meta_minutos
            FROM desafio ORDER BY id_desafio
            """,
        )
        return [Desafio(*linha) for linha in linhas]

    def buscar_por_id(self, id_desafio):
        linhas = consultar(
            self.caminho_banco,
            """
            SELECT id_desafio, id_modalidade, titulo, data_inicio, data_fim, meta_minutos
            FROM desafio WHERE id_desafio = ?
            """,
            (id_desafio,),
        )
        if linhas:
            return Desafio(*linhas[0])
        return None


class InscricaoDAO:
    def __init__(self, caminho_banco=CAMINHO_BANCO):
        self.caminho_banco = caminho_banco

    def inserir(self, inscricao):
        dados = inscricao.to_dict()
        return inserir_no_banco(
            self.caminho_banco,
            """
            INSERT INTO inscricao (id_participante, id_desafio, data_inscricao)
            VALUES (?, ?, ?)
            """,
            (dados["id_participante"], dados["id_desafio"], dados["data_inscricao"]),
        )

    def buscar_todos(self):
        linhas = consultar(
            self.caminho_banco,
            """
            SELECT id_inscricao, id_participante, id_desafio, data_inscricao
            FROM inscricao ORDER BY id_inscricao
            """,
        )
        return [Inscricao(*linha) for linha in linhas]

    def buscar_por_id(self, id_inscricao):
        linhas = consultar(
            self.caminho_banco,
            """
            SELECT id_inscricao, id_participante, id_desafio, data_inscricao
            FROM inscricao WHERE id_inscricao = ?
            """,
            (id_inscricao,),
        )
        if linhas:
            return Inscricao(*linhas[0])
        return None


class RegistroAtividadeDAO:
    def __init__(self, caminho_banco=CAMINHO_BANCO):
        self.caminho_banco = caminho_banco

    def inserir(self, registro):
        dados = registro.to_dict()
        return inserir_no_banco(
            self.caminho_banco,
            """
            INSERT INTO registro_atividade (id_inscricao, data_atividade, duracao_minutos)
            VALUES (?, ?, ?)
            """,
            (dados["id_inscricao"], dados["data_atividade"], dados["duracao_minutos"]),
        )

    def buscar_todos(self):
        linhas = consultar(
            self.caminho_banco,
            """
            SELECT id_registro, id_inscricao, data_atividade, duracao_minutos
            FROM registro_atividade ORDER BY id_registro
            """,
        )
        return [RegistroAtividade(*linha) for linha in linhas]

    def buscar_por_inscricao(self, id_inscricao):
        linhas = consultar(
            self.caminho_banco,
            """
            SELECT id_registro, id_inscricao, data_atividade, duracao_minutos
            FROM registro_atividade WHERE id_inscricao = ? ORDER BY id_registro
            """,
            (id_inscricao,),
        )
        return [RegistroAtividade(*linha) for linha in linhas]
