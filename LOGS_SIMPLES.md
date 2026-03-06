# 📊 Logs SerHu - Guia Simplificado

## ✅ Logs Sempre Ativos

Os logs agora estão **sempre ativos automaticamente** em nível **INFO**.

### 🚀 Como Executar

```bash
# Simplesmente execute a API - logs já estarão ativos
cd packages/api
python -m uvicorn serhu_api.app:app --host 0.0.0.0 --port 8000
```

**Pronto!** Os logs aparecerão automaticamente no console e também em `serhu.log`.

## 📝 O Que Você Verá

### Logs Principais (INFO)

```
🚀 SerHu API starting up...
📍 [POST /beings] Creating Being: name='Luna'
✨ create_being: tabula rasa ~ id=abc123
✓ Being created successfully
🗨️ chat: processing 'Hello...'
✓ chat complete: response='hello...'
😴 sleep: starting continuous AIXI dreaming
✓ Sleep cycle complete: facts=12, beliefs=8
⏰ wake: requesting stop
✓ Being woke up: facts=12, beliefs=8
🌅 consolidate: archiving working memory
✓ consolidation complete: 15 entries
```

## 📂 Arquivo de Log

Todos os logs são salvos automaticamente em:
```
/home/jodaltro/jod_projetos/serhu-monorepo/serhu.log
```

### Ver Logs em Tempo Real

```bash
# Em outro terminal
tail -f serhu.log
```

### Filtrar por Tipo

```bash
# Apenas chat
tail -f serhu.log | grep "🗨️"

# Apenas sleep
tail -f serhu.log | grep "😴"

# Apenas criação de beings
tail -f serhu.log | grep "✨"

# Apenas erros
tail -f serhu.log | grep "ERROR"
```

## 🎯 Emojis Principais

| Emoji | O Que Significa |
|-------|----------------|
| 🚀 | API iniciando |
| 📍 | Request HTTP |
| ✨ | Novo Being criado |
| 🗨️ | Chat/conversa |
| 😴 | Sleep/aprendizado |
| ⏰ | Wake/despertar |
| 🌅 | Consolidação |
| ✓ | Sucesso |
| ✗ | Erro |

## ⚙️ Configuração

### Arquivo: `logging.ini`

Todos os módulos estão configurados em **INFO**:

```ini
[logger_root]
level=INFO

[logger_serhu_api]
level=INFO

[logger_serhu_orchestrator]
level=INFO
```

**Não precisa mudar nada!** Está pronto para uso.

## 🔧 Troubleshooting

### Não vejo logs

1. Verifique se `logging.ini` existe na raiz do projeto
2. Reinicie a aplicação

### Logs muito verbosos

Os logs agora estão em INFO (médio). Se quiser menos logs, edite `logging.ini` e mude para `WARNING`:

```ini
[logger_root]
level=WARNING
```

### Logs muito poucos

Se quiser mais detalhes (debug), mude para `DEBUG`:

```ini
[logger_root]
level=DEBUG
```

## ✅ Resumo

- ✅ Logs **sempre ativos** automaticamente
- ✅ Nível **INFO** (médio, ideal)
- ✅ Console + arquivo (`serhu.log`)
- ✅ Sem necessidade de variáveis de ambiente
- ✅ Sem necessidade de configuração adicional

**Simplesmente execute a API e os logs aparecerão!**
