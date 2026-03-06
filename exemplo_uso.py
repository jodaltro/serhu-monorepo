"""Exemplo de uso completo do Orchestrator com integração LLM (GPT-5.4)."""

import os
from dotenv import load_dotenv
from serhu_orchestrator.orchestrator import Orchestrator
from serhu_orchestrator.llm.openai_client import OpenAIClient
from serhu_orchestrator.personality.prompt_builder import build_system_prompt

load_dotenv()


def main():
    # 1. Criar Cliente LLM (GPT-5.4)
    print("🚀 Inicializando cliente OpenAI (GPT-5.4)...")
    
    llm_client = OpenAIClient(
        api_key=os.environ["OPENAI_API_KEY"],
        model=os.environ.get("OPENAI_MODEL", "gpt-5.4"),
    )
    print("✅ LLM client inicializado!\n")

    # 2. Criar ou carregar um Ser com LLM integrado
    print("🌟 Criando um novo Ser com suporte a LLM...")
    
    orch = Orchestrator(
        qdrant_url=os.environ["QDRANT_URL"],
        qdrant_api_key=os.environ["QDRANT_API_KEY"],
        supabase_url=os.environ["SUPABASE_URL"],
        supabase_key=os.environ["SUPABASE_KEY"],
        being_name="Estrela",
        language="pt",  # Idioma padrão do Ser
        working_memory_size=20,
        llm_client=llm_client,  # ← Integração da LLM!
    )
    
    being_id = orch.being_id
    print(f"✅ Ser criado! ID: {being_id}\n")

    # 3. Conversar com o Ser usando LLM (OPÇÃO A: chat() com extração automática)
    print("💬 Conversando com o Ser via LLM (com extração automática de traços)...\n")
    
    user_input_1 = "Olá! Me fale sobre você e o que te deixa curioso."
    print(f"👤 Usuário: {user_input_1}")
    
    being_response_1, context_1 = orch.chat(user_input_1, auto_traits=True)
    print(f"✨ Ser: {being_response_1}\n")
    print(f"  📊 Working memory agora tem {len(context_1.working)} entradas\n")

    # 4. Segunda conversa
    user_input_2 = "Que tipo de coisas você gostaria de aprender?"
    print(f"👤 Usuário: {user_input_2}")
    
    being_response_2, context_2 = orch.chat(user_input_2, auto_traits=True)
    print(f"✨ Ser: {being_response_2}\n")

    # 5. Ver personalidade evoluída (traits foram atualizados automaticamente)
    print("🎭 Estado da Personalidade (após LLM interactions):")
    p = orch.personality
    print(f"  - Nome: {p.name}")
    print(f"  - Idioma: {p.language}")
    print(f"  - Estágio cognitivo: {p.development.stage}")
    print(f"  - Conflito Erikson: {p.development.erikson_conflict}")
    print(f"  - Interações: {p.development.interaction_count}")
    print(f"  - Sociabilidade (HEXACO): {p.hexaco.sociability:.2f}")
    print(f"  - Curiosidade (HEXACO): {p.hexaco.inquisitiveness:.2f}")
    print(f"  - Excitabilidade Exploratória (TCI): {p.tci_temperament.exploratory_excitability:.2f}")
    print(f"  - Empatia (Caráter TCI): {p.tci_character.empathy:.2f}\n")

    # 6. OPÇÃO B: process_message() com trait_deltas manual (se preferir controle fino)
    print("🧬 Evoluindo traços manualmente (OPÇÃO B: process_message)...")
    ctx = orch.process_message(
        role="user",
        content="Você é realmente fascinante!",
        trait_deltas={
            "hexaco": {"inquisitiveness": 0.08, "sociability": 0.05},
            "tci_character": {"empathy": 0.03},
            "schwartz": {"universalism_nature": 0.02},
        },
    )
    print("✅ Traços atualizados manualmente\n")

    # 7. Consolidar memória
    print("🌙 Consolidando memória (twilight phase)...")
    archived = orch.consolidate()
    print(f"  Entradas arquivadas: {archived}\n")

    # 8. Ciclo de sono com LLM integration (semantização e beliefs enriquecidos)
    print("😴 Executando ciclo de sono com LLM...")
    sleep_result = orch.sleep(num_rollouts=100, svd_rank=8, seed=42)
    print(f"  ✓ Fatos extraídos: {len(sleep_result.facts_extracted)} (com LLM!)")
    print(f"  ✓ Hipóteses geradas: {len(sleep_result.hypotheses)}")
    print(f"  ✓ Novas crenças: {len(sleep_result.beliefs_added)} (com LLM!)")
    print(f"  ✓ Traits antes: {len(sleep_result.traits_before)} dimensões")
    print(f"  ✓ Traits depois: {len(sleep_result.traits_after)} dimensões\n")

    # 9. Gerar system prompt
    print("📜 System Prompt gerado:")
    print("=" * 60)
    prompt = orch.build_prompt()
    print(prompt[:500] + "...")  # Primeiros 500 chars
    print("=" * 60)

    print(f"\n✨ Exemplo concluído! Being ID para reusar: {being_id}")


if __name__ == "__main__":
    main()
