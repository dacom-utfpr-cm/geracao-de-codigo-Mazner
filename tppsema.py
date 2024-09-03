# Autor: Marcos Bezner Rampaso
# Entrega 3 - Implementação de Linguagens de Programação
# Data: 29/08/2024
# Descrição: Analisador Semântico para a linguagem T++.
#            Verifica regras semânticas do código, como declaração de variáveis, funções, uso de variáveis e funções, etc.
#            Realiza a poda da árvore sintática para simplificar a análise semântica.
#            Gera a tabela de símbolos a partir da árvore sintática.
#            Gera avisos e erros de acordo com as regras semânticas da linguagem.
#            Realiza a análise semântica do código e a poda da árvore sintática.

import sys
import os
from sys import argv, exit
import logging
import ply.yacc as yacc

from anytree import NodeMixin
from anytree.exporter import UniqueDotExporter
from anytree import RenderTree, findall_by_attr
from myerror import MyError

# Configuração do logger para registrar mensagens de depuração
logging.basicConfig(
    level=logging.DEBUG,
    filename="sema.log",
    filemode="w",
    format="%(filename)10s:%(lineno)4d:%(message)s"
)
log = logging.getLogger()

# Inicialização do analisador de erros
error_handler = MyError('SemaErrors')

# Raiz da árvore sintática
root = None

# Tabela de erros de variáveis
variablesError = []

# Adiciona uma variável com erro na tabela de erros
def adicionaErroVariavel(nome, escopo):
    variablesError.append({
        'name': nome,
        'escopo': escopo
    })

# Verifica se uma variável já tem um erro associado em um escopo específico
def variavelComErro(nome, escopo):
    for variavel in variablesError:
        if variavel['name'] == nome and variavel['escopo'] == escopo:
            return True
    return False

# Gera a tabela de símbolos a partir da árvore sintática
# Tal tabela foi criada a partir do slide do professor Rogério Gonçalves
# descrita no relatório anexado à este programa
def tabelaDeSimbolos():
    resultados = findall_by_attr(root, "declaracao")
    variaveis = []
    for p in resultados:
        item = [noh for pre, fill, noh in RenderTree(p)]
        if item[1].name == "declaracao_variaveis":
            variavel = processaVariavel(primeiroNo=item[1], escopo="global")
            if declaracaoVariavel(tabelaSimbolica=variaveis, name=variavel['name'], escopo='global'):
                tipoVariavel = buscaTipo(tabelaSimbolica=variaveis, name=variavel['name'], escopo='global')
                print(error_handler.newError(False, 'WAR-SEM-VAR-DECL-PREV').format(variavel['name'], tipoVariavel))
            else:
                variaveis.append(variavel)
        elif item[1].name == "declaracao_funcao":
            if item[2].name == "tipo":
                name = item[7].name
                token = item[6].name
                type = item[4].name
                line = item[4].line
            else:
                name = item[4].name
                token = item[3].name
                type = 'vazio'
                line = item[4].line

            variavel = {
                "tipoDeclaracao": 'func',
                "type": type,
                "line": line,
                "usado": "S" if name == "principal" else "N",
                "dimensao": 0,
                "tamanhoDimensao1": 1,
                "token": token,
                "name": name,
                "escopo": "global",
                "tamanhoDimensao2": 0,
                "parametros": declaracaoParams(item)
            }
            if declaracaoVariavel(tabelaSimbolica=variaveis, name=name, escopo='global'):
                tipoVariavel = buscaTipo(tabelaSimbolica=variaveis, name=name, escopo='global')
                print(error_handler.newError(False, 'WAR-SEM-FUNC-DECL-PREV').format(name, tipoVariavel))
            else:
                variaveis.append(variavel)
                declaracaoFunc(primeiroNo=item[1], escopo=name, tabelaSimbolica=variaveis)
    return variaveis

# Processa a declaração de uma variável, determinando suas propriedades
def processaVariavel(primeiroNo, escopo):
    # Inicializa variáveis para armazenar as dimensões
    unidimensional = 1
    bidimensional = 0
    dimensao = 0
    
    # Cria uma lista com todos os nós da árvore
    renderNodeTree = [noh for pre, fill, noh in RenderTree(primeiroNo)]
    
    # Inicializa variáveis para armazenar propriedades da variável
    tipo = None
    line = None
    token = None
    name = None

    for i, node in enumerate(renderNodeTree):
        if node.name == 'tipo':
            tipo = renderNodeTree[i + 2].name
            line = renderNodeTree[i + 2].line
        elif node.name == 'ID':
            token = node.name
            name = renderNodeTree[i + 1].name
        elif node.name == 'fecha_colchete':
            dimensao += 1
            
            # Verifica se o índice é um número ponto flutuante
            if renderNodeTree[i - 2].name == 'NUM_PONTO_FLUTUANTE':
                if not variavelComErro(name, escopo):
                    adicionaErroVariavel(name, escopo)
                    print(error_handler.newError(False, 'ERR-SEM-ARRAY-INDEX-NOT-INT').format(name))
            
            indice = renderNodeTree[i - 1].name
            if dimensao == 2:
                bidimensional = indice
            else:
                unidimensional = indice

    # Cria e retorna o dicionário com as propriedades da variável
    variavel = {
        'tipoDeclaracao': 'var',
        'type': tipo,
        'line': line,
        'token': token,
        'name': name,
        'escopo': escopo,
        'init': 'N',
        'usado': 'N',
        'dimensao': dimensao,
        'tamanhoDimensao1': unidimensional,
        'tamanhoDimensao2': bidimensional,
        'errors': 0
    }

    return variavel

