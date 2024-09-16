import os
import sys
from sys import argv
from myerror import MyError
from anytree import RenderTree, findall_by_attr
from anytree.exporter import UniqueDotExporter

error_handler = MyError('SemaErrors')
root = None

################################# Lista de variaveis de controele ###########################################
listaDeVariaveisComErro = []    # Lista de variáveis com erro                                               #
tipoDado = []                   # Lista de tipos de dados                                                   #
parameters = []                 # Lista de parâmetro                                                        #
                                                                                                            #
################################# Lista de identificadores ##################################################
identificadores = [                                                                                         #
    'ID',                                                                                                   #
    'ABRE_PARENTESE',                                                                                       #
    'FECHA_PARENTESE',                                                                                      #
    'FIM',                                                                                                  #
    'abre_colchete',                                                                                        #
    'fecha_colchete'                                                                                        #
]                                                                                                           #
#############################################################################################################


# Função para inicializar o analisador semântico
def validarSemantica():
    tabelaDeSimbolos = montarTabelaDeSimbolos()
    if (not verificaMain(tabelaDeSimbolos)):
        print(error_handler.newError(False, 'ERR-SEM-MAIN-NOT-DECL'))
    verificaVariaveis(tabelaDeSimbolos)
    variavelEmUso(tabelaDeSimbolos)
    verificaFuncoes(tabelaDeSimbolos)

# Função para montar a tabela de símbolos
def montarTabelaDeSimbolos():
    resultados = findall_by_attr(root, "declaracao")
    variaveis = []
    for item in resultados:
        nodes = [node for fill, pre, node in RenderTree(item)]
        if (nodes[1].name == "declaracao_variaveis"):
            variavel = declaracaoDeVariavel(node1=nodes[1], escopo="global")
            if variavelDeclarada(tabelaDeSimbolos=variaveis, name=variavel['name'], escopo='global'):
                tipoVariavel = buscarTipo(tabelaDeSimbolos=variaveis, name=variavel['name'], escopo='global')
                print(error_handler.newError(False, 'WAR-SEM-VAR-DECL-PREV').format(variavel['name'], tipoVariavel))
            else:
                variaveis.append(variavel)
        elif (nodes[1].name == "declaracao_funcao"):
            if nodes[2].name == "tipo":
                nome = nodes[7].name
                token = nodes[6].name
                tipo = nodes[4].name
                linha = nodes[4].line
            else:
                nome = nodes[4].name
                token = nodes[3].name
                tipo = 'vazio'
                linha = nodes[4].line

            variavel = {
                "tipoDeclaracao": 'func',
                "type": tipo,
                "line": linha,
                "token": token,
                "name": nome,
                "escopo": "global",
                "used": "True" if nome == "principal" else "False",
                "dimension": 0,
                "sizeDimension1": 1,
                "sizeDimension2": 0,
                "parameters": declaracaoDeParametros(nodes)
            }
            if variavelDeclarada(tabelaDeSimbolos=variaveis, name=nome, escopo='global'):
                tipoVariavel = buscarTipo(tabelaDeSimbolos=variaveis, name=nome, escopo='global')
                print(error_handler.newError(False, 'WAR-SEM-FUNC-DECL-PREV').format(nome, tipoVariavel))
            else:
                variaveis.append(variavel)
                declaracaoFuncao(node1=nodes[1], escopo=nome, tabelaDeSimbolos=variaveis)

    return variaveis

# Verifica se há main
def verificaMain(tabelaDeSimbolos):
    for indice in range(len(tabelaDeSimbolos)):
        if tabelaDeSimbolos[indice]['tipoDeclaracao'] == 'func' and tabelaDeSimbolos[indice]['name'] == 'principal':
            return True
    return False, 'principal'

# Função para buscar o tipo de variável
def buscarTipo(tabelaDeSimbolos, name, escopo):
    for indice in range(len(tabelaDeSimbolos)):
        if tabelaDeSimbolos[indice]['name'] == name and (tabelaDeSimbolos[indice]['escopo'] == 'global' or tabelaDeSimbolos[indice]['escopo'] == escopo):
            return tabelaDeSimbolos[indice]['type']
        elif escopo != 'global' and tabelaDeSimbolos[indice]['tipoDeclaracao'] == 'func':
            parameters = tabelaDeSimbolos[indice]['parameters']
            for j in parameters:
                if j['name'] == name:
                    return tabelaDeSimbolos[indice]['type']
    return None

