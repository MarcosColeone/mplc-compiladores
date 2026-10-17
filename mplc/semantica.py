"""
Entrega 3: analise semantica.

Tabela de simbolos, escopos aninhados e verificacao de tipos.

Tres coisas que costumam ser esquecidas e valem nota:
  - o corpo de uma funcao abre DOIS escopos (o dos parametros e o do bloco);
  - uma funcao pode ser chamada antes de aparecer no arquivo, entao a
    primeira passada so coleta assinaturas;
  - funcao com retorno declarado precisa garantir o retorno em TODOS os
    caminhos.

Leiam antes: LINGUAGEM.md secoes 3 a 5, e CONTRATOS.md secao 4.
"""
from mplc.erros import ErroMPL


NUMERICOS = ('inteiro', 'real')


def _partes(rotulo):
    """Quebra o rotulo de um no nos seus campos.

    Os rotulos sao definidos na secao 3 do contrato, entao le-los aqui nao e
    gambiarra: e usar o mesmo formato documentado que o --ast imprime. O limite
    de duas quebras preserva o valor de um 'literal texto "a b c"' inteiro.
    """
    return rotulo.split(' ', 2)


def _cabe(origem, destino):
    """A unica conversao implicita da MPL: inteiro vira real (LINGUAGEM 3.1).

    Nenhuma outra existe. Real nao vira inteiro, logico nao vira numero e
    numero nao vira texto.
    """
    if origem == destino:
        return True
    return origem == 'inteiro' and destino == 'real'


# ----------------------------------------------------------------- a tabela

class Simbolo:
    """Um nome que vive em algum escopo."""

    def __init__(self, nome, categoria, tipo, linha, parametros=None):
        self.nome = nome
        self.categoria = categoria    # 'funcao', 'parametro' ou 'variavel'
        self.tipo = tipo              # o tipo da variavel, ou o RETORNO da funcao
        self.linha = linha
        self.parametros = parametros  # so para funcao: a lista de tipos
        self.posicao = None           # a Entrega 4 preenche com o lugar na memoria

    def assinatura(self):
        if self.categoria == 'funcao':
            return f"{self.tipo}({','.join(self.parametros)})"
        return self.tipo


class Escopo:
    """Um nivel da tabela.

    A estrutura e uma ARVORE de escopos, guardada numa lista pela ordem em que
    cada um abriu. Cada escopo aponta para o pai, e a busca de um nome sobe por
    essa corrente ate o global. E o que da sombreamento de graca: a busca para
    no primeiro escopo que conhece o nome, entao o de dentro esconde o de fora
    sem ninguem precisar apagar nada ao fechar o bloco.
    """

    def __init__(self, numero, descricao, pai):
        self.numero = numero
        self.descricao = descricao    # 'global', 'funcao <nome>' ou 'bloco'
        self.pai = pai                # outro Escopo, ou None no global
        self.simbolos = []            # na ordem de declaracao
        self.indice = {}              # nome -> Simbolo, so deste nivel

    def declarado_aqui(self, nome):
        """So este nivel. E o que define redeclaracao: o mesmo nome no MESMO escopo."""
        return self.indice.get(nome)

    def buscar(self, nome):
        """Este nivel e os de fora, parando no primeiro que conhecer o nome."""
        escopo = self
        while escopo is not None:
            simbolo = escopo.indice.get(nome)
            if simbolo is not None:
                return simbolo
            escopo = escopo.pai
        return None

    def declarar(self, simbolo):
        self.simbolos.append(simbolo)
        self.indice[simbolo.nome] = simbolo
        return simbolo


class Tabela:
    """Todos os escopos do programa, na ordem em que abriram."""

    def __init__(self):
        self.escopos = []
        self.global_ = self.abrir('global', None)

    def abrir(self, descricao, pai):
        escopo = Escopo(len(self.escopos), descricao, pai)
        self.escopos.append(escopo)
        return escopo


# ------------------------------------------------------------- o analisador

