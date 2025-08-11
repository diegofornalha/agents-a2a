#!/bin/bash
# Script para executar o Turso Agent no padrão A2A

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Iniciando Turso Agent (A2A)${NC}"

# Verificar se o uv está instalado
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ uv não está instalado. Instale com: curl -LsSf https://astral.sh/uv/install.sh | sh${NC}"
    exit 1
fi

# Instalar dependências
echo -e "${YELLOW}📦 Instalando dependências...${NC}"
uv sync

# Configurar variáveis de ambiente
export PORT=${PORT:-4243}
export AGENT_ID=${AGENT_ID:-"turso-agent-a2a"}
export AGENT_NAME=${AGENT_NAME:-"TursoAgent"}
export TURSO_DATABASE_URL=${TURSO_DATABASE_URL:-"file:local.db"}

# Exibir configuração
echo -e "${GREEN}✅ Configuração:${NC}"
echo -e "   Porta: ${PORT}"
echo -e "   Agent ID: ${AGENT_ID}"
echo -e "   Database: ${TURSO_DATABASE_URL}"
echo -e "   Padrão: A2A com SDK oficial"

# Executar o servidor
echo -e "${GREEN}🔄 Iniciando servidor...${NC}"
uv run python server.py