# Função para incializar a declaração parâmetros
def declaracaoDeParametros(node1):
    for item in node1:
        if item.name == 'cabecalho':
            aux = item.children[2]
            parametrosEncontrados = findall_by_attr(aux, "parametro")
            for parametroAnterior in parametrosEncontrados:
                parametroAtual = {} 
                parametroAtual['name'] = parametroAnterior.children[2].children[0].name
                parametroAtual['type'] = parametroAnterior.children[0].children[0].children[0].name
                parameters.append(parametroAtual)
    return parameters

# Função para inicializar a declaração da função
def declaracaoFuncao(node1, escopo, tabelaDeSimbolos):
    variaveisEncontradas = findall_by_attr(node1, "declaracao_variaveis")
    for variavelNode in variaveisEncontradas:
        variavel = declaracaoDeVariavel(node1=variavelNode, escopo=escopo)
        if variavelDeclarada(tabelaDeSimbolos=tabelaDeSimbolos, name=variavel['name'], escopo=escopo):
            tipoVariavel = buscarTipo(tabelaDeSimbolos=tabelaDeSimbolos, name=variavel['name'], escopo=escopo)
            print(error_handler.newError(False, 'WAR-SEM-VAR-DECL-PREV').format(variavel['name'], tipoVariavel))
        else:
            tabelaDeSimbolos.append(variavel)

# Função para inicializar a declaração de variáveis
def declaracaoDeVariavel(node1, escopo):
    tamanhoDimensao1 = 1  # Tamanho da primeira dimensão
    tamanhoDimensao2 = 0  # Tamanho da segunda dimensão
    dimensao = 0  # Dimensão da variável
    renderNodeTree = [node for fill, pre, node in RenderTree(node1)]
    for indice in range(len(renderNodeTree)):
        if (renderNodeTree[indice].name == 'tipo'):
            tipo = renderNodeTree[indice+2].name
            linha = renderNodeTree[indice+2].line
        elif (renderNodeTree[indice].name == 'fecha_colchete'):
            dimensao += 1
            if renderNodeTree[indice-2].name == 'NUM_PONTO_FLUTUANTE':
                if not buscaVariaveisComErro(nome, escopo):
                    adicionaErroVariavel(nome, escopo)
                    print(error_handler.newError(False, 'ERR-SEM-ARRAY-INDEX-NOT-INT').format(nome))
            indice = renderNodeTree[indice-1].name
            if (dimensao == 2):
                tamanhoDimensao2 = indice
            else:
                tamanhoDimensao1 = indice
        elif (renderNodeTree[indice].name == 'ID'): 
            token = renderNodeTree[indice].name
            nome = renderNodeTree[indice+1].name

    variavel = {
        'tipoDeclaracao': 'var',
        'type': tipo,
        'line': linha,
        'token': token,
        'name': nome,
        'escopo': escopo,
        'inicializada': 'Falso',
        'used': 'Falso',
        'dimension': dimensao,
        'sizeDimension1': tamanhoDimensao1,
        'sizeDimension2': tamanhoDimensao2,
        'errors': 0
    }

    return variavel

# Função para verificar se a variável já foi declarada
def variavelDeclarada(tabelaDeSimbolos, name, escopo):
    for indice in range(len(tabelaDeSimbolos)):
        if tabelaDeSimbolos[indice]['name'] == name and (tabelaDeSimbolos[indice]['escopo'] == 'global' or tabelaDeSimbolos[indice]['escopo'] == escopo):
            return True
        elif escopo != 'global' and tabelaDeSimbolos[indice]['tipoDeclaracao'] == 'func':
            parameters = tabelaDeSimbolos[indice]['parameters']
            for j in parameters:
                if j['name'] == name:
                    return True
    return False

# Função para adicionar erro de variável
def adicionaErroVariavel(name, escopo):
    listaDeVariaveisComErro.append({
        'name': name,
        'escopo': escopo
    })

# Função para buscar variáveis com erro
def buscaVariaveisComErro(name, escopo):
    for variavel in listaDeVariaveisComErro:
        if variavel['name'] == name and variavel['escopo'] == escopo:
            return True
    return False

# Função para verificar e adicionar tipo de dado
def verificaTipoDado(tipoDado, factor, type, value):
    # Verifica se os dados estão completos
    if factor is None or type is None or value is None:
        print(f"Erro: Dados incompletos - factor: {factor}, type: {type}, value: {value}")
        return False
    
    # Verifica se o tipo de dado já foi adicionado
    if type not in ['inteiro', 'flutuante']:
        print(f"Erro: Tipo desconhecido - {type}")
        return False

    tipoDado.append({
        'factor': factor,
        'type': type,
        'value': value
    })
    
    return True

