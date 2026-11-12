from datetime import date, timedelta

from dao import abrir_conexao


def preparar_demonstracao(caminho_banco):
    hoje = date.today()
    inicio = (hoje - timedelta(days=3)).isoformat()
    ontem = (hoje - timedelta(days=1)).isoformat()
    fim = (hoje + timedelta(days=7)).isoformat()
    hoje = hoje.isoformat()

    conexao = abrir_conexao(caminho_banco)
    try:
        with conexao:
            conexao.execute("BEGIN IMMEDIATE")
            pronta = conexao.execute("PRAGMA user_version").fetchone()[0]
            if pronta:
                return

            conexao.executemany(
                "INSERT INTO modalidade (id_modalidade, nome) VALUES (?, ?)",
                [(1, "Caminhada"), (2, "Corrida"), (3, "Ciclismo")],
            )
            conexao.executemany(
                "INSERT INTO participante (id_participante, nome, email) VALUES (?, ?, ?)",
                [
                    (1, "Ana Ribeiro", "ana@example.com"),
                    (2, "Bruno Lima", "bruno@example.com"),
                    (3, "Camila Santos", "camila@example.com"),
                    (4, "Diego Costa", "diego@example.com"),
                ],
            )
            conexao.executemany(
                """
                INSERT INTO desafio
                    (id_desafio, id_modalidade, titulo, data_inicio, data_fim, meta_minutos)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (1, 1, "Caminhada da semana", inicio, fim, 90),
                    (2, 2, "Corrida no seu ritmo", inicio, fim, 120),
                    (3, 3, "Pedal da turma", inicio, fim, 150),
                ],
            )
            conexao.executemany(
                """
                INSERT INTO inscricao (id_inscricao, id_participante, id_desafio, data_inscricao)
                VALUES (?, ?, ?, ?)
                """,
                [(1, 1, 1, inicio), (2, 2, 2, inicio), (3, 3, 3, inicio), (4, 4, 1, inicio)],
            )
            conexao.executemany(
                """
                INSERT INTO registro_atividade (id_inscricao, data_atividade, duracao_minutos)
                VALUES (?, ?, ?)
                """,
                [(1, ontem, 30), (1, hoje, 35), (2, hoje, 40), (3, ontem, 55), (4, hoje, 20)],
            )
            conexao.execute("PRAGMA user_version = 1")
    finally:
        conexao.close()
