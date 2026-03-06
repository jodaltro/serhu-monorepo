# 📋 SerHu Logging Guide

Este documento explica como ativar, visualiza e entender os logs do SerHu.

## Configuração Rápida

### 1. Ativar Logging (Python)

O logging está configurado automaticamente com níveis apropriados para cada módulo:

```python
import logging
import logging.config

# Carregar configuração de logging
logging.config.fileConfig('logging.ini')

# Agora todos os logs serão exibidos
logger = logging.getLogger(__name__)
logger.info("Log message")
```

### 2. Via Variável de Ambiente

Você pode definir o nível de logging via variável de ambiente:

```bash
# DEBUG (mais verbose)
LOG_LEVEL=DEBUG python -m uvicorn serhu_api.app:app

# INFO (padrão, recomendado)
LOG_LEVEL=INFO python -m uvicorn serhu_api.app:app

# WARNING (apenas avisos e erros)
LOG_LEVEL=WARNING python -m uvicorn serhu_api.app:app
```

### 3. Arquivo de Configuração

O arquivo `logging.ini` define:
- **Nível ROOT**: INFO
- **serhu_api**: INFO
- **serhu_orchestrator**: DEBUG (mais detalhes)
- **serhu_morphogenesis**: DEBUG
- **serhu_grpc**: INFO

Os logs são salvos em `serhu.log` e também exibidos no console.

## Entendendo os Logs

### Símbolos de Log

Os logs usam emojis para facilitar a leitura rápida:

| Emoji | Significado | Exemplos |
|-------|-------------|----------|
| 🚀 | Inicialização | `🚀 SerHu API starting up...` |
| 🛑 | Encerramento | `🛑 SerHu API shutting down...` |
| 📍 | Endpoint HTTP | `📍 [POST /beings] Creating Being` |
| 🆕 | Novo recurso | `🆕 Creating new Being: name='Luna'` |
| ♻️ | Cache/Reutilização | `♻️ Using cached Orchestrator` |
| 📂 | Carregamento | `📂 Loading Being from database` |
| ✓ | Sucesso | `✓ Being created successfully` |
| 🗨️ | Chat/Conversação | `🗨️ chat: processing 'Hello...'` |
| 😴 | Sleep/Sonho | `😴 sleep: starting continuous AIXI dreaming` |
| ⏰ | Wake/Despertar | `⏰ wake: requesting stop` |
| 🌅 | Consolidação | `🌅 consolidate: archiving working memory` |
| 💬 | Interação | `💬 add_interaction: user='Hello...'` |
| 🧠 | Treinamento Neural | `🧠 train: 50 episodes` |
| 🎯 | Geração de Resposta | `🎯 generate_response: max_tokens=50` |
| ✨ | Criação tabula rasa | `✨ create_being: tabula rasa ~ id=abc123...` |
| 📊 | Atualização de Traits | `📊 update_traits: applying 3 facet deltas` |
| 🧹 | Limpeza | `🧹 Clearing orchestrator cache` |
| 🔓 | CORS/Segurança | `🔓 CORS origins: ['http://localhost:3000']` |
| 🚨 | Erro/Aviso | `🚨 Wake timeout: sleep thread...` |
| ✗ | Falha | `✗ Sleep cycle error: ...` |

### Exemplos de Log Completo

#### Criação de um Novo Being

```
🆕 Creating new Being: name='Luna', language='pt'
✓ Being created successfully: being_id=abc123def456
✨ create_being: tabula rasa ~ id=abc123def456, name='Luna', lang=pt
  → Personality persisted to relational memory
```

#### Chat com o Being

```
📍 [POST /beings/abc123/chat] User message: Hello, how are you?...
🗨️ chat: processing 'Hello, how are you?...'
  → Being is sleeping, waking up...
⏰ wake: requesting stop (timeout=30s)
⏱️ Wake timeout: no results available
  → Stage=sensorimotor, age=0.0m, max_tokens=40, temp=0.9
  → Generating response (neural engine)...
🎯 generate_response: max_tokens=40
  → Engine untrained, fallback response
✓ Response generated: hello... (stage=sensorimotor)
✓ chat complete: response='hello...'
```

#### Sleep/Sonho

```
😴 sleep: starting continuous AIXI dreaming (num_rollouts=1000, svd_rank=8)
  → Retrieved 50 episodes for dreaming
  → Sleep worker started
🧠 train: 50 episodes
  → Phase 1 (Tokenize): 2500 total tokens
  → Phase 2 (TF-IDF): 345 unique tokens
  → Phase 3 (Embeddings): 50 episode vectors
  → Phase 4 (Attention): 50x50 matrix
  → Phase 5 (Patterns): 120 bigrams, 45 trigrams
✓ Sleep cycle complete: facts=12, beliefs=8, cycles=1
```

## Monitoramento em Tempo Real