# Função para obter os elementos de fator (número, variável, chamada de função)
def obterElementosDeFator(node1, tabelaDeSimbolos, escopo):
     # Inicialize a lista
    fatoresEncontrados = findall_by_attr(node1, "fator") 

    for fatores in fatoresEncontrados:
        if not verificaIndice(fatores) and not verificaArgumento(fatores):
            elemento = fatores.children[0].name
            elemento = elemento if elemento != 'chamada_funcao' else 'func'
            
            dado = fatores.children[0].children[0].children[0].name
            categoria = fatores.children[0].children[0].name
            escopoAtual = escopo if elemento != 'func' else 'global'
            categoria = ('flutuante' if categoria == 'NUM_PONTO_FLUTUANTE' else 'inteiro') if elemento == 'numero' else buscarTipo(tabelaDeSimbolos, dado, escopoAtual)
            
            # Chamar a função para verificar e adicionar o tipo de dado
            verificaTipoDado(tipoDado, elemento, categoria, dado)
    
    return tipoDado

# Função para verificar se o nó é um argumento
def verificaArgumento(node):
    anchestors = list(node.anchestors)
    for indice in range(len(anchestors)):
        if anchestors[indice].name == 'lista_argumentos':
            return True
    return False

# Função para verificar se o nó é um índice
def verificaIndice(node):
    anchestors = list(node.anchestors)
    for indice in range(len(anchestors)):
        if anchestors[indice].name == 'indice':
            return True
    return False

# Função para inicializar a declaração de variáveis
def inicializaVariavel(tabelaDeSimbolos, name, escopo, node):
    if not variavelDeclarada(tabelaDeSimbolos=tabelaDeSimbolos, name=name, escopo=escopo):
        chamadasFuncaoEncontradas = findall_by_attr(node, 'chamada_funcao')
        if not chamadasFuncaoEncontradas and not buscaVariaveisComErro(name, escopo):
            adicionaErroVariavel(name, escopo)
            print(error_handler.newError(False, 'ERR-SEM-VAR-NOT-DECL').format(name))
    else:
        buscaCoercao(tabelaDeSimbolos=tabelaDeSimbolos, name=name, escopo=escopo, node=node)
        for indice in range(len(tabelaDeSimbolos)):
            if tabelaDeSimbolos[indice]['name'] == name and (tabelaDeSimbolos[indice]['escopo'] == 'global' or tabelaDeSimbolos[indice]['escopo'] == escopo):
                tabelaDeSimbolos[indice]['inicializada'] = 'True'

# FUnção para buscar coerção
def buscaCoercao(tabelaDeSimbolos, name, escopo, node):
    tipoDado = obterElementosDeFator(node, tabelaDeSimbolos, escopo)
    tipo = None
    for indice in range(len(tabelaDeSimbolos)):
        tipo = None

        try:
            parametro = tabelaDeSimbolos[indice]['parameters']
        except:
            parametro = None

        if parametro != None and len(parametro) > 0:
            for parametro in parametro:
                if parametro['name'] == name:
                    tipo = parametro['type']
        elif tabelaDeSimbolos[indice]['name'] == name and (tabelaDeSimbolos[indice]['escopo'] == 'global' or tabelaDeSimbolos[indice]['escopo'] == escopo):
            tipo = tabelaDeSimbolos[indice]['type']
        
        if tipo != None:
            if len(tipoDado) == 1:
                tipoDado = tipoDado[0]['type']
                if tipoDado != tipo:
                    valorDado = tipoDado[0]['value']
                    factor = tipoDado[0]['factor']
                    if factor == 'func' and tipo == 'vazio':
                        print(error_handler.newError(False, 'WAR-SEM-ATR-DIFF-TYPES-IMP-COERC-OF-RET-VAL').format(valorDado, tipoDado, name, tipo))
                    elif factor == 'var' and tipo == 'vazio':
                        print(error_handler.newError(False, 'WAR-SEM-ATR-DIFF-TYPES-IMP-COERC-OF-VAR').format(valorDado, tipoDado, name, tipo))
                    elif factor == 'numero' and tipo == 'vazio':
                        print(error_handler.newError(False, 'WAR-SEM-ATR-DIFF-TYPES-IMP-COERC-OF-NUM').format(valorDado, tipoDado, name, tipo))                        
            else:
                tipoDado = encontrarTipoCorrespondente(tipoDado, tipo)
                if tipoDado != tipo:
                    valorDado = 'expressao'
                    print(error_handler.newError(False, 'WAR-SEM-ATR-DIFF-TYPES-IMP-COERC-OF-EXP').format(valorDado, tipoDado, name, tipo))

