"""Exemplo de uso completo do Orchestrator."""

import os
from dotenv import load_dotenv
from serhu_orchestrator.orchestrator import Orchestrator
from serhu_orchestrator.personality.prompt_builder import build_system_prompt

load_dotenv()


def main():
    # 1. Criar ou carregar um Ser
    print("🌟 Criando um novo Ser...")
    
    orch = Orchestrator(
        qdrant_url=os.environ["QDRANT_URL"],
        qdrant_api_key=os.environ["QDRANT_API_KEY"],
        supabase_url=os.environ["SUPABASE_URL"],
        supabase_key=os.environ["SUPABASE_KEY"],
        being_name="Estrela",
        language="pt",  # Idioma padrão do Ser
        working_memory_size=20,
    )
    
    being_id = orch.being_id
    print(f"✅ Ser criado! ID: {being_id}\n")

    # 2. Interagir
    print("💬 Conversando com o Ser...\n")
    
    messages = [
        ("user", "Olá! Me fale sobre você."),
        ("being", "Eu sou Estrela, um ser em desenvolvimento. Estou aprendendo sobre o mundo."),
        ("user", "O que te deixa curioso?"),
        ("being", "Estou curioso sobre as emoções humanas e como funcionam."),
    ]
    
    for role, content in messages:
        ctx = orch.process_message(role, content)
        print(f"[{role}] {content}")
    
    print(f"\n📊 Working memory size: {len(ctx.working)}")

    # 3. Evoluir traços baseado na interação
    print("\n🧬 Evoluindo traços...")
    ctx = orch.process_message(
        role="user",
        content="Você parece muito curiosa sobre o universo!",
        trait_deltas={
            "hexaco": {"inquisitiveness": 0.08, "sociability": 0.05},
            "tci_character": {"empathy": 0.03},
            "schwartz": {"universalism_nature": 0.02},
        },
    )

    # 4. Ver personalidade
    print("\n🎭 Estado da Personalidade:")
    p = orch.personality
    print(f"  - Nome: {p.name}")
    print(f"  - Idioma: {p.language}")
    print(f"  - Estágio cognitivo: {p.development.stage}")
    print(f"  - Conflito Erikson: {p.development.erikson_conflict}")
    print(f"  - Interações: {p.development.interaction_count}")
    print(f"  - Sociabilidade (HEXACO): {p.hexaco.sociability:.2f}")
    print(f"  - Curiosidade (HEXACO): {p.hexaco.inquisitiveness:.2f}")
    print(f"  - Excitabilidade Exploratória (TCI): {p.tci_temperament.exploratory_excitability:.2f}")
    print(f"  - Empatia (Caráter TCI): {p.tci_character.empathy:.2f}")

    # 5. Consolidar memória
    print("\n🌙 Consolidando memória (twilight)...")
    archived = orch.consolidate()
    print(f"  Entradas arquivadas: {archived}")

    # 6. Ciclo de sono
    print("\n😴 Executando ciclo de sono...")
    sleep_result = orch.sleep(num_rollouts=100, svd_rank=8, seed=42)
    print(f"  Fatos extraídos: {len(sleep_result.facts_extracted)}")
    print(f"  Hipóteses geradas: {len(sleep_result.hypotheses)}")
    print(f"  Novas crenças: {len(sleep_result.beliefs_added)}")
    print(f"  Traits antes: {len(sleep_result.traits_before)} dims")
    print(f"  Traits depois: {len(sleep_result.traits_after)} dims")

    # 7. Gerar system prompt
    print("\n📜 System Prompt gerado:")
    print("=" * 60)
    prompt = orch.build_prompt()
    print(prompt[:500] + "...")  # Primeiros 500 chars
    print("=" * 60)

    print(f"\n✨ Exemplo concluído! Being ID para reusar: {being_id}")


if __name__ == "__main__":
    main()