# Processa a declaração de variáveis dentro do escopo de uma função
def declaracaoFunc(primeiroNo, escopo, tabelaSimbolica):
    variaveisDeclaradas = findall_by_attr(primeiroNo, "declaracao_variaveis")
    
    for variavelNoh in variaveisDeclaradas:
        variavel = processaVariavel(primeiroNo=variavelNoh, escopo=escopo)
        
        if declaracaoVariavel(tabelaSimbolica=tabelaSimbolica, name=variavel['name'], escopo=escopo):
            tipoVariavel = buscaTipo(tabelaSimbolica=tabelaSimbolica, name=variavel['name'], escopo=escopo)
            print(error_handler.newError(False, 'WAR-SEM-VAR-DECL-PREV').format(variavel['name'], tipoVariavel))
        else:
            tabelaSimbolica.append(variavel)
            

# Verifica se uma variável está declarada na tabela de símbolos dentro de um escopo específico
def declaracaoVariavel(tabelaSimbolica, name, escopo):
    for entry in tabelaSimbolica:
        # Verifica se a variável está no escopo global ou no escopo especificado
        if entry['name'] == name and (entry['escopo'] == 'global' or entry['escopo'] == escopo):
            return True
        # Verifica se a variável é um parâmetro de função no escopo especificado
        elif escopo != 'global' and entry['tipoDeclaracao'] == 'func':
            for param in entry['parametros']:
                if param['name'] == name:
                    return True
    return False

# Verifica se a função principal ("principal") existe na tabela de símbolos
def existeMain(tabelaSimbolica):
    for entry in tabelaSimbolica:
        if entry['tipoDeclaracao'] == 'func' and entry['name'] == 'principal':
            return True
    return False



# Obtém o escopo de uma função a partir de um nó na árvore sintática
def buscaEscopo(noh):
    for ancestor in noh.ancestors:
        if ancestor.name == 'cabecalho' and ancestor.children[0].name == 'ID':
            return ancestor.children[0].children[0].name
    return 'global'

# Verifica se um valor está sendo usado como índice em uma expressão
def verificaIndice(noh):
    return any(ancestor.name == 'indice' for ancestor in noh.ancestors)

# Retorna o tipo de uma variável ou parâmetro de acordo com a tabela de símbolos
def buscaTipo(tabelaSimbolica, name, escopo):
    for entry in tabelaSimbolica:
        # Verifica se a variável está no escopo global ou no escopo especificado
        if entry['name'] == name and (entry['escopo'] == 'global' or entry['escopo'] == escopo):
            return entry['type']
        
        # Verifica se a variável é um parâmetro de função no escopo especificado
        if entry['tipoDeclaracao'] == 'func' and escopo != 'global':
            for param in entry['parametros']:
                if param['name'] == name:
                    return param['type']
                    
    return None

# Verifica se todos os fatores de uma expressão são do mesmo tipo; caso contrário, retorna o tipo predominante
def buscaTipoFator(fatores, type):
    tipoFator = type
    for factor in fatores:
        if factor['type'] != type:
            tipoFator = factor['type']
    return tipoFator

# Gera a lista de parâmetros de uma função a partir da árvore sintática
def declaracaoParams(primeiroNo):
    parametros = []
    for item in primeiroNo:
        if item.name == 'cabecalho':
            # Obtém a lista de parâmetros
            listaParametros = findall_by_attr(item.children[2], "parametro")
            for parametro in listaParametros:
                # Extrai o tipo e o nome do parâmetro
                tipo = parametro.children[0].children[0].children[0].name
                nome = parametro.children[2].children[0].name
                parametros.append({
                    'type': tipo,
                    'name': nome
                })
    return parametros

# Verifica se um valor está sendo usado como argumento em uma função
def verificaArgumento(noh):
    # Obtém todos os ancestrais do nó
    ancestrais = list(noh.ancestors)
    
    # Verifica se algum dos ancestrais é uma lista de argumentos
    for ancestral in ancestrais:
        if ancestral.name == 'lista_argumentos':
            return True
    
    return False