# Função para verificar se a variável foi inicializada
def variaveisEmUso(tabelaDeSimbolos, name, escopo, node):
    if not variavelDeclarada(tabelaDeSimbolos=tabelaDeSimbolos, name=name, escopo=escopo):
        variavelEmUso = findall_by_attr(node, 'chamada_funcao')
        if not variavelEmUso and not buscaVariaveisComErro(name, escopo):
            adicionaErroVariavel(name, escopo)
            print(error_handler.newError(False, 'ERR-SEM-VAR-NOT-DECL').format(name))
    else:
        for indice in range(len(tabelaDeSimbolos)):
            if tabelaDeSimbolos[indice]['name'] == name and (tabelaDeSimbolos[indice]['escopo'] == 'global' or tabelaDeSimbolos[indice]['escopo'] == escopo):
                tabelaDeSimbolos[indice]['used'] = 'True'

# Funcao para verificar o uso das variáveis e seus respectivos tipos
def verificaVariaveis(tabelaDeSimbolos):
    nodosComAcoes = findall_by_attr(root, "acao")
    for nodoAcao in nodosComAcoes:
        renderNodeTree = [node for fill, pre, node in RenderTree(nodoAcao)]
        for nodo1 in renderNodeTree:
            renderNode1Tree = [node for fill, pre, node in RenderTree(nodo1)]
            if nodo1.name == 'expressao':
                for index in range(len(renderNode1Tree)):
                    if renderNode1Tree[index].name == 'ID':
                        name = renderNode1Tree[index+1].name
                        escopo = buscaEscopo(nodo1)
                        variaveisEmUso(tabelaDeSimbolos=tabelaDeSimbolos, name=name, escopo=escopo, node=nodo1)
                else:
                    if renderNode1Tree[1].name == 'atribuicao':
                        escopo = buscaEscopo(nodo1)
                        name = renderNode1Tree[4].name
                        inicializaVariavel(tabelaDeSimbolos=tabelaDeSimbolos, name=name, escopo=escopo, node=nodo1)
            elif nodo1.name in ['se','repita','escreva','retorna']:
                for index in range(len(renderNode1Tree)):
                    if renderNode1Tree[index].name == 'ID':
                        escopo = buscaEscopo(nodo1)
                        name = renderNode1Tree[index+1].name
                        variaveisEmUso(tabelaDeSimbolos=tabelaDeSimbolos, name=name, escopo=escopo, node=nodo1)
            elif nodo1.name == 'leia':
                for index in range(len(renderNode1Tree)):
                    if renderNode1Tree[index].name == 'ID':
                        escopo = buscaEscopo(nodo1)
                        name = renderNode1Tree[index+1].name
                        inicializaVariavel(tabelaDeSimbolos=tabelaDeSimbolos, name=name, escopo=escopo, node=nodo1)   
            elif nodo1.name == 'chamada_funcao':
                escopo = buscaEscopo(nodo1)
                name = nodo1.children[0].children[0].name
                variaveisEmUso(tabelaDeSimbolos=tabelaDeSimbolos, name=name, escopo=escopo, node=nodo1)

# Função para verificar se a variável foi inicializada
def variavelEmUso(tabelaDeSimbolos):
    for indice in range(len(tabelaDeSimbolos)):
        variavel = tabelaDeSimbolos[indice]['name']
        escopo = tabelaDeSimbolos[indice]['escopo']
        if tabelaDeSimbolos[indice]['tipoDeclaracao'] == 'var' and tabelaDeSimbolos[indice]['errors'] <= 0 and not buscaVariaveisComErro(variavel, escopo):    
            if tabelaDeSimbolos[indice]['inicializada'] == 'Falso' and tabelaDeSimbolos[indice]['used'] == 'Falso':
                print(error_handler.newError(False, 'WAR-SEM-VAR-DECL-NOT-USED').format(variavel))
            elif tabelaDeSimbolos[indice]['inicializada'] == 'True' and tabelaDeSimbolos[indice]['used'] == 'Falso':
                print(error_handler.newError(False, 'WAR-SEM-VAR-DECL-INIT-NOT-USED').format(variavel))
            elif tabelaDeSimbolos[indice]['inicializada'] == 'Falso':
                print(error_handler.newError(False, 'WAR-SEM-VAR-DECL-NOT-INIT').format(variavel))

# Função para verificar se a variável já foi declarada
def buscaEscopo(node):
    anchestors = list(node.anchestors)
    for indice in range(len(anchestors)):
        if anchestors[indice].name == 'cabecalho' and anchestors[indice].children[0].name == 'ID':
            escopo = anchestors[indice].children[0].children[0].name
            return escopo
    return 'global'

