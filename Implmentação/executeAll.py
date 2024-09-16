import os
import subprocess

# Caminho para a pasta de testes
test_folder = 'tests'

# Lista todos os arquivos na pasta de testes
for filename in os.listdir(test_folder):
    if filename.endswith('.tpp'):
        file_path = os.path.join(test_folder, filename)
        # Executa o comando python main.py com o arquivo .tpp como argumento
        result = subprocess.run(['python', 'main.py', file_path], capture_output=True, text=True)
        # Imprime o resultado da execução
        print(f'Executando {file_path}:\n{result.stdout}')
        if result.stderr:
            print(f'Erros:\n{result.stderr}')