# Obtém os fatores (variáveis, números ou funções) de uma expressão
def buscaFator(primeiroNo, escopo, tabelaSimbolica):
    fatores = []
    
    # Encontra todos os nós do tipo "fator"
    resultados = findall_by_attr(primeiroNo, "fator")
    
    for fator in resultados:
        # Verifica se o fator não é um índice ou argumento de função
        if not verificaIndice(fator) and not verificaArgumento(fator):
            # Obtém o tipo de fator e ajusta se for uma chamada de função
            tipoFator = fator.children[0].name
            tipoFator = 'func' if tipoFator == 'chamada_funcao' else tipoFator
            
            # Obtém o valor e o tipo do fator
            valor = fator.children[0].children[0].children[0].name
            tipo = fator.children[0].children[0].name
            
            # Define o escopo atual
            escopoAtual = 'global' if tipoFator == 'func' else escopo
            
            # Determina o tipo do fator
            if tipoFator == 'numero':
                tipo = 'inteiro' if tipo == 'NUM_INTEIRO' else 'flutuante'
            else:
                tipo = buscaTipo(tabelaSimbolica, valor, escopoAtual)
            
            if tipo is not None:
                fatores.append({
                    'factor': tipoFator,
                    'type': tipo,
                    'value': valor
                })
    
    return fatores


# Conta o número de parâmetros em uma lista de argumentos
def contagemParametros(noh):
    i = 1
    item = noh
    while item.name == 'lista_argumentos':
        if item.name == 'lista_argumentos' and len(item.children) > 1 and item.children[1].name == 'VIRGULA':
            i += 1
        item = item.children[0]
    return i

# Verifica coerções de tipos em atribuições e operações, emitindo avisos se necessário
def verificarCoercao(tabelaSimbolica, name, escopo, noh):
    type = None
    fatores = buscaFator(noh, escopo, tabelaSimbolica)
    for i in range(len(tabelaSimbolica)):
        type = None
        try:
            parametros = tabelaSimbolica[i]['parametros']
        except KeyError:
            parametros = None

        # Verifica o tipo da variável ou parâmetro na tabela de símbolos
        if tabelaSimbolica[i]['name'] == name and (tabelaSimbolica[i]['escopo'] == 'global' or tabelaSimbolica[i]['escopo'] == escopo):
            type = tabelaSimbolica[i]['type']
        elif parametros is not None and len(parametros) > 0:
            for parametro in parametros:
                if parametro['name'] == name:
                    type = parametro['type']
        
        if type is not None:
            # Se a expressão contém um único fator, verifica se o tipo precisa de coerção
            if len(fatores) == 1:
                tipoFator = fatores[0]['type']
                if tipoFator != type:
                    valorFator = fatores[0]['value']
                    fator = fatores[0]['factor']
                    if fator == 'var':
                        print(error_handler.newError(False, 'WAR-SEM-ATR-DIFF-TYPES-IMP-COERC-OF-VAR').format(valorFator, tipoFator, name, type))
                    elif fator == 'func':
                        print(error_handler.newError(False, 'WAR-SEM-ATR-DIFF-TYPES-IMP-COERC-OF-RET-VAL').format(valorFator, tipoFator, name, type))
                    else:
                        print(error_handler.newError(False, 'WAR-SEM-ATR-DIFF-TYPES-IMP-COERC-OF-NUM').format(valorFator, tipoFator, name, type))
            else:
                # Se a expressão contém múltiplos fatores, determina o tipo predominante
                tipoFator = buscaTipoFator(fatores, type)
                if tipoFator != type:
                    valorFator = 'expressao'
                    print(error_handler.newError(False, 'WAR-SEM-ATR-DIFF-TYPES-IMP-COERC-OF-EXP').format(valorFator, tipoFator, name, type))

# Inicializa a variável na tabela de símbolos e verifica coerção de tipos
def inicializarVariavel(tabelaSimbolica, name, escopo, noh):
    if declaracaoVariavel(tabelaSimbolica=tabelaSimbolica, name=name, escopo=escopo):
        verificarCoercao(tabelaSimbolica=tabelaSimbolica, name=name, escopo=escopo, noh=noh)
        for i in range(len(tabelaSimbolica)):
            if tabelaSimbolica[i]['name'] == name and (tabelaSimbolica[i]['escopo'] == 'global' or tabelaSimbolica[i]['escopo'] == escopo):
                tabelaSimbolica[i]['init'] = 'Y'  # Marca a variável como inicializada
    else:
        # Se a variável não está declarada, verifica se não é uma chamada de função antes de reportar erro
        resultados = findall_by_attr(noh, 'chamada_funcao')
        if not resultados and not variavelComErro(name, escopo):
            adicionaErroVariavel(name, escopo)
            print(error_handler.newError(False, 'ERR-SEM-VAR-NOT-DECL').format(name))