# Funcao para buscar o retorno da funcao
def buscaRetornoFuncao(tabelaDeSimbolos):
    funcoesDeclaradas = findall_by_attr(root, 'declaracao_funcao')
    for funcao in funcoesDeclaradas:
        arvoreDeNos = [node for fill, pre, node in RenderTree(funcao)]
        for noCabecalho in arvoreDeNos:
            if noCabecalho.name == 'cabecalho':
                arvoreDeNosCabecalho = [node for fill, pre, node in RenderTree(noCabecalho)]
                retornos = findall_by_attr(noCabecalho, 'retorna')
                nomeFuncao = arvoreDeNosCabecalho[2].name
                existeRetorno = bool(retornos)  # Verifica se existe retorno
                if existeRetorno:  # verifica se existe retorno
                    for retorno in retornos:
                        if retorno.children:
                            expressao = retorno.children[2]
                            if expressao.name == 'expressao':
                                escopo = buscaEscopo(retorno)
                                tipoDado = obterElementosDeFator(expressao, tabelaDeSimbolos, escopo)
                                for indice in range(len(tabelaDeSimbolos)):
                                    if (tabelaDeSimbolos[indice]['name'] == nomeFuncao and 
                                            tabelaDeSimbolos[indice]['tipoDeclaracao'] == 'func'):
                                        tipoFuncao = tabelaDeSimbolos[indice]['type']
                                        tipoFator = encontrarTipoCorrespondente(tipoDado, tipoFuncao)
                                        if tipoFator != tipoFuncao:
                                            print(error_handler.newError(False, 'ERR-SEM-FUNC-RET-TYPE-ERROR').format(nomeFuncao, tipoFuncao, tipoFator))
                else:
                    for indice in range(len(tabelaDeSimbolos)):
                        if (tabelaDeSimbolos[indice]['name'] == nomeFuncao 
                                and tabelaDeSimbolos[indice]['tipoDeclaracao'] == 'func' 
                                and tabelaDeSimbolos[indice]['type'] != 'vazio'):
                            print(error_handler.newError(False, 'ERR-SEM-FUNC-RET-TYPE-ERROR').format(nomeFuncao, tabelaDeSimbolos[indice]['type'], 'vazio'))


# Função para encontrar o tipo correspondente da variável
def encontrarTipoCorrespondente(listaTipos, tipoReferencia):
    tipoCorrespondente = tipoReferencia  # Inicializa com o tipoReferencia fornecido
    for tipo in listaTipos:
        if tipo['type'] == tipoReferencia:
            tipoCorrespondente = tipo['type']  # Atualiza apenas se encontrar o tipo correspondente
    return tipoCorrespondente

# Função para buscar chamadas de funções
def buscaChamadasDeFuncoes(tabelaDeSimbolos):
    chamadasFuncao = findall_by_attr(root, 'chamada_funcao')
    for chamada in chamadasFuncao:
        renderNodeTree = [node for fill, pre, node in RenderTree(chamada)]
        name = renderNodeTree[2].name
        # Verificar se a variável não está declarada
        if not variavelDeclarada(tabelaDeSimbolos=tabelaDeSimbolos, name=name, escopo='global'):
            print(error_handler.newError(False, 'ERR-SEM-CALL-FUNC-NOT-DECL').format(name))
        else:
            escopoChamada = buscaEscopo(chamada)
            if name == 'principal':
                if escopoChamada == 'principal':
                    print(error_handler.newError(False, 'WAR-SEM-CALL-REC-FUNC-MAIN').format(name))
                print(error_handler.newError(False, 'ERR-SEM-CALL-FUNC-MAIN-NOT-ALLOWED'))
            else:
                node1 = renderNodeTree[5]
                if node1.name == 'lista_argumentos':
                    if node1.children[0].name != 'vazio':
                        numeroArgumentos = contaParametros(node1)
                        for indice in range(len(tabelaDeSimbolos)):
                            if tabelaDeSimbolos[indice]['name'] == name and tabelaDeSimbolos[indice]['tipoDeclaracao'] == 'func':
                                parameters = tabelaDeSimbolos[indice]['parameters']
                                if numeroArgumentos > len(parameters):
                                    print(error_handler.newError(False, 'ERR-SEM-CALL-FUNC-WITH-MANY-ARGS').format(name))
                                elif numeroArgumentos < len(parameters):
                                    print(error_handler.newError(False, 'ERR-SEM-CALL-FUNC-WITH-FEW-ARGS').format(name))