class _Analisador:

    def __init__(self, arvore):
        self.arvore = arvore
        self.tabela = Tabela()
        self.funcao_atual = None      # o Simbolo da funcao sendo visitada

    def erro(self, no, mensagem):
        raise ErroMPL('semantico', no.linha, no.coluna, mensagem)

    # ------------------------------------------------- primeira passada

    def coletar_assinaturas(self):
        """So as assinaturas, sem olhar nenhum corpo.

        E o que permite uma funcao chamar outra declarada mais abaixo no
        arquivo, inclusive recursao mutua. Sem esta passada, 'par' nao
        conseguiria chamar 'impar' se 'impar' viesse depois.
        """
        for no in self.arvore.filhos:
            _, nome, tipo = _partes(no.rotulo)

            if self.tabela.global_.declarado_aqui(nome):
                self.erro(no, f"a funcao '{nome}' ja foi declarada")

            parametros = [_partes(p.rotulo)[2] for p in no.filhos[0].filhos]
            self.tabela.global_.declarar(
                Simbolo(nome, 'funcao', tipo, no.linha, parametros))

        self.conferir_principal()

    def conferir_principal(self):
        principal = self.tabela.global_.declarado_aqui('principal')

        if principal is None:
            # Nao ha no para apontar, entao o erro fica no comeco do arquivo.
            raise ErroMPL('semantico', 1, 1,
                          "todo programa precisa de uma funcao 'principal'")

        no = self.no_da_funcao('principal')
        if principal.parametros:
            self.erro(no, "a funcao 'principal' nao recebe parametros")
        if principal.tipo != 'vazio':
            self.erro(no, "a funcao 'principal' precisa devolver vazio")

    def no_da_funcao(self, nome):
        for no in self.arvore.filhos:
            if _partes(no.rotulo)[1] == nome:
                return no
        return self.arvore

    # ------------------------------------------------- segunda passada

    def analisar_corpos(self):
        for no in self.arvore.filhos:
            self.analisar_funcao(no)

    def analisar_funcao(self, no):
        _, nome, _tipo = _partes(no.rotulo)
        self.funcao_atual = self.tabela.global_.declarado_aqui(nome)

        # O primeiro dos dois escopos da funcao: o dos parametros.
        escopo_funcao = self.tabela.abrir(f'funcao {nome}', self.tabela.global_)
        for p in no.filhos[0].filhos:
            _, nome_p, tipo_p = _partes(p.rotulo)
            if escopo_funcao.declarado_aqui(nome_p):
                self.erro(p, f"o parametro '{nome_p}' foi declarado duas vezes")
            escopo_funcao.declarar(Simbolo(nome_p, 'parametro', tipo_p, p.linha))

        # O segundo: o bloco do corpo, onde moram as variaveis locais.
        self.analisar_bloco(no.filhos[1], escopo_funcao)

        # A garantia de retorno e ESTRUTURAL, nunca uma avaliacao da condicao.
        if self.funcao_atual.tipo != 'vazio' and not self.garante_retorno(no.filhos[1]):
            self.erro(no, f"a funcao '{nome}' tem caminho sem retorne")

        self.funcao_atual = None

    def garante_retorno(self, no):
        """Todo caminho desta construcao termina em retorne?

        O compilador olha a FORMA do programa, nao o valor das condicoes. Um se
        sem senao nunca garante, porque existe o caminho em que a condicao e
        falsa, por mais obvia que ela pareca para quem escreveu. Um enquanto
        tambem nao, porque pode rodar zero vezes.
        """
        rotulo = _partes(no.rotulo)[0]

        if rotulo == 'retorne':
            return True
        if rotulo == 'bloco':
            return any(self.garante_retorno(f) for f in no.filhos)
        if rotulo == 'se':
            # Tres filhos quer dizer que existe senao. Os DOIS lados precisam
            # garantir; com um lado so, o outro caminho fica sem retorno.
            return (len(no.filhos) == 3
                    and self.garante_retorno(no.filhos[1])
                    and self.garante_retorno(no.filhos[2]))
        return False

    # ------------------------------------------------------- os comandos

    def analisar_bloco(self, no, pai):
        """Todo bloco abre um escopo, mesmo vazio."""
        escopo = self.tabela.abrir('bloco', pai)
        for comando in no.filhos:
            self.analisar_comando(comando, escopo)
        return escopo

    def analisar_comando(self, no, escopo):
        rotulo = _partes(no.rotulo)[0]

        if rotulo == 'declaracao':
            self.comando_declaracao(no, escopo)
        elif rotulo == 'atribuicao':
            self.comando_atribuicao(no, escopo)
        elif rotulo == 'se':
            self.comando_se(no, escopo)
        elif rotulo == 'enquanto':
            self.comando_enquanto(no, escopo)
        elif rotulo == 'escreva':
            self.comando_escreva(no, escopo)
        elif rotulo == 'retorne':
            self.comando_retorne(no, escopo)
        elif rotulo == 'chamada':
            # Chamada usada como comando: aqui o retorno vazio e permitido.
            self.tipo_da_chamada(no, escopo, aceita_vazio=True)
        elif rotulo == 'bloco':
            self.analisar_bloco(no, escopo)

    def comando_declaracao(self, no, escopo):
        _, nome, tipo = _partes(no.rotulo)

        if tipo == 'vazio':
            self.erro(no, "nao existe variavel de tipo vazio")

        # So o MESMO escopo conta. Uma variavel de mesmo nome num bloco de
        # dentro nao e redeclaracao: e sombreamento, e isso e permitido.
        if escopo.declarado_aqui(nome):
            self.erro(no, f"'{nome}' ja foi declarado neste escopo")

        if no.filhos:
            valor = self.tipo_de(no.filhos[0], escopo)
            if not _cabe(valor, tipo):
                self.erro(no, f"nao da para guardar {valor} em {tipo}")

        escopo.declarar(Simbolo(nome, 'variavel', tipo, no.linha))

    def comando_atribuicao(self, no, escopo):
        _, nome = _partes(no.rotulo)
        simbolo = escopo.buscar(nome)

        if simbolo is None:
            self.erro(no, f"'{nome}' nao foi declarado")
        if simbolo.categoria == 'funcao':
            self.erro(no, f"'{nome}' e uma funcao, nao da para atribuir")

        valor = self.tipo_de(no.filhos[0], escopo)
        if not _cabe(valor, simbolo.tipo):
            self.erro(no, f"nao da para guardar {valor} em {simbolo.tipo}")

    def comando_se(self, no, escopo):
        self.conferir_condicao(no.filhos[0], escopo)
        self.analisar_bloco(no.filhos[1], escopo)
        if len(no.filhos) == 3:
            self.analisar_bloco(no.filhos[2], escopo)

    def comando_enquanto(self, no, escopo):
        self.conferir_condicao(no.filhos[0], escopo)
        self.analisar_bloco(no.filhos[1], escopo)

    def conferir_condicao(self, no, escopo):
        tipo = self.tipo_de(no, escopo)
        if tipo != 'logico':
            self.erro(no, f'a condicao precisa ser logico, e nao {tipo}')

    def comando_escreva(self, no, escopo):
        # tipo_de ja recusa chamada de funcao vazio dentro de expressao, entao
        # aqui nao sobra nenhum tipo proibido.
        self.tipo_de(no.filhos[0], escopo)

    def comando_retorne(self, no, escopo):
        esperado = self.funcao_atual.tipo

        if esperado == 'vazio':
            if no.filhos:
                self.erro(no, 'funcao vazio nao devolve valor')
            return

        if not no.filhos:
            self.erro(no, f'esta funcao precisa devolver {esperado}')

        devolvido = self.tipo_de(no.filhos[0], escopo)
        if not _cabe(devolvido, esperado):
            self.erro(no, f'esta funcao devolve {esperado}, e nao {devolvido}')

    # ----------------------------------------------------- as expressoes

    def tipo_de(self, no, escopo):
        rotulo = _partes(no.rotulo)
        marca = rotulo[0]

        if marca == 'literal':
            return rotulo[1]

        if marca == 'variavel':
            nome = rotulo[1]
            simbolo = escopo.buscar(nome)
            if simbolo is None:
                self.erro(no, f"'{nome}' nao foi declarado")
            if simbolo.categoria == 'funcao':
                self.erro(no, f"'{nome}' e uma funcao, e so vale quando chamada")
            return simbolo.tipo

        if marca == 'chamada':
            return self.tipo_da_chamada(no, escopo, aceita_vazio=False)

        if marca == 'unario':
            return self.tipo_do_unario(no, escopo, rotulo[1])

        if marca == 'binario':
            return self.tipo_do_binario(no, escopo, rotulo[1])

        self.erro(no, f'expressao que nao sei conferir: {no.rotulo}')

    def tipo_da_chamada(self, no, escopo, aceita_vazio):
        nome = _partes(no.rotulo)[1]
        simbolo = self.tabela.global_.declarado_aqui(nome)

        if simbolo is None:
            self.erro(no, f"a funcao '{nome}' nao existe")

        if len(no.filhos) != len(simbolo.parametros):
            self.erro(no, f"'{nome}' espera {len(simbolo.parametros)} "
                          f"argumento(s), e recebeu {len(no.filhos)}")

        for argumento, tipo_p in zip(no.filhos, simbolo.parametros):
            tipo_a = self.tipo_de(argumento, escopo)
            if not _cabe(tipo_a, tipo_p):
                self.erro(argumento,
                          f'este argumento devia ser {tipo_p}, e e {tipo_a}')

        # Uma funcao vazio nao produz valor, entao so pode ser comando.
        if simbolo.tipo == 'vazio' and not aceita_vazio:
            self.erro(no, f"'{nome}' devolve vazio e nao pode estar numa expressao")

        return simbolo.tipo

    def tipo_do_unario(self, no, escopo, operador):
        operando = self.tipo_de(no.filhos[0], escopo)

        if operador == 'nao':
            if operando != 'logico':
                self.erro(no, f'nao espera logico, e recebeu {operando}')
            return 'logico'

        if operando not in NUMERICOS:
            self.erro(no, f'o menos unario espera numero, e recebeu {operando}')
        return operando

    def tipo_do_binario(self, no, escopo, operador):
        esquerda = self.tipo_de(no.filhos[0], escopo)
        direita = self.tipo_de(no.filhos[1], escopo)

        if operador in ('e', 'ou'):
            if esquerda != 'logico' or direita != 'logico':
                self.erro(no, f"'{operador}' espera logico dos dois lados, "
                              f'e recebeu {esquerda} e {direita}')
            return 'logico'

        if operador == '+':
            # O unico operador com dois sentidos: soma de numeros ou juncao de
            # textos. Misturar os dois e erro de tipo, nunca concatenacao.
            if esquerda == 'texto' and direita == 'texto':
                return 'texto'
            if esquerda in NUMERICOS and direita in NUMERICOS:
                return self.promover(esquerda, direita)
            self.erro(no, f"'+' nao combina {esquerda} com {direita}")

        if operador in ('-', '*', '/'):
            if esquerda not in NUMERICOS or direita not in NUMERICOS:
                self.erro(no, f"'{operador}' espera numeros, "
                              f'e recebeu {esquerda} e {direita}')
            return self.promover(esquerda, direita)

        if operador == '%':
            # O resto e o unico que nao aceita real, nem de um lado so.
            if esquerda != 'inteiro' or direita != 'inteiro':
                self.erro(no, f"'%' so vale entre inteiros, "
                              f'e recebeu {esquerda} e {direita}')
            return 'inteiro'

        if operador in ('<', '<=', '>', '>='):
            if esquerda not in NUMERICOS or direita not in NUMERICOS:
                self.erro(no, f"'{operador}' compara numeros, "
                              f'e recebeu {esquerda} e {direita}')
            return 'logico'

        if operador in ('==', '!='):
            # Vale entre tipos iguais, e entre inteiro e real pela conversao.
            if not (_cabe(esquerda, direita) or _cabe(direita, esquerda)):
                self.erro(no, f"'{operador}' nao compara {esquerda} com {direita}")
            return 'logico'

        self.erro(no, f'operador que nao sei conferir: {operador}')

    def promover(self, esquerda, direita):
        """Inteiro com inteiro da inteiro. Qualquer real no meio puxa para real."""
        return 'inteiro' if esquerda == 'inteiro' and direita == 'inteiro' else 'real'

    # ------------------------------------------------------------ o roteiro

    def executar(self):
        self.coletar_assinaturas()
        self.analisar_corpos()
        return self.tabela


def analisar(arvore):
    """Percorre a arvore, monta a tabela e confere os tipos. Devolve a tabela."""
    return _Analisador(arvore).executar()


def despejar(tabela):
    """Devolve as linhas do --tabela, no formato da secao 4 do contrato."""
    linhas = []
    for escopo in tabela.escopos:
        if escopo.pai is None:
            linhas.append(f'escopo {escopo.numero} {escopo.descricao}')
        else:
            linhas.append(f'escopo {escopo.numero} {escopo.descricao} '
                          f'pai {escopo.pai.numero}')
        for simbolo in escopo.simbolos:
            linhas.append(f'  {simbolo.nome}|{simbolo.categoria}|'
                          f'{simbolo.assinatura()}|{simbolo.linha}')
    return linhas
