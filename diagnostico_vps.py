import streamlit as st
import docker
import psutil
import subprocess
import os
import psycopg2
from dotenv import load_dotenv
load_dotenv()

client = docker.from_env()

st.set_page_config(page_title="Painel VPS", layout="wide")
st.title("Diagnóstico e Gerenciamento da VPS")

# Botão para visualizar o README
if st.button("📖 Visualizar README"):
    with open("readme.md", "r") as f:
        readme_content = f.read()
    st.markdown(readme_content)

# Uso de disco
st.header("Uso de Disco")
disk = psutil.disk_usage('/')
col1, col2, col3 = st.columns(3)
col1.metric("Total (GB)", f"{disk.total / (1024**3):.2f}")
col2.metric("Usado (GB)", f"{disk.used / (1024**3):.2f}")
col3.metric("Uso (%)", f"{disk.percent}%")


# Containers
st.header("Containers Docker")
containers = client.containers.list(all=True)
container_data = [{
    "Nome": c.name,
    "Imagem": ', '.join(c.image.tags) if c.image.tags else 'sem tag',
    "Status": c.status,
    "Memória (MB)": round(c.stats(stream=False).get("memory_stats", {}).get("usage", 0) / (1024 ** 2), 2)
} for c in containers]

if container_data:
    selected_names = st.multiselect("Selecione containers para ação", [c["Nome"] for c in container_data])
    st.dataframe(container_data, use_container_width=True)

    col1, col2 = st.columns(2)
    if col1.button("Parar Selecionados"):
        for c in containers:
            if c.name in selected_names:
                c.stop()
        st.experimental_rerun()

    if col2.button("Remover Selecionados"):
        for c in containers:
            if c.name in selected_names:
                c.remove(force=True)
        st.experimental_rerun()
else:
    st.info("Nenhum container encontrado.")

col1, col2 = st.columns(2)
with col1:
    st.header("Editar docker-compose.yml")
    compose_app = st.selectbox("Escolha o container para editar", [c.name for c in containers])
    compose_path = f"/home/collos/apps/{compose_app}/docker-compose.yml"
    if os.path.exists(compose_path):
        with open(compose_path, 'r') as f:
            yaml_content = f.read()
        updated = st.text_area("Conteúdo do docker-compose.yml", yaml_content, height=300, key="compose_editor")
        if st.button("Salvar e Recriar"):
            with open(compose_path, 'w') as f:
                f.write(updated)
            subprocess.run(["docker-compose", "-f", compose_path, "up", "-d", "--build"])
            st.success("Atualizado com sucesso!")
    else:
        st.warning(f"Arquivo não encontrado: {compose_path}")

with col2:
    st.header("Criar Novo Container via Compose")
    new_name = st.text_input("Nome do novo app")
    new_yaml = st.text_area("YAML do novo docker-compose", height=300, key="new_yaml")
    if st.button("Criar Novo Container"):
        path = f"/home/collos/apps/{new_name}"
        os.makedirs(path, exist_ok=True)
        compose_file = f"{path}/docker-compose.yml"
        with open(compose_file, 'w') as f:
            f.write(new_yaml)
        subprocess.run(["docker-compose", "-f", compose_file, "up", "-d", "--build"])
        st.success("Novo container criado!")

col1, col2 = st.columns(2)
with col1:
    st.header("Portas em Uso")
    connections = psutil.net_connections(kind='inet')
    port_table = []
    for conn in connections:
        if conn.status == 'LISTEN':
            try:
                proc = psutil.Process(conn.pid)
                port_table.append({
                    "Porta": conn.laddr.port,
                    "PID": conn.pid,
                    "Processo": proc.name(),
                    "Comando": " ".join(proc.cmdline())
                })
            except:
                continue
    if port_table:
        st.dataframe(port_table, use_container_width=True)
    else:
        st.info("Nenhuma porta em escuta identificada.")

with col2:
    st.header("Portas Expostas por Container (Docker)")
    port_map = []
    for c in containers:
        ports = c.attrs["NetworkSettings"]["Ports"] or {}
        seen_ports = set()
        for port, bindings in ports.items():
            if bindings:
                for b in bindings:
                    key = (c.name, b["HostPort"], port)
                    if key not in seen_ports:
                        seen_ports.add(key)
                        port_map.append({
                            "Container": c.name,
                            "Porta Externa": b["HostPort"],
                            "Porta Interna": port,
                            "Status": c.status
                        })

    if port_map:
        st.dataframe(port_map, use_container_width=True)
    else:
        st.info("Nenhuma porta exposta encontrada nos containers.")

