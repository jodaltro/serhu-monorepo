# 🌍 Suporte Multilíngue - SerHu Orchestrator

O SerHu agora suporta **múltiplos idiomas** padrão para cada Ser. O idioma é configurado na criação e persiste através de toda a interação, desde a geração de prompts até o armazenamento de personalidade.

## Idiomas Suportados

- 🇬🇧 **English** (`en`) - Padrão
- 🇧🇷 **Português** (`pt`)
- 🇪🇸 **Español** (`es`)
- 🇫🇷 **Français** (`fr`)

## Por que Isso Importa?

Quando um Ser é criado em um idioma, **tudo** é gerado nesse idioma:

1. **System Prompts**: Instruções Piaget (capacidades/limitações)
2. **Erikson Conflicts**: Descrição do conflito psicossocial atual
3. **Respostas do LLM**: O modelo receberá instruções no idioma correto
4. **Memória Conceitual**: Crenças e fatos são armazenados no contexto do idioma

## Como Usar

### 1️⃣ Criar um Ser em um Idioma Específico

```python
from serhu_orchestrator.orchestrator import Orchestrator

# Criar um Ser em português
orch = Orchestrator(
    qdrant_url="...",
    qdrant_api_key="...",
    supabase_url="...",
    supabase_key="...",
    being_name="Lua",
    language="pt",  # ← Define o idioma
)

print(f"Ser criado em: {orch.personality.language}")  # Output: "pt"
```

### 2️⃣ Verificar o Idioma de um Ser

```python
personality = orch.personality
print(f"Idioma padrão: {personality.language}")  # Saída: "pt"
```

### 3️⃣ Ver o Prompt no Idioma Correto

```python
from serhu_orchestrator.personality.prompt_builder import build_system_prompt

prompt = build_system_prompt(orch.personality)
print(prompt)

# Se language="pt", você verá:
# - "Você está navegando CONFIANÇA vs. DESCONFIANÇA..."
# - "Reagir a estímulos imediatos..."
# - etc.

# Se language="en", você verá:
# - "You are navigating TRUST vs. MISTRUST..."
# - "React to immediate stimuli..."
# - etc.
```

### 4️⃣ Carregar um Ser Existente

O idioma é persistido automaticamente no banco de dados:

```python
# Um Ser criado em português...
orch1 = Orchestrator(
    being_name="Estrela",
    language="pt",
    ...
)
being_id = orch1.being_id  # "abc123..."

# ...mais tarde, quando carregado, mantém o idioma português
orch2 = Orchestrator(
    being_id=being_id,  # Carrega "Estrela"
    ...
)

assert orch2.personality.language == "pt"  # ✅ Mesmo idioma!
```

## Exemplo Prático: Múltiplos Seres

Veja [exemplo_multilingue.py](exemplo_multilingue.py) para criar Seres em múltiplos idiomas:

```bash
python exemplo_multilingue.py
```

Isso criará:
- `Luna` em English
- `Estrela` em Portuguese
- `Sirius` em Spanish
- `Lua` em French

## Como Funciona Internamente

### 1. Armazenamento da Preferência

O campo `language` é armazenado na `PersonalityState`:

```python
class PersonalityState(BaseModel):
    being_id: str
    name: str
    language: str = "en"  # ← Campo padrão
    # ... outros campos ...
```

### 2. Recuperação de Traduções

O `prompt_builder.py` consulta `i18n.py` para obter conteúdo traduzido:

```python
# Em prompt_builder.py
caps = get_stage_capabilities(language, stage)  # Busca no idioma correto
erikson_desc = get_erikson_description(language, conflict)  # Idem
```

### 3. Arquivo de Traduções

Todas as traduções estão em [i18n.py](packages/orchestrator/src/serhu_orchestrator/personality/i18n.py):

```python
STAGE_CAPABILITIES = {
    "en": { ... },
    "pt": { ... },
    "es": { ... },
    "fr": { ... },
}

ERIKSON_DESCRIPTIONS = {
    "en": { ... },
    "pt": { ... },
    "es": { ... },
    "fr": { ... },
}
```

## Adicionando Novos Idiomas

Para adicionar um novo idioma (ex: Italiano `it`):

### 1. Edite `i18n.py`

```python
STAGE_CAPABILITIES = {
    "en": { ... },
    "pt": { ... },
    "es": { ... },
    "fr": { ... },
    "it": {  # ← Novo idioma
        "sensorimotor": {
            "can": "Reagire agli stimoli immediati...",
            "cannot": "Usare simboli o metafore...",
            "language": "Molto semplice, frasi brevi...",
        },
        # ... outros stages ...
    },
}

ERIKSON_DESCRIPTIONS = {
    "en": { ... },
    "pt": { ... },
    "es": { ... },
    "fr": { ... },
    "it": {  # ← Novo idioma
        "trust_vs_mistrust": "Stai navigando FIDUCIA vs. SFIDUCIA...",
        # ... outros conflitos ...
    },
}
```

### 2. Teste o Novo Idioma

```python
orch = Orchestrator(
    being_name="Giuseppe",
    language="it",  # ← Novo idioma
    ...
)
```

## Casos de Uso

### 🌐 Aplicação Multilíngue
Crie Seres em português para usuários brasileiros, em espanhol para latino-americanos, etc.

### 🎓 Educação
Um Ser pode ser criado no idioma de ensino de uma criança.

### 🤝 Suporte Localizado
Cada Ser "fala" no idioma do seu usuário, personalizando a experiência.

### 🧠 Pesquisa
Estude como diferentes idiomas afetam o desenvolvimento cognitivo simulado.

## Testes

Para validar o suporte a idiomas:

```bash
pytest packages/orchestrator/tests/unit/test_language_support.py -v
```

Testes cobertos:
- ✅ Idioma padrão (English)
- ✅ Idiomas customizados
- ✅ Capacidades Piaget traduzidas
- ✅ Conflitos Erikson traduzidos
- ✅ Persistência de idioma
- ✅ Fallback para English se idioma desconhecido

## ⚠️ Notas Importantes

1. **Idioma é fixo após criação**: Se um Ser é criado em português, permanecerá em português. Não há suporte para mudança dinâmica de idioma (por design, para consistência).

2. **Compatibilidade com LLMs**: O system prompt é gerado no idioma do Ser, então o LLM deve ser instruído nesse idioma. Recomenda-se usar modelos multilíngues (ChatGPT, Claude, etc.).

3. **Validação**: O sistema não valida se o `language` é um idioma suportado, mas faz fallback para English automaticamente.

## 📚 Referências

- [Arquivo i18n.py](packages/orchestrator/src/serhu_orchestrator/personality/i18n.py) - Todas as traduções
- [Teste de Language Support](packages/orchestrator/tests/unit/test_language_support.py) - Validação
- [Exemplo Multilíngue](exemplo_multilingue.py) - Demonstração prática
