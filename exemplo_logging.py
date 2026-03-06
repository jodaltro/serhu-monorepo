#!/usr/bin/env python3
"""
exemplo_logging.py - Demonstrarä como usar logging no SerHu

Execute este script para ver os logs em ação:
    python exemplo_logging.py
"""

import logging
import logging.config
import sys

# ============================================================================
# 1. CONFIGURAR LOGGING
# ============================================================================

# Opção A: Usar arquivo logging.ini (recomendado para produção)
logging.config.fileConfig('logging.ini')

# Opção B: Configurar programaticamente (para desenvolvimento)
def setup_logging_basic(level=logging.INFO):
    """Configuração rápida de logging."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

# Descomente para usar configuração básica em vez de logging.ini
# setup_logging_basic(level=logging.DEBUG)


# ============================================================================
# 2. OBTER LOGGERS
# ============================================================================

logger_api = logging.getLogger('serhu_api')
logger_orchestrator = logging.getLogger('serhu_orchestrator')
logger_neural = logging.getLogger('serhu_orchestrator.sleep.neural_engine')
logger_personality = logging.getLogger('serhu_orchestrator.personality.personality_engine')


# ============================================================================
# 3. SIMULAR OPERAÇÕES DO SERHU COM LOGS
# ============================================================================

def example_api_initialization():
    """Simula inicialização da API."""
    print("\n" + "="*70)
    print("EXEMPLO 1: Inicialização da API")
    print("="*70)
    
    logger_api.info("🚀 SerHu API starting up...")
    logger_api.info("📌 Registering routes...")
    logger_api.info("🔓 CORS origins: ['http://localhost:3000', 'http://localhost:5173']")
    logger_api.info("✓ FastAPI application created successfully")


def example_being_creation():
    """Simula criação de um novo Being."""
    print("\n" + "="*70)
    print("EXEMPLO 2: Criação de um Novo Being")
    print("="*70)
    
    being_id = "abc123def456"
    name = "Luna"
    language = "pt"
    
    logger_api.info(f"📍 [POST /beings] Creating Being: name={name}, language={language}")
    logger_api.info(f"🆕 Creating new Being: name={name!r}, language={language!r}")
    
    logger_personality.info(f"✨ create_being: tabula rasa ~ id={being_id}, name={name!r}, lang={language}")
    logger_personality.debug(f"  → Personality persisted to relational memory")
    
    logger_api.info(f"✓ Being created: being_id={being_id}")


def example_chat():
    """Simula uma conversa com o Being."""
    print("\n" + "="*70)
    print("EXEMPLO 3: Chat com o Being")
    print("="*70)
    
    being_id = "abc123def456"
    user_message = "Hello, how are you?"
    
    logger_api.info(f"📍 [POST /beings/{being_id}/chat] User message: {user_message}...")
    logger_orchestrator.info(f"🗨️ chat: processing '{user_message}...'")
    logger_orchestrator.debug(f"  → Stage=preoperational, age=2.5m, max_tokens=150, temp=0.7")
    logger_orchestrator.debug(f"  → Generating response (neural engine)...")
    
    logger_neural.debug(f"🎯 generate_response: max_tokens=150")
    logger_neural.debug(f"  → Context tokens: 25")
    logger_neural.debug(f"  → Scored 45 patterns")
    logger_neural.debug(f"  ✓ Response: 'I am learning...'")
    
    response = "I am learning about the world"
    logger_orchestrator.debug(f"  → Response: '{response[:30]}...'")
    logger_orchestrator.debug(f"  → Extracting trait deltas...")
    logger_orchestrator.debug(f"  → Traits updated: ['tci_character', 'hexaco']")
    logger_orchestrator.info(f"✓ chat complete: response='{response[:30]}...'")
    logger_api.info(f"✓ Response generated: {response[:30]}... (stage=preoperational)")


def example_memory_operations():
    """Simula operações de memória."""
    print("\n" + "="*70)
    print("EXEMPLO 4: Operações de Memória")
    print("="*70)
    
    being_id = "abc123def456"
    
    logger_api.info(f"📍 [POST /beings/{being_id}/process] Processing message from user: Hello...")
    logger_orchestrator.debug(f"💬 add_interaction: user='Hello, world!'")
    logger_orchestrator.debug(f"  → Archiving 1 evicted entry")
    logger_orchestrator.debug(f"  → Retrieved 3 archival results")
    logger_orchestrator.debug(f"  → Retrieved 5 semantic facts")
    logger_api.debug(f"✓ Message processed: working_memory=4, archival=3, semantic_facts=5")


def example_sleep_cycle():
    """Simula um ciclo de sono."""
    print("\n" + "="*70)
    print("EXEMPLO 5: Sleep Cycle (Aprendizado)")
    print("="*70)
    
    being_id = "abc123def456"
    
    logger_api.info(f"📍 [POST /beings/{being_id}/sleep] Starting sleep cycle: num_rollouts=1000, svd_rank=8")
    logger_orchestrator.info(f"😴 sleep: starting continuous AIXI dreaming (num_rollouts=1000, svd_rank=8)")
    logger_orchestrator.debug(f"  → Retrieved 50 episodes for dreaming")
    logger_orchestrator.debug(f"  → Sleep worker started")
    
    logger_neural.info(f"🧠 train: 50 episodes")
    logger_neural.debug(f"  → Phase 1 (Tokenize): 2500 total tokens")
    logger_neural.debug(f"  → Phase 2 (TF-IDF): 345 unique tokens")
    logger_neural.debug(f"  → Phase 3 (Embeddings): 50 episode vectors")
    logger_neural.debug(f"  → Phase 4 (Attention): 50x50 matrix")
    logger_neural.debug(f"  → Phase 5 (Patterns): 120 bigrams, 45 trigrams")
    logger_neural.debug(f"  → Phase 6 (Personality-weighted): Scoring patterns")
    
    logger_orchestrator.info(f"  ✓ Sleep cycle complete: facts=12, beliefs=8, cycles=1")
    logger_api.info(f"✓ Sleep cycle started (running in background)")


def example_wake():
    """Simula despertar do sono."""
    print("\n" + "="*70)
    print("EXEMPLO 6: Wake (Resultado do Sleep)")
    print("="*70)
    
    being_id = "abc123def456"
    
    logger_api.info(f"📍 [POST /beings/{being_id}/wake] Waking Being from sleep (timeout=30s)")
    logger_orchestrator.info(f"⏰ wake: requesting stop (timeout=30s)")
    logger_orchestrator.info(f"✓ Being {being_id} woke up: facts=12, beliefs=8")
    logger_api.info(f"✓ Being woken: facts_extracted=12, beliefs_added=8, cycles_completed=1")


def example_consolidate():
    """Simula consolidação de memória."""
    print("\n" + "="*70)
    print("EXEMPLO 7: Consolidação de Memória")
    print("="*70)
    
    being_id = "abc123def456"
    
    logger_api.info(f"📍 [POST /beings/{being_id}/consolidate] Starting consolidation")
    logger_orchestrator.info(f"🌅 consolidate: archiving working memory")
    logger_orchestrator.info(f"✓ consolidation complete: 15 entries archived")
    logger_api.info(f"✓ Consolidation complete: 15 entries archived")


def example_visual_state():
    """Simula cálculo do estado visual."""
    print("\n" + "="*70)
    print("EXEMPLO 8: Estado Visual (Morfogênese)")
    print("="*70)
    
    being_id = "abc123def456"
    
    logger_api.info(f"📍 [GET /beings/{being_id}/visual] Computing visual state")
    logger_api.debug(f"✓ Visual state computed: color=HSL(250.5, 65.0%, 45.2%)")


def example_error_handling():
    """Simula tratamento de erros."""
    print("\n" + "="*70)
    print("EXEMPLO 9: Tratamento de Erros")
    print("="*70)
    
    being_id = "nonexistent_id"
    
    logger_api.info(f"📍 [GET /beings/{being_id}] Fetching Being summary")
    logger_api.error(f"✗ Being not found: {being_id}")
    logger_api.warning(f"🚨 404 error raised for being_id={being_id}")
    
    being_id = "abc123def456"
    
    logger_api.info(f"📍 [POST /beings/{being_id}/sleep] Starting sleep cycle")
    logger_orchestrator.error(f"✗ Sleep cycle error: Being is already sleeping. Call wake() first.")
    logger_api.error(f"✗ Sleep cycle error: Being is already sleeping")


# ============================================================================
# 4. MOSTRAR NÍVEIS DE LOG
# ============================================================================

def show_log_levels():
    """Demonstra diferentes níveis de logging."""
    print("\n" + "="*70)
    print("EXEMPLO 10: Diferentes Níveis de Logger")
    print("="*70)
    
    logger = logging.getLogger('serhu_orchestrator')
    
    logger.debug("ℹ️ DEBUG: Mensagem de debug (nível mais baixo, max verbosidade)")
    logger.info("ℹ️ INFO: Mensagem informativa (padrão)")
    logger.warning("⚠️ WARNING: Mensagem de aviso (problema potencial)")
    logger.error("❌ ERROR: Erro (operação falhou)")
    logger.critical("🔴 CRITICAL: Crítico (sistema pode estar comprometido)")


# ============================================================================
# 5. MAIN
# ============================================================================

def main():
    """Execute todos os exemplos."""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "EXEMPLOS DE LOGGING DO SERHU" + " "*27 + "║")
    print("╚" + "="*68 + "╝")
    
    try:
        example_api_initialization()
        example_being_creation()
        example_chat()
        example_memory_operations()
        example_sleep_cycle()
        example_wake()
        example_consolidate()
        example_visual_state()
        example_error_handling()
        show_log_levels()
        
        print("\n" + "="*70)
        print("✓ Todos os exemplos executados com sucesso!")
        print("="*70)
        print("\n📄 Logs também foram salvos em: serhu.log")
        print("📖 Para mais informações, veja: LOGGING.md")
        print("\n")
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.exception(f"Erro ao executar exemplos: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
