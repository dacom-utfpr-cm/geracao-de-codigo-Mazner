# Compilador para a linguagem Tpp

## Descrição

O código contido nesse repositório se diz respeito a um compilador feito para a linguagem Tpp, onde existem 4 funções principais para executar o processo
de compilação, sendo elas:

- Análise léxica (tpplex.py);
- Análise sintática (tppparser.py);
- Análise semântica (tppsema.py);
- Geração de código (tppgencode.py).

## Funcionalidades

O código será capaz de gerar código para a llvm, podendo ser então compilado e executado de uma linguagem tpp para linguagem executável

## Pré-requisitos

- Biblioteca Ply e yacc;
- Anytree;
- Llvmlite.

## Instalação

- Instale as dependências com o pip install ply, pip install anytree e pip install llvlite (é recomendável criar um ambiente virtual python);

- Clone o repositório em sua máquina e execute.

## Uso

Para executar o projeto, basta executar o seguinte comando no terminal:
python main.py tests/<nome_do_arquivo_de_teste>