def contaParametros(node):
    indice = 1
    item = node
    while item.name == 'lista_argumentos':
        if item.name == 'lista_argumentos' and len(item.children) > 1 and item.children[1].name == 'VIRGULA':
            indice+=1
        item = item.children[0]
    return indice

def verificaUsoFuncao(tabelaDeSimbolos):
    for indice in range(len(tabelaDeSimbolos)):
        if tabelaDeSimbolos[indice]['tipoDeclaracao'] == 'func':
            name = tabelaDeSimbolos[indice]['name']
            if tabelaDeSimbolos[indice]['used'] == 'Falso':
                print(error_handler.newError(False, 'WAR-SEM-FUNC-DECL-NOT-USED').format(name))

def verificaFuncoes(tabelaDeSimbolos):
    buscaChamadasDeFuncoes(tabelaDeSimbolos)
    buscaRetornoFuncao(tabelaDeSimbolos)
    verificaUsoFuncao(tabelaDeSimbolos)

################################# Funções de poda da árvore sintática ####################################
listaDeclaracoes = ()
##########################################################################################################

# Função para podar a árvore sintática
def simplificarDeclaracoes(tree):
    global listaDeclaracoes  # Faz listaDeclaracoes ser acessível globalmente
    item = tree.children[0]
    while item.name == 'lista_declaracoes':
        if item.name == 'lista_declaracoes':
            if len(item.children) == 1:
                node = item.children[0]
            else:
                node = item.children[1]
            listaDeclaracoes = node.children + listaDeclaracoes
        item = item.children[0]
    
    for indice in listaDeclaracoes:
        if indice.name == 'declaracao_variaveis':
            simplificaDeclaracaoVariavel(indice)
        elif indice.name == 'declaracao_funcao':
            simplificaDeclaracaoFuncao(indice)
        else:
            simplificaInicializacaoVariavel(indice)
    tree.children[0].children = listaDeclaracoes

# Função para simplificar a declaração de variáveis
def simplificaDeclaracaoVariavel(tree):
    listaDeclaracoes = ()
    listaDeclaracoes += tree.children[0].children[0].children
    listaDeclaracoes += tree.children[1].children

    listaVariaveisPodadas = ()
    item = tree.children[2]
    while item.name == 'lista_variaveis':
        if item.name == 'lista_variaveis':
            if len(item.children) == 1:
                listaVariaveisPodadas = (simplificaVariavel(item.children[0]),) + listaVariaveisPodadas
            else:
                listaVariaveisPodadas = (simplificaVariavel(item.children[2]),) + listaVariaveisPodadas
        item = item.children[0]
    tree.children[2].children = listaVariaveisPodadas
    listaDeclaracoes += (tree.children[2],)
    tree.children = listaDeclaracoes
    return tree

# Função para simplificar a declaração de funções
def simplificaDeclaracaoFuncao(tree):
    listaDeclaracoes = ()
    if len(tree.children) == 1:
        listaDeclaracoes += tree.children[0].children
    else:
        listaDeclaracoes += tree.children[0].children[0].children
        for child in tree.children[1].children:
            if child.name in identificadores:
                listaDeclaracoes += child.children
            elif child.name == 'corpo':
                listaDeclaracoes += (simplificaCorpo(child),)
            elif child.name == 'lista_parametros':
                listaDeclaracoesAuxiliar = ()
                for parametro in child.children:
                    if parametro.name == 'vazio':
                        listaDeclaracoesAuxiliar = (parametro,) + listaDeclaracoesAuxiliar
                    elif parametro.name == 'parametro':
                        listaDeclaracoesAuxiliar = (simplificaParametro(parametro),) + listaDeclaracoesAuxiliar
                child.children = listaDeclaracoesAuxiliar
                listaDeclaracoes += (child,)
            else:
                listaDeclaracoes += (child,)
    tree.children = listaDeclaracoes

# Função para podar o corpo da função
def simplificaInicializacaoVariavel(tree):
    listaDeclaracoes = ()
    # Adiciona a variável simplificada
    listaDeclaracoes += (simplificaVariavel(tree.children[0]),)
    # Adiciona o primeiro filho da expressão de inicialização
    listaDeclaracoes += (tree.children[1].children[0],)
    # Simplifica a expressão e adiciona ao resultado
    tree.children[2].children = simplificaExpressao(tree.children[2])
    listaDeclaracoes += (tree.children[2],)
    # Atualiza os filhos da árvore com a lista simplificada
    tree.children = listaDeclaracoes
    return tree

