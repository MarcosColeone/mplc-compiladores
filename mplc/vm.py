"""
Entrega 4, terceira metade (sim, sao tres): a maquina virtual.

Le o .mplb e executa. Precisa de:
  - uma pilha de operandos;
  - um registro de ativacao por chamada, com os locais e o ponto de volta;
  - deteccao de divisao por zero e de estouro de pilha, com codigo de saida 2.

Essa e a materia da aula 11 virando codigo: sem registro de ativacao, a
recursao nao funciona.
"""
import sys

from mplc.erros import ErroMPL


# Quantas chamadas MPL podem estar abertas ao mesmo tempo. O limite e nosso, e
# nao o do Python: cada chamada da MPL gasta alguns quadros do interpretador,
# entao o limite dele e levantado para que o NOSSO estoure primeiro. Sem isso,
# quem relata o estouro e o Python, e a linha do erro se perde.
PROFUNDIDADE_MAXIMA = 900

sys.setrecursionlimit(max(sys.getrecursionlimit(), 10000))

ESCAPES = {'n': '\n', 't': '\t', '"': '"', '\\': '\\'}


def _texto_de(lexema):
    """Tira as aspas e traduz os escapes que o lexico guardou crus."""
    corpo = lexema[1:-1]
    saida = []
    i = 0
    while i < len(corpo):
        if corpo[i] == '\\' and i + 1 < len(corpo):
            saida.append(ESCAPES.get(corpo[i + 1], corpo[i + 1]))
            i += 2
        else:
            saida.append(corpo[i])
            i += 1
    return ''.join(saida)


def _valor_de(tipo, texto):
    if tipo == 'inteiro':
        return int(texto)
    if tipo == 'real':
        return float(texto)
    if tipo == 'logico':
        return texto == 'verdadeiro'
    return _texto_de(texto)


def _mostrar(valor):
    """A forma impressa de cada tipo, na secao 4.5 da especificacao.

    A ordem importa: em Python, logico e um caso especial de inteiro, entao
    testar logico primeiro e o que impede 'verdadeiro' de virar '1'.
    """
    if isinstance(valor, bool):
        return 'verdadeiro' if valor else 'falso'
    if isinstance(valor, int):
        return str(valor)
    if isinstance(valor, float):
        return f'{valor:.6f}'
    return valor


def _dividir(a, b, linha):
    if b == 0:
        raise ErroMPL('execucao', linha, 1, 'divisao por zero')

    if isinstance(a, float) or isinstance(b, float):
        return a / b

    # Divisao inteira truncada EM DIRECAO A ZERO: -7 / 2 e -3, nao -4.
    # O // do Python arredonda para baixo, entao nao serve aqui.
    quociente = abs(a) // abs(b)
    return quociente if (a < 0) == (b < 0) else -quociente


def _resto(a, b, linha):
    if b == 0:
        raise ErroMPL('execucao', linha, 1, 'resto por zero')

    # O resto tem o sinal do DIVIDENDO: -7 % 3 e -1, e 7 % -3 e 1.
    # O % do Python segue o sinal do divisor e daria 2 no primeiro caso.
    sobra = abs(a) % abs(b)
    return sobra if a >= 0 else -sobra


class Funcao:
    def __init__(self, nome, tipo):
        self.nome = nome
        self.tipo = tipo
        self.parametros = []
        self.instrucoes = []        # lista de (operacao, argumentos)
        self.rotulos = {}           # nome do rotulo -> indice da instrucao


class Quadro:
    """Um registro de ativacao: os locais de UMA chamada.

    E o que faz a recursao funcionar. Cada chamada de fatorial tem o seu
    proprio quadro, com o seu proprio n. Se os locais fossem da maquina em vez
    de serem do quadro, fatorial(5) se atropelaria, e o pior e que fatorial(1)
    continuaria funcionando, porque so existe uma chamada.
    """

    def __init__(self, funcao):
        self.funcao = funcao
        self.locais = {}
        self.pilha = []
        self.ponteiro = 0
        self.linha = 0


def carregar(texto):
    """Le o .mplb e devolve as funcoes prontas para executar."""
    funcoes = {}
    atual = None
    lendo_corpo = False

    for bruta in texto.splitlines():
        linha = bruta.strip()
        if not linha or linha.startswith('#'):
            continue

        if linha.startswith('funcao '):
            _, nome, tipo = linha.split(' ', 2)
            atual = Funcao(nome, tipo)
            funcoes[nome] = atual
            lendo_corpo = False
            continue

        if linha.startswith('parametros'):
            resto = linha[len('parametros'):].strip()
            atual.parametros = [] if resto == '-' else resto.split()
            continue

        if linha == 'corpo':
            lendo_corpo = True
            continue

        if linha == 'fim':
            lendo_corpo = False
            continue

        if not lendo_corpo:
            continue

        if linha.endswith(':'):
            # Um rotulo nao ocupa posicao: ele aponta para a proxima instrucao.
            atual.rotulos[linha[:-1]] = len(atual.instrucoes)
            continue

        partes = linha.split(' ', 1)
        operacao = partes[0]
        argumentos = partes[1] if len(partes) > 1 else ''
        atual.instrucoes.append((operacao, argumentos))

    return funcoes


