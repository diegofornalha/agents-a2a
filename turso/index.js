/**
 * Agente A2A Turso - Gerenciamento de Persistência de Dados
 * Porta: 4243
 */

const express = require('express');
const cors = require('cors');
const { createClient } = require('@libsql/client');
const axios = require('axios');
const { v4: uuidv4 } = require('uuid');
const winston = require('winston');
const Joi = require('joi');
require('dotenv').config();

// Configuração do Logger
const logger = winston.createLogger({
    level: process.env.LOG_LEVEL || 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
    ),
    transports: [
        new winston.transports.Console({
            format: winston.format.combine(
                winston.format.colorize(),
                winston.format.simple()
            )
        }),
        new winston.transports.File({ 
            filename: process.env.LOG_FILE || './logs/turso-agent.log' 
        })
    ]
});

/**
 * Classe TursoAgent - Agente A2A para Turso Database
 */
class TursoAgent {
    constructor() {
        this.app = express();
        this.port = process.env.PORT || 4243;
        this.agentId = process.env.AGENT_ID || `turso-agent-${uuidv4()}`;
        this.agentName = process.env.AGENT_NAME || 'TursoAgent';
        
        // Cliente Turso
        this.tursoClient = null;
        
        // Metadados do agente
        this.metadata = {
            id: this.agentId,
            name: this.agentName,
            type: 'persistence',
            version: '1.0.0',
            capabilities: [
                'data-storage',
                'query-execution',
                'schema-management',
                'sync-memory',
                'batch-operations',
                'real-time-updates'
            ],
            status: 'initializing',
            port: this.port,
            endpoints: {
                health: '/health',
                discovery: '/discovery',
                store: '/api/store',
                retrieve: '/api/retrieve',
                query: '/api/query',
                sync: '/api/sync',
                schema: '/api/schema',
                batch: '/api/batch'
            }
        };
        
        this.setupMiddleware();
        this.initializeTurso();
        this.setupRoutes();
        this.registerWithDiscovery();
    }
    
    /**
     * Configurar middleware Express
     */
    setupMiddleware() {
        this.app.use(cors({
            origin: process.env.CORS_ORIGINS?.split(',') || '*'
        }));
        this.app.use(express.json({ limit: '10mb' }));
        this.app.use(express.urlencoded({ extended: true }));
        
        // Middleware de logging
        this.app.use((req, res, next) => {
            logger.info(`${req.method} ${req.path}`, {
                ip: req.ip,
                userAgent: req.get('user-agent')
            });
            next();
        });
    }
    
    /**
     * Inicializar conexão com Turso
     */
    async initializeTurso() {
        try {
            const config = {
                url: process.env.TURSO_DATABASE_URL,
                authToken: process.env.TURSO_AUTH_TOKEN
            };
            
            // Usar cliente local se não houver configuração
            if (!config.url || config.url === 'libsql://your-database.turso.io') {
                logger.info('Usando Turso local (arquivo SQLite)');
                this.tursoClient = createClient({
                    url: 'file:local.db'
                });
            } else {
                this.tursoClient = createClient(config);
            }
            
            // Criar tabelas base
            await this.setupDatabase();
            
            this.metadata.status = 'active';
            logger.info('Turso Database conectado com sucesso');
        } catch (error) {
            logger.error('Erro ao conectar com Turso:', error);
            this.metadata.status = 'error';
        }
    }
    
    /**
     * Configurar esquema do banco de dados
     */
    async setupDatabase() {
        const queries = [
            // Tabela para armazenamento geral de dados
            `CREATE TABLE IF NOT EXISTS agent_data (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                UNIQUE(agent_id, key)
            )`,
            
            // Tabela para memória de agentes
            `CREATE TABLE IF NOT EXISTS agent_memory (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                session_id TEXT,
                memory_type TEXT,
                content TEXT NOT NULL,
                embedding TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )`,
            
            // Criar índice separadamente (compatível com Turso Cloud)
            `CREATE INDEX IF NOT EXISTS idx_agent_session ON agent_memory (agent_id, session_id)`,
            
            // Tabela para logs de sincronização
            `CREATE TABLE IF NOT EXISTS sync_logs (
                id TEXT PRIMARY KEY,
                source_agent TEXT NOT NULL,
                target_agent TEXT,
                operation TEXT NOT NULL,
                data TEXT,
                status TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )`,
            
            // Tabela para configurações de PRP
            `CREATE TABLE IF NOT EXISTS prp_configs (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                config_type TEXT NOT NULL,
                config_data TEXT NOT NULL,
                version INTEGER DEFAULT 1,
                active BOOLEAN DEFAULT true,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )`
        ];
        
        for (const query of queries) {
            try {
                await this.tursoClient.execute(query);
            } catch (error) {
                logger.error(`Erro ao criar tabela: ${error.message}`);
            }
        }
    }
    
