# RitmoFit

**Projeto Integrado de DWS, POO e Banco de Dados**

O RitmoFit organiza desafios coletivos de atividade física com metas individuais. Cada desafio define uma modalidade, um período e uma meta em minutos. Ao se inscrever, o participante pode registrar atividades e acompanhar o progresso. Em um desafio de caminhada de 90 minutos, duas atividades de 30 e 35 minutos somam 65 minutos de progresso.

## Modelo de dados

| Entidade | Finalidade |
|---|---|
| Participante | Identifica a pessoa que se inscreve nos desafios. |
| Modalidade | Classifica o tipo de atividade, como caminhada ou ciclismo. |
| Desafio | Define a modalidade, o período e a meta individual em minutos. |
| Inscrição | Vincula um participante a um desafio e registra a data de adesão. |
| Registro de atividade | Guarda a data e a duração de uma atividade vinculada à inscrição. |

O esquema SQLite contém cinco tabelas e quatro chaves estrangeiras. Cada participante pode se inscrever uma vez por desafio. A API valida a duração das atividades e o período em que foram realizadas.

## Modelagem

- **Modelo conceitual** — `docs/modelo_conceitual.png`, com entidades, atributos, relacionamentos e cardinalidades.
- **Modelo lógico** — `docs/modelo_logico.png`, com tabelas, campos, chaves primárias, chaves estrangeiras e relacionamentos.
- **Modelo físico** — [banco/ritmofit.sql](banco/ritmofit.sql), com a criação das tabelas e das restrições.
- **Diagrama de classes** — [docs/diagrama_classes.pdf](docs/diagrama_classes.pdf), com as classes, os atributos, os métodos e as multiplicidades.

## Executar

Use Python 3.12 ou superior com SQLite 3.37 ou superior. Na raiz do projeto, instale o Flask e inicie o servidor.

```powershell
python -m pip install -r .\py\requirements.txt
python .\py\app.py
```

Abra [o RitmoFit no navegador](http://127.0.0.1:5000/). Na primeira execução, o Flask usa o SQL da Etapa 1 para criar `ritmofit.db`.

## Apresentação

Para iniciar com dados fictícios, rode `python .\py\app.py --demo`. O modo de demonstração usa `ritmofit-demo.db` e salva as alterações nesse arquivo. Na primeira execução, a inscrição de Ana Ribeiro na Caminhada da semana mostra **65 de 90 minutos**. Registre mais **25 minutos** nessa inscrição para ver **Meta atingida**. Reabra a página para conferir que o registro foi salvo.

Para testar o fluxo com cadastros próprios, crie uma modalidade e um participante. Em **Desafios**, crie um desafio, clique em **Inscrever** e selecione a pessoa. Registre uma atividade dentro do período. Use **Ver progresso** na lista de inscrições para consultar o total e os minutos restantes.

## GitHub Pages

A demonstração online permite cadastrar, editar e excluir registros, filtrar desafios e consultar o progresso. Na primeira visita, carrega exemplos em JSON via Fetch. Os cadastros ficam no navegador em que foram feitos, inclusive depois de recarregar a página. A execução local usa as rotas Flask e guarda os dados no SQLite. [Abrir a demonstração](https://victorhugodocarmo.github.io/Projeto-RitmoFit/)

No GitHub, abra **Settings → Pages**. Em **Source**, escolha **Deploy from a branch** e selecione **main** e **/docs**. O arquivo inicial da publicação fica em `docs/index.html`.

Para atualizar a versão online depois de alterar a interface, execute `python .\py\gerar_pages.py` e inclua os arquivos atualizados de `docs/` no commit.

## Organização

| Arquivo | Responsabilidade |
|---|---|
| [py/templates/index.html](py/templates/index.html) | Painel, listas e formulários em HTML |
| [py/static/css/estilo.css](py/static/css/estilo.css) | Layout responsivo e identidade visual |
| [py/static/js/ritmofit.js](py/static/js/ritmofit.js) | Envio de formulários, Fetch e atualização das listas |
| [py/static/js/pages.js](py/static/js/pages.js) | Armazenamento e validações da demonstração no navegador |
| [py/app.py](py/app.py) | Página inicial e rotas Flask que recebem e devolvem JSON |
| [py/models.py](py/models.py) | Classes do RitmoFit e cálculo de progresso |
| [py/dao.py](py/dao.py) | Operações no SQLite |

## API

| Caminho | GET | POST |
|---|---|---|
| `/participantes` | Lista participantes | Cadastra nome e e-mail |
| `/modalidades` | Lista modalidades | Cadastra uma modalidade |
| `/desafios` | Lista desafios | Cadastra modalidade, título, período e meta |
| `/inscricoes` | Lista inscrições | Inscreve um participante em um desafio |
| `/atividades` | Lista atividades | Registra data e duração na inscrição |
| `/inscricoes/<id>/progresso` | Mostra o total, a meta e os minutos restantes | — |

As cinco coleções também aceitam `PUT /<coleção>/<id>` para editar e `DELETE /<coleção>/<id>` para excluir. Os formulários enviam JSON e as listas são consultadas novamente após cada alteração. As chaves estrangeiras protegem cadastros que ainda estão vinculados a outros registros.

Use [a rota de status](http://127.0.0.1:5000/api) para conferir a resposta JSON do Flask.
