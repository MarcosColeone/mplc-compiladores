// Relatorio de numeros, escrito em MPL.
//
// Este e o programa do grupo. Ele usa, de proposito, tudo o que a linguagem
// tem: recursao direta e mutua, laco, os quatro tipos, as duas formas de
// divisao e a concatenacao de texto.

/* Monta uma linha de estrelas por recursao, sem laco e sem vetor:
   so chamada de funcao e concatenacao de texto. */
funcao texto estrelas(inteiro quantas) {
  se (quantas <= 0) {
    retorne "";
  } senao {
    retorne "*" + estrelas(quantas - 1);
  }
}

funcao vazio titulo(texto nome) {
  escreva("");
  escreva(nome);
  escreva(estrelas(22));
}

funcao inteiro fatorial(inteiro n) {
  se (n <= 1) {
    retorne 1;
  } senao {
    retorne n * fatorial(n - 1);
  }
}

// Recursao mutua: cada uma chama a outra, e ehImpar aparece no arquivo depois
// de ja ter sido usada. So funciona porque a analise semantica coleta todas as
// assinaturas numa passada separada, antes de olhar qualquer corpo.
funcao logico ehPar(inteiro n) {
  se (n == 0) {
    retorne verdadeiro;
  } senao {
    retorne ehImpar(n - 1);
  }
}

funcao logico ehImpar(inteiro n) {
  se (n == 0) {
    retorne falso;
  } senao {
    retorne ehPar(n - 1);
  }
}

funcao logico primo(inteiro n) {
  se (n < 2) {
    retorne falso;
  }
  inteiro divisor = 2;
  enquanto (divisor * divisor <= n) {
    se (n % divisor == 0) {
      retorne falso;
    }
    divisor = divisor + 1;
  }
  retorne verdadeiro;
}

funcao vazio piramide(inteiro altura) {
  inteiro linha = 1;
  enquanto (linha <= altura) {
    escreva(estrelas(linha));
    linha = linha + 1;
  }
}

funcao vazio fatoriais(inteiro ate) {
  inteiro n = 1;
  enquanto (n <= ate) {
    escreva(fatorial(n));
    n = n + 1;
  }
}

funcao vazio primosAte(inteiro limite) {
  inteiro n = 2;
  enquanto (n <= limite) {
    se (primo(n)) {
      escreva(n);
    }
    n = n + 1;
  }
}

funcao vazio paridade(inteiro ate) {
  inteiro n = 0;
  enquanto (n <= ate) {
    escreva(ehPar(n));
    n = n + 1;
  }
}

funcao vazio principal() {
  escreva("RELATORIO DE NUMEROS");
  escreva(estrelas(22));

  titulo("piramide");
  piramide(6);

  titulo("fatoriais de 1 a 8");
  fatoriais(8);

  titulo("primos ate 30");
  primosAte(30);

  titulo("par? de 0 a 5");
  paridade(5);

  titulo("as duas divisoes");
  // A divisao acontece ANTES da conversao: 7 / 2 da 3, e so depois vira
  // 3.000000. A linha seguinte forca real de um lado e da 3.500000.
  real inteiraDepoisConvertida = 7 / 2;
  real realDeVerdade = 7.0 / 2;
  escreva(inteiraDepoisConvertida);
  escreva(realDeVerdade);

  titulo("o resto segue o dividendo");
  escreva(-7 % 3);
  escreva(7 % -3);

  titulo("texto com escapes");
  escreva("tabulado:\tassim");
  escreva("aspas: \"citado\"");
  escreva("barra: \\");
}
