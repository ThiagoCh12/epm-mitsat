# EPM → MITSAT

Serviço de sincronização horária de vazão de defluência entre o **Elipse EPM** e a plataforma **MITSAT**.

A cada hora, o serviço lê o valor mais recente da variável configurada no EPM e o envia para a MITSAT com o timestamp `HH:00:00 UTC-3`.

---

## Requisitos

- Python 3.11+
- Acesso à rede para o EPM (HTTPS local) e para `prod.mitsat.com.br`
- Credenciais EPM e MITSAT configuradas no `.env`

---

## Instalação

```bash
# Clone o repositório e entre na pasta
cd EPM-MITSAT

# Crie e ative o ambiente virtual
python -m venv venv

# Windows
venv\Scripts\activate

# Linux
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
```

---

## Configuração

Renomeie `.env.example` para `.env` e preencha as variáveis:

```env
# EPM
EPM_AUTH=https://localhost:44333
EPM_API=https://localhost:44332
EPM_USER=sa
EPM_PASSWORD=senha

# MITSAT
MITSAT_BASE_URL=https://prod.mitsat.com.br/api
JUR_API_KEY=sua_client_key
JUR_SECRET_KEY=sua_key_secret
```

---

## Uso

### Execução direta (teste manual)

```bash
python app/main.py
```

O serviço acorda em `HH:05` de cada hora, lê o EPM da hora anterior e envia para a MITSAT.

### Simulação sem EPM

```bash
python app/test_run.py
```

Envia um valor fixo (`42.00 m³/s`) a cada `HH:00` — útil para validar a integração com a MITSAT sem depender do EPM.

### Logs

Os logs ficam em `logs/epm_mitsat.log`, com rotação diária e retenção de 30 dias.

---

## Rodar como serviço 24/7

### Linux — systemd

1. Crie o arquivo de serviço:

```bash
sudo nano /etc/systemd/system/epm-mitsat.service
```

```ini
[Unit]
Description=EPM para MITSAT - Sincronização de Vazão
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/EPM-MITSAT
ExecStart=/opt/EPM-MITSAT/venv/bin/python app/main.py
Restart=always
RestartSec=30
StandardOutput=append:/opt/EPM-MITSAT/logs/service.log
StandardError=append:/opt/EPM-MITSAT/logs/service.log

[Install]
WantedBy=multi-user.target
```

> Ajuste `User` e `WorkingDirectory` conforme seu servidor.

2. Ative e inicie:

```bash
sudo systemctl daemon-reload
sudo systemctl enable epm-mitsat
sudo systemctl start epm-mitsat
```

3. Comandos úteis:

```bash
sudo systemctl status epm-mitsat    # status
sudo systemctl restart epm-mitsat   # reiniciar
sudo systemctl stop epm-mitsat      # parar
journalctl -u epm-mitsat -f         # logs em tempo real
```

---

### Windows — NSSM

O [NSSM](https://nssm.cc) instala qualquer executável como serviço Windows.

1. Baixe o NSSM e coloque `nssm.exe` em `C:\nssm\`

2. Instale o serviço (execute como Administrador):

```cmd
C:\nssm\nssm.exe install EPM-MITSAT
```

Na janela que abrir, preencha:

| Campo | Valor |
|---|---|
| Path | `C:\EPM-MITSAT\venv\Scripts\python.exe` |
| Startup directory | `C:\EPM-MITSAT` |
| Arguments | `app/main.py` |

3. Na aba **I/O**, configure o log de saída:
   - Stdout: `C:\EPM-MITSAT\logs\service.log`
   - Stderr: `C:\EPM-MITSAT\logs\service.log`

4. Comandos úteis:

```cmd
nssm start EPM-MITSAT
nssm stop EPM-MITSAT
nssm restart EPM-MITSAT
nssm status EPM-MITSAT
```

Ou gerencie pelo **Gerenciador de Serviços** do Windows (`services.msc`).

---

## Estrutura do projeto

```
EPM-MITSAT/
├── app/
│   ├── clients/
│   │   ├── epm_client.py       # Conexão com Elipse EPM
│   │   └── mitsat_client.py    # Integração com API MITSAT
│   ├── services/
│   │   └── mitsat_helpers.py   # Formatação de payload
│   ├── config.py               # Carregamento do .env
│   ├── main.py                 # Serviço principal (produção)
│   ├── test_run.py             # Simulação sem EPM
├── logs/                       # Logs rotativos (criado automaticamente)
├── .env                        # Credenciais (não versionar)
├── requirements.txt
└── README.md
```