# Marca a variável como usada na tabela de símbolos
def variavelUsada(tabelaSimbolica, name, escopo, noh):
    if declaracaoVariavel(tabelaSimbolica=tabelaSimbolica, name=name, escopo=escopo):
        for i in range(len(tabelaSimbolica)):
            if tabelaSimbolica[i]['name'] == name and (tabelaSimbolica[i]['escopo'] == 'global' or tabelaSimbolica[i]['escopo'] == escopo):
                tabelaSimbolica[i]['usado'] = 'Y'  # Marca a variável como usada
    else:
        # Se a variável não está declarada, verifica se não é uma chamada de função antes de reportar erro
        resultados = findall_by_attr(noh, 'chamada_funcao')
        if not resultados and not variavelComErro(name, escopo):
            adicionaErroVariavel(name, escopo)
            print(error_handler.newError(False, 'ERR-SEM-VAR-NOT-DECL').format(name))

# Verifica todas as variáveis em uso no código, identificando e inicializando ou marcando-as como usadas
def verificarVariavel(tabelaSimbolica):
    resultados = findall_by_attr(root, "acao")
    for p in resultados:
        renderNodeTree = [noh for pre, fill, noh in RenderTree(p)]
        for primeiroNo in renderNodeTree:
            renderNode1Tree = [noh for pre, fill, noh in RenderTree(primeiroNo)]
            if primeiroNo.name == 'expressao':
                if renderNode1Tree[1].name == 'atribuicao':
                    escopo = buscaEscopo(primeiroNo)
                    name = renderNode1Tree[4].name
                    inicializarVariavel(tabelaSimbolica=tabelaSimbolica, name=name, escopo=escopo, noh=primeiroNo)
                else:
                    for indice in range(len(renderNode1Tree)):
                        if renderNode1Tree[indice].name == 'ID':
                            escopo = buscaEscopo(primeiroNo)
                            name = renderNode1Tree[indice+1].name
                            variavelUsada(tabelaSimbolica=tabelaSimbolica, name=name, escopo=escopo, noh=primeiroNo)
            elif primeiroNo.name == 'leia':
                for indice in range(len(renderNode1Tree)):
                    if renderNode1Tree[indice].name == 'ID':
                        escopo = buscaEscopo(primeiroNo)
                        name = renderNode1Tree[indice+1].name
                        inicializarVariavel(tabelaSimbolica=tabelaSimbolica, name=name, escopo=escopo, noh=primeiroNo)
            elif primeiroNo.name in ['se', 'repita', 'escreva', 'retorna']:
                for indice in range(len(renderNode1Tree)):
                    if renderNode1Tree[indice].name == 'ID':
                        escopo = buscaEscopo(primeiroNo)
                        name = renderNode1Tree[indice+1].name
                        variavelUsada(tabelaSimbolica=tabelaSimbolica, name=name, escopo=escopo, noh=primeiroNo)
            elif primeiroNo.name == 'chamada_funcao':
                escopo = buscaEscopo(primeiroNo)
                name = primeiroNo.children[0].children[0].name
                variavelUsada(tabelaSimbolica=tabelaSimbolica, name=name, escopo=escopo, noh=primeiroNo)

# Verifica se as variáveis declaradas estão em uso, e se foram inicializadas corretamente
def variavelEmUso(tabelaSimbolica):
    for i in range(len(tabelaSimbolica)):
        name = tabelaSimbolica[i]['name']
        escopo = tabelaSimbolica[i]['escopo']
        if tabelaSimbolica[i]['tipoDeclaracao'] == 'var' and tabelaSimbolica[i]['errors'] <= 0 and not variavelComErro(name, escopo):
            if tabelaSimbolica[i]['init'] == 'N' and tabelaSimbolica[i]['usado'] == 'N':
                print(error_handler.newError(False, 'WAR-SEM-VAR-DECL-NOT-USED').format(name))
            elif tabelaSimbolica[i]['init'] == 'Y' and tabelaSimbolica[i]['usado'] == 'N':
                print(error_handler.newError(False, 'WAR-SEM-VAR-DECL-INIT-NOT-USED').format(name))
            elif tabelaSimbolica[i]['init'] == 'N':
                print(error_handler.newError(False, 'WAR-SEM-VAR-DECL-NOT-INIT').format(name))

