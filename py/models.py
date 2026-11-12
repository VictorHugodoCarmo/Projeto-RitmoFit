class Participante:
    def __init__(self, id_participante, nome, email):
        self.__id_participante = id_participante
        self.__nome = nome
        self.__email = email

    def to_dict(self):
        return {
            "id_participante": self.__id_participante,
            "nome": self.__nome,
            "email": self.__email,
        }


class Modalidade:
    def __init__(self, id_modalidade, nome):
        self.__id_modalidade = id_modalidade
        self.__nome = nome

    def to_dict(self):
        return {"id_modalidade": self.__id_modalidade, "nome": self.__nome}


class Desafio:
    def __init__(self, id_desafio, id_modalidade, titulo, data_inicio, data_fim, meta_minutos):
        self.__id_desafio = id_desafio
        self.__id_modalidade = id_modalidade
        self.__titulo = titulo
        self.__data_inicio = data_inicio
        self.__data_fim = data_fim
        self.__meta_minutos = meta_minutos

    @property
    def meta_minutos(self):
        return self.__meta_minutos

    def aceita_data(self, data_atividade):
        return self.__data_inicio <= data_atividade <= self.__data_fim

    def to_dict(self):
        return {
            "id_desafio": self.__id_desafio,
            "id_modalidade": self.__id_modalidade,
            "titulo": self.__titulo,
            "data_inicio": self.__data_inicio,
            "data_fim": self.__data_fim,
            "meta_minutos": self.__meta_minutos,
        }


class Inscricao:
    def __init__(self, id_inscricao, id_participante, id_desafio, data_inscricao):
        self.__id_inscricao = id_inscricao
        self.__id_participante = id_participante
        self.__id_desafio = id_desafio
        self.__data_inscricao = data_inscricao

    @property
    def id_desafio(self):
        return self.__id_desafio

    def total_minutos(self, registros):
        total = 0
        for registro in registros:
            if registro.id_inscricao == self.__id_inscricao:
                total += registro.duracao_minutos
        return total

    def meta_atingida(self, desafio, registros):
        return self.total_minutos(registros) >= desafio.meta_minutos

    def to_dict(self):
        return {
            "id_inscricao": self.__id_inscricao,
            "id_participante": self.__id_participante,
            "id_desafio": self.__id_desafio,
            "data_inscricao": self.__data_inscricao,
        }


class RegistroAtividade:
    def __init__(self, id_registro, id_inscricao, data_atividade, duracao_minutos):
        self.__id_registro = id_registro
        self.__id_inscricao = id_inscricao
        self.__data_atividade = data_atividade
        self.__duracao_minutos = duracao_minutos

    @property
    def id_inscricao(self):
        return self.__id_inscricao

    @property
    def duracao_minutos(self):
        return self.__duracao_minutos

    def to_dict(self):
        return {
            "id_registro": self.__id_registro,
            "id_inscricao": self.__id_inscricao,
            "data_atividade": self.__data_atividade,
            "duracao_minutos": self.__duracao_minutos,
        }
