"""
Entrega 4, segunda metade: geracao do codigo executavel.

Traduz o codigo de tres enderecos para o formato que a VM de voces executa.
O formato do .mplb e de voces, com uma exigencia: tem que ser TEXTO legivel.
Na apresentacao a gente vai abrir um .mplb e ler junto.

Leiam antes: CONTRATOS.md secao 6.

O formato escolhido aqui e uma maquina de PILHA. Cada linha do codigo de tres
enderecos vira uma sequencia curta: empilha os operandos, aplica a operacao,
guarda o resultado. E o jeito mais legivel de escrever, porque a ordem em que
as instrucoes aparecem e exatamente a ordem em que acontecem.
"""

# Nome que cada operador da linguagem recebe no bytecode. Os simbolos viram
# palavras porque o .mplb e para ser lido por gente.
BINARIOS = {
    '+': 'soma',
    '-': 'subtrai',
    '*': 'multiplica',
    '/': 'divide',
    '%': 'resto',
    '==': 'igual',
    '!=': 'diferente',
    '<': 'menor',
    '<=': 'menorIgual',
    '>': 'maior',
    '>=': 'maiorIgual',
    'e': 'conjuncao',
    'ou': 'disjuncao',
}

UNARIOS = {
    '-': 'negativo',
    'nao': 'negacao',
}


def _empilhar(operando):
    """Uma instrucao que poe um operando no topo da pilha."""
    if operando[0] == 'lit':
        return f'  const {operando[1]} {operando[2]}'
    return f'  carrega {operando[1]}'


def gerar(codigo_intermediario):
    """Devolve as linhas do arquivo .mplb."""
    linhas = ['# bytecode MPL, formato texto, uma instrucao por linha']

    for funcao in codigo_intermediario:
        nomes = [nome for nome, _ in funcao.parametros]
        linhas.append('')
        linhas.append(f'funcao {funcao.nome} {funcao.tipo}')
        linhas.append('parametros ' + (' '.join(nomes) if nomes else '-'))
        linhas.append('corpo')

        ultima_linha = None
        for instrucao in funcao.instrucoes:
            # So marca a linha quando ela muda. A VM guarda esse valor e o usa
            # para dizer onde um erro de execucao aconteceu.
            if instrucao.linha and instrucao.linha != ultima_linha:
                linhas.append(f'  linha {instrucao.linha}')
                ultima_linha = instrucao.linha

            op = instrucao.op
            a = instrucao.args

            if op == 'copia':
                linhas.append(_empilhar(a[1]))
                linhas.append(f'  guarda {a[0]}')

            elif op == 'paraReal':
                linhas.append(_empilhar(a[1]))
                linhas.append('  paraReal')
                linhas.append(f'  guarda {a[0]}')

            elif op == 'binario':
                linhas.append(_empilhar(a[2]))
                linhas.append(_empilhar(a[3]))
                linhas.append(f'  {BINARIOS[a[1]]}')
                linhas.append(f'  guarda {a[0]}')

            elif op == 'unario':
                linhas.append(_empilhar(a[2]))
                linhas.append(f'  {UNARIOS[a[1]]}')
                linhas.append(f'  guarda {a[0]}')

            elif op == 'chama':
                for argumento in a[2]:
                    linhas.append(_empilhar(argumento))
                linhas.append(f'  chama {a[1]} {len(a[2])}')
                if a[0]:
                    linhas.append(f'  guarda {a[0]}')
                else:
                    linhas.append('  descarta')

            elif op == 'escreve':
                linhas.append(_empilhar(a[0]))
                linhas.append('  escreve')

            elif op == 'retorna':
                if a[0] is None:
                    linhas.append('  retornaVazio')
                else:
                    linhas.append(_empilhar(a[0]))
                    linhas.append('  retorna')

            elif op == 'rotulo':
                linhas.append(f'{a[0]}:')

            elif op == 'desvia':
                linhas.append(f'  desvia {a[0]}')

            elif op == 'seFalso':
                linhas.append(_empilhar(a[0]))
                linhas.append(f'  seFalso {a[1]}')

        linhas.append('fim')

    return linhas
