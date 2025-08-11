# Agente A2A Turso

## 📋 Descrição

O **Agente Turso** é um componente especializado do sistema A2A responsável pelo gerenciamento de persistência de dados usando Turso Database. Ele fornece uma interface unificada para armazenamento, recuperação e sincronização de dados entre agentes.

## 🚀 Características

- **Persistência Distribuída**: Armazenamento confiável com Turso Database
- **API RESTful**: Interface HTTP completa para operações de dados
- **Sincronização com Claude Flow**: Integração nativa com memória persistente
- **Operações em Lote**: Suporte para operações múltiplas em uma única transação
- **Cache Inteligente**: TTL configurável para dados temporários
- **Discovery A2A**: Auto-registro no sistema de descoberta de agentes

## 📦 Instalação

### Pré-requisitos

- Node.js 18+
- NPM ou Yarn
- Conta Turso (opcional, pode usar SQLite local)

### Configuração

1. **Instalar dependências:**
```bash
cd prp-crewai-system/agents/turso
npm install
```

2. **Configurar variáveis de ambiente:**
```bash
cp .env.example .env
# Editar .env com suas configurações
```

3. **Iniciar o agente:**
```bash
npm start
# ou em modo desenvolvimento
npm run dev
```

## 🔧 Configuração

### Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|---------|
| `PORT` | Porta do servidor | 4243 |
| `AGENT_NAME` | Nome do agente | TursoAgent |
| `TURSO_DATABASE_URL` | URL do banco Turso | file:local.db |
| `TURSO_AUTH_TOKEN` | Token de autenticação | - |
| `A2A_DISCOVERY_URL` | URL do serviço discovery | http://localhost:4240 |
| `CLAUDE_FLOW_SYNC_ENABLED` | Habilitar sync com Claude Flow | true |

## 📡 API Endpoints

### Health Check
```http
GET /health
```
Retorna o status de saúde do agente.

### Discovery
```http
GET /discovery
```
Retorna metadados do agente para o sistema A2A.

### Armazenar Dados
```http
POST /api/store
Content-Type: application/json

{
  "agent_id": "estrategista-001",
  "key": "campaign_data",
  "value": {
    "name": "Black Friday 2024",
    "budget": 50000
  },
  "metadata": {
    "type": "campaign",
    "version": 1
  },
  "ttl": 3600
}
```

### Recuperar Dados
```http
GET /api/retrieve/{agent_id}/{key}
```

### Executar Query
```http
POST /api/query
Content-Type: application/json

{
  "sql": "SELECT * FROM agent_data WHERE agent_id = ?",
  "args": ["estrategista-001"]
}
```

### Sincronizar com Claude Flow
```http
POST /api/sync
Content-Type: application/json

{
  "source_agent": "estrategista-001",
  "operation": "memory_update",
  "data": {
    "memories": [...]
  }
}
```

### Operações em Lote
```http
POST /api/batch
Content-Type: application/json

{
  "operations": [
    {
      "sql": "INSERT INTO agent_data (id, agent_id, key, value) VALUES (?, ?, ?, ?)",
      "args": ["id1", "agent1", "key1", "value1"]
    },
    {
      "sql": "UPDATE agent_data SET value = ? WHERE id = ?",
      "args": ["new_value", "id2"]
    }
  ]
}
```

## 🔌 Integração com Outros Agentes

### Exemplo: Estrategista salvando dados de campanha

```javascript
const axios = require('axios');

class EstrategistaAgent {
  async saveCampaignData(campaign) {
    try {
      const response = await axios.post('http://localhost:4243/api/store', {
        agent_id: this.agentId,
        key: `campaign_${campaign.id}`,
        value: campaign,
        metadata: {
          type: 'campaign',
          created_by: 'estrategista',
          timestamp: new Date().toISOString()
        },
        ttl: 86400 // 24 horas
      });
      
      console.log('Campanha salva:', response.data);
    } catch (error) {
      console.error('Erro ao salvar campanha:', error);
    }
  }
  
  async getCampaignData(campaignId) {
    try {
      const response = await axios.get(
        `http://localhost:4243/api/retrieve/${this.agentId}/campaign_${campaignId}`
      );
      
      return response.data.value;
    } catch (error) {
      console.error('Erro ao recuperar campanha:', error);
      return null;
    }
  }
}
```

### Exemplo: Sincronização com Claude Flow

```javascript
const syncWithClaudeFlow = async (agentMemories) => {
  try {
    const response = await axios.post('http://localhost:4243/api/sync', {
      source_agent: 'orchestrator',
      operation: 'memory_sync',
      data: {
        memories: agentMemories,
        timestamp: new Date().toISOString()
      }
    });
    
    console.log('Sincronização concluída:', response.data);
  } catch (error) {
    console.error('Erro na sincronização:', error);
  }
};
```

## 🗄️ Esquema do Banco de Dados

### Tabela: agent_data
Armazena dados gerais dos agentes com suporte a TTL.

```sql
CREATE TABLE agent_data (
  id TEXT PRIMARY KEY,
  agent_id TEXT NOT NULL,
  key TEXT NOT NULL,
  value TEXT NOT NULL,
  metadata TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  expires_at DATETIME,
  UNIQUE(agent_id, key)
)
```

### Tabela: agent_memory
Armazena memórias e contexto dos agentes.

```sql
CREATE TABLE agent_memory (
  id TEXT PRIMARY KEY,
  agent_id TEXT NOT NULL,
  session_id TEXT,
  memory_type TEXT,
  content TEXT NOT NULL,
  embedding TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

### Tabela: sync_logs
Registra operações de sincronização.

```sql
CREATE TABLE sync_logs (
  id TEXT PRIMARY KEY,
  source_agent TEXT NOT NULL,
  target_agent TEXT,
  operation TEXT NOT NULL,
  data TEXT,
  status TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

### Tabela: prp_configs
Configurações específicas de PRP.

```sql
CREATE TABLE prp_configs (
  id TEXT PRIMARY KEY,
  agent_id TEXT NOT NULL,
  config_type TEXT NOT NULL,
  config_data TEXT NOT NULL,
  version INTEGER DEFAULT 1,
  active BOOLEAN DEFAULT true,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

## 🐳 Docker

### Build da imagem
```bash
docker build -t turso-agent:latest .
```

### Executar container
```bash
docker run -d \
  --name turso-agent \
  -p 4243:4243 \
  -e TURSO_DATABASE_URL=your-url \
  -e TURSO_AUTH_TOKEN=your-token \
  turso-agent:latest
```

## 🧪 Testes

```bash
# Executar testes
npm test

# Testes com cobertura
npm run test:coverage
```

## 📊 Monitoramento

O agente expõe métricas e logs que podem ser monitorados:

- **Logs**: Arquivo em `./logs/turso-agent.log`
- **Health Check**: `http://localhost:4243/health`
- **Métricas**: Integração com Prometheus (futuro)

## 🔒 Segurança

- Suporte a JWT para autenticação (configurável)
- API Keys para autorização
- Validação de entrada com Joi
- Queries parametrizadas para prevenir SQL injection
- CORS configurável

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

MIT License - veja o arquivo LICENSE para detalhes.

## 🆘 Suporte

Para suporte, abra uma issue no repositório ou contate a equipe de desenvolvimento.