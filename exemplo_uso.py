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
        language="pt",  # Set language to Portuguese
        working_memory_size=20,
    )
    
    being_id = orch.being_id
    print(f"✅ Ser criado! ID: {being_id}\n")

    # 2. Interagir
    print("💬 Conversando com o Ser...\n")
    
    messages = [
        ("user", "Olá! Me fale sobre você."),
        ("assistant", "Eu sou Estrela, um ser em desenvolvimento. Estou aprendendo sobre o mundo."),
        ("user", "O que te deixa curioso?"),
        ("assistant", "Estou curioso sobre as emoções humanas e como funcionam."),
    ]
    
    for role, content in messages:
        ctx = orch.process_message(role, content)
        print(f"[{role}] {content}")
    
    print(f"\n📊 Working memory size: {len(ctx.working)}")

    # 3. Ver personalidade
    print("\n🎭 Estado da Personalidade:")
    p = orch.personality
    print(f"  - Nome: {p.name}")
    print(f"  - Idioma: {p.language}")
    print(f"  - Estágio cognitivo: {p.development.stage}")
    print(f"  - Interações: {p.development.interaction_count}")
    print(f"  - Sociabilidade (HEXACO): {p.hexaco.sociability:.2f}")
    print(f"  - Excitabilidade Exploratória (TCI): {p.tci_temperament.exploratory_excitability:.2f}")
    print(f"  - Empatia (Caráter TCI): {p.tci_character.empathy:.2f}")

    # 4. Consolidar memória
    print("\n🌙 Consolidando memória (twilight)...")
    summary = orch.consolidate()
    print(f"  {summary}")

    # 5. Ciclo de sono
    print("\n😴 Executando ciclo de sono...")
    sleep_result = orch.sleep()
    print(f"  Fatos extraídos: {len(sleep_result.facts_extracted)}")
    print(f"  Hipóteses geradas: {len(sleep_result.hypotheses)}")
    print(f"  Novas crenças: {len(sleep_result.beliefs_added)}")
    print(f"  Traits antes: {len(sleep_result.traits_before)} dims")
    print(f"  Traits depois: {len(sleep_result.traits_after)} dims")

    # 6. Gerar system prompt
    print("\n📜 System Prompt gerado:")
    print("=" * 60)
    prompt = build_system_prompt(p)
    print(prompt[:500] + "...")  # Primeiros 500 chars
    print("=" * 60)

    print(f"\n✨ Exemplo concluído! Being ID para reusar: {being_id}")


if __name__ == "__main__":
    main()
