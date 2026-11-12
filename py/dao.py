import sqlite3
from pathlib import Path

from models import Desafio, Inscricao, Modalidade, Participante, RegistroAtividade


RAIZ_PROJETO = Path(__file__).resolve().parent.parent
CAMINHO_BANCO = RAIZ_PROJETO / "ritmofit.db"


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

        with open(RAIZ_PROJETO / "banco" / "ritmofit.sql", encoding="utf-8-sig") as arquivo:
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


def alterar_no_banco(caminho_banco, comando, parametros):
    conexao = abrir_conexao(caminho_banco)
    try:
        cursor = conexao.cursor()
        cursor.execute(comando, parametros)
        conexao.commit()
        return cursor.rowcount > 0
    finally:
        conexao.close()


def data_valida(data, caminho_banco=CAMINHO_BANCO):
    linhas = consultar(caminho_banco, "SELECT date(?, '+0 days')", (data,))
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

    def atualizar(self, id_participante, participante):
        dados = participante.to_dict()
        return alterar_no_banco(
            self.caminho_banco,
            "UPDATE participante SET nome = ?, email = ? WHERE id_participante = ?",
            (dados["nome"], dados["email"], id_participante),
        )

    def remover(self, id_participante):
        return alterar_no_banco(
            self.caminho_banco,
            "DELETE FROM participante WHERE id_participante = ?",
            (id_participante,),
        )


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

    def atualizar(self, id_modalidade, modalidade):
        dados = modalidade.to_dict()
        return alterar_no_banco(
            self.caminho_banco,
            "UPDATE modalidade SET nome = ? WHERE id_modalidade = ?",
            (dados["nome"], id_modalidade),
        )

    def remover(self, id_modalidade):
        return alterar_no_banco(
            self.caminho_banco,
            "DELETE FROM modalidade WHERE id_modalidade = ?",
            (id_modalidade,),
        )


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

    def atualizar(self, id_desafio, desafio):
        dados = desafio.to_dict()
        return alterar_no_banco(
            self.caminho_banco,
            """
            UPDATE desafio
            SET id_modalidade = ?, titulo = ?, data_inicio = ?, data_fim = ?, meta_minutos = ?
            WHERE id_desafio = ?
              AND NOT EXISTS (
                  SELECT 1 FROM inscricao AS i
                  JOIN registro_atividade AS r ON r.id_inscricao = i.id_inscricao
                  WHERE i.id_desafio = desafio.id_desafio
                    AND r.data_atividade NOT BETWEEN ? AND ?
              )
            """,
            (
                dados["id_modalidade"],
                dados["titulo"],
                dados["data_inicio"],
                dados["data_fim"],
                dados["meta_minutos"],
                id_desafio,
                dados["data_inicio"],
                dados["data_fim"],
            ),
        )

    def remover(self, id_desafio):
        return alterar_no_banco(
            self.caminho_banco,
            "DELETE FROM desafio WHERE id_desafio = ?",
            (id_desafio,),
        )


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

    def atualizar(self, id_inscricao, inscricao):
        dados = inscricao.to_dict()
        return alterar_no_banco(
            self.caminho_banco,
            """
            UPDATE inscricao SET id_participante = ?, id_desafio = ?, data_inscricao = ?
            WHERE id_inscricao = ?
              AND (
                  (id_participante = ? AND id_desafio = ?)
                  OR NOT EXISTS (
                      SELECT 1 FROM registro_atividade AS r
                      WHERE r.id_inscricao = inscricao.id_inscricao
                  )
              )
            """,
            (
                dados["id_participante"], dados["id_desafio"], dados["data_inscricao"],
                id_inscricao, dados["id_participante"], dados["id_desafio"],
            ),
        )

    def remover(self, id_inscricao):
        return alterar_no_banco(
            self.caminho_banco,
            "DELETE FROM inscricao WHERE id_inscricao = ?",
            (id_inscricao,),
        )


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

    def buscar_por_id(self, id_registro):
        linhas = consultar(
            self.caminho_banco,
            """
            SELECT id_registro, id_inscricao, data_atividade, duracao_minutos
            FROM registro_atividade WHERE id_registro = ?
            """,
            (id_registro,),
        )
        if linhas:
            return RegistroAtividade(*linhas[0])
        return None

    def atualizar(self, id_registro, registro):
        dados = registro.to_dict()
        return alterar_no_banco(
            self.caminho_banco,
            """
            UPDATE registro_atividade SET id_inscricao = ?, data_atividade = ?, duracao_minutos = ?
            WHERE id_registro = ?
              AND EXISTS (
                  SELECT 1 FROM inscricao AS i
                  JOIN desafio AS d ON d.id_desafio = i.id_desafio
                  WHERE i.id_inscricao = ? AND ? BETWEEN d.data_inicio AND d.data_fim
              )
            """,
            (
                dados["id_inscricao"], dados["data_atividade"], dados["duracao_minutos"],
                id_registro, dados["id_inscricao"], dados["data_atividade"],
            ),
        )

    def remover(self, id_registro):
        return alterar_no_banco(
            self.caminho_banco,
            "DELETE FROM registro_atividade WHERE id_registro = ?",
            (id_registro,),
        )
