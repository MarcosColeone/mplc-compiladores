"""
Entrega 4, primeira metade: codigo de tres enderecos.

A propriedade que define a representacao, e a unica que o verificador mede:
cada linha de operacao tem NO MAXIMO UM OPERADOR. Uma expressao como
a + b * c vira duas linhas, com um temporario no meio.

O formato do despejo e de voces. A propriedade nao e.

Leiam antes: CONTRATOS.md secao 5.
"""

TIPOS_PADRAO = {
    'inteiro': ('inteiro', '0'),
    'real': ('real', '0.000000'),
    'logico': ('logico', 'falso'),
    'texto': ('texto', '""'),
}


def _partes(rotulo):
    """Mesma leitura de rotulo usada na semantica (CONTRATOS secao 3)."""
    return rotulo.split(' ', 2)


class Instrucao:
    """Uma linha do codigo de tres enderecos.

    O campo `linha` e o que permite a VM dizer em que linha do programa original
    um erro de execucao aconteceu. Sem ele, uma divisao por zero seria relatada
    em lugar nenhum.
    """

    def __init__(self, op, *args, linha=0):
        self.op = op
        self.args = args
        self.linha = linha


class FuncaoIR:
    def __init__(self, nome, tipo, parametros):
        self.nome = nome
        self.tipo = tipo
        self.parametros = parametros      # lista de (nome_interno, tipo)
        self.instrucoes = []
        self.locais = []                  # nomes internos declarados no corpo

    def emitir(self, op, *args, linha=0):
        self.instrucoes.append(Instrucao(op, *args, linha=linha))


