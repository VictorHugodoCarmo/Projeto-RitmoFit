# RitmoFit

**Projeto Integrado de DWS, POO e Banco de Dados · AV1, Etapa 1**

O RitmoFit organiza desafios coletivos de atividade física com metas individuais. Cada desafio define uma modalidade, um período e uma meta em minutos. Ao se inscrever, o participante pode registrar atividades e acompanhar o progresso. Em um desafio de caminhada de 90 minutos, duas atividades de 30 e 35 minutos somam 65 minutos de progresso.

## Modelo de dados

| Entidade | Finalidade |
|---|---|
| Participante | Identifica a pessoa que se inscreve nos desafios. |
| Modalidade | Classifica o tipo de atividade, como caminhada ou ciclismo. |
| Desafio | Define a modalidade, o período e a meta individual em minutos. |
| Inscrição | Vincula um participante a um desafio e registra a data de adesão. |
| Registro de atividade | Guarda a data e a duração de uma atividade vinculada à inscrição. |

O esquema SQLite contém cinco tabelas e quatro chaves estrangeiras. Cada participante pode se inscrever uma vez por desafio. O banco valida se as atividades têm duração positiva e estão dentro do período definido.

## Arquivos da etapa

- **Modelo conceitual** — `docs/modelo_conceitual.png`, com entidades, atributos, relacionamentos e cardinalidades.
- **Modelo lógico** — `docs/modelo_logico.png`, com tabelas, campos, chaves primárias, chaves estrangeiras e relacionamentos.
- **Modelo físico** — [banco/ritmofit.sql](banco/ritmofit.sql), com a criação das tabelas e das restrições.

## Criação e verificação do banco

Para executar no Windows, use Python 3.12 ou superior com SQLite 3.37 ou superior. Execute o bloco abaixo uma vez no PowerShell, na raiz do repositório. Ele cria o arquivo local `ritmofit.db` e lista as cinco tabelas.

```powershell
@'
from contextlib import closing
from pathlib import Path
import sqlite3

sql = Path("banco/ritmofit.sql").read_text(encoding="utf-8")
with closing(sqlite3.connect("ritmofit.db")) as banco:
    banco.executescript(sql)
    tabelas = banco.execute(
        "SELECT name FROM sqlite_schema WHERE type = 'table' ORDER BY name"
    )
    for (nome,) in tabelas:
        print(nome)

    (total,) = banco.execute("SELECT COUNT(*) FROM participante").fetchone()
    print(f"Total de participantes cadastrados = {total}")
'@ | python -
```

A consulta de verificação retorna zero participantes no banco recém-criado. Em cada nova conexão da aplicação, `PRAGMA foreign_keys = ON` ativa a validação das chaves estrangeiras. [Chaves estrangeiras no SQLite](https://www.sqlite.org/foreignkeys.html#fk_enable)
