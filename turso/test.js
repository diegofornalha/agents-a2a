/**
 * Script de teste para o Agente Turso
 */

const axios = require('axios');

const TURSO_URL = 'http://localhost:4243';
const TEST_AGENT_ID = 'test-agent-001';

// Cores para output
const colors = {
    reset: '\x1b[0m',
    green: '\x1b[32m',
    red: '\x1b[31m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m'
};

const log = {
    success: (msg) => console.log(`${colors.green}✓${colors.reset} ${msg}`),
    error: (msg) => console.log(`${colors.red}✗${colors.reset} ${msg}`),
    info: (msg) => console.log(`${colors.blue}ℹ${colors.reset} ${msg}`),
    warn: (msg) => console.log(`${colors.yellow}⚠${colors.reset} ${msg}`)
};

/**
 * Testes do Agente Turso
 */
class TursoAgentTests {
    constructor() {
        this.testResults = [];
    }
    
    async runAllTests() {
        console.log('\n🧪 Iniciando testes do Agente Turso...\n');
        
        // Verificar se o agente está rodando
        const isRunning = await this.checkHealth();
        if (!isRunning) {
            log.error('Agente Turso não está rodando na porta 4243');
            log.info('Inicie o agente com: npm start');
            return;
        }
        
        // Executar testes
        await this.testDiscovery();
        await this.testStore();
        await this.testRetrieve();
        await this.testQuery();
        await this.testBatch();
        await this.testSync();
        await this.testTTL();
        
        // Exibir resumo
        this.showSummary();
    }
    
    async checkHealth() {
        try {
            const response = await axios.get(`${TURSO_URL}/health`);
            if (response.data.status === 'active') {
                log.success('Health check passou - Agente está ativo');
                return true;
            }
            return false;
        } catch (error) {
            return false;
        }
    }
    
    async testDiscovery() {
        console.log('\n📡 Testando Discovery Endpoint...');
        try {
            const response = await axios.get(`${TURSO_URL}/discovery`);
            const data = response.data;
            
            if (data.name === 'TursoAgent' && data.port === 4243) {
                log.success('Discovery retornou metadados corretos');
                log.info(`Capacidades: ${data.capabilities.join(', ')}`);
                this.testResults.push({ test: 'Discovery', passed: true });
            } else {
                throw new Error('Metadados incorretos');
            }
        } catch (error) {
            log.error(`Discovery falhou: ${error.message}`);
            this.testResults.push({ test: 'Discovery', passed: false });
        }
    }
    
    async testStore() {
        console.log('\n💾 Testando Armazenamento de Dados...');
        try {
            const testData = {
                agent_id: TEST_AGENT_ID,
                key: 'test_campaign',
                value: {
                    name: 'Campanha Teste',
                    budget: 10000,
                    status: 'active'
                },
                metadata: {
                    type: 'campaign',
                    version: 1
                }
            };
            
            const response = await axios.post(`${TURSO_URL}/api/store`, testData);
            
            if (response.data.success && response.data.id) {
                log.success('Dados armazenados com sucesso');
                log.info(`ID gerado: ${response.data.id}`);
                this.testResults.push({ test: 'Store', passed: true });
            } else {
                throw new Error('Resposta inválida');
            }
        } catch (error) {
            log.error(`Store falhou: ${error.message}`);
            this.testResults.push({ test: 'Store', passed: false });
        }
    }
    
    async testRetrieve() {
        console.log('\n🔍 Testando Recuperação de Dados...');
        try {
            const response = await axios.get(
                `${TURSO_URL}/api/retrieve/${TEST_AGENT_ID}/test_campaign`
            );
            
            if (response.data.value && response.data.value.name === 'Campanha Teste') {
                log.success('Dados recuperados corretamente');
                log.info(`Campanha: ${response.data.value.name}`);
                log.info(`Budget: R$ ${response.data.value.budget}`);
                this.testResults.push({ test: 'Retrieve', passed: true });
            } else {
                throw new Error('Dados incorretos');
            }
        } catch (error) {
            log.error(`Retrieve falhou: ${error.message}`);
            this.testResults.push({ test: 'Retrieve', passed: false });
        }
    }
    
    async testQuery() {
        console.log('\n🔎 Testando Execução de Query...');
        try {
            const queryData = {
                sql: "SELECT COUNT(*) as total FROM agent_data WHERE agent_id = ?",
                args: [TEST_AGENT_ID]
            };
            
            const response = await axios.post(`${TURSO_URL}/api/query`, queryData);
            
            if (response.data.rows && response.data.rows.length > 0) {
                log.success('Query executada com sucesso');
                log.info(`Total de registros: ${response.data.rows[0].total}`);
                this.testResults.push({ test: 'Query', passed: true });
            } else {
                throw new Error('Query sem resultados');
            }
        } catch (error) {
            log.error(`Query falhou: ${error.message}`);
            this.testResults.push({ test: 'Query', passed: false });
        }
    }
    