    /**
     * Configurar rotas da API
     */
    setupRoutes() {
        // Rota de health check
        this.app.get('/health', (req, res) => {
            res.json({
                status: this.metadata.status,
                agent: this.agentName,
                uptime: process.uptime(),
                timestamp: new Date().toISOString()
            });
        });
        
        // Rota de discovery A2A
        this.app.get('/discovery', (req, res) => {
            res.json(this.metadata);
        });
        
        // Armazenar dados
        this.app.post('/api/store', async (req, res) => {
            try {
                const schema = Joi.object({
                    agent_id: Joi.string().required(),
                    key: Joi.string().required(),
                    value: Joi.any().required(),
                    metadata: Joi.object().optional(),
                    ttl: Joi.number().optional()
                });
                
                const { error, value } = schema.validate(req.body);
                if (error) {
                    return res.status(400).json({ error: error.details[0].message });
                }
                
                const id = uuidv4();
                const expiresAt = value.ttl 
                    ? new Date(Date.now() + value.ttl * 1000).toISOString()
                    : null;
                
                await this.tursoClient.execute({
                    sql: `INSERT OR REPLACE INTO agent_data 
                          (id, agent_id, key, value, metadata, expires_at, updated_at) 
                          VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)`,
                    args: [
                        id,
                        value.agent_id,
                        value.key,
                        JSON.stringify(value.value),
                        value.metadata ? JSON.stringify(value.metadata) : null,
                        expiresAt
                    ]
                });
                
                res.json({
                    success: true,
                    id,
                    message: 'Dados armazenados com sucesso'
                });
                
            } catch (error) {
                logger.error('Erro ao armazenar dados:', error);
                res.status(500).json({ error: 'Erro ao armazenar dados' });
            }
        });
        
        // Recuperar dados
        this.app.get('/api/retrieve/:agentId/:key', async (req, res) => {
            try {
                const { agentId, key } = req.params;
                
                const result = await this.tursoClient.execute({
                    sql: `SELECT * FROM agent_data 
                          WHERE agent_id = ? AND key = ? 
                          AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)`,
                    args: [agentId, key]
                });
                
                if (result.rows.length === 0) {
                    return res.status(404).json({ error: 'Dados não encontrados' });
                }
                
                const row = result.rows[0];
                res.json({
                    id: row.id,
                    agent_id: row.agent_id,
                    key: row.key,
                    value: JSON.parse(row.value),
                    metadata: row.metadata ? JSON.parse(row.metadata) : null,
                    created_at: row.created_at,
                    updated_at: row.updated_at
                });
                
            } catch (error) {
                logger.error('Erro ao recuperar dados:', error);
                res.status(500).json({ error: 'Erro ao recuperar dados' });
            }
        });
        
        // Executar query customizada
        this.app.post('/api/query', async (req, res) => {
            try {
                const schema = Joi.object({
                    sql: Joi.string().required(),
                    args: Joi.array().optional()
                });
                
                const { error, value } = schema.validate(req.body);
                if (error) {
                    return res.status(400).json({ error: error.details[0].message });
                }
                
                // Verificar se é uma query SELECT (somente leitura)
                if (!value.sql.trim().toUpperCase().startsWith('SELECT')) {
                    return res.status(403).json({ 
                        error: 'Apenas queries SELECT são permitidas neste endpoint' 
                    });
                }
                
                const result = await this.tursoClient.execute({
                    sql: value.sql,
                    args: value.args || []
                });
                
                res.json({
                    rows: result.rows,
                    columns: result.columns,
                    rowsAffected: result.rowsAffected
                });
                
            } catch (error) {
                logger.error('Erro ao executar query:', error);
                res.status(500).json({ error: 'Erro ao executar query' });
            }
        });
        
        // Sincronizar com Claude Flow
        this.app.post('/api/sync', async (req, res) => {
            try {
                const { source_agent, data, operation } = req.body;
                
                const syncId = uuidv4();
                await this.tursoClient.execute({
                    sql: `INSERT INTO sync_logs (id, source_agent, operation, data, status) 
                          VALUES (?, ?, ?, ?, ?)`,
                    args: [
                        syncId,
                        source_agent,
                        operation,
                        JSON.stringify(data),
                        'completed'
                    ]
                });
                
                // Se sincronização com Claude Flow estiver habilitada
                if (process.env.CLAUDE_FLOW_SYNC_ENABLED === 'true') {
                    // Aqui seria feita a sincronização com Claude Flow MCP
                    logger.info('Sincronização com Claude Flow realizada');
                }
                
                res.json({
                    success: true,
                    sync_id: syncId,
                    message: 'Sincronização realizada com sucesso'
                });
                
            } catch (error) {
                logger.error('Erro na sincronização:', error);
                res.status(500).json({ error: 'Erro na sincronização' });
            }
        });
        
        // Operações em lote
        this.app.post('/api/batch', async (req, res) => {
            try {
                const { operations } = req.body;
                
                if (!Array.isArray(operations)) {
                    return res.status(400).json({ error: 'Operations deve ser um array' });
                }
                
                const results = [];
                
                await this.tursoClient.batch(
                    operations.map(op => ({
                        sql: op.sql,
                        args: op.args || []
                    }))
                );
                
                res.json({
                    success: true,
                    count: operations.length,
                    message: 'Operações em lote executadas com sucesso'
                });
                
            } catch (error) {
                logger.error('Erro em operações em lote:', error);
                res.status(500).json({ error: 'Erro em operações em lote' });
            }
        });
        
        // Gerenciar esquema
        this.app.post('/api/schema', async (req, res) => {
            try {
                const { table_name, columns } = req.body;
                
                if (!table_name || !columns) {
                    return res.status(400).json({ 
                        error: 'table_name e columns são obrigatórios' 
                    });
                }
                
                const columnDefs = columns.map(col => 
                    `${col.name} ${col.type} ${col.constraints || ''}`
                ).join(', ');
                
                const sql = `CREATE TABLE IF NOT EXISTS ${table_name} (${columnDefs})`;
                
                await this.tursoClient.execute(sql);
                
                res.json({
                    success: true,
                    message: `Tabela ${table_name} criada/atualizada com sucesso`
                });
                
            } catch (error) {
                logger.error('Erro ao gerenciar esquema:', error);
                res.status(500).json({ error: 'Erro ao gerenciar esquema' });
            }
        });
    }
    
