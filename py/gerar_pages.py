import json
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory

import app as sistema
from dao import preparar_banco
from demonstracao import preparar_demonstracao


def gerar_pages():
    destino = sistema.RAIZ_PROJETO / "docs"
    destino.mkdir(exist_ok=True)
    copytree(Path(sistema.app.static_folder), destino / "static", dirs_exist_ok=True)
    (destino / ".nojekyll").touch()

    def url_estatica(endpoint, filename):
        if endpoint != "static":
            raise ValueError("A publicação do Pages usa apenas arquivos estáticos.")
        return "./static/" + filename

    with sistema.app.app_context():
        modelo = sistema.app.jinja_env.get_template("index.html")
        pagina = modelo.render(modo_pages=True, url_for=url_estatica)
    linhas = [linha.rstrip() for linha in pagina.splitlines()]
    (destino / "index.html").write_text("\n".join(linhas) + "\n", encoding="utf-8")

    # A exportação usa somente o banco temporário de demonstração.
    with TemporaryDirectory() as pasta:
        banco = Path(pasta) / "pages.db"
        preparar_banco(banco)
        preparar_demonstracao(banco)
        daos = (
            sistema.participante_dao, sistema.modalidade_dao, sistema.desafio_dao,
            sistema.inscricao_dao, sistema.registro_dao,
        )
        caminhos = [dao.caminho_banco for dao in daos]
        try:
            for dao in daos:
                dao.caminho_banco = banco
            with sistema.app.test_client() as cliente:
                rotas = ["participantes", "modalidades", "desafios", "inscricoes", "atividades"]
                inscricoes = cliente.get("/inscricoes").get_json()
                for inscricao in inscricoes:
                    rotas.append(f"inscricoes/{inscricao['id_inscricao']}/progresso")
                for rota in rotas:
                    resposta = cliente.get("/" + rota)
                    if resposta.status_code != 200:
                        raise RuntimeError(f"Falha ao exportar /{rota}.")
                    arquivo = destino / "dados" / (rota + ".json")
                    arquivo.parent.mkdir(parents=True, exist_ok=True)
                    conteudo = json.dumps(resposta.get_json(), ensure_ascii=False, indent=2)
                    arquivo.write_text(conteudo + "\n", encoding="utf-8")
        finally:
            for dao, caminho in zip(daos, caminhos):
                dao.caminho_banco = caminho

    print("Demonstração pronta em docs/index.html.")


if __name__ == "__main__":
    gerar_pages()
