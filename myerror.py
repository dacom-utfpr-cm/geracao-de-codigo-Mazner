import configparser

class MyError:
    VERMELHO = '\033[31;1m'   # Código para vermelho escuro
    AMARELO = '\033[93m'  # Código para amarelo
    RESET = '\033[0m'        # Código para resetar a cor
    
    def __init__(self, et):
        self.config = configparser.RawConfigParser()
        self.config.read('ErrorMessages.properties', encoding='UTF-8')
        self.errorType = et

    def newError(self, optkey, key, **data):
        message = ''
        if optkey:
            return key
        if key:
            message = self.config.get(self.errorType, key)
        if data:
            for k, v in data.items():
                message = f"{message}, {k}: {v}"
        
        # Adiciona formatação de cor com base no tipo de mensagem
        if key and key.startswith('ERR'):
            color = self.VERMELHO
        elif key and key.startswith('WAR'):
            color = self.AMARELO
        else:
            color = self.RESET
        
        return f"{color}{message}{self.RESET}"