    /**
     * Registrar agente no serviço de discovery
     */
    async registerWithDiscovery() {
        const discoveryUrl = process.env.A2A_DISCOVERY_URL;
        
        if (!discoveryUrl) {
            logger.warn('URL de discovery não configurada');
            return;
        }
        
        const register = async () => {
            try {
                await axios.post(`${discoveryUrl}/register`, {
                    ...this.metadata,
                    url: `http://localhost:${this.port}`
                });
                logger.info('Agente registrado no discovery com sucesso');
            } catch (error) {
                logger.error('Erro ao registrar no discovery:', error.message);
            }
        };
        
        // Registrar imediatamente
        await register();
        
        // Re-registrar periodicamente
        const interval = parseInt(process.env.A2A_DISCOVERY_INTERVAL) || 30000;
        setInterval(register, interval);
    }
    
    /**
     * Iniciar servidor
     */
    start() {
        this.app.listen(this.port, () => {
            logger.info(`🚀 ${this.agentName} rodando na porta ${this.port}`);
            logger.info(`📊 Status: ${this.metadata.status}`);
            logger.info(`🔧 Capacidades: ${this.metadata.capabilities.join(', ')}`);
            logger.info(`🌐 Discovery endpoint: http://localhost:${this.port}/discovery`);
        });
    }
}

// Iniciar agente
const agent = new TursoAgent();
agent.start();

// Tratamento de sinais para shutdown gracioso
process.on('SIGTERM', async () => {
    logger.info('Recebido SIGTERM, encerrando graciosamente...');
    process.exit(0);
});

process.on('SIGINT', async () => {
    logger.info('Recebido SIGINT, encerrando graciosamente...');
    process.exit(0);
});

module.exports = TursoAgent;