# Verifica se as funções têm o retorno adequado ao seu tipo declarado
def buscaRetornoFuncao(tabelaSimbolica):
    resultados = findall_by_attr(root, 'declaracao_funcao')
    for p in resultados:
        renderNodeTree = [noh for pre, fill, noh in RenderTree(p)]
        for primeiroNo in renderNodeTree:
            if primeiroNo.name == 'cabecalho':
                renderNode1Tree = [noh for pre, fill, noh in RenderTree(primeiroNo)]
                returns = findall_by_attr(primeiroNo, 'retorna')
                funcName = renderNode1Tree[2].name
                if not returns:
                    for i in range(len(tabelaSimbolica)):
                        if tabelaSimbolica[i]['name'] == funcName and tabelaSimbolica[i]['tipoDeclaracao'] == 'func' and tabelaSimbolica[i]['type'] != 'vazio':
                            print(error_handler.newError(False, 'ERR-SEM-FUNC-RET-TYPE-ERROR').format(funcName, tabelaSimbolica[i]['type'], 'vazio'))
                else:
                    for return1 in returns:
                        if return1.children:
                            expression = return1.children[2]
                            if expression.name == 'expressao':
                                escopo = buscaEscopo(return1)
                                fatores = buscaFator(expression, escopo, tabelaSimbolica)
                                for i in range(len(tabelaSimbolica)):
                                    if tabelaSimbolica[i]['name'] == funcName and tabelaSimbolica[i]['tipoDeclaracao'] == 'func':
                                        type = tabelaSimbolica[i]['type']
                                        tipoFator = buscaTipoFator(fatores, type)
                                        if tipoFator != type:
                                            print(error_handler.newError(False, 'ERR-SEM-FUNC-RET-TYPE-ERROR').format(funcName, type, tipoFator))

# Verifica se as funções são chamadas corretamente e se os argumentos correspondem aos parâmetros
def verificaChamada(tabelaSimbolica):
    resultados = findall_by_attr(root, 'chamada_funcao')
    for p in resultados:
        renderNodeTree = [noh for pre, fill, noh in RenderTree(p)]
        name = renderNodeTree[2].name
        if declaracaoVariavel(tabelaSimbolica=tabelaSimbolica, name=name, escopo='global'):
            escopoCall = buscaEscopo(p)
            if name == 'principal':
                if escopoCall == 'principal':
                    print(error_handler.newError(False, 'WAR-SEM-CALL-REC-FUNC-MAIN').format(name))
                print(error_handler.newError(False, 'ERR-SEM-CALL-FUNC-MAIN-NOT-ALLOWED'))
            else:
                primeiroNo = renderNodeTree[5]
                if primeiroNo.name == 'lista_argumentos':
                    if primeiroNo.children[0].name != 'vazio':
                        numberArguments = contagemParametros(primeiroNo)
                        for i in range(len(tabelaSimbolica)):
                            if tabelaSimbolica[i]['name'] == name and tabelaSimbolica[i]['tipoDeclaracao'] == 'func':
                                parametros = tabelaSimbolica[i]['parametros']
                                if numberArguments < len(parametros):
                                    print(error_handler.newError(False, 'ERR-SEM-CALL-FUNC-WITH-FEW-ARGS').format(name))
                                elif numberArguments > len(parametros):
                                    print(error_handler.newError(False, 'ERR-SEM-CALL-FUNC-WITH-MANY-ARGS').format(name))
        else:
            print(error_handler.newError(False, 'ERR-SEM-CALL-FUNC-NOT-DECL').format(name))

# Verifica se as funções declaradas foram usadas em algum ponto do código
def verificaUsoFuncao(tabelaSimbolica):
    for i in range(len(tabelaSimbolica)):
        if tabelaSimbolica[i]['tipoDeclaracao'] == 'func':
            name = tabelaSimbolica[i]['name']
            if tabelaSimbolica[i]['usado'] == 'N':
                print(error_handler.newError(False, 'WAR-SEM-FUNC-DECL-NOT-USED').format(name))

# Realiza as verificações de retorno, chamada e uso de funções
def verificarFuncoes(tabelaSimbolica):
    buscaRetornoFuncao(tabelaSimbolica)
    verificaChamada(tabelaSimbolica)
    verificaUsoFuncao(tabelaSimbolica)

# Função principal para verificar as regras semânticas do código
def checkRules():
    tabelaSimbolica = tabelaDeSimbolos()
    if not existeMain(tabelaSimbolica):
        print(error_handler.newError(False, 'ERR-SEM-MAIN-NOT-DECL'))
    verificarVariavel(tabelaSimbolica)
    variavelEmUso(tabelaSimbolica)
    verificarFuncoes(tabelaSimbolica)

# Lista de tokens relevantes para a poda
string_tokens = [
    'ID',
    'ABRE_PARENTESE',
    'FECHA_PARENTESE',
    'FIM',
    'abre_colchete',
    'fecha_colchete'
]

# Função principal para podar a lista de declarações
def podaDeclaracoes(tree):
    item = tree.children[0]
    descritorArvore = ()
    
    # Navega pela lista de declarações, acumulando nós relevantes
    while item.name == 'lista_declaracoes':
        if item.name == 'lista_declaracoes':
            if len(item.children) == 1:
                noh = item.children[0]
            else:
                noh = item.children[1]
            descritorArvore = noh.children + descritorArvore
        item = item.children[0]
    
    # Realiza a poda em cada tipo de declaração
    for i in descritorArvore:
        if i.name == 'declaracao_funcao':
            PodaDeclaracaoFuncao(i)
        elif i.name == 'declaracao_variaveis':
            podaDeclaracaoVariavel(i)
        else:
            podaInicilizacaoVariavel(i)
    
    # Atualiza os filhos da árvore com as declarações podadas
    tree.children[0].children = descritorArvore

