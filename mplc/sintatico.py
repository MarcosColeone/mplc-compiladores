"""
Entrega 2: analise sintatica.

Transformar a lista de tokens numa arvore.

Descida recursiva, uma funcao por nivel de precedencia, na ordem da secao 3.3
da especificacao. E como voces vao enxergar a precedencia virar formato de
arvore.

Gerador de parser (ANTLR, PLY, yacc) esta proibido nesta entrega e na
anterior. O objetivo e entender, e o gerador esconde exatamente a parte que
esta sendo ensinada.

Leiam antes: LINGUAGEM.md secoes 3 a 5, e CONTRATOS.md secao 3.
"""
from mplc.erros import ErroMPL


# Os cinco tokens de tipo, e o nome que eles tem dentro de um rotulo da arvore.
TIPOS = {
    'TIPO_INTEIRO': 'inteiro',
    'TIPO_REAL': 'real',
    'TIPO_LOGICO': 'logico',
    'TIPO_TEXTO': 'texto',
    'TIPO_VAZIO': 'vazio',
}

# O simbolo que cada operador binario mostra no rotulo 'binario <op>'.
BINARIOS = {
    'OU': 'ou',
    'E': 'e',
    'IGUAL': '==', 'DIFERENTE': '!=',
    'MENOR': '<', 'MENOR_IGUAL': '<=', 'MAIOR': '>', 'MAIOR_IGUAL': '>=',
    'MAIS': '+', 'MENOS': '-',
    'VEZES': '*', 'DIVIDE': '/', 'RESTO': '%',
}


class No:
    """Um no da arvore. O rotulo e o que sai no --ast."""

    def __init__(self, rotulo, filhos=None, linha=0, coluna=0, **extra):
        self.rotulo = rotulo      # 'binario +', 'literal inteiro 1', 'bloco', ...
        self.filhos = filhos or []
        self.linha = linha
        self.coluna = coluna
        self.extra = extra        # o que a semantica quiser pendurar depois


