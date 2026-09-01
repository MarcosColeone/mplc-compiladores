# MPL, Minha Pequena Linguagem

Compilador da MPL escrito para o trabalho semestral de Compiladores.

UNISAGRADO, Ciência da Computação, 2026-2. Prof. Luiz Ricardo Mantovani da Silva.

Esqueleto de origem: [compiladores-lab](https://github.com/LuizRMSilva1973/compiladores-lab).

## Grupo

| Nome | RA | E-mail |
|---|---|---|
| Marcos Coleone de Arruda | 23110557 | marcos.23110557@alunos.unisagrado.edu.br |
| Maria Fernanda Carreon | 23110626 | maria.23110626@alunos.unisagrado.edu.br |
| Aline Herrera | 23111220 | aline.23111220@alunos.unisagrado.edu.br |
| Laryssa Patez da Silva | 23110710 | laryssa.23110710@alunos.unisagrado.edu.br |
| Gabriel Rocha Guimarães | 23110134 | gabriel.23110134@alunos.unisagrado.edu.br |
| Jean Beltrame | 23111307 | jean.23111307@alunos.unisagrado.edu.br |

Turma B (segunda-feira).

## Como rodar

Só precisa de Python 3, sem nenhuma biblioteca externa.

```bash
./compilar --tokens programa.mpl    # lista de tokens (Entrega 1)
./compilar --ast    programa.mpl    # árvore sintática (Entrega 2)
./compilar --tabela programa.mpl    # tabela de símbolos (Entrega 3)
./compilar --ir     programa.mpl    # código de três endereços (Entrega 4)
./compilar          programa.mpl    # gera programa.mplb
./executar          programa.mplb   # roda o programa
```

Verificação:

```bash
make verificar E=1     # confere a Entrega 1
make prova E=1         # confere num clone limpo, que é o que a correção faz
make evidencias E=1    # grava evidencias/verificacao-1.txt
```

## Estado das entregas

| Entrega | Arquivo | Situação |
|---|---|---|
| 1. Analisador léxico | `mplc/lexico.py` | pronta, 20 de 20 provas |
| 2. Analisador sintático | `mplc/sintatico.py` | a fazer |
| 3. Tabela de símbolos e tipos | `mplc/semantica.py` | a fazer |
| 4. Intermediário, geração e VM | `mplc/intermediario.py`, `gerador.py`, `vm.py` | a fazer |

---

# Entrega 1: tabela de tokens

O analisador léxico é um scanner escrito à mão, que percorre o texto caractere a caractere.
Não usa a biblioteca `re`. A posição fica toda concentrada na classe `_Leitor`, que é a única
que move o cursor: ela incrementa a coluna a cada caractere e zera a coluna ao passar por um
`\n`. Como só existe um lugar que anda no texto, a coluna sai certa em todo token sem nenhum
ajuste espalhado pelo código.

A primeira coluna de cada linha é 1.

## Descarte: espaços e comentários

Estes não geram token. São consumidos antes de cada token pela função
`_pular_espacos_e_comentarios`.

| O que é | Reconhecido por | Observação |
|---|---|---|
| espaço em branco | `[ \t\r\n]+` | separa tokens |
| comentário de linha | `//[^\n]*` | vai até o fim da linha |
| comentário de bloco | `/\*` até o primeiro `*/` | não aninha, e pode atravessar linhas |

## Literais

| Tipo do token | Expressão regular | Exemplos | Função |
|---|---|---|---|
| `INTEIRO` | `[0-9]+` | `0`, `42`, `1000` | `_ler_numero` |
| `REAL` | `[0-9]+\.[0-9]+` | `3.14`, `0.5`, `10.0` | `_ler_numero` |
| `LOGICO` | `verdadeiro\|falso` | `verdadeiro`, `falso` | `_ler_identificador`, via tabela `PALAVRAS` |
| `TEXTO` | `"([^"\\\n]\|\\[ntr"\\])*"` | `"oi"`, `"a\nb"`, `""` | `_ler_texto` |

O ponto do `REAL` exige dígito dos dois lados, então `3.` e `.5` são erro léxico.

O lexema de um `TEXTO` sai cru, exatamente como apareceu no fonte: com as aspas e com os
escapes na forma original. O fonte `"a\nb"` produz o lexema `"a\nb"`, com cinco caracteres
entre aspas. A tradução do escape para o caractere de verdade é assunto da Entrega 4.

Escapes aceitos dentro de um texto: `\n`, `\t`, `\"` e `\\`. Qualquer outro é erro léxico.

## Identificador

| Tipo do token | Expressão regular | Exemplos |
|---|---|---|
| `ID` | `[a-zA-Z_][a-zA-Z0-9_]*`, desde que não esteja em `PALAVRAS` | `x`, `soma`, `_tmp`, `sePossivel` |

Só letras ASCII. Um identificador com acento é erro léxico, porque a especificação restringe
o alfabeto a `a-z`, `A-Z` e `_`.

O nome é lido inteiro primeiro e só depois consultado na tabela de palavras reservadas. É o
que faz `sePossivel` ser um `ID`, e não um `se` seguido de `Possivel`.

## Palavras reservadas

Todas casam com a mesma expressão do identificador, `[a-zA-Z_][a-zA-Z0-9_]*`, e são separadas
por consulta ao dicionário `PALAVRAS`.

| Lexema | Tipo do token |
|---|---|
| `funcao` | `FUNCAO` |
| `retorne` | `RETORNE` |
| `se` | `SE` |
| `senao` | `SENAO` |
| `enquanto` | `ENQUANTO` |
| `escreva` | `ESCREVA` |
| `inteiro` | `TIPO_INTEIRO` |
| `real` | `TIPO_REAL` |
| `logico` | `TIPO_LOGICO` |
| `texto` | `TIPO_TEXTO` |
| `vazio` | `TIPO_VAZIO` |
| `verdadeiro` | `LOGICO` |
| `falso` | `LOGICO` |
| `e` | `E` |
| `ou` | `OU` |
| `nao` | `NAO` |

`verdadeiro` e `falso` são palavras reservadas na hora de recusar o nome de uma variável, mas
o token que sai delas é o literal `LOGICO`, porque é isso que elas são dentro de uma
expressão.

## Operadores e delimitadores

Reconhecidos por comparação direta de prefixo, na ordem da lista `OPERADORES`.

| Lexema | Tipo do token |
|---|---|
| `<=` | `MENOR_IGUAL` |
| `>=` | `MAIOR_IGUAL` |
| `==` | `IGUAL` |
| `!=` | `DIFERENTE` |
| `+` | `MAIS` |
| `-` | `MENOS` |
| `*` | `VEZES` |
| `/` | `DIVIDE` |
| `%` | `RESTO` |
| `<` | `MENOR` |
| `>` | `MAIOR` |
| `=` | `ATRIBUI` |
| `(` | `ABRE_PAR` |
| `)` | `FECHA_PAR` |
| `{` | `ABRE_CHAVE` |
| `}` | `FECHA_CHAVE` |
| `,` | `VIRGULA` |
| `;` | `PONTO_VIRGULA` |

**A ordem dessa lista é o ponto sensível da entrega.** Os símbolos de dois caracteres estão
antes dos de um. Se `<` fosse testado primeiro, `x <= 3` viraria quatro tokens em vez de três,
e o defeito só apareceria na Entrega 2, num lugar sem relação nenhuma com o léxico. A regra
que evita isso se chama maximal munch: casar sempre o maior símbolo possível. Vale para os
quatro pares em que um símbolo é prefixo do outro, `<=` e `<`, `>=` e `>`, `==` e `=`,
`!=` e `!`.

O caractere `!` sozinho não existe na MPL. A negação é a palavra `nao`. Então `!` fora de
`!=` é erro léxico.

## Fim de arquivo

| Tipo do token | Lexema | Posição |
|---|---|---|
| `FIM_ARQUIVO` | vazio | onde o cursor parou depois de consumir os espaços finais |

Se o arquivo termina com quebra de linha, isso dá a linha seguinte à última, na coluna 1. Se
não termina, dá logo depois do último caractere. As duas regras do contrato saem do mesmo
código, sem caso especial.

## Erros léxicos

Todos saem como `ErroMPL('lexico', linha, coluna, mensagem)`, que o `mplc/principal.py`
imprime em `stderr` no formato do contrato e devolve o código de saída 1.

| Situação | Onde a posição é ancorada |
|---|---|
| escape inválido dentro de um texto | a barra invertida que abre o escape |
| texto sem a aspa de fechamento na mesma linha | a aspa de abertura |
| comentário de bloco aberto e nunca fechado | o `/*` que abriu o comentário |
| ponto de real sem dígito depois, como `3.` | o ponto |
| ponto sem dígito antes, como `.5` | o ponto, que não inicia token nenhum |
| caractere fora da linguagem, como `@` ou `ç` | o próprio caractere |

A ideia por trás dessas escolhas é sempre a mesma: apontar o caractere que estragou o token,
não o começo do token nem o fim do anterior. É o que o contrato pede na seção 7.
