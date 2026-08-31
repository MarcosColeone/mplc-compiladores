"""
Entrega 1: analise lexica.

Transformar o texto do programa numa lista de tokens.

O que voces tem que devolver: uma lista de Token. O ultimo elemento e sempre
um token FIM_ARQUIVO. A regra de posicao dele esta em CONTRATOS.md, secao 7.

Leiam antes: LINGUAGEM.md secao 2, e CONTRATOS.md secao 2.
"""
from mplc.erros import ErroMPL


# --------------------------------------------------------------- as tabelas

# Palavras reservadas (LINGUAGEM.md 2.1). Nenhuma delas pode virar ID.
# 'verdadeiro' e 'falso' sao literais do tipo logico, nao palavras de comando,
# entao saem com o tipo LOGICO e nao com um tipo proprio.
PALAVRAS = {
    'funcao': 'FUNCAO',
    'retorne': 'RETORNE',
    'se': 'SE',
    'senao': 'SENAO',
    'enquanto': 'ENQUANTO',
    'escreva': 'ESCREVA',
    'inteiro': 'TIPO_INTEIRO',
    'real': 'TIPO_REAL',
    'logico': 'TIPO_LOGICO',
    'texto': 'TIPO_TEXTO',
    'vazio': 'TIPO_VAZIO',
    'verdadeiro': 'LOGICO',
    'falso': 'LOGICO',
    'e': 'E',
    'ou': 'OU',
    'nao': 'NAO',
}

# A ordem desta lista e a armadilha da Entrega 1.
# Os simbolos de dois caracteres vem antes dos de um. Se '<' fosse testado
# primeiro, 'x <= 3' viraria quatro tokens (x, <, =, 3) em vez de tres, e o
# defeito so apareceria na Entrega 2, num lugar sem relacao com este. A regra
# tem nome: maximal munch, ou seja, casar sempre o maior simbolo possivel.
OPERADORES = [
    ('<=', 'MENOR_IGUAL'),
    ('>=', 'MAIOR_IGUAL'),
    ('==', 'IGUAL'),
    ('!=', 'DIFERENTE'),
    ('+', 'MAIS'),
    ('-', 'MENOS'),
    ('*', 'VEZES'),
    ('/', 'DIVIDE'),
    ('%', 'RESTO'),
    ('<', 'MENOR'),
    ('>', 'MAIOR'),
    ('=', 'ATRIBUI'),
    ('(', 'ABRE_PAR'),
    (')', 'FECHA_PAR'),
    ('{', 'ABRE_CHAVE'),
    ('}', 'FECHA_CHAVE'),
    (',', 'VIRGULA'),
    (';', 'PONTO_VIRGULA'),
]

# Os unicos escapes que a MPL aceita dentro de um texto (LINGUAGEM.md 2.3).
ESCAPES = ('n', 't', '"', '\\')

ESPACOS = ' \t\r\n'


def _e_letra(c):
    # A MPL so aceita letras ASCII em identificadores. Usar c.isalpha() direto
    # deixaria passar letras acentuadas, que aqui sao erro lexico.
    return c == '_' or (c.isascii() and c.isalpha())


def _e_digito(c):
    return c.isascii() and c.isdigit()


class Token:
    __slots__ = ('tipo', 'lexema', 'linha', 'coluna')

    def __init__(self, tipo, lexema, linha, coluna):
        self.tipo = tipo          # 'ID', 'INTEIRO', 'MAIS', ... (a lista esta no contrato)
        self.lexema = lexema      # o texto exato como apareceu no fonte
        self.linha = linha
        self.coluna = coluna      # a coluna do PRIMEIRO caractere do token

    def __str__(self):
        # esta e a linha que o --tokens imprime; nao mexam no formato
        return f"{self.linha},{self.coluna},{self.tipo},{self.lexema}"


# ---------------------------------------------------------------- o leitor

class _Leitor:
    """Um cursor sobre o texto, que sabe em que linha e coluna esta.

    Todo o controle de posicao mora aqui, num lugar so. E o que faz a coluna
    sair certa: quem move o cursor e sempre o metodo avancar, nunca quem chama.
    """

    def __init__(self, fonte):
        self.fonte = fonte
        self.i = 0
        self.linha = 1
        self.coluna = 1       # a primeira coluna de cada linha e 1, nao 0

    def fim(self):
        return self.i >= len(self.fonte)

    def olhar(self, adiante=0):
        """O caractere na posicao atual (ou adiante dela). '' depois do fim."""
        j = self.i + adiante
        return self.fonte[j] if j < len(self.fonte) else ''

    def avancar(self):
        c = self.fonte[self.i]
        self.i += 1
        if c == '\n':
            self.linha += 1
            self.coluna = 1
        else:
            self.coluna += 1
        return c


# ------------------------------------------------------- espacos e comentarios