class _Maquina:

    def __init__(self, funcoes, saida):
        self.funcoes = funcoes
        self.saida = saida
        self.quadros = []

    def linha_atual(self):
        return self.quadros[-1].linha if self.quadros else 1

    def executar(self, nome, argumentos):
        if len(self.quadros) >= PROFUNDIDADE_MAXIMA:
            raise ErroMPL('execucao', self.linha_atual(), 1, 'estouro de pilha')

        funcao = self.funcoes[nome]
        quadro = Quadro(funcao)

        # A linha herdada da chamada vale ate a primeira marca do corpo, para
        # que um estouro de pilha seja relatado onde a recursao comecou.
        quadro.linha = self.linha_atual()
        for parametro, valor in zip(funcao.parametros, argumentos):
            quadro.locais[parametro] = valor

        self.quadros.append(quadro)
        try:
            return self.rodar(quadro)
        finally:
            self.quadros.pop()

    def rodar(self, quadro):
        instrucoes = quadro.funcao.instrucoes
        rotulos = quadro.funcao.rotulos

        while quadro.ponteiro < len(instrucoes):
            operacao, argumento = instrucoes[quadro.ponteiro]
            quadro.ponteiro += 1
            pilha = quadro.pilha

            if operacao == 'linha':
                quadro.linha = int(argumento)

            elif operacao == 'const':
                tipo, texto = argumento.split(' ', 1)
                pilha.append(_valor_de(tipo, texto))

            elif operacao == 'carrega':
                pilha.append(quadro.locais[argumento])

            elif operacao == 'guarda':
                quadro.locais[argumento] = pilha.pop()

            elif operacao == 'descarta':
                pilha.pop()

            elif operacao == 'paraReal':
                pilha.append(float(pilha.pop()))

            elif operacao == 'escreve':
                self.saida.write(_mostrar(pilha.pop()) + '\n')

            elif operacao == 'chama':
                nome, quantos = argumento.rsplit(' ', 1)
                quantos = int(quantos)
                argumentos = pilha[len(pilha) - quantos:] if quantos else []
                del pilha[len(pilha) - quantos:]
                pilha.append(self.executar(nome, argumentos))

            elif operacao == 'retorna':
                return pilha.pop()

            elif operacao == 'retornaVazio':
                return None

            elif operacao == 'desvia':
                quadro.ponteiro = rotulos[argumento]

            elif operacao == 'seFalso':
                if not pilha.pop():
                    quadro.ponteiro = rotulos[argumento]

            else:
                self.operar(operacao, quadro)

        return None

    def operar(self, operacao, quadro):
        pilha = quadro.pilha
        linha = quadro.linha

        if operacao == 'negativo':
            pilha.append(-pilha.pop())
            return
        if operacao == 'negacao':
            pilha.append(not pilha.pop())
            return

        direita = pilha.pop()
        esquerda = pilha.pop()

        if operacao == 'soma':
            pilha.append(esquerda + direita)
        elif operacao == 'subtrai':
            pilha.append(esquerda - direita)
        elif operacao == 'multiplica':
            pilha.append(esquerda * direita)
        elif operacao == 'divide':
            pilha.append(_dividir(esquerda, direita, linha))
        elif operacao == 'resto':
            pilha.append(_resto(esquerda, direita, linha))
        elif operacao == 'igual':
            pilha.append(esquerda == direita)
        elif operacao == 'diferente':
            pilha.append(esquerda != direita)
        elif operacao == 'menor':
            pilha.append(esquerda < direita)
        elif operacao == 'menorIgual':
            pilha.append(esquerda <= direita)
        elif operacao == 'maior':
            pilha.append(esquerda > direita)
        elif operacao == 'maiorIgual':
            pilha.append(esquerda >= direita)
        elif operacao == 'conjuncao':
            # A MPL nao tem curto-circuito: os dois lados ja foram avaliados
            # antes de chegar aqui, e isso e deliberado na especificacao.
            pilha.append(esquerda and direita)
        elif operacao == 'disjuncao':
            pilha.append(esquerda or direita)
        else:
            raise AssertionError(f'instrucao desconhecida: {operacao}')


def executar(texto_mplb, saida):
    """Executa o bytecode. Escreve o que o programa imprimir em `saida`."""
    funcoes = carregar(texto_mplb)
    _Maquina(funcoes, saida).executar('principal', [])
