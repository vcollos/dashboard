## Painel de Diagnóstico VPS - Collos

### 📁 Projeto

Dashboard de diagnóstico e gerenciamento dos containers e serviços ativos na VPS da Collos.

---

### 📄 Descrição

Este painel interativo foi construído com Python + Streamlit para:

* Mapear containers Docker em execução ou parados
* Mostrar imagens, volumes, redes, uso de disco e portas abertas
* Gerenciar `docker-compose.yml` de forma visual
* Criar, editar, atualizar e remover containers diretamente da interface
* Listar bancos de dados e tabelas (PostgreSQL)

---

### 🚀 Infraestrutura

* **Servidor:** Oracle Cloud VPS (Always Free)
* **Sistema Operacional:** Ubuntu Server
* **Proxy Reverso:** Cloudflare Tunnel (via painel)

#### 🌐 Subdomínios em uso

| Subdomínio             | Descrição             | Rodando em              |
| ---------------------- | --------------------- | ----------------------- |
| `nonono.collos.com.br`   | Painel do VPS         | Streamlit na porta 8504 |
| `nonono.collos.com.br` | Collos Fiscal         | Fora do Docker          |
| `nonono.collos.com.br` | Câmara de Compensação | Fora do Docker          |

---

### 🛋️ Funcionalidades

* Painel com colunas organizadas por seções:

  * Containers (ativo/inativo)
  * Portas abertas (uso real + expostas por container)
  * Imagens em uso e inutilizadas
  * Volumes e redes por container
  * Bancos PostgreSQL com tabelas
  * Tempo de uptime e criação de containers

* Ações disponíveis:

  * Selecionar e excluir containers parados
  * Editar `docker-compose.yml` diretamente
  * Criar novo container via Compose
  * Atualizar, reinstalar ou remover qualquer container

---

### 🔐 Segurança

* Conexão segura através da Cloudflare (HTTPS)
* Variáveis sensíveis (como senha do banco) são carregadas via `.env`
* Sem exposição de dados confidenciais na interface

---

### 📅 Execução do Painel

#### Comando manual

```bash
cd ~/apps/dashboard
source venv/bin/activate
streamlit run diagnostico_vps.py --server.port=8504
```

#### Script background

```bash
./start_dashboard.sh
```

---

### 📖 Requisitos

Arquivo `requirements.txt`:

```text
streamlit==1.35.0
psutil==5.9.8
docker==7.1.0
python-dotenv==1.0.1
```

---

### 🔧 Manutenção futura

* Sempre que abrir o painel, ele escaneia em tempo real tudo que está ativo
* Atualizações devem ser feitas diretamente no painel ou no repositório de composição (`docker-compose.yml`)

Para qualquer mudança futura, este README pode ser consultado como base de referência técnica e operacional.