class _Analisador:
    """A descida recursiva.

    O parser anda por uma lista de tokens que ja existe inteira, entao nao
    precisa de leitura antecipada complicada: basta um indice e a capacidade de
    espiar o token atual antes de decidir para onde descer.
    """

    def __init__(self, tokens):
        self.tokens = tokens
        self.i = 0

    # ---------------------------------------------------------- o basico

    @property
    def atual(self):
        return self.tokens[self.i]

    def espiar(self, adiante=1):
        """O token adiante do atual, sem consumir. Usado para desempatar comando."""
        j = self.i + adiante
        return self.tokens[j] if j < len(self.tokens) else self.tokens[-1]

    def checar(self, *tipos):
        return self.atual.tipo in tipos

    def avancar(self):
        token = self.atual
        if self.i < len(self.tokens) - 1:
            self.i += 1
        return token

    def aceitar(self, *tipos):
        """Consome o token se ele for de um dos tipos. Devolve o token ou None."""
        if self.checar(*tipos):
            return self.avancar()
        return None

    def esperar(self, tipo, descricao):
        """Consome o token exigido, ou para com erro no token que apareceu.

        Esta e a unica funcao que levanta erro de sintaxe, e e o que faz os seis
        casos do corpus cairem no lugar certo. A posicao relatada e sempre a do
        token ATUAL, ou seja, o que apareceu no lugar do esperado. Faltando o ';'
        no fim de uma linha, o erro sai no primeiro token da linha seguinte, que
        e onde o parser percebeu o problema.
        """
        if self.checar(tipo):
            return self.avancar()
        self.erro(descricao)

    def erro(self, descricao):
        token = self.atual
        visto = token.lexema if token.lexema else 'o fim do arquivo'
        raise ErroMPL('sintatico', token.linha, token.coluna,
                      f'esperava {descricao}, mas veio {visto}')

    # -------------------------------------------------------- o programa

    def programa(self):
        funcoes = []
        while not self.checar('FIM_ARQUIVO'):
            funcoes.append(self.funcao())
        return No('programa', funcoes)

    def funcao(self):
        inicio = self.atual
        self.esperar('FUNCAO', "a palavra 'funcao'")

        # O tipo de retorno vem ANTES do nome. E o que o caso sin-06 cobra: em
        # 'funcao principal()' o erro sai no 'principal', que apareceu onde
        # deveria haver um tipo.
        if not self.checar(*TIPOS):
            self.erro('o tipo de retorno da funcao')
        tipo = TIPOS[self.avancar().tipo]

        nome = self.esperar('ID', 'o nome da funcao').lexema

        parametros = self.parametros()
        corpo = self.bloco()

        # No rotulo o nome vem antes do tipo: 'funcao fatorial inteiro'.
        return No(f'funcao {nome} {tipo}', [parametros, corpo],
                  inicio.linha, inicio.coluna)

    def parametros(self):
        self.esperar('ABRE_PAR', "'(' depois do nome da funcao")
        lista = []
        if not self.checar('FECHA_PAR'):
            lista.append(self.parametro())
            while self.aceitar('VIRGULA'):
                lista.append(self.parametro())
        self.esperar('FECHA_PAR', "')' fechando os parametros")
        return No('parametros', lista)

    def parametro(self):
        if not self.checar(*TIPOS):
            self.erro('o tipo do parametro')
        token = self.avancar()
        tipo = TIPOS[token.tipo]
        nome = self.esperar('ID', 'o nome do parametro').lexema
        return No(f'parametro {nome} {tipo}', [], token.linha, token.coluna)

    # --------------------------------------------------------- comandos

    def bloco(self):
        abre = self.esperar('ABRE_CHAVE', "'{' abrindo um bloco")
        comandos = []
        # O laco tambem para no fim do arquivo. Sem isso, um '}' que falta vira
        # laco infinito em vez do erro do caso sin-02.
        while not self.checar('FECHA_CHAVE', 'FIM_ARQUIVO'):
            comandos.append(self.comando())
        self.esperar('FECHA_CHAVE', "'}' fechando o bloco")
        return No('bloco', comandos, abre.linha, abre.coluna)

    def comando(self):
        token = self.atual

        if self.checar(*TIPOS):
            return self.declaracao()
        if self.checar('SE'):
            return self.comando_se()
        if self.checar('ENQUANTO'):
            return self.comando_enquanto()
        if self.checar('ESCREVA'):
            return self.comando_escreva()
        if self.checar('RETORNE'):
            return self.comando_retorne()
        if self.checar('ABRE_CHAVE'):
            # Um bloco solto tambem e um comando, e abre escopo proprio.
            return self.bloco()

        if self.checar('ID'):
            # Duas coisas comecam com um nome: a atribuicao e a chamada de uma
            # funcao 'vazio' usada como comando. O token seguinte desempata.
            if self.espiar().tipo == 'ATRIBUI':
                return self.atribuicao()
            if self.espiar().tipo == 'ABRE_PAR':
                chamada = self.chamada(self.avancar())
                self.esperar('PONTO_VIRGULA', "';' no fim da chamada")
                return chamada

        self.erro('um comando')

    def declaracao(self):
        token = self.avancar()
        tipo = TIPOS[token.tipo]
        nome = self.esperar('ID', 'o nome da variavel').lexema

        filhos = []
        if self.aceitar('ATRIBUI'):
            filhos.append(self.expressao())

        self.esperar('PONTO_VIRGULA', "';' no fim da declaracao")
        return No(f'declaracao {nome} {tipo}', filhos, token.linha, token.coluna)

    def atribuicao(self):
        nome_token = self.avancar()
        self.esperar('ATRIBUI', "'=' na atribuicao")
        valor = self.expressao()
        self.esperar('PONTO_VIRGULA', "';' no fim da atribuicao")
        return No(f'atribuicao {nome_token.lexema}', [valor],
                  nome_token.linha, nome_token.coluna)

    def comando_se(self):
        token = self.avancar()
        self.esperar('ABRE_PAR', "'(' depois do se")
        condicao = self.expressao()
        self.esperar('FECHA_PAR', "')' fechando a condicao do se")

        # As chaves sao obrigatorias mesmo para um comando so. E o caso sin-05:
        # o erro sai no comando que apareceu onde deveria haver um '{'.
        filhos = [condicao, self.bloco()]
        if self.aceitar('SENAO'):
            filhos.append(self.bloco())

        return No('se', filhos, token.linha, token.coluna)

    def comando_enquanto(self):
        token = self.avancar()
        self.esperar('ABRE_PAR', "'(' depois do enquanto")
        condicao = self.expressao()
        self.esperar('FECHA_PAR', "')' fechando a condicao do enquanto")
        return No('enquanto', [condicao, self.bloco()], token.linha, token.coluna)

    def comando_escreva(self):
        token = self.avancar()
        self.esperar('ABRE_PAR', "'(' depois do escreva")
        valor = self.expressao()
        self.esperar('FECHA_PAR', "')' fechando o escreva")
        self.esperar('PONTO_VIRGULA', "';' no fim do escreva")
        return No('escreva', [valor], token.linha, token.coluna)

    def comando_retorne(self):
        token = self.avancar()
        filhos = []
        if not self.checar('PONTO_VIRGULA'):
            filhos.append(self.expressao())
        self.esperar('PONTO_VIRGULA', "';' no fim do retorne")
        return No('retorne', filhos, token.linha, token.coluna)

    # ------------------------------------------------------ expressoes
    #
    # Daqui para baixo vem um nivel de precedencia por funcao, do mais fraco
    # para o mais forte, na ordem da secao 3.3 da especificacao:
    #
    #   1. ou          2. e           3. == !=       4. < <= > >=
    #   5. + -         6. * / %       7. nao, - unario
    #   8. chamada de funcao e parenteses
    #
    # A precedencia nao esta escrita em lugar nenhum: ela E a ordem em que uma
    # funcao chama a outra. Quem e chamado por ultimo fica mais fundo na arvore,
    # e por isso liga mais forte.
    #
    # Todos os binarios usam LACO, nunca recursao a direita, e e isso que da a
    # associatividade a esquerda. Em '10 - 4 - 3' o laco monta '(10 - 4)' e usa
    # esse no inteiro como lado esquerdo do proximo '-', chegando a
    # '((10 - 4) - 3)'. Se a funcao chamasse a si mesma a direita, sairia
    # '10 - (4 - 3)', que vale 9 em vez de 3, e nenhum teste com dois operandos
    # perceberia a diferenca.

    def expressao(self):
        return self.nivel_ou()

    def binario_a_esquerda(self, proximo_nivel, *tipos):
        """O esqueleto comum dos seis niveis binarios, todos a esquerda."""
        no = proximo_nivel()
        while self.checar(*tipos):
            operador = self.avancar()
            direita = proximo_nivel()      # o nivel de baixo, nunca este mesmo
            no = No(f'binario {BINARIOS[operador.tipo]}', [no, direita],
                    operador.linha, operador.coluna)
        return no

    def nivel_ou(self):
        return self.binario_a_esquerda(self.nivel_e, 'OU')

    def nivel_e(self):
        return self.binario_a_esquerda(self.nivel_igualdade, 'E')

    def nivel_igualdade(self):
        return self.binario_a_esquerda(self.nivel_comparacao, 'IGUAL', 'DIFERENTE')

    def nivel_comparacao(self):
        return self.binario_a_esquerda(self.nivel_soma,
                                       'MENOR', 'MENOR_IGUAL', 'MAIOR', 'MAIOR_IGUAL')

    def nivel_soma(self):
        return self.binario_a_esquerda(self.nivel_termo, 'MAIS', 'MENOS')

    def nivel_termo(self):
        return self.binario_a_esquerda(self.nivel_unario, 'VEZES', 'DIVIDE', 'RESTO')

    def nivel_unario(self):
        # 'nao' e o '-' unario associam a DIREITA, entao aqui a recursao no
        # proprio nivel e a forma certa: '- - 2' precisa virar '-(-2)'.
        if self.checar('NAO', 'MENOS'):
            operador = self.avancar()
            simbolo = 'nao' if operador.tipo == 'NAO' else '-'
            return No(f'unario {simbolo}', [self.nivel_unario()],
                      operador.linha, operador.coluna)
        return self.nivel_primario()

    def nivel_primario(self):
        token = self.atual

        if self.checar('INTEIRO', 'REAL', 'LOGICO', 'TEXTO'):
            return self.literal(self.avancar())

        if self.checar('ABRE_PAR'):
            self.avancar()
            interna = self.expressao()
            self.esperar('FECHA_PAR', "')' fechando a expressao")
            return interna

        if self.checar('ID'):
            nome = self.avancar()
            if self.checar('ABRE_PAR'):
                return self.chamada(nome)
            return No(f'variavel {nome.lexema}', [], nome.linha, nome.coluna)

        # Chegou aqui quem nao consegue comecar uma expressao. E o caso sin-04:
        # em 'escreva(1 + )' o erro sai no ')', que apareceu onde faltava um
        # operando.
        self.erro('uma expressao')

    def chamada(self, nome):
        self.esperar('ABRE_PAR', "'(' na chamada de funcao")
        argumentos = []
        if not self.checar('FECHA_PAR'):
            argumentos.append(self.expressao())
            while self.aceitar('VIRGULA'):
                argumentos.append(self.expressao())
        self.esperar('FECHA_PAR', "')' fechando os argumentos")
        return No(f'chamada {nome.lexema}', argumentos, nome.linha, nome.coluna)

    def literal(self, token):
        if token.tipo == 'INTEIRO':
            valor = token.lexema
        elif token.tipo == 'REAL':
            # O contrato pede real sempre com seis casas: 3.5 vira 3.500000.
            valor = f'{float(token.lexema):.6f}'
        elif token.tipo == 'LOGICO':
            valor = token.lexema
        else:
            # O texto sai como veio do lexico: com as aspas e com os escapes na
            # forma original.
            valor = token.lexema

        tipo = {'INTEIRO': 'inteiro', 'REAL': 'real',
                'LOGICO': 'logico', 'TEXTO': 'texto'}[token.tipo]
        return No(f'literal {tipo} {valor}', [], token.linha, token.coluna)


def analisar(tokens):
    """Recebe a lista de Token. Devolve a raiz da arvore (um No 'programa')."""
    return _Analisador(tokens).programa()


def despejar(no, nivel=0, saida=None):
    """Imprime a arvore no formato do --ast. Ja esta pronto: dois espacos por nivel."""
    saida = saida if saida is not None else []
    saida.append('  ' * nivel + no.rotulo)
    for f in no.filhos:
        despejar(f, nivel + 1, saida)
    return saida