col1, col2, col3 = st.columns(3)
with col1:
    st.header("Bancos de Dados (PostgreSQL)")
    try:
        pg_password = os.getenv("PG_PASSWORD")

        conn = psycopg2.connect(
            dbname='postgres',
            user='collos',
            password=pg_password,
            host='localhost'
        )
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
        databases = cursor.fetchall()
        db_list = [{"Database": db[0]} for db in databases]
        cursor.close()
        conn.close()
        if db_list:
            st.dataframe(db_list, use_container_width=True)
        else:
            st.info("Nenhum banco de dados encontrado.")
    except Exception as e:
        st.warning(f"Erro ao conectar no PostgreSQL: {e}")

with col2:
    st.header("Volumes e Redes por Container")
    volume_net_data = []
    for c in containers:
        mounts = [m['Destination'] for m in c.attrs['Mounts']]
        networks = list(c.attrs['NetworkSettings']['Networks'].keys())
        volume_net_data.append({
            "Container": c.name,
            "Volumes": ", ".join(mounts) if mounts else "Nenhum",
            "Redes": ", ".join(networks) if networks else "Nenhuma"
        })

    if volume_net_data:
        st.dataframe(volume_net_data, use_container_width=True)
    else:
        st.info("Nenhum volume ou rede detectado.")

with col3:
    st.header("Imagens em Uso")
    images = set()
    for c in containers:
        images.add(c.image.tags[0] if c.image.tags else "sem tag")

    if images:
        st.dataframe([{"Imagem": img} for img in sorted(images)], use_container_width=True)
    else:
        st.info("Nenhuma imagem em uso encontrada.")

col1, col2 = st.columns(2)
with col1:
    st.header("Tempo de Execução e Criação dos Containers")
    import datetime

    container_uptime_data = []
    for c in containers:
        created = datetime.datetime.fromisoformat(c.attrs["Created"].replace("Z", "+00:00"))
        state = c.attrs["State"]
        started_at = state.get("StartedAt")
        uptime = "-"
        if started_at:
            try:
                started_dt = datetime.datetime.fromisoformat(started_at.replace("Z", "+00:00"))
                uptime = datetime.datetime.now(datetime.timezone.utc) - started_dt
                uptime = str(uptime).split(".")[0]
            except:
                uptime = "indefinido"

        container_uptime_data.append({
            "Container": c.name,
            "Criado em": created.strftime("%Y-%m-%d %H:%M:%S"),
            "Uptime": uptime
        })

    if container_uptime_data:
        st.dataframe(container_uptime_data, use_container_width=True)
    else:
        st.info("Sem dados de criação ou tempo de execução.")

with col2:
    st.header("Detalhes Avançados das Imagens e Containers")

    image_details = []
    for image in client.images.list():
        tags = ', '.join(image.tags) if image.tags else 'sem tag'
        size_mb = round(image.attrs['Size'] / (1024 ** 2), 2)
        created_str = image.attrs['Created']
        created_dt = datetime.datetime.fromisoformat(created_str.replace("Z", "+00:00"))
        created_at = created_dt.strftime("%Y-%m-%d %H:%M:%S")
        image_details.append({
            "Tags": tags,
            "Tamanho (MB)": size_mb,
            "Criada em": created_at
        })

    if image_details:
        st.dataframe(image_details, use_container_width=True)
    else:
        st.info("Nenhuma imagem localizada.")

# Imagens não usadas
st.header("Imagens não utilizadas")
cmd = ['docker', 'images', '--filter', 'dangling=true', '--format', '{{.ID}} {{.Repository}}:{{.Tag}}']
output = subprocess.getoutput(" ".join(cmd)).strip().splitlines()
if output:
    for img in output:
        img_id = img.split()[0]
        col1, col2 = st.columns([6, 1])
        col1.markdown(f"`{img}`")
        if col2.button(f"Remover", key=img_id):
            subprocess.run(["docker", "rmi", img_id])
            st.experimental_rerun()
else:
    st.info("Nenhuma imagem dangling encontrada.")