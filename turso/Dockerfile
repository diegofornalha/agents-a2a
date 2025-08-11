# Dockerfile para Agente A2A Turso
FROM node:18-alpine

# Criar diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apk add --no-cache \
    python3 \
    make \
    g++ \
    sqlite

# Copiar arquivos de configuração
COPY package*.json ./

# Instalar dependências
RUN npm ci --only=production

# Copiar código fonte
COPY . .

# Criar diretório de logs
RUN mkdir -p logs

# Expor porta
EXPOSE 4243

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:4243/health', (r) => {r.statusCode === 200 ? process.exit(0) : process.exit(1)})"

# Comando de inicialização
CMD ["node", "index.js"]