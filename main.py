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

        if tppparser.root is not None and tppparser.root.children != ():
            # Análise semântica
            try:
                tppsema.root = tppparser.root
                tppsema.checkRules()  # Realiza a análise semântica
            except Exception as e:
                raise IOError(error_handler.newError(False, 'ERR-MAIN-SEM-ERR'))
            tppsema.podaArvore()   # Realiza a poda da árvore sintática
            # Geração de código
            gen_code = GenCode()
            gen_code.declaration(tppsema.root, argv[1])  # Passa o nome do arquivo para a declaração
        else:
            raise IOError(error_handler.newError(False, 'ERR-MAIN-SYN-ERR'))