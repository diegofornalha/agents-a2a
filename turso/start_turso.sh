#!/bin/bash
# Script de inicialização do Turso Agent

echo "🚀 Iniciando Turso Agent..."

# Navegar para o diretório do Turso
cd /Users/agents/Desktop/claude-20x/agents-a2a/.conductor/hangzhou/turso

# Usar uv para executar com as dependências corretas
uv run python server.py