# Função para podar a declaração de função
def PodaDeclaracaoFuncao(tree):
    descritorArvore = ()
    
    # Caso a função tenha apenas um nó filho
    if len(tree.children) == 1:
        descritorArvore += tree.children[0].children
    else:
        descritorArvore += tree.children[0].children[0].children
        # Processa os filhos da função
        for child in tree.children[1].children:
            if child.name in string_tokens:
                descritorArvore += child.children
            elif child.name == 'corpo':
                descritorArvore += (podaCorpo(child),)
            elif child.name == 'listaParametros':
                item = child
                elementosPoda = ()
                # Poda da lista de parâmetros
                while item.name == 'listaParametros':
                    if item.children[0].name == 'vazio':
                        variavelAuxiliar = item.children[0]
                        elementosPoda = (variavelAuxiliar,) + elementosPoda
                    elif len(item.children) == 1:
                        elementosPoda = (podaParametros(item.children[0]),) + elementosPoda
                    else:
                        elementosPoda = (podaParametros(item.children[2]),) + elementosPoda
                    item = item.children[0]
                child.children = elementosPoda
                descritorArvore += (child,)
            else:
                descritorArvore += (child,)
    
    # Atualiza os filhos da árvore com a função podada
    tree.children = descritorArvore

# Função para podar a declaração de variáveis
def podaDeclaracaoVariavel(tree):
    descritorArvore = ()
    
    # Adiciona o tipo da variável e sua inicialização
    descritorArvore += tree.children[0].children[0].children
    descritorArvore += tree.children[1].children

    # Processa a lista de variáveis
    elementosPoda = ()
    item = tree.children[2]
    while item.name == 'lista_variaveis':
        if item.name == 'lista_variaveis':
            if len(item.children) == 1:
                elementosPoda = (podaVariavel(item.children[0]),) + elementosPoda
            else:
                elementosPoda = (podaVariavel(item.children[2]),) + elementosPoda
        item = item.children[0]
    
    # Atualiza a lista de variáveis podada
    tree.children[2].children = elementosPoda
    descritorArvore += (tree.children[2],)
    
    # Retorna a declaração de variável podada
    tree.children = descritorArvore
    return tree

# Função para podar a inicialização de variáveis
def podaInicilizacaoVariavel(tree):
    podaInicializacao(tree.children[0])

def podaInicializacao(tree):
    descritorArvore = ()
    descritorArvore += (podaVariavel(tree.children[0]),)
    descritorArvore += (tree.children[1].children[0],)
    
    # Poda da expressão de inicialização
    tree.children[2].children = podaExpressao(tree.children[2])
    descritorArvore += (tree.children[2],)
    
    # Atualiza a árvore com a inicialização podada
    tree.children = descritorArvore
    return tree

def podaExpressao(tree):
    variavelAuxiliar = tree.children
    name = tree.name
    
    # Condensa a expressão em uma forma mais simples
    while len(variavelAuxiliar) == 1 and name != 'expressao_unaria':
        name = variavelAuxiliar[0].name
        variavelAuxiliar = variavelAuxiliar[0].children
    
    descritorArvore = ()
    
    # Verifica se a expressão é unária
    if variavelAuxiliar[0].parent.name == 'expressao_unaria':
        if len(variavelAuxiliar) == 1:
            if variavelAuxiliar[0].children[0].name == 'chamada_funcao':
                descritorArvore += (podaChamadaFuncao(variavelAuxiliar[0].children[0]),)
            elif variavelAuxiliar[0].children[0].name == 'var':
                descritorArvore += (podaVariavel(variavelAuxiliar[0].children[0]),)
            elif variavelAuxiliar[0].children[0].name == 'numero':
                descritorArvore += variavelAuxiliar[0].children[0].children
            else:
                descritorArvore += variavelAuxiliar[0].children[0].children
                descritorArvore += podaExpressao(variavelAuxiliar[0].children[1])
                descritorArvore += variavelAuxiliar[0].children[2].children
        else:
            descritorArvore += variavelAuxiliar[0].children[0].children
            descritorArvore += variavelAuxiliar[1].children[0].children
        variavelAuxiliar = descritorArvore
    else:
        descritorArvore += podaExpressao(variavelAuxiliar[0])
        descritorArvore += (variavelAuxiliar[1].children[0].children[0],)
        descritorArvore += podaExpressao(variavelAuxiliar[2])
        variavelAuxiliar = descritorArvore
    
    # Retorna a expressão podada
    return variavelAuxiliar