class _Gerador:
    """Percorre a arvore e produz o codigo de tres enderecos.

    Duas coisas valem explicacao.

    A primeira e a conversao para real. A regra 3.1 da linguagem diz que
    inteiro vira real quando o contexto exige real, e os contextos sao quatro:
    atribuicao, argumento, retorno e os lados de um operador. Os tres primeiros
    sao resolvidos aqui emitindo `paraReal` sempre que o DESTINO e real, sem
    precisar descobrir o tipo da expressao: converter um real em real nao muda
    nada. O quarto caso a VM resolve sozinha, porque um inteiro somado a um real
    ja da real.

    A segunda e o sombreamento. Tres variaveis chamadas x em blocos aninhados
    viveriam no mesmo registro de ativacao e se atropelariam, entao cada
    declaracao ganha um nome interno unico dentro da funcao. O x de dentro vira
    x.2, e quem le o --ir enxerga qual e qual.
    """

    def __init__(self, arvore, tabela):
        self.arvore = arvore
        self.tabela = tabela
        self.funcoes = {}         # nome -> (tipo de retorno, lista de tipos dos parametros)
        self.atual = None
        self.escopos = []         # pilha de dicionarios: nome no fonte -> nome interno
        self.usados = set()       # nomes internos ja usados nesta funcao
        self.tipos = {}           # nome interno -> tipo declarado
        self.n_temp = 0
        self.n_rotulo = 0

    # ------------------------------------------------------------ apoio

    def novo_temp(self):
        nome = f't{self.n_temp}'
        self.n_temp += 1
        self.atual.locais.append(nome)
        return ('var', nome)

    def novo_rotulo(self):
        nome = f'L{self.n_rotulo}'
        self.n_rotulo += 1
        return nome

    def abrir_escopo(self):
        self.escopos.append({})

    def fechar_escopo(self):
        self.escopos.pop()

    def declarar(self, nome, tipo):
        """Da um nome interno unico, para que o sombreamento sobreviva."""
        interno = nome
        n = 2
        while interno in self.usados:
            interno = f'{nome}.{n}'
            n += 1
        self.usados.add(interno)
        self.escopos[-1][nome] = interno
        self.tipos[interno] = tipo
        return interno

    def resolver(self, nome):
        for escopo in reversed(self.escopos):
            if nome in escopo:
                return escopo[nome]
        return nome

    # --------------------------------------------------------- programa

    def executar(self):
        for no in self.arvore.filhos:
            _, nome, tipo = _partes(no.rotulo)
            tipos = [_partes(p.rotulo)[2] for p in no.filhos[0].filhos]
            self.funcoes[nome] = (tipo, tipos)

        return [self.gerar_funcao(no) for no in self.arvore.filhos]

    def gerar_funcao(self, no):
        _, nome, tipo = _partes(no.rotulo)

        self.usados = set()
        self.escopos = []
        self.tipos = {}
        self.n_temp = 0

        # O escopo dos parametros, o primeiro dos dois que a funcao abre.
        self.abrir_escopo()
        parametros = []
        for p in no.filhos[0].filhos:
            _, nome_p, tipo_p = _partes(p.rotulo)
            parametros.append((self.declarar(nome_p, tipo_p), tipo_p))

        self.atual = FuncaoIR(nome, tipo, parametros)
        self.gerar_bloco(no.filhos[1])

        # Uma funcao vazio pode acabar sem retorne escrito. A de tipo declarado
        # nao chega aqui sem retorno, porque a Entrega 3 ja recusou esse caso.
        if tipo == 'vazio':
            self.atual.emitir('retorna', None, linha=no.linha)

        self.fechar_escopo()
        return self.atual

    # --------------------------------------------------------- comandos

    def gerar_bloco(self, no):
        self.abrir_escopo()
        for comando in no.filhos:
            self.gerar_comando(comando)
        self.fechar_escopo()

    def gerar_comando(self, no):
        marca = _partes(no.rotulo)[0]
        metodo = getattr(self, f'comando_{marca}')
        metodo(no)

    def comando_declaracao(self, no):
        _, nome, tipo = _partes(no.rotulo)

        if no.filhos:
            valor = self.expressao(no.filhos[0])
        else:
            _, padrao = TIPOS_PADRAO[tipo]
            valor = ('lit', tipo, padrao)

        interno = self.declarar(nome, tipo)
        self.atual.locais.append(interno)
        self.guardar(interno, valor, tipo, no.linha)

    def comando_atribuicao(self, no):
        nome = _partes(no.rotulo)[1]
        interno = self.resolver(nome)
        valor = self.expressao(no.filhos[0])
        self.guardar(interno, valor, self.tipos.get(interno, 'inteiro'), no.linha)

    def guardar(self, interno, valor, tipo, linha):
        """Guarda um valor num local, convertendo se o destino for real."""
        if tipo == 'real':
            self.atual.emitir('paraReal', interno, valor, linha=linha)
        else:
            self.atual.emitir('copia', interno, valor, linha=linha)

    def comando_se(self, no):
        condicao = self.expressao(no.filhos[0])

        if len(no.filhos) == 3:
            senao = self.novo_rotulo()
            fim = self.novo_rotulo()
            self.atual.emitir('seFalso', condicao, senao, linha=no.linha)
            self.gerar_bloco(no.filhos[1])
            self.atual.emitir('desvia', fim, linha=no.linha)
            self.atual.emitir('rotulo', senao, linha=no.linha)
            self.gerar_bloco(no.filhos[2])
            self.atual.emitir('rotulo', fim, linha=no.linha)
        else:
            fim = self.novo_rotulo()
            self.atual.emitir('seFalso', condicao, fim, linha=no.linha)
            self.gerar_bloco(no.filhos[1])
            self.atual.emitir('rotulo', fim, linha=no.linha)

    def comando_enquanto(self, no):
        topo = self.novo_rotulo()
        fim = self.novo_rotulo()

        self.atual.emitir('rotulo', topo, linha=no.linha)
        condicao = self.expressao(no.filhos[0])
        self.atual.emitir('seFalso', condicao, fim, linha=no.linha)
        self.gerar_bloco(no.filhos[1])
        self.atual.emitir('desvia', topo, linha=no.linha)
        self.atual.emitir('rotulo', fim, linha=no.linha)

    def comando_escreva(self, no):
        valor = self.expressao(no.filhos[0])
        self.atual.emitir('escreve', valor, linha=no.linha)

    def comando_retorne(self, no):
        if no.filhos:
            valor = self.expressao(no.filhos[0])
            if self.atual.tipo == 'real':
                temp = self.novo_temp()
                self.atual.emitir('paraReal', temp[1], valor, linha=no.linha)
                valor = temp
            self.atual.emitir('retorna', valor, linha=no.linha)
        else:
            self.atual.emitir('retorna', None, linha=no.linha)

    def comando_chamada(self, no):
        self.chamada(no, descarta=True)

    def comando_bloco(self, no):
        self.gerar_bloco(no)

    # ------------------------------------------------------- expressoes

    def expressao(self, no):
        """Devolve um OPERANDO: ('lit', tipo, valor) ou ('var', nome).

        Nunca devolve uma expressao composta. E isso que garante no maximo um
        operador por linha: cada operacao vira a sua propria linha, com um
        temporario guardando o resultado parcial.
        """
        partes = _partes(no.rotulo)
        marca = partes[0]

        if marca == 'literal':
            return ('lit', partes[1], partes[2])

        if marca == 'variavel':
            return ('var', self.resolver(partes[1]))

        if marca == 'chamada':
            return self.chamada(no, descarta=False)

        if marca == 'unario':
            operando = self.expressao(no.filhos[0])
            destino = self.novo_temp()
            self.atual.emitir('unario', destino[1], partes[1], operando, linha=no.linha)
            return destino

        if marca == 'binario':
            esquerda = self.expressao(no.filhos[0])
            direita = self.expressao(no.filhos[1])
            destino = self.novo_temp()
            self.atual.emitir('binario', destino[1], partes[1], esquerda, direita,
                              linha=no.linha)
            return destino

        raise AssertionError(f'expressao inesperada: {no.rotulo}')

    def chamada(self, no, descarta):
        nome = _partes(no.rotulo)[1]
        tipo_retorno, tipos_parametros = self.funcoes[nome]

        argumentos = []
        for argumento, tipo_p in zip(no.filhos, tipos_parametros):
            valor = self.expressao(argumento)
            if tipo_p == 'real':
                temp = self.novo_temp()
                self.atual.emitir('paraReal', temp[1], valor, linha=no.linha)
                valor = temp
            argumentos.append(valor)

        if descarta or tipo_retorno == 'vazio':
            self.atual.emitir('chama', None, nome, argumentos, linha=no.linha)
            return ('lit', 'inteiro', '0')

        destino = self.novo_temp()
        self.atual.emitir('chama', destino[1], nome, argumentos, linha=no.linha)
        return destino


