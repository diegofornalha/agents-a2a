# INSTRUÇÕES IMPORTANTES

## ⚠️ REGRAS PARA ESTE DIRETÓRIO

### NÃO CRIAR ARQUIVOS DESNECESSÁRIOS
Este diretório (`/Users/agents/Desktop/claude-20x/agents-a2a/.conductor/hangzhou/`) contém apenas os componentes essenciais do sistema A2A. 

**PROIBIDO:**
- ❌ Criar arquivos de teste na raiz
- ❌ Adicionar scripts auxiliares desnecessários
- ❌ Gerar arquivos de validação ou descoberta
- ❌ Criar componentes que não sejam explicitamente solicitados
- ❌ Adicionar arquivos de cache ou temporários

**PERMITIDO APENAS:**
- ✅ Modificar arquivos existentes quando necessário
- ✅ Trabalhar dentro dos subdiretórios dos agentes (como `marvin/`)
- ✅ Criar arquivos SOMENTE quando explicitamente solicitado pelo usuário

## 📁 ESTRUTURA AUTORIZADA

```
hangzhou/
├── CLAUDE.md           # Este arquivo de instruções
├── a2a-python/         # SDK Python do A2A (manter)
└── marvin/             # Agente Marvin (manter)
    ├── .env            # Configurações do ambiente
    ├── .venv/          # Ambiente virtual Python
    └── [arquivos do Marvin]
```

## 🎯 PRINCÍPIO FUNDAMENTAL
**Mantenha este diretório LIMPO e ORGANIZADO.** Apenas componentes funcionais e em uso devem existir aqui.

---
*Última atualização: 11 de Agosto de 2025*