# MPL, Minha Pequena Linguagem

Compilador da MPL escrito para o trabalho semestral de Compiladores.

UNISAGRADO, Ciência da Computação, 2026-2. Prof. Luiz Ricardo Mantovani da Silva.

Esqueleto de origem: [compiladores-lab](https://github.com/LuizRMSilva1973/compiladores-lab).

## Grupo

| Nome | RA | E-mail |
|---|---|---|
| Marcos Coleone de Arruda | 23110557 | marcos.23110557@alunos.unisagrado.edu.br |
| Aline Herrera | 23111220 | aline.23111220@alunos.unisagrado.edu.br |
| Maria Fernanda Carreon | 23110626 | maria.23110626@alunos.unisagrado.edu.br |
| Gabriel Rocha Guimarães | 23110134 | gabriel.23110134@alunos.unisagrado.edu.br |
| Laryssa Patez da Silva | 23110710 | laryssa.23110710@alunos.unisagrado.edu.br |
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
| 2. Analisador sintático | `mplc/sintatico.py` | pronta, 36 de 36 provas |
| 3. Tabela de símbolos e tipos | `mplc/semantica.py` | pronta, 70 de 70 provas |
| 4. Intermediário, geração e VM | `mplc/intermediario.py`, `gerador.py`, `vm.py` | pronta, 93 de 93 provas |

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

---

# Entrega 2: a gramática implementada

O parser é uma **descida recursiva escrita à mão**, sem gerador. Cada regra da gramática
abaixo é uma função de `mplc/sintatico.py` com o mesmo nome, e cada nível de precedência é
uma função separada.

Notação EBNF: `{ x }` quer dizer zero ou mais repetições de `x`, `[ x ]` quer dizer que `x`
é opcional, e o que está entre aspas é o lexema literal. Os nomes em maiúsculas são tipos de
token que vêm do analisador léxico.

## Estrutura do programa

```ebnf
programa          ::= { funcao } FIM_ARQUIVO

funcao            ::= "funcao" tipo ID parametros bloco
tipo              ::= "inteiro" | "real" | "logico" | "texto" | "vazio"
parametros        ::= "(" [ parametro { "," parametro } ] ")"
parametro         ::= tipo ID
```

O tipo de retorno vem antes do nome. Não existe código fora de função.

## Comandos

```ebnf
bloco             ::= "{" { comando } "}"

comando           ::= declaracao
                    | atribuicao
                    | comando_se
                    | comando_enquanto
                    | comando_escreva
                    | comando_retorne
                    | chamada_comando
                    | bloco

declaracao        ::= tipo ID [ "=" expressao ] ";"
atribuicao        ::= ID "=" expressao ";"
comando_se        ::= "se" "(" expressao ")" bloco [ "senao" bloco ]
comando_enquanto  ::= "enquanto" "(" expressao ")" bloco
comando_escreva   ::= "escreva" "(" expressao ")" ";"
comando_retorne   ::= "retorne" [ expressao ] ";"
chamada_comando   ::= chamada ";"
```

As chaves do `se` e do `enquanto` são obrigatórias, mesmo para um comando só, porque `bloco`
aparece diretamente na regra e `bloco` sempre começa com `{`.

Um `bloco` solto também é um comando, e é o que permite abrir um escopo novo no meio do
código.

Duas regras começam com `ID`, a atribuição e a chamada usada como comando. O parser desempata
espiando o token seguinte, sem consumir: `=` leva para a atribuição, `(` leva para a chamada.

## Expressões, um nível por regra

```ebnf
expressao         ::= nivel_ou

nivel_ou          ::= nivel_e          { "ou" nivel_e }
nivel_e           ::= nivel_igualdade  { "e"  nivel_igualdade }
nivel_igualdade   ::= nivel_comparacao { ( "==" | "!=" ) nivel_comparacao }
nivel_comparacao  ::= nivel_soma       { ( "<" | "<=" | ">" | ">=" ) nivel_soma }
nivel_soma        ::= nivel_termo      { ( "+" | "-" ) nivel_termo }
nivel_termo       ::= nivel_unario     { ( "*" | "/" | "%" ) nivel_unario }
nivel_unario      ::= ( "nao" | "-" ) nivel_unario
                    | nivel_primario
nivel_primario    ::= INTEIRO | REAL | LOGICO | TEXTO
                    | chamada
                    | ID
                    | "(" expressao ")"

chamada           ::= ID "(" [ expressao { "," expressao } ] ")"
```

## Como a precedência está codificada nesta gramática

**A precedência é a ordem em que uma regra chama a outra.** Ela não está declarada em lugar
nenhum: `nivel_ou` só sabe produzir `nivel_e`, que só sabe produzir `nivel_igualdade`, e assim
por diante até `nivel_primario`. Quem é chamado por último fica mais fundo na árvore, e por
isso liga mais forte.

Em `1 + 2 * 3` a função `nivel_soma` monta o `+` e chama `nivel_termo` para cada lado. O `*`
nasce lá embaixo, dentro do lado direito, então o `+` fica na raiz e a multiplicação acontece
primeiro. Se as duas regras trocassem de lugar, a árvore sairia invertida, e é isso que o
`--ast` mostra mesmo sem o compilador calcular nada.

## Como a associatividade está codificada

Os seis níveis binários usam **repetição**, o `{ }` da EBNF, que no código é um laço `while`.
O laço monta o nó e usa o resultado como lado esquerdo da próxima volta, então a árvore cresce
para a esquerda:

```
10 - 4 - 3   vira   ((10 - 4) - 3)

        -
       / \
      -   3
     / \
   10   4
```

Se essas regras fossem escritas com recursão à direita, do tipo
`nivel_soma ::= nivel_termo "-" nivel_soma`, o mesmo programa produziria `10 - (4 - 3)`, que
vale 9 em vez de 3. O defeito passa despercebido em qualquer teste com dois operandos e só
aparece com três.

A regra `nivel_unario` é a única que se chama de volta, e isso é proposital: `nao` e o `-`
unário associam à direita, então `- - 2` precisa virar `-(-2)`.

## Erros sintáticos

Existe uma única função que interrompe o parser, a `esperar`, e ela sempre reporta a posição
do **token atual**, ou seja, o que apareceu no lugar do esperado. Nunca o fim do token
anterior.

| Situação | Onde o erro sai |
|---|---|
| falta o `;` no fim de um comando | no primeiro token da linha seguinte |
| falta o `}` que fecha a função | no `FIM_ARQUIVO` |
| `se` sem parênteses na condição | no token que apareceu no lugar do `(` |
| operando faltando, como em `1 + )` | no `)` |
| `se` sem as chaves obrigatórias | no comando que apareceu no lugar do `{` |
| função sem tipo de retorno | no nome da função, que apareceu onde deveria haver um tipo |

É a mesma ideia da Entrega 1, adaptada: apontar o símbolo que quebrou a expectativa, no
momento em que o parser percebeu.

---

# Entrega 3: a estrutura de escopos

## Como representamos os escopos, e por quê

Os escopos formam uma **árvore**, guardada numa lista pela ordem em que cada um abriu. Cada
escopo tem um dicionário dos nomes declarados nele e um ponteiro para o escopo pai, e a busca
de um nome sobe por essa corrente até o global.

Escolhemos árvore com ponteiro para o pai, e não uma pilha, por duas razões. A primeira é que
o sombreamento sai de graça: a busca para no primeiro escopo que conhece o nome, então a
variável de dentro esconde a de fora sem ninguém precisar apagar nada ao fechar o bloco. A
segunda é que uma pilha perde a informação quando desempilha, e nós precisamos que todos os
escopos continuem existindo depois da análise, porque o `--tabela` imprime todos eles e a
Entrega 4 vai percorrer cada um de novo para transformar nome em posição de memória.

Por isso cada `Simbolo` já nasce com um campo `posicao` vazio, reservado para a geração de
código preencher.

## Quantos escopos cada construção abre

| Construção | Escopos que abre |
|---|---|
| programa | 1, o global, que contém só funções |
| função | 2, o dos parâmetros e o do bloco do corpo |
| `se` sem `senao` | 1, o bloco do então |
| `se` com `senao` | 2, um bloco para cada lado |
| `enquanto` | 1, o bloco |
| bloco solto `{ }` | 1 |

Os escopos são numerados na ordem em que abrem, percorrendo o programa de cima para baixo e
entrando nos blocos. Um escopo vazio aparece mesmo assim, com o cabeçalho e nenhuma linha
abaixo.

## Duas passadas

A análise percorre a árvore duas vezes.

A primeira passada só coleta as **assinaturas** das funções e as coloca no escopo global. Ela
não olha nenhum corpo. É o que permite uma função chamar outra declarada mais abaixo no
arquivo, incluindo recursão mútua: sem essa passada, uma função `par` não conseguiria chamar
`impar` se `impar` viesse depois dela.

A segunda passada entra nos corpos, cria os escopos, declara variáveis e confere os tipos.
Quando ela encontra uma chamada, a assinatura já está na tabela, não importa a ordem do
arquivo.

## Regras de tipo

Existe **uma única conversão implícita**: `inteiro` vira `real` quando o contexto pede `real`.
Vale na atribuição, no argumento de chamada, no retorno e nos dois lados de um operador
aritmético ou relacional. Nenhuma outra existe, então `real` não vira `inteiro`, `logico` não
vira número e número não vira `texto`.

Três operadores merecem nota:

O `+` é o único com dois sentidos. Entre dois textos ele junta, entre dois números ele soma, e
misturar os dois é erro de tipo, nunca concatenação.

O `%` é o único que não aceita `real`, nem de um lado só.

O `==` e o `!=` comparam tipos iguais, e também `inteiro` com `real` por causa da conversão.
Já `<`, `<=`, `>` e `>=` só comparam números.

## Garantia de retorno

A verificação é **estrutural**. O compilador olha a forma do programa e nunca avalia o valor
de uma condição.

| Construção | Garante retorno? |
|---|---|
| `retorne` com valor | sim |
| bloco | sim, se algum comando dele garantir |
| `se` sem `senao` | **não**, sempre |
| `se` com `senao` | sim, se os **dois** lados garantirem |
| `enquanto` | **não**, porque pode rodar zero vezes |

Um `se` sem `senao` nunca garante, por mais óbvia que a condição pareça para quem escreveu,
porque existe o caminho em que ela é falsa. Um `enquanto` também não, porque o corpo pode
nunca executar.

## Onde cada erro é apontado

O verificador confere fase e linha nesta fase, e não a coluna, porque a posição de um erro
semântico nem sempre é única. Ainda assim cada erro aponta o nó da árvore que o causou.

| Erro | Nó apontado |
|---|---|
| nome não declarado | o uso do nome |
| redeclaração no mesmo escopo | a segunda declaração |
| tipo incompatível na atribuição | a declaração ou a atribuição |
| condição que não é lógico | a expressão da condição |
| operador com tipos errados | o operador |
| chamada com aridade ou tipo errado | a chamada, ou o argumento culpado |
| função `vazio` dentro de expressão | a chamada |
| caminho sem `retorne` | a declaração da função |
| falta de `principal` | linha 1, porque não existe nó para apontar |

---

# Entrega 4: o código intermediário, o `.mplb` e a VM

## As três peças

O código de três endereços é montado em `mplc/intermediario.py`, traduzido para o `.mplb` em
`mplc/gerador.py` e executado em `mplc/vm.py`.

```bash
./compilar --ir exemplos/relatorio.mpl     # o código de três endereços
./compilar     exemplos/relatorio.mpl      # gera exemplos/relatorio.mplb
./executar     exemplos/relatorio.mplb     # roda
```

## O código de três endereços

A regra é uma só: **cada linha de operação tem no máximo um operador**. Toda expressão
composta é quebrada em linhas simples, com temporários guardando os resultados parciais.

Para `funcao inteiro fatorial(inteiro n)` o compilador produz:

```
funcao fatorial inteiro (n inteiro)
  t0 = n <= 1
  seFalso t0 desvie L0
  retorne 1
  desvie L1
L0:
  t1 = n - 1
  t2 = chama fatorial t1
  t3 = n * t2
  retorne t3
L1:
fim
```

Duas decisões aparecem aí.

**Conversão para real.** A regra 3.1 da linguagem diz que `inteiro` vira `real` quando o
contexto exige. Em vez de recalcular o tipo de cada expressão, o gerador emite `paraReal`
sempre que o **destino** é real, na atribuição, no argumento e no retorno. Converter um real
em real não muda nada, então a regra fica simples e não erra. O caso dos dois lados de um
operador a VM resolve sozinha, porque inteiro somado a real já dá real.

**Sombreamento.** Três variáveis chamadas `x` em blocos aninhados viveriam no mesmo registro
de ativação e se atropelariam. Por isso cada declaração ganha um nome interno único dentro da
função: o `x` de dentro vira `x.2`, e quem lê o `--ir` enxerga qual é qual.

## O formato do `.mplb`

Texto legível, uma instrução por linha, como o contrato exige. É uma **máquina de pilha**:
empilha os operandos, aplica a operação, guarda o resultado. A ordem em que as instruções
aparecem é exatamente a ordem em que acontecem.

```
# bytecode MPL, formato texto, uma instrucao por linha

funcao fatorial inteiro
parametros n
corpo
  linha 2
  carrega n
  const inteiro 1
  menorIgual
  guarda t0
  carrega t0
  seFalso L0
  ...
fim
```

## O conjunto de instruções da VM

Cada linha diz o que a instrução faz com a pilha de operandos.

### Valores e locais

| Instrução | O que faz com a pilha |
|---|---|
| `const <tipo> <valor>` | empilha um literal, já convertido para o tipo |
| `carrega <nome>` | empilha o valor do local `<nome>` do quadro atual |
| `guarda <nome>` | desempilha um valor e guarda no local `<nome>` |
| `descarta` | desempilha um valor e joga fora |
| `paraReal` | desempilha, converte para real e empilha de volta |

### Aritmética

Todas desempilham dois valores, com o da direita no topo, e empilham um resultado.

| Instrução | O que faz |
|---|---|
| `soma` | soma números, ou junta dois textos |
| `subtrai` | subtrai |
| `multiplica` | multiplica |
| `divide` | divide, inteira e truncada para zero se os dois forem inteiros |
| `resto` | resto com o sinal do dividendo |

### Comparação e lógica

| Instrução | O que faz |
|---|---|
| `igual`, `diferente` | desempilham dois valores, empilham um lógico |
| `menor`, `menorIgual`, `maior`, `maiorIgual` | desempilham dois números, empilham um lógico |
| `conjuncao`, `disjuncao` | desempilham dois lógicos, empilham um lógico |
| `negativo` | desempilha um número e empilha o oposto |
| `negacao` | desempilha um lógico e empilha o inverso |

### Controle

| Instrução | O que faz |
|---|---|
| `<nome>:` | rótulo, não ocupa posição e não mexe na pilha |
| `desvia <rótulo>` | salta sem condição |
| `seFalso <rótulo>` | desempilha um lógico e salta se ele for falso |
| `chama <nome> <n>` | desempilha `n` argumentos, abre um quadro novo e empilha o retorno |
| `retorna` | desempilha o valor e devolve ao chamador |
| `retornaVazio` | devolve sem valor |

### Apoio

| Instrução | O que faz |
|---|---|
| `linha <n>` | marca a linha do programa original, para o erro de execução saber onde está |
| `escreve` | desempilha um valor e imprime, na forma da seção 4.5 da especificação |

## O registro de ativação

Cada chamada abre um **quadro** próprio, com os seus locais, a sua pilha de operandos e o seu
ponteiro de instrução. É o que faz a recursão funcionar: cada `fatorial` em andamento tem o
seu próprio `n`.

Se os locais pertencessem à máquina em vez de pertencerem ao quadro, `fatorial(5)` devolveria
lixo, e o pior é que `fatorial(1)` continuaria funcionando, porque só existe uma chamada.

O estouro de pilha é detectado em 900 quadros abertos. O limite de recursão do próprio Python
é levantado junto, para que o nosso limite estoure primeiro: assim quem relata o erro é a VM,
que sabe em que linha do programa estava, e não o interpretador.

## As três armadilhas

**A divisão inteira.** `7 / 2` é `3`, e `real x = 7 / 2;` é `3.000000`, porque a divisão
acontece antes da conversão. O `//` do Python arredonda para baixo, então `-7 / 2` daria `-4`.
A VM trunca em direção a zero e devolve `-3`.

**O sinal do resto.** `-7 % 3` é `-1`, não `2`. O resto tem o sinal do dividendo. O `%` do
Python segue o sinal do divisor, então a conta é feita com os valores absolutos e o sinal é
reposto no fim.

**O registro de ativação.** Resolvido pelo quadro por chamada, descrito acima.

## O programa do grupo

`exemplos/relatorio.mpl`, com a saída em `exemplos/relatorio.saida`.

Ele usa de propósito tudo o que a linguagem tem: recursão direta em `fatorial` e `estrelas`,
recursão mútua em `ehPar` e `ehImpar`, laço em `primo`, os quatro tipos, concatenação de
texto, as duas formas de divisão e os escapes.

A função `ehImpar` aparece no arquivo **depois** de já ter sido usada por `ehPar`. Isso só
compila porque a análise semântica coleta todas as assinaturas numa passada separada, antes
de olhar qualquer corpo.

```bash
./compilar exemplos/relatorio.mpl && ./executar exemplos/relatorio.mplb
```