# Função para podar o corpo da função
def simplificaVariavel(tree):
    nodoVariavel = tree
    declaracoesSimplificadas = ()
    declaracoesAninhadas = ()

    # Adiciona o primeiro nível de filhos
    declaracoesSimplificadas += (nodoVariavel.children[0].children[0],)
    
    # Verifica se há um segundo nível de filhos
    if len(nodoVariavel.children) > 1:
        filhosSegundoNivel = nodoVariavel.children[1].children
        # Caso não haja exatamente 4 filhos no segundo nível, o bloco abaixo será executado
        if len(filhosSegundoNivel) != 4:
            declaracoesAninhadas += filhosSegundoNivel[0].children
            filhosSegundoNivel[1].children = simplificaExpressao(filhosSegundoNivel[1])
            declaracoesAninhadas += (filhosSegundoNivel[1],)
            declaracoesAninhadas += filhosSegundoNivel[2].children
        else:
            # Processa o primeiro conjunto de colchetes
            declaracoesAninhadas += filhosSegundoNivel[0].children[0].children
            filhosSegundoNivel[0].children[1].children = simplificaExpressao(filhosSegundoNivel[0].children[1])
            declaracoesAninhadas += (filhosSegundoNivel[0].children[1],)
            declaracoesAninhadas += filhosSegundoNivel[0].children[2].children

            # Processa o segundo conjunto de colchetes
            declaracoesAninhadas += filhosSegundoNivel[1].children
            filhosSegundoNivel[2].children = simplificaExpressao(filhosSegundoNivel[2])
            declaracoesAninhadas += (filhosSegundoNivel[2],)
            declaracoesAninhadas += filhosSegundoNivel[3].children
        
        nodoVariavel.children[1].children = declaracoesAninhadas
        declaracoesSimplificadas += (nodoVariavel.children[1],)
    
    tree.children = declaracoesSimplificadas
    return tree

# Função para podar o corpo da função
def simplificaParametro(tree):
    listaDeclaracoes = ()
    item = tree
    while item.name == 'parametro':
        if item.children[0].name == 'parametro':
            listaDeclaracoes = item.children[2].children + listaDeclaracoes
            listaDeclaracoes = item.children[1].children + listaDeclaracoes
        else:
            listaDeclaracoes = item.children[2].children + listaDeclaracoes
            listaDeclaracoes = item.children[1].children + listaDeclaracoes
            listaDeclaracoes = item.children[0].children[0].children + listaDeclaracoes
        item = item.children[0]
    tree.children = listaDeclaracoes
    return tree

# Função para podar o corpo da função
def simplificaExpressao(tree):
    nodos = tree.children
    nome = tree.name
    while len(nodos) == 1 and nome != 'expressao_unaria':
        nome = nodos[0].name
        nodos = nodos[0].children
    
    listaDeclaracoes = ()
    if nodos[0].parent.name != 'expressao_unaria':
        listaDeclaracoes += simplificaExpressao(nodos[0])
        listaDeclaracoes += (nodos[1].children[0].children[0],)
        listaDeclaracoes += simplificaExpressao(nodos[2])
        nodos = listaDeclaracoes
    else:
        if len(nodos) == 1:
            if nodos[0].children[0].name == 'chamada_funcao':
                listaDeclaracoes += (simplificaChamadaFuncao(nodos[0].children[0]),)
            else:
                if nodos[0].children[0].name == 'numero':
                    listaDeclaracoes += nodos[0].children[0].children
                else:
                    if nodos[0].children[0].name == 'var':
                        listaDeclaracoes += (simplificaVariavel(nodos[0].children[0]),)
                    else:
                        listaDeclaracoes += nodos[0].children[0].children
                        listaDeclaracoes += simplificaExpressao(nodos[0].children[1])
                        listaDeclaracoes += nodos[0].children[2].children
        else:
            listaDeclaracoes += nodos[0].children[0].children
            listaDeclaracoes += nodos[1].children[0].children
        nodos = listaDeclaracoes
    
    return nodos

# Função para simplificar o corpo do código
def simplificaCorpo(tree):
    listaDeclaracoes = ()
    item = tree
    while item.name == 'corpo':
        if len(item.children) == 2:
            acao = item.children[1].children[0]
            if acao.name == 'expressao':
                if acao.children[0].name == 'atribuicao':
                    listaDeclaracoes = (simplificaInicializacaoVariavel(acao.children[0]),) + listaDeclaracoes
                else:
                    acao.children = simplificaExpressao(acao)
                    listaDeclaracoes = (acao,) + listaDeclaracoes
            elif acao.name == 'se':
                listaDeclaracoes = (simplificaCondicionais(acao),) + listaDeclaracoes
            elif acao.name == 'repita':
                listaDeclaracoes = (simplificaLoop(acao),) + listaDeclaracoes
            elif acao.name == 'declaracao_variaveis':
                listaDeclaracoes = (simplificaDeclaracaoVariavel(acao),) + listaDeclaracoes
            else:
                listaDeclaracoes = (simplificaEntradaSaidaRetorno(acao),) + listaDeclaracoes
        item = item.children[0]
    tree.children = listaDeclaracoes
    return tree

