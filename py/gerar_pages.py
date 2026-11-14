import json
from hashlib import sha256
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory

import app as sistema
from dao import preparar_banco
from demonstracao import preparar_demonstracao


def gerar_pages():
    destino = sistema.RAIZ_PROJETO
    pasta_estatica = destino / "docs" / "static"
    copytree(Path(sistema.app.static_folder), pasta_estatica, dirs_exist_ok=True)
    (destino / ".nojekyll").touch()

    def url_estatica(endpoint, filename):
        if endpoint != "static":
            raise ValueError("A publicação do Pages usa apenas arquivos estáticos.")
        conteudo = (pasta_estatica / filename).read_bytes()
        versao = sha256(conteudo).hexdigest()[:12]
        return f"./docs/static/{filename}?v={versao}"

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

    print("Demonstração pronta em index.html na raiz do projeto.")


if __name__ == "__main__":
    gerar_pages()