# ------------------------------------------------------------- o despejo

def _texto_operando(operando):
    return operando[2] if operando[0] == 'lit' else operando[1]


def gerar(arvore, tabela):
    """Devolve o codigo de tres enderecos."""
    return _Gerador(arvore, tabela).executar()


def despejar(codigo):
    """Devolve as linhas do --ir."""
    linhas = []

    for funcao in codigo:
        parametros = ', '.join(f'{nome} {tipo}' for nome, tipo in funcao.parametros)
        linhas.append(f'funcao {funcao.nome} {funcao.tipo} ({parametros})')

        for instrucao in funcao.instrucoes:
            op = instrucao.op
            a = instrucao.args

            if op == 'copia':
                linhas.append(f'  {a[0]} = {_texto_operando(a[1])}')
            elif op == 'paraReal':
                linhas.append(f'  {a[0]} = paraReal {_texto_operando(a[1])}')
            elif op == 'binario':
                # A unica linha com operador, e so um deles.
                linhas.append(f'  {a[0]} = {_texto_operando(a[2])} {a[1]} '
                              f'{_texto_operando(a[3])}')
            elif op == 'unario':
                linhas.append(f'  {a[0]} = {a[1]} {_texto_operando(a[2])}')
            elif op == 'chama':
                argumentos = ' '.join(_texto_operando(x) for x in a[2])
                alvo = f'{a[0]} = ' if a[0] else ''
                linhas.append(f'  {alvo}chama {a[1]}'
                              + (f' {argumentos}' if argumentos else ''))
            elif op == 'escreve':
                linhas.append(f'  escreva {_texto_operando(a[0])}')
            elif op == 'retorna':
                linhas.append('  retorne' + (f' {_texto_operando(a[0])}' if a[0] else ''))
            elif op == 'rotulo':
                linhas.append(f'{a[0]}:')
            elif op == 'desvia':
                linhas.append(f'  desvie {a[0]}')
            elif op == 'seFalso':
                linhas.append(f'  seFalso {_texto_operando(a[0])} desvie {a[1]}')

        linhas.append('fim')

    return linhas
