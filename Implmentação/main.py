# Autor: Marcos Bezner Rampaso
# Entrega 3 - Implementação de Linguagens de Programação
# Data: 29/08/2024
# Descrição: Programa principal que chama o analisador léxico, sintático e semântico.
#            O programa chama o analisador léxico e sintático, e caso a árvore sintática
#            não seja vazia, chama o analisador semântico.

import tppparser
import tppsema
from tppgencode import GenCode
from myerror import MyError
from sys import argv
import os

# Inicializa o manipulador de erros com o arquivo de erros adequado
error_handler = MyError('MainErrors')

def is_tree_empty(tree):
    """ Verifica se a árvore está vazia ou não """
    return tree is None or len(tree.children) == 0

if __name__ == "__main__":
    numParameters = len(argv) # Número de parâmetros

    if numParameters != 2:
        error = "Número de parâmetros Inválido, verifique a sintaxe. "
        if numParameters < 2: 
            error += "Envie um arquivo .tpp."
            raise IOError(error_handler.newError(False, 'ERR-MAIN-USE'))
        raise IOError(error_handler.newError(False, 'ERR-MAIN-USE'))

    aux = argv[1].split('.')
    if aux[-1] != 'tpp':
        raise IOError(error_handler.newError(False, 'ERR-MAIN-NOT-TPP'))
    elif not os.path.exists(argv[1]):
        raise IOError(error_handler.newError(False, 'ERR-MAIN-FILE-NOT-EXISTS'))
    else:
        try:
            tppparser.main()
        except Exception as e:
            raise IOError(error_handler.newError(False, 'ERR-MAIN-SYN-ERR'))

        if not is_tree_empty(tppparser.root):
            # Análise semântica
            try:
                tppsema.root = tppparser.root
                tppsema.validarSemantica()  # Realiza a análise semântica
            except Exception as e:
                raise IOError(error_handler.newError(False, 'ERR-MAIN-SEM-ERR'))
            tppsema.simplificaArvore()   # Realiza a simplificação da árvore
            # Geração de código
            # Supondo que tppsema.root seja a raiz da árvore
            gen_code = GenCode()
            gen_code.inicializacao(tppsema.root)
            # Chame o método print_tree para a raiz da árvore
            if tppsema.root:
                tppsema.root.print_tree()
            else:
                print("A árvore está vazia.")
        else:
            print("A árvore está vazia ou não foi gerada corretamente.")
