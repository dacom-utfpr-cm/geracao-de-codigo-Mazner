from myerror import MyError
from llvmlite import binding as llvm
from llvmlite import ir

error_handler = MyError('GenCodeErrors')
root = None

# Inicializa o objeto gerador de código llvm
class GenCode():
    def __init__(self):

        ### Inicialização de variáveis globais ####################
        ''' esse trecho de código é responsável por inicializar as variáveis globais utilizadas no código gerado.
            essas variaveis são utilizadas para armazenar as funções, variáveis locais, argumentos de funções e variáveis globais.'''
        self.functions = []
        self.variaveisDoEscopoAtual = []
        self.argumentosFuncao = []
        self.variaveisGlobais = []
        ###########################################################

        #### Inicialização do LLVM ################################
        ''' esse trecho de código é responsável por inicializar o LLVM e criar o módulo e as funções de entrada e saída do código gerado.'''
        llvm.initialize()                   # Inicializa o LLVM
        llvm.initialize_all_targets()       # Inicializa todos os targets
        llvm.initialize_native_target()     # Inicializa o target nativo
        llvm.initialize_native_asmprinter() # Inicializa o asm printer
        ############################################################
        
        ######### Criação do módulo e funções #######################################################################
        '''' esse trecho de código é responsável por criar o módulo e as funções de entrada e saída do código gerado.'''

        self.module = ir.Module('geracao_codigo.bc')            # Cria um novo módulo LLVM com o nome 'geracao_codigo.bc', 
                                                                # que serve como container para as funções e variáveis globais geradas 

        self.module.triple = llvm.get_process_triple()          # Obtém o triple do processo
        target = llvm.Target.from_triple(self.module.triple)    # Cria o target a partir do triple
        target_machine = target.create_target_machine()         # Cria a máquina alvo a partir do target
        self.module.data_layout = target_machine.target_data    # Define o layout dos dados do módulo
        ############################################################################################################


        ######### Declaração das funções de entrada e saída #######################################################
        ''' esse trecho de código é responsável por declarar as funções de entrada e saída do código gerado.'''
        self.escrevaInteiro = ir.Function(self.module,ir.FunctionType(ir.VoidType(), [ir.IntType(32)]),name="escrevaInteiro")
        self.escrevaFlutuante = ir.Function(self.module,ir.FunctionType(ir.VoidType(),[ir.FloatType()]),name="escrevaFlutuante")
        self.leiaInteiro = ir.Function(self.module,ir.FunctionType(ir.IntType(32),[]),name="leiaInteiro")
        self.leiaFlutuante = ir.Function(self.module,ir.FunctionType(ir.FloatType(),[]),name="leiaFlutuante")
        ###########################################################################################################

        ######### Declaração dos blocos de entrada e saída ########################################################
        ''' esse trecho de código é responsável por declarar os blocos de entrada e saída do código gerado.'''
        self.blocoEntrada = None        # bloco de entrada
        self.blocoAtual = None          # bloco atual
        self.blocoSaida = None          # bloco de saída
        ###########################################################################################################

        ######### Declaração dos tipos de dados ###################################################################
        ''' esse trecho de código é responsável por declarar os tipos de dados que serão utilizados no código gerado.'''
        self.INT = ir.IntType(32)
        self.FLOAT = ir.FloatType()
        self.ZERO = ir.Constant(ir.IntType(32), 0)
        ###########################################################################################################

    # Função principal que inicia a geração de código
    def inicializacao(self, tree):
        atribuicoes = tree.children[0].children
        indice = 0
        while indice < len(atribuicoes):
            declaracao = atribuicoes[indice]
            if declaracao.name == 'declaracao_funcao':
                self.navegaNaFuncao(declaracao)
            elif declaracao.name == 'declaracao_variaveis':
                self.variaveisGlobais.extend(self.inicializaVariavel(declaracao))
            else:
                print('inicialização de variáveis')
            indice += 1
        self.salvaResultado()

    def navegaNaFuncao(self, tree):
        # Variáveis locais da função (argumentos e variáveis locais)
        self.argumentosFuncao = []
        self.variaveisDoEscopoAtual = []

        # Verifica o tipo da função (inteiro ou flutuante)
        if tree.children[0].name not in ['inteiro', 'flutuante']:
            # Se o tipo não for inteiro nem flutuante, assume tipo Void
            name = tree.children[0].name
            params = tree.children[2]
            corpoRecebido = tree.children[4]
            type = ir.VoidType()
        else:
            # Se o tipo for inteiro ou flutuante
            name = tree.children[1].name
            params = tree.children[3]
            corpoRecebido = tree.children[5]
            type = self.retornaTipo(tree.children[0].name)


        # Se o nome da função for 'principal', renomeia para 'main'
        name = 'main' if name == 'principal' else name

        # Obtém os parâmetros da função (nomes e tipos) e cria a função
        parametros = self.retornaParametros(params)
        tipoFuncao = ir.FunctionType(type, parametros['types'])
        func = ir.Function(self.module, tipoFuncao, name)

        # Atribui nomes aos argumentos da função
        i = 0
        while i < len(func.args):
            func.args[i].name = parametros['names'][i]
            i += 1

        self.functions.append(func)

        # Armazena os argumentos da função para acesso futuro e inicializa o bloco de entrada
        self.argumentosFuncao = func.args
        self.blocoEntrada = func.append_basic_block("bloco_entrada")

        # Inicializa o construtor IRBuilder para o bloco de entrada
        self.blocoAtual = ir.IRBuilder(self.blocoEntrada)
        self.navegaNoCorpo(corpoRecebido, func)

    # Navega no corpo da função
    def navegaNoCorpo(self, tree, func: ir.Function):
        listaDeAtribuicoes = tree.children
        possuiRetorno = False
        i = 0
        while i < len(listaDeAtribuicoes):
            item = listaDeAtribuicoes[i]
            if item.name == 'declaracao_variaveis':
                self.variaveisDoEscopoAtual.extend(self.inicializaVariavel(item, escopoGlobal=False))
            elif item.name == 'chamada_funcao':
                self.retornaBloco(tree)
            elif item.name == 'atribuicao':
                self.processarAtribuicao(item)
            elif item.name in ['escreva', 'leia', 'retorna']:
                if item.name == 'retorna':
                    possuiRetorno = True
                self.funcaoEspecial(item, func)
            elif item.name == 'se':
                self.processarCondicional(item, func)
            elif item.name == 'repita':
                self.processaLoop(item, func)
            i += 1
        return possuiRetorno
    
    # Busca a função e a chama
    def retornaBloco(self, tree):
        name = tree.children[0].name
        func = None
        
        # Busca a função pelo nome
        i = 0
        while i < len(self.functions):
            if self.functions[i].name == name:
                func = self.functions[i]
                break
            i += 1
        
        if func is None:
            raise ValueError(f"Função '{name}' não encontrada.")
        
        variaveis = self.retornaArgumentos(tree.children[2])
        return self.blocoAtual.call(func, args=variaveis)
    
    # Retorna os argumentos da função
    def retornaArgumentos(self, tree):
        listaArgumentos = tree.children
        argumentos = []

        i = 0
        while i < len(listaArgumentos):
            arg = listaArgumentos[i]
            name = arg.name
            if name != 'vazio':
                aux = self.montarExpressao(arg)
                argumentos.append(aux)
            i += 1

        return argumentos
    
    # Processa a atribuição
    def processarAtribuicao(self, tree):
        name = tree.children[0].children[0].name
        variavaelAtribuida = self.buscaVariavel(name)

        if len(tree.children[0].children) > 1:
            indice = self.montarExpressao(tree.children[0].children[1].children[1])
            array_1 = self.blocoAtual.gep(variavaelAtribuida, [self.INT(0), indice], name='array_1')
            variavaelAtribuida = array_1
        
        expr = self.montarExpressao(tree.children[2])
        self.blocoAtual.store(expr, variavaelAtribuida, align=4)

    # Função que processa as funções especiais (leia, escreva e retorna)
    def funcaoEspecial(self, tree, func: ir.Function):
        if tree.name == 'leia':
            valor = self.buscaVariavel(tree.children[2].children[0].name)
            tipoVariavel = valor.type.pointee
            if tipoVariavel == self.INT:
                valor_leitura = self.blocoAtual.call(self.leiaInteiro, args=[])
            else:
                valor_leitura = self.blocoAtual.call(self.leiaFlutuante, args=[])
            self.blocoAtual.store(valor_leitura, valor, align=4)
        elif tree.name == 'escreva':
            valor = self.montarExpressao(tree.children[2])
            tipoVariavel = valor.type
            if tipoVariavel == self.INT:
                self.blocoAtual.call(self.escrevaInteiro, args=[valor])
            else:
                self.blocoAtual.call(self.escrevaFlutuante, args=[valor])
        else: # Retorna
            resultado = self.montarExpressao(tree.children[2])
            self.blocoSaida = func.append_basic_block("bloco_saida")
            self.blocoAtual.branch(self.blocoSaida)
            self.blocoAtual = ir.IRBuilder(self.blocoSaida)
            self.blocoAtual.ret(resultado)

    def processarCondicional(self, tree, func: ir.Function):
        ''' Processa a estrutura condicional '''
        
        # Verifica se o número de filhos na árvore é diferente de 5
        # Caso contrário, trata-se de uma estrutura condicional com um "else"
        if len(tree.children) != 5:
            # Cria blocos básicos para as partes da condicional
            iftrue = func.append_basic_block('iftrue')   # Bloco para o caso em que a condição é verdadeira
            iffalse = func.append_basic_block('iffalse') # Bloco para o caso em que a condição é falsa
            ifend = func.append_basic_block('ifend')     # Bloco final que será alcançado após o bloco verdadeiro ou falso

            # Avalia a condição da estrutura condicional
            cond = self.montarExpressao(tree.children[1])  # Avalia a expressão condicional
            self.blocoAtual.cbranch(cond, iftrue, iffalse)  # Cria uma ramificação condicional baseada no resultado da condição

            # Bloco para o caso verdadeiro
            self.blocoAtual.position_at_end(iftrue)  # Move a posição de construção para o bloco 'iftrue'
            possuiRetorno = self.navegaNoCorpo(tree.children[3], func)  # Processa o corpo do 'if'
            if not possuiRetorno:
                self.blocoAtual.branch(ifend)  # Se não houver retorno, faz a transição para o bloco final

            # Bloco para o caso falso
            self.blocoAtual.position_at_end(iffalse)  # Move a posição de construção para o bloco 'iffalse'
            possuiRetorno = self.navegaNoCorpo(tree.children[5], func)  # Processa o corpo do 'else'
            if not possuiRetorno:
                self.blocoAtual.branch(ifend)  # Se não houver retorno, faz a transição para o bloco final

            # Bloco final
            self.blocoAtual.position_at_end(ifend)  # Move a posição de construção para o bloco final

        else:
            # Cria blocos básicos para a estrutura condicional sem "else"
            iftrue = func.append_basic_block('iftrue')  # Bloco para o caso em que a condição é verdadeira
            ifend = func.append_basic_block('ifend')    # Bloco final que será alcançado após o bloco verdadeiro

            # Avalia a condição da estrutura condicional
            cond = self.montarExpressao(tree.children[1])  # Avalia a expressão condicional
            self.blocoAtual.cbranch(cond, iftrue, ifend)  # Cria uma ramificação condicional baseada no resultado da condição

            # Bloco para o caso verdadeiro
            self.blocoAtual.position_at_end(iftrue)  # Move a posição de construção para o bloco 'iftrue'
            possuiRetorno = self.navegaNoCorpo(tree.children[3], func)  # Processa o corpo do 'if'
            if not possuiRetorno:
                self.blocoAtual.branch(ifend)  # Se não houver retorno, faz a transição para o bloco final

            # Bloco final
            self.blocoAtual.position_at_end(ifend)  # Move a posição de construção para o bloco final

    def processaLoop(self, tree, func: ir.Function):
        ''' Processa a estrutura de loop (repetição) '''
        
        # Cria blocos básicos para o controle do fluxo do laço de repetição
        inicioLoop = self.blocoAtual.append_basic_block('loop')       # Bloco que marca o ponto inicial do laço
        condicaoLoop = self.blocoAtual.append_basic_block('loop_val') # Bloco que avalia a condição do laço
        finalLoop = self.blocoAtual.append_basic_block('loop_end')    # Bloco que marca o ponto de término do laço

        # Direciona o fluxo de execução para o bloco 'inicioLoop'
        self.blocoAtual.branch(inicioLoop)

        # Define o ponto de execução no início do bloco do laço e processa o corpo do mesmo
        self.blocoAtual.position_at_end(inicioLoop)
        self.navegaNoCorpo(tree.children[1], func)  # Processa o corpo do laço

        # Após a execução do corpo, direciona o fluxo para o bloco de validação da condição
        self.blocoAtual.branch(condicaoLoop)

        # Define o ponto de execução no início do bloco de validação da condição
        self.blocoAtual.position_at_end(condicaoLoop)

        # Avalia a condição de continuidade do loop
        cond = self.montarExpressao(tree.children[3])  # Realiza a construção da expressão condicional

        # Verifica se a condição do loop é verdadeira ou falsa
        # Se verdadeira, o fluxo é redirecionado para 'inicioLoop' para uma nova iteração
        # Se falsa, o fluxo segue para 'finalLoop', indicando a saída do loop
        self.blocoAtual.cbranch(cond, finalLoop, inicioLoop)

        # Define o ponto de execução no bloco final, após o término do loop
        self.blocoAtual.position_at_end(finalLoop)


    # Inicializa variáveis com base na árvore de sintaxe
    def inicializaVariavel(self, tree, escopoGlobal=True):
        variaveis = tree.children[2].children
        atributo = self.retornaTipo(tree.children[0].name)

        tipoVariavel = []
        i = 0
        while i < len(variaveis):
            variavel = variaveis[i]
            name = variavel.children[0].name

            if len(variavel.children) == 1:
                if escopoGlobal:
                    resultado = ir.GlobalVariable(self.module, atributo, name)
                    resultado.initializer = ir.Constant(atributo, None)
                else:
                    resultado = self.blocoAtual.alloca(atributo, name=name)
            else:
                indice = variavel.children[1].children
                value_type = ir.ArrayType(ir.IntType(32), 1000)
                if len(indice) > 3:
                    value_type = ir.ArrayType(value_type, 10)
                if escopoGlobal:
                    resultado = ir.GlobalVariable(self.module, value_type, name)
                    resultado.linkage = "common"
                    resultado.initializer = ir.Constant(value_type, 0)
                else:
                    resultado = self.blocoAtual.alloca(value_type, name=name)
            
            resultado.align = 4
            tipoVariavel.append(resultado)
            i += 1

        return tipoVariavel

    # Realiza a busca da variavel
    def buscaVariavel(self, var_name):
        indice = 0
        while indice < len(self.variaveisGlobais):
            varGlobal = self.variaveisGlobais[indice]
            if varGlobal.name == var_name:
                return varGlobal
            indice += 1
        indice = 0
        while indice < len(self.variaveisDoEscopoAtual):
            varLocal = self.variaveisDoEscopoAtual[indice]
            if varLocal.name == var_name:
                return varLocal
            indice += 1

        return None
    
    # Retorna os parametros
    def retornaParametros(self, tree):

        listaParametros = tree.children
        nomeParametros = []
        tipoParametros = []

        i = 0
        while i < len(listaParametros):
            param = listaParametros[i]
            if param.name != 'vazio':
                name = param.children[2].name
                type = self.retornaTipo(param.children[0].name)
                nomeParametros.append(name)
                tipoParametros.append(type)
            i += 1

        novosParametros = {
            'names': nomeParametros,
            'types': tipoParametros
        }
        return novosParametros

    # Processa um elemento e retorna o argumento correspondente
    def processarElemento(self, elemento):
        ''' Processa um elemento e retorna o argumento correspondente '''
        nomeElemento = elemento.name
        
        if 'NUM_' in nomeElemento:
            valor = elemento.children[0].name
            if valor in ['0']:
                return self.ZERO
            else:
                tipoValor = self.retornaTipo(nomeElemento)
                valor = float(valor) if tipoValor == self.FLOAT else int(valor)
                return ir.Constant(tipoValor, valor)
        
        elif nomeElemento == 'var':
            variavel = self.buscaVariavel(elemento.children[0].name)
            if variavel is None:
                variavel = self.retornaArgumentos(elemento.children[0].name)
                return variavel
            else:
                if len(elemento.children) > 1:
                    indiceArray = self.montarExpressao(elemento.children[1].children[1])
                    arrayTemp = self.blocoAtual.gep(variavel, [self.INT(0), indiceArray], name='arrayTemp')
                    variavel = arrayTemp
                return self.blocoAtual.load(variavel)
        
        elif nomeElemento == 'chamada_funcao':
            return self.retornaBloco(elemento)

        return None
    
    def defineMetodo(self, operador, primeiroArgumento, segundoArgumento):
        ''' Executa a operação baseada no operador '''
        if operador == "+":
            return self.blocoAtual.add(primeiroArgumento, segundoArgumento, name='soma')
        elif operador in ["<", ">", "=", ">=", "<=", "&&", "||"]:
            operador = "==" if operador == '=' else operador
            return self.blocoAtual.icmp_signed(operador, primeiroArgumento, segundoArgumento, name='comparacao')
        elif operador == "-":
            return self.blocoAtual.sub(primeiroArgumento, segundoArgumento, name='subtracao')
        elif operador == "/":
            return self.blocoAtual.sdiv(primeiroArgumento, segundoArgumento, name='divisao')
        elif operador == "*":
            return self.blocoAtual.mul(primeiroArgumento, segundoArgumento, name='multiplicacao')
        else:
            print("Operador não reconhecido.")
   # Monta a expressão 
    def montarExpressao(self, tree):
        ''' Processa os argumentos da árvore '''
        auxiliar = tree.children
        primeiroArgumento = None
        indice = 0 if auxiliar[0].name != '(' else 1

        primeiroArgumento = self.processarElemento(auxiliar[indice])

        if len(tree.children) > 1:
            nomeElemento = auxiliar[indice + 2].name
            segundoArgumento = self.processarElemento(auxiliar[indice + 2])
            operador = auxiliar[indice + 1].name
            
            return self.defineMetodo(operador, primeiroArgumento, segundoArgumento)

        return primeiroArgumento
    
    # Retorna o tipo
    def retornaTipo(self, type_name):
        return self.INT if type_name == 'inteiro' or type_name == 'NUM_INTEIRO' else self.FLOAT        
    # Retorna os argumentos
    
    def retornaArgumentos(self, var_name):
        indice = 0
        while indice < len(self.argumentosFuncao):
            argumentoAtual = self.argumentosFuncao[indice]
            if argumentoAtual.name == var_name:
                return argumentoAtual
            indice += 1
        return None

    def salvaResultado(self):
        file = open('resultado.ll', 'w')
        file.write(str(self.module))
        file.close()