# Função para simplificar a chamada de uma função
def simplificaChamadaFuncao(tree):
    listaDeclaracoes = ()
    if len(tree.children) == 1:
        # Se há apenas um filho, adiciona os filhos desse nó
        listaDeclaracoes += tree.children[0].children
    else:
        # Se há mais de um filho, processa o primeiro conjunto de filhos
        listaDeclaracoes += tree.children[0].children[0].children
        
        i = 0
        while i < len(tree.children):
            filho = tree.children[i]
            if filho.name in identificadores:
                listaDeclaracoes += filho.children
            elif filho.name == 'lista_argumentos':
                listaArgumentos = ()
                item = filho
                
                # Substitui o while por for
                for _ in range(len(item.children)):
                    if item.children[0].name == 'vazio':
                        vazio = item.children[0]
                        listaArgumentos = (vazio,) + listaArgumentos
                    elif len(item.children) == 1:
                        argumento = item.children[0]
                        argumento.children = simplificaExpressao(item.children[0])
                        listaArgumentos = (argumento,) + listaArgumentos
                    else:
                        argumento = item.children[2]
                        argumento.children = simplificaExpressao(item.children[2])
                        listaArgumentos = (argumento,) + listaArgumentos
                    item = item.children[0]
                
                filho.children = listaArgumentos
                listaDeclaracoes += (filho,)
            else:
                listaDeclaracoes += (filho,)
            i += 1
            
    tree.children = listaDeclaracoes
    return tree

# Função para simplificar as operações de entrada, saída e retorno
def simplificaEntradaSaidaRetorno(tree):
    listaDeclaracoes = ()
    listaDeclaracoes += tree.children[0].children
    listaDeclaracoes += tree.children[1].children
    if tree.name == 'leia':
        # Se a operação é 'leia', simplifica a variável
        listaDeclaracoes += (simplificaVariavel(tree.children[2]),)
    else:
        # Para outras operações, simplifica a expressão
        tree.children[2].children = simplificaExpressao(tree.children[2])
        listaDeclaracoes += (tree.children[2],)
    listaDeclaracoes += tree.children[3].children
    tree.children = listaDeclaracoes
    return tree

# Função para simplificar as condicionais
def simplificaCondicionais(tree):
    listaDeclaracoes = ()
    listaDeclaracoes += tree.children[0].children  # Adiciona o bloco 'SE'
    tree.children[1].children = simplificaExpressao(tree.children[1])  # Simplifica a expressão
    listaDeclaracoes += (tree.children[1],)  # Adiciona a expressão simplificada
    listaDeclaracoes += tree.children[2].children  # Adiciona o bloco 'ENTAO'
    listaDeclaracoes += (simplificaCorpo(tree.children[3]),)  # Simplifica e adiciona o corpo do bloco 'SE'
    if len(tree.children) == 5:
        listaDeclaracoes += (tree.children[4],)  # Adiciona o bloco 'FIM' se presente
    else:
        listaDeclaracoes += (tree.children[4],)  # Adiciona o bloco 'SENAO'
        listaDeclaracoes += (simplificaCorpo(tree.children[5]),)  # Simplifica e adiciona o corpo do bloco 'SENAO'
        listaDeclaracoes += (tree.children[6],)  # Adiciona o bloco 'FIM'
    tree.children = listaDeclaracoes
    return tree

# Função para simplificar loops
def simplificaLoop(tree):
    listaDeclaracoes = ()
    listaDeclaracoes += tree.children[0].children  # Adiciona o bloco 'REPITA'
    listaDeclaracoes += (simplificaCorpo(tree.children[1]),)  # Simplifica e adiciona o corpo do loop
    listaDeclaracoes += tree.children[2].children  # Adiciona o bloco da condição 'ATE'
    tree.children[3].children = simplificaExpressao(tree.children[3])  # Simplifica a expressão do loop
    listaDeclaracoes += (tree.children[3],)  # Adiciona a expressão simplificada
    tree.children = listaDeclaracoes
    return tree

# Função principal de simplificação da árvore
def simplificaArvore():
    tree = root
    simplificarDeclaracoes(tree)
    #UniqueDotExporter(tree).to_picture("prunedTree.png")