    async testBatch() {
        console.log('\n⚡ Testando Operações em Lote...');
        try {
            const batchData = {
                operations: [
                    {
                        sql: "INSERT INTO agent_data (id, agent_id, key, value) VALUES (?, ?, ?, ?)",
                        args: ['batch1', TEST_AGENT_ID, 'batch_test_1', JSON.stringify({ test: 1 })]
                    },
                    {
                        sql: "INSERT INTO agent_data (id, agent_id, key, value) VALUES (?, ?, ?, ?)",
                        args: ['batch2', TEST_AGENT_ID, 'batch_test_2', JSON.stringify({ test: 2 })]
                    }
                ]
            };
            
            const response = await axios.post(`${TURSO_URL}/api/batch`, batchData);
            
            if (response.data.success && response.data.count === 2) {
                log.success('Operações em lote executadas com sucesso');
                log.info(`${response.data.count} operações processadas`);
                this.testResults.push({ test: 'Batch', passed: true });
            } else {
                throw new Error('Batch incompleto');
            }
        } catch (error) {
            log.error(`Batch falhou: ${error.message}`);
            this.testResults.push({ test: 'Batch', passed: false });
        }
    }
    
    async testSync() {
        console.log('\n🔄 Testando Sincronização...');
        try {
            const syncData = {
                source_agent: TEST_AGENT_ID,
                operation: 'memory_update',
                data: {
                    memories: [
                        { type: 'short_term', content: 'Test memory 1' },
                        { type: 'long_term', content: 'Test memory 2' }
                    ]
                }
            };
            
            const response = await axios.post(`${TURSO_URL}/api/sync`, syncData);
            
            if (response.data.success && response.data.sync_id) {
                log.success('Sincronização realizada com sucesso');
                log.info(`Sync ID: ${response.data.sync_id}`);
                this.testResults.push({ test: 'Sync', passed: true });
            } else {
                throw new Error('Sincronização falhou');
            }
        } catch (error) {
            log.error(`Sync falhou: ${error.message}`);
            this.testResults.push({ test: 'Sync', passed: false });
        }
    }
    
    async testTTL() {
        console.log('\n⏱️  Testando TTL (Time To Live)...');
        try {
            // Armazenar com TTL de 2 segundos
            const ttlData = {
                agent_id: TEST_AGENT_ID,
                key: 'ttl_test',
                value: { temp: 'data' },
                ttl: 2
            };
            
            await axios.post(`${TURSO_URL}/api/store`, ttlData);
            log.info('Dados armazenados com TTL de 2 segundos');
            
            // Verificar imediatamente
            const response1 = await axios.get(
                `${TURSO_URL}/api/retrieve/${TEST_AGENT_ID}/ttl_test`
            );
            
            if (response1.data.value) {
                log.success('Dados disponíveis imediatamente');
            }
            
            // Aguardar 3 segundos
            log.info('Aguardando 3 segundos para TTL expirar...');
            await new Promise(resolve => setTimeout(resolve, 3000));
            
            // Tentar recuperar após expiração
            try {
                await axios.get(`${TURSO_URL}/api/retrieve/${TEST_AGENT_ID}/ttl_test`);
                log.warn('Dados ainda disponíveis após TTL (pode ser cache)');
                this.testResults.push({ test: 'TTL', passed: false });
            } catch (error) {
                if (error.response && error.response.status === 404) {
                    log.success('TTL funcionou - dados expiraram corretamente');
                    this.testResults.push({ test: 'TTL', passed: true });
                } else {
                    throw error;
                }
            }
        } catch (error) {
            log.error(`TTL falhou: ${error.message}`);
            this.testResults.push({ test: 'TTL', passed: false });
        }
    }
    
    showSummary() {
        console.log('\n' + '='.repeat(50));
        console.log('📊 RESUMO DOS TESTES');
        console.log('='.repeat(50));
        
        const passed = this.testResults.filter(r => r.passed).length;
        const failed = this.testResults.filter(r => !r.passed).length;
        const total = this.testResults.length;
        
        this.testResults.forEach(result => {
            const status = result.passed 
                ? `${colors.green}✓ PASSOU${colors.reset}` 
                : `${colors.red}✗ FALHOU${colors.reset}`;
            console.log(`${result.test}: ${status}`);
        });
        
        console.log('='.repeat(50));
        console.log(`Total: ${total} | Passou: ${passed} | Falhou: ${failed}`);
        
        if (failed === 0) {
            console.log(`\n${colors.green}🎉 Todos os testes passaram!${colors.reset}\n`);
        } else {
            console.log(`\n${colors.yellow}⚠️  ${failed} teste(s) falharam${colors.reset}\n`);
        }
    }
}

// Executar testes
const tester = new TursoAgentTests();
tester.runAllTests().catch(error => {
    console.error('Erro ao executar testes:', error);
    process.exit(1);
});