# Função para podar uma variável
def podaVariavel(tree):
    variavelAuxiliar = tree
    descritorArvore = ()
    
    # Adiciona o primeiro filho da árvore à variável 'descritorArvore'
    descritorArvore += (variavelAuxiliar.children[0].children[0],)
    
    # Verifica se a variável é um array (possui colchetes)
    if len(variavelAuxiliar.children) > 1:
        variavelAuxiliar1 = variavelAuxiliar.children[1].children
        elementosPoda = ()
        
        if len(variavelAuxiliar1) == 4:
            # Poda o array com dois colchetes
            elementosPoda += (variavelAuxiliar1[0].children[0].children[0],)
            variavelAuxiliar1[0].children[1].children = podaExpressao(variavelAuxiliar1[0].children[1])
            elementosPoda += (variavelAuxiliar1[0].children[1],)
            elementosPoda += (variavelAuxiliar1[0].children[2].children[0],)
            elementosPoda += variavelAuxiliar1[1].children
            variavelAuxiliar1[2].children = podaExpressao(variavelAuxiliar1[2])
            elementosPoda += (variavelAuxiliar1[2],)
            elementosPoda += variavelAuxiliar1[3].children
        else:
            # Poda o array com um colchete
            elementosPoda += variavelAuxiliar1[0].children
            variavelAuxiliar1[1].children = podaExpressao(variavelAuxiliar1[1])
            elementosPoda += (variavelAuxiliar1[1],)
            elementosPoda += variavelAuxiliar1[2].children
        
        # Atualiza os filhos da variável com a expressão podada
        variavelAuxiliar.children[1].children = elementosPoda
    
    # Atualiza a árvore com a variável podada
    tree.children = descritorArvore
    return tree

def podaChamadaFuncao(tree):
    descritorArvore = ()
    
    # Processa a chamada de função com base nos filhos
    if len(tree.children) == 1:
        descritorArvore += tree.children[0].children
    else:
        descritorArvore += tree.children[0].children[0].children
        for child in tree.children:
            if child.name in string_tokens:
                descritorArvore += child.children
            elif child.name == 'lista_argumentos':
                item = child
                elementosPoda = ()
                # Poda da lista de argumentos
                while item.name == 'lista_argumentos':
                    if item.children[0].name == 'vazio':
                        variavelAuxiliar = item.children[0]
                        elementosPoda = (variavelAuxiliar,) + elementosPoda
                    elif len(item.children) == 1:
                        variavelAuxiliar = item.children[0]
                        variavelAuxiliar.children = podaExpressao(item.children[0])
                        elementosPoda = (variavelAuxiliar,) + elementosPoda
                    else:
                        variavelAuxiliar = item.children[2]
                        variavelAuxiliar.children = podaExpressao(item.children[2])
                        elementosPoda = (variavelAuxiliar,) + elementosPoda
                    item = item.children[0]
                child.children = elementosPoda
                descritorArvore += (child,)
            else:
                descritorArvore += (child,)
    
    # Retorna a chamada de função podada
    tree.children = descritorArvore
    return tree

# Função variavelAuxiliariliar para podar a lista de argumentos
def podaListaArgumentos(node):
    elementosPoda = []
    item = node
    
    while item.name == 'lista_argumentos':
        if item.children[0].name == 'vazio':
            variavelAuxiliar = item.children[0]
            elementosPoda.append(variavelAuxiliar)
        elif len(item.children) == 1:
            variavelAuxiliar = item.children[0]
            variavelAuxiliar.children = podaExpressao(item.children[0])
            elementosPoda.append(variavelAuxiliar)
        else:
            variavelAuxiliar = item.children[2]
            variavelAuxiliar.children = podaExpressao(item.children[2])
            elementosPoda.append(variavelAuxiliar)
        item = item.children[0]
    
    return [node for node in elementosPoda if isinstance(node, NodeMixin)]

# Função para podar a lista de parâmetros de uma função
def podaParametros(tree):
    descritorArvore = ()
    item = tree
    
    # Itera sobre os parâmetros e os condensa
    while item.name == 'parametro':
        if item.children[0].name == 'parametro':
            descritorArvore = item.children[2].children + descritorArvore
            descritorArvore = item.children[1].children + descritorArvore
        else:
            descritorArvore = item.children[2].children + descritorArvore
            descritorArvore = item.children[1].children + descritorArvore
            descritorArvore = item.children[0].children[0].children + descritorArvore
        item = item.children[0]
    
    # Atualiza a árvore com os parâmetros podados
    tree.children = descritorArvore
    return tree