### 1. Tail do Log File

```bash
# Terminal 1: Execute a aplicação
cd packages/api
LOG_LEVEL=DEBUG uvicorn serhu_api.app:app --host 0.0.0.0 --port 8000

# Terminal 2: Monitore os logs
tail -f /path/to/serhu.log | grep "🗨️\|😴\|✓"
```

### 2. Filtrar Específicos

```bash
# Apenas erros
tail -f serhu.log | grep "✗\|🚨\|ERROR"

# Apenas chat
tail -f serhu.log | grep "🗨️"

# Apenas sleep
tail -f serhu.log | grep "😴\|⏰"

# Apenas requests HTTP
tail -f serhu.log | grep "📍"
```

### 3. Com Timestamp

```bash
tail -f serhu.log | grep --line-buffered "ERROR\|WARNING"
```

## Customizando Níveis de Log

### Por Módulo (em código)

```python
import logging

# Apenas módulos específicos verbose
logging.getLogger('serhu_orchestrator').setLevel(logging.DEBUG)
logging.getLogger('serhu_api').setLevel(logging.INFO)
```

### Via Arquivo logging.ini

Edit `logging.ini` para ajustar níveis:

```ini
[logger_serhu_orchestrator]
level=DEBUG  # Mudar para DEBUG, INFO, WARNING, ERROR
```

## Estrutura de Logs por Camada

### 🔴 API Layer (serhu_api/)

```
📍 [POST /beings/id/chat] User message...
✓ Response generated: ...
```

**Nível**: INFO (principais operações), DEBUG (detalhes)

### 🔴 Orchestrator Layer (serhu_orchestrator/)

```
🗨️ chat: processing '...'
✓ chat complete: response='...'
😴 sleep: starting continuous AIXI dreaming
```

**Nível**: DEBUG (muito detalhado sobre operações)

### 🔴 Memory Layer (serhu_orchestrator/memory/)

```
💬 add_interaction: user='...'
  → Archiving 2 evicted entries
  → Retrieved 3 archival results
```

**Nível**: DEBUG (detalhes de memória)

### 🔴 Sleep/Neural Layer (serhu_orchestrator/sleep/)

```
🧠 train: 50 episodes
  → Phase 1 (Tokenize): 2500 tokens
  → Phase 5 (Patterns): 120 bigrams
```

**Nível**: DEBUG (detalhes de aprendizado)

### 🔴 Personality Layer (serhu_orchestrator/personality/)

```
✨ create_being: tabula rasa ~ id=...
📊 update_traits: applying 3 facet deltas
```

**Nível**: INFO (eventos principais), DEBUG (detalhes)

## Troubleshooting

### 1. Não vejo logs

**Solução**: Verifique se `logging.ini` está no diretório correto:

```bash
# Verificar localização
ls -la logging.ini

# Ou especifique o caminho
LOG_CONFIG=/path/to/logging.ini python app.py
```

### 2. Muitos logs (INFO/DEBUG)

**Solução**: Aumentar o nível mínimo:

```bash
LOG_LEVEL=WARNING python app.py
```

Ou editar `logging.ini`:

```ini
[logger_serhu_orchestrator]
level=WARNING
```

### 3. Log File muito grande

**Solução**: Configure rotação de logs em `logging.ini`:

```ini
[handler_fileHandler]
class=handlers.RotatingFileHandler
args=('serhu.log', 'a', 10485760, 5)  # 10MB, 5 backups
```

## Integração com Ferramentas

### ELK Stack (Elasticsearch + Kibana)

Para enviar logs ao Elasticsearch, adicione handler:

```ini
[handler_elasticsearchHandler]
class=pythonjsonlogger.jsonlogger.JsonFormatter
```

### Splunk

Configure via `logging.json` ou environment variables.

### CloudWatch (AWS)

```python
import watchtower
handler = watchtower.CloudWatchLogHandler()
logger.addHandler(handler)
```

## Performance

### Impacto de Logging

- **INFO**: ~1-2% overhead
- **DEBUG**: ~3-5% overhead (recomendado apenas para desenvolvimento)
- **WARNING**: <1% overhead

Para máxima performance em produção:

```ini
[logger_root]
level=WARNING
```

## Resumo

| Tarefa | Comando |
|--------|---------|
| Ver todos os logs | `tail -f serhu.log` |
| Apenas erros | `tail -f serhu.log \| grep "ERROR\|✗\|🚨"` |
| Chat apenas | `tail -f serhu.log \| grep "🗨️\|chat"` |
| Sleep apenas | `tail -f serhu.log \| grep "😴\|⏰\|sleep"` |
| Debug máximo | `LOG_LEVEL=DEBUG python app.py` |
| Production | `LOG_LEVEL=WARNING python app.py` |

---

**Última atualização**: Março 2026  
**Versão SerHu**: 0.1.0
