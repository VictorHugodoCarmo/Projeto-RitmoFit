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

## Back-end da Etapa 2

- [models.py](models.py) reúne as classes do RitmoFit e o cálculo do progresso.
- [dao.py](dao.py) usa SQLite para cadastrar registros e recuperar os dados.
- [app.py](app.py) recebe as requisições HTTP e devolve as respostas em JSON.

### Executar

Use Python 3.12 ou superior com SQLite 3.37 ou superior. Execute estes comandos na raiz do projeto.

```powershell
python -m pip install -r requirements.txt
python app.py
```

Na primeira execução, o programa usa o SQL da Etapa 1 para criar `ritmofit.db`. Abra [http://127.0.0.1:5000](http://127.0.0.1:5000/) para verificar se a API está em execução.

### Rotas

| Caminho | GET | POST |
|---|---|---|
| `/participantes` | Lista participantes | Cadastra nome e e-mail |
| `/modalidades` | Lista modalidades | Cadastra uma modalidade |
| `/desafios` | Lista desafios | Cadastra modalidade, título, período e meta |
| `/inscricoes` | Lista inscrições | Inscreve um participante em um desafio |
| `/atividades` | Lista atividades | Registra data e duração na inscrição |
| `/inscricoes/<id>/progresso` | Mostra o total, a meta e os minutos restantes | — |

### Testar o fluxo

Use o navegador para as consultas GET. Para cadastrar, use o Postman ou o Thunder Client com o método POST e o corpo em JSON. A resposta de cada cadastro devolve o ID gerado. Nos exemplos abaixo, substitua `1` pelos IDs recebidos se o banco já tiver dados.

| Ordem | Rota POST | Corpo JSON |
|---|---|---|
| 1 | `/participantes` | `{"nome": "Ana", "email": "ana@example.com"}` |
| 2 | `/modalidades` | `{"nome": "Caminhada"}` |
| 3 | `/desafios` | `{"id_modalidade": 1, "titulo": "Caminhada da semana", "data_inicio": "2026-11-09", "data_fim": "2026-11-15", "meta_minutos": 90}` |
| 4 | `/inscricoes` | `{"id_participante": 1, "id_desafio": 1, "data_inscricao": "2026-11-09"}` |
| 5 | `/atividades` | `{"id_inscricao": 1, "data_atividade": "2026-11-10", "duracao_minutos": 30}` |
| 6 | `/atividades` | `{"id_inscricao": 1, "data_atividade": "2026-11-12", "duracao_minutos": 35}` |

Ao consultar `GET /inscricoes/1/progresso`, o resultado esperado é de **65 minutos de 90**, com **25 minutos restantes**.
