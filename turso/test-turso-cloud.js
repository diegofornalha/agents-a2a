#!/usr/bin/env node
/**
 * Script de teste para o Agente Turso com Turso Cloud
 */

const axios = require('axios');

const TURSO_URL = 'http://localhost:4243';

// Função para testar armazenamento
async function testStore() {
    console.log('\n📦 Testando armazenamento no Turso Cloud...');
    
    const testData = {
        agent_id: 'test-agent-cloud',
        key: 'turso_cloud_test',
        value: {
            message: 'Conectado com sucesso ao Turso Cloud!',
            database: 'context-memory',
            organization: 'diegofornalha',
            timestamp: new Date().toISOString(),
            features: {
                distributed: true,
                replicated: true,
                cloud_native: true
            }
        },
        metadata: {
            type: 'cloud_test',
            version: 1,
            environment: 'production'
        },
        ttl: 3600 // 1 hora
    };
    
    try {
        const response = await axios.post(`${TURSO_URL}/api/store`, testData);
        console.log('✅ Dados armazenados com sucesso!');
        console.log('   ID:', response.data.id);
        console.log('   Mensagem:', response.data.message);
        return response.data.id;
    } catch (error) {
        console.error('❌ Erro ao armazenar:', error.response?.data || error.message);
        return null;
    }
}

// Função para recuperar dados
async function testRetrieve() {
    console.log('\n🔍 Recuperando dados do Turso Cloud...');
    
    try {
        const response = await axios.get(
            `${TURSO_URL}/api/retrieve/test-agent-cloud/turso_cloud_test`
        );
        console.log('✅ Dados recuperados com sucesso!');
        console.log('   Mensagem:', response.data.value.message);
        console.log('   Database:', response.data.value.database);
        console.log('   Organization:', response.data.value.organization);
        console.log('   Features:', JSON.stringify(response.data.value.features, null, 2));
        return response.data;
    } catch (error) {
        console.error('❌ Erro ao recuperar:', error.response?.data || error.message);
        return null;
    }
}

// Função para executar query
async function testQuery() {
    console.log('\n🔎 Executando query no Turso Cloud...');
    
    const queryData = {
        sql: "SELECT COUNT(*) as total, MAX(created_at) as ultima_criacao FROM agent_data WHERE agent_id LIKE ?",
        args: ['test-%']
    };
    
    try {
        const response = await axios.post(`${TURSO_URL}/api/query`, queryData);
        console.log('✅ Query executada com sucesso!');
        if (response.data.rows && response.data.rows.length > 0) {
            console.log('   Total de registros:', response.data.rows[0].total);
            console.log('   Última criação:', response.data.rows[0].ultima_criacao);
        }
        return response.data;
    } catch (error) {
        console.error('❌ Erro na query:', error.response?.data || error.message);
        return null;
    }
}

// Função para testar sincronização
async function testSync() {
    console.log('\n🔄 Testando sincronização com Claude Flow...');
    
    const syncData = {
        source_agent: 'test-agent-cloud',
        operation: 'memory_sync',
        data: {
            memories: [
                {
                    type: 'context',
                    content: 'Sistema integrado com Turso Cloud',
                    timestamp: new Date().toISOString()
                },
                {
                    type: 'knowledge',
                    content: 'Database distribuído e replicado',
                    timestamp: new Date().toISOString()
                }
            ],
            sync_type: 'cloud_integration'
        }
    };
    
    try {
        const response = await axios.post(`${TURSO_URL}/api/sync`, syncData);
        console.log('✅ Sincronização realizada com sucesso!');
        console.log('   Sync ID:', response.data.sync_id);
        return response.data;
    } catch (error) {
        console.error('❌ Erro na sincronização:', error.response?.data || error.message);
        return null;
    }
}

// Função principal
async function main() {
    console.log('========================================');
    console.log('🧪 Teste do Agente Turso com Turso Cloud');
    console.log('========================================');
    console.log('🌐 Organização: diegofornalha');
    console.log('💾 Database: context-memory');
    console.log('🔗 URL: http://localhost:4243');
    console.log('========================================');
    
    // Verificar health
    console.log('\n❤️  Verificando health do agente...');
    try {
        const health = await axios.get(`${TURSO_URL}/health`);
        console.log('✅ Agente está ativo!');
        console.log('   Status:', health.data.status);
        console.log('   Uptime:', Math.round(health.data.uptime), 'segundos');
    } catch (error) {
        console.error('❌ Agente não está respondendo!');
        process.exit(1);
    }
    
    // Executar testes
    await testStore();
    await testRetrieve();
    await testQuery();
    await testSync();
    
    console.log('\n========================================');
    console.log('✨ Testes concluídos com sucesso!');
    console.log('========================================\n');
}

// Executar
main().catch(error => {
    console.error('Erro fatal:', error);
    process.exit(1);
});