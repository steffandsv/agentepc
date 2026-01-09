#!/bin/bash

# Configurações Absolutas
PROJECT_DIR="/home/steff/agentepc"
SERVICE_NAME="agent-app.service"
LOG_FILE="$PROJECT_DIR/update.log"

# Função de Log
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> $LOG_FILE
}

log "Verificando integridade da realidade (GitHub)..."

cd $PROJECT_DIR || { log "Erro: Diretório não encontrado!"; exit 1; }

# 1. Busca a verdade remota sem tocar nos arquivos ainda
git fetch origin

# 2. Verifica se a realidade local difere da remota
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
    # Se já estamos perfeitos, não faz nada
    exit 0
fi

log "Divergência detectada. Impondo a vontade do GitHub ($REMOTE)..."

# 3. A MUDANÇA CRÍTICA: RESET --HARD
# Em vez de tentar mesclar (pull), destruímos qualquer alteração local
# e fazemos o código ser idêntico ao remote.
git reset --hard origin/main

if [ $? -ne 0 ]; then
    log "Falha crítica ao resetar o repositório."
    exit 1
fi

# 4. LIMPEZA DE ARTEFATOS (Opcional, mas recomendado)
# Remove arquivos não rastreados (como aqueles .pyc chatos que causaram o erro)
git clean -fd

# 5. BUILD (Sincroniza dependências)
log "Reconstruindo dependências (uv sync)..."
/home/steff/.local/bin/uv sync
if [ $? -ne 0 ]; then
    log "Erro ao sincronizar dependências via uv."
    exit 1
fi

# 6. DEPLOY (Reinicia o serviço)
log "Reiniciando a consciência do agente ($SERVICE_NAME)..."
sudo systemctl restart $SERVICE_NAME

log "Sincronização forçada concluída com sucesso."