def _pular_espacos_e_comentarios(leitor):
    """Consome tudo o que nao vira token: espacos e os dois tipos de comentario."""
    while not leitor.fim():
        c = leitor.olhar()

        if c in ESPACOS:
            leitor.avancar()

        elif c == '/' and leitor.olhar(1) == '/':
            # comentario de linha: vai ate o \n, que fica para o laco de cima
            while not leitor.fim() and leitor.olhar() != '\n':
                leitor.avancar()

        elif c == '/' and leitor.olhar(1) == '*':
            # O erro de bloco nao fechado e relatado onde o comentario comecou
            # (LINGUAGEM.md 2.5), entao a posicao fica guardada antes de andar.
            linha, coluna = leitor.linha, leitor.coluna
            leitor.avancar()
            leitor.avancar()
            fechou = False
            while not leitor.fim():
                if leitor.olhar() == '*' and leitor.olhar(1) == '/':
                    leitor.avancar()
                    leitor.avancar()
                    fechou = True
                    break
                leitor.avancar()      # comentario de bloco nao aninha: so o primeiro */ fecha
            if not fechou:
                raise ErroMPL('lexico', linha, coluna,
                              'comentario de bloco aberto e nunca fechado')

        else:
            return


# ---------------------------------------------------------------- os tokens

def _ler_identificador(leitor, linha, coluna):
    inicio = leitor.i
    while not leitor.fim() and (_e_letra(leitor.olhar()) or _e_digito(leitor.olhar())):
        leitor.avancar()
    lexema = leitor.fonte[inicio:leitor.i]
    # O nome inteiro e lido primeiro e so depois consultado na tabela. E por
    # isso que 'sePossivel' e um ID, e nao um 'se' seguido de 'Possivel'.
    return Token(PALAVRAS.get(lexema, 'ID'), lexema, linha, coluna)


def _ler_numero(leitor, linha, coluna):
    inicio = leitor.i
    while not leitor.fim() and _e_digito(leitor.olhar()):
        leitor.avancar()

    if leitor.olhar() == '.':
        # O ponto de um real exige digito dos dois lados, entao '3.' e erro.
        # A posicao relatada e a do ponto, o caractere que estragou o token.
        if not _e_digito(leitor.olhar(1)):
            raise ErroMPL('lexico', leitor.linha, leitor.coluna,
                          'o ponto de um real exige digito depois dele')
        leitor.avancar()
        while not leitor.fim() and _e_digito(leitor.olhar()):
            leitor.avancar()
        return Token('REAL', leitor.fonte[inicio:leitor.i], linha, coluna)

    return Token('INTEIRO', leitor.fonte[inicio:leitor.i], linha, coluna)


def _ler_texto(leitor, linha, coluna):
    inicio = leitor.i
    leitor.avancar()          # a aspa de abertura

    while True:
        # Um texto vive numa linha so. Se a linha (ou o arquivo) acabou antes da
        # aspa de fechamento, o erro e relatado na aspa de abertura.
        if leitor.fim() or leitor.olhar() == '\n':
            raise ErroMPL('lexico', linha, coluna,
                          'texto aberto e nao fechado')

        c = leitor.olhar()

        if c == '"':
            leitor.avancar()
            break

        if c == '\\':
            # a posicao do erro e a da barra, nao a do caractere que veio depois
            linha_escape, coluna_escape = leitor.linha, leitor.coluna
            leitor.avancar()
            if leitor.olhar() not in ESCAPES:
                raise ErroMPL('lexico', linha_escape, coluna_escape,
                              'escape invalido: so valem \\n, \\t, \\" e \\\\')
            leitor.avancar()
            continue

        leitor.avancar()

    # O lexema e a fatia crua do fonte, com as aspas e com os escapes na forma
    # original. O fonte "a\nb" vira o lexema "a\nb", cinco caracteres entre
    # aspas. Quem interpreta o escape de verdade e a Entrega 4, nao esta.
    return Token('TEXTO', leitor.fonte[inicio:leitor.i], linha, coluna)


def _ler_operador(leitor, linha, coluna):
    for simbolo, tipo in OPERADORES:
        if leitor.fonte.startswith(simbolo, leitor.i):
            for _ in simbolo:
                leitor.avancar()
            return Token(tipo, simbolo, linha, coluna)
    return None


def _proximo_token(leitor):
    linha, coluna = leitor.linha, leitor.coluna
    c = leitor.olhar()

    if _e_letra(c):
        return _ler_identificador(leitor, linha, coluna)

    if _e_digito(c):
        return _ler_numero(leitor, linha, coluna)

    if c == '"':
        return _ler_texto(leitor, linha, coluna)

    token = _ler_operador(leitor, linha, coluna)
    if token is not None:
        return token

    # Sobrou o que nao pertence a linguagem. O '.' solto cai aqui, e '.5' e erro
    # pelo mesmo motivo que '@' e: nao existe token que comece assim.
    raise ErroMPL('lexico', linha, coluna,
                  f'caractere que nao pertence a linguagem: {c}')


# ------------------------------------------------------------------ a fase

def analisar(fonte):
    """Recebe o texto do programa. Devolve a lista de Token."""
    leitor = _Leitor(fonte)
    tokens = []

    while True:
        _pular_espacos_e_comentarios(leitor)
        if leitor.fim():
            break
        tokens.append(_proximo_token(leitor))

    # O FIM_ARQUIVO fica onde o cursor parou depois de engolir os espacos do
    # final. Se o arquivo termina com quebra de linha, isso da a linha seguinte
    # na coluna 1. Se nao termina, da logo depois do ultimo caractere. As duas
    # regras do contrato saem sozinhas, sem nenhum caso especial.
    tokens.append(Token('FIM_ARQUIVO', '', leitor.linha, leitor.coluna))
    return tokens