# Função para podar as funções de entrada e saída (leia, escreva, retorna)
def podaFuncoesEntradaSaida(tree):
    descritorArvore = ()
    
    # Adiciona o token inicial e a expressão/variável correspondente
    descritorArvore += tree.children[0].children
    descritorArvore += tree.children[1].children
    
    # Verifica se é a função 'leia'
    if tree.name == 'leia':
        descritorArvore += (podaVariavel(tree.children[2]),)
    else:
        tree.children[2].children = podaExpressao(tree.children[2])
        descritorArvore += (tree.children[2],)
    
    # Adiciona o token final
    descritorArvore += tree.children[3].children
    
    # Atualiza a árvore com a função podada
    tree.children = descritorArvore
    return tree

# Função para podar a estrutura de controle 'se'
def podaSe(tree):
    descritorArvore = ()
    
    # Adiciona o token 'SE' e a expressão condicional
    descritorArvore += tree.children[0].children
    tree.children[1].children = podaExpressao(tree.children[1])
    descritorArvore += (tree.children[1],)
    
    # Adiciona o token 'ENTAO' e o corpo correspondente
    descritorArvore += tree.children[2].children
    descritorArvore += (podaCorpo(tree.children[3]),)
    
    # Verifica se há um bloco 'SENAO'
    if len(tree.children) == 5:
        descritorArvore += (tree.children[4],) # Adiciona 'FIM'
    else:
        descritorArvore += (tree.children[4],) # Adiciona 'SENAO'
        descritorArvore += (podaCorpo(tree.children[5]),) # Adiciona corpo do 'SENAO'
        descritorArvore += (tree.children[6],) # Adiciona 'FIM'
    
    # Atualiza a árvore com a estrutura 'se' podada
    tree.children = descritorArvore
    return tree

# Função para podar a estrutura de repetição 'repita'
def podaRepita(tree):
    descritorArvore = ()
    
    # Adiciona o token 'REPITA' e o corpo correspondente
    descritorArvore += tree.children[0].children
    
    # Poda o corpo da estrutura de repetição
    corpo = podaCorpo(tree.children[1])
    descritorArvore += (corpo,)
    
    # Adiciona o token 'ATE' e a expressão condicional
    descritorArvore += tree.children[2].children
    
    # Poda a expressão condicional
    expressao = podaExpressao(tree.children[3])
    tree.children[3].children = expressao
    descritorArvore += (tree.children[3],)
    
    # Atualiza a árvore com a estrutura 'repita' podada
    tree.children = descritorArvore
    return tree
# Função para podar o corpo das funções e estruturas
def podaCorpo(tree):
    descritorArvore = ()
    item = tree
    
    # Itera sobre o corpo da função/estrutura
    while item == 'corpo':
        if len(item.children) == 2:
            action = item.children[1].children[0]
            
            # Identifica o tipo de ação e realiza a poda correspondente
            if action.name == 'expressao':
                if len(action.children) > 0 and action.children[0].name == 'atribuicao':
                    descritorArvore = (podaInicializacao(action.children[0]),) + descritorArvore
                else:
                    action.children = podaExpressao(action)
                    descritorArvore = (action,) + descritorArvore
            elif action.name == 'declaracao_variaveis':
                descritorArvore = (podaDeclaracaoVariavel(action),) + descritorArvore
            elif action.name == 'se':
                descritorArvore = (podaSe(action),) + descritorArvore
            elif action.name == 'repita':
                descritorArvore = (podaRepita(action),) + descritorArvore
            elif action.name == 'entrada_saida':
                descritorArvore = (podaFuncoesEntradaSaida(action),) + descritorArvore
            else:
                VERMELHO = '\033[31;1m'  # Código para vermelho escuro
                RESET = '\033[0m'        # Código para resetar a cor

                print(f"{VERMELHO}Erro na {action.name}{RESET}")
        else:
            VERMELHO = '\033[31;1m'  # Código para vermelho escuro
            RESET = '\033[0m'        # Código para resetar a cor

            # Exemplo de uso:
            print(f"{VERMELHO}Erro na {item.name}{RESET}")

        
        # Passa para o próximo nó
        item = item.children[0] if len(item.children) > 0 else None
    
    # Atualiza a árvore com o corpo podado
    tree.children = descritorArvore
    return tree

# Função principal para iniciar a poda da árvore
def podaArvore():
    tree = root
    podaDeclaracoes(tree)
    UniqueDotExporter(tree).to_picture("prunedTree.png")

# Função principal do programa
def main():
    if(len(sys.argv) < 2):
        raise TypeError(error_handler.newError(False, 'ERR-SEM-USE'))
    
    variavelAuxiliar = argv[1].split('.')
    
    # Verifica se o arquivo fornecido é do tipo '.tpp'
    if variavelAuxiliar[-1] != 'tpp':
        raise IOError(error_handler.newError(False, 'ERR-SEM-NOT-TPP'))
    elif not os.path.exists(argv[1]):
        raise IOError(error_handler.newError(False, 'ERR-SEM-FILE-NOT-EXISTS'))
    else:
        # Lê o arquivo fonte
        data = open(argv[1])
        source_file = data.read()

if __name__ == "__main__":
    main()
