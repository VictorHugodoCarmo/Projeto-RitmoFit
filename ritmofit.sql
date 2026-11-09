CREATE TABLE participante (
id_participante INTEGER PRIMARY KEY AUTOINCREMENT,
nome VARCHAR(100) NOT NULL,
email VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE modalidade (
id_modalidade INTEGER PRIMARY KEY AUTOINCREMENT,
nome VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE desafio (
id_desafio INTEGER PRIMARY KEY AUTOINCREMENT,
id_modalidade INTEGER NOT NULL,
titulo VARCHAR(100) NOT NULL,
data_inicio DATE NOT NULL,
data_fim DATE NOT NULL,
meta_minutos INTEGER NOT NULL CHECK (meta_minutos > 0),
CHECK (data_fim >= data_inicio),
FOREIGN KEY (id_modalidade) REFERENCES modalidade (id_modalidade)
);

CREATE TABLE inscricao (
id_inscricao INTEGER PRIMARY KEY AUTOINCREMENT,
id_participante INTEGER NOT NULL,
id_desafio INTEGER NOT NULL,
data_inscricao DATE NOT NULL,
UNIQUE (id_participante, id_desafio),
FOREIGN KEY (id_participante) REFERENCES participante (id_participante),
FOREIGN KEY (id_desafio) REFERENCES desafio (id_desafio)
);

CREATE TABLE registro_atividade (
id_registro INTEGER PRIMARY KEY AUTOINCREMENT,
id_inscricao INTEGER NOT NULL,
data_atividade DATE NOT NULL,
duracao_minutos INTEGER NOT NULL CHECK (duracao_minutos > 0),
FOREIGN KEY (id_inscricao) REFERENCES inscricao (id_inscricao)
);

-- Trigger simples para validar a data ao inserir a atividade
CREATE TRIGGER validar_data_atividade
BEFORE INSERT ON registro_atividade
BEGIN
SELECT RAISE(ABORT, 'A atividade deve ocorrer dentro do período do desafio.')
FROM inscricao AS i
JOIN desafio AS d ON d.id_desafio = i.id_desafio
WHERE i.id_inscricao = NEW.id_inscricao
AND (NEW.data_atividade < d.data_inicio OR NEW.data_atividade > d.data_fim);
END;
