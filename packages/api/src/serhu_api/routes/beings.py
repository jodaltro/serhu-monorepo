"""Being lifecycle routes — CRUD, chat, sleep, recall, and visual state.

Exposes the Orchestrator's functionality via REST endpoints for the
mobile app and web frontend.
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException

from serhu_api.schemas import (
    CreateBeingRequest,
    BeingResponse,
    ChatRequest,
    ChatResponse,
    ProcessMessageRequest,
    ContextWindowResponse,
    SleepRequest,
    SleepResponse,
    SleepOnceRequest,
    SleepOnceResponse,
    WakeRequest,
    WakeResponse,
    RecallRequest,
    RecallResponse,
    LearnFactRequest,
    LearnFactResponse,
    VisualStateResponse,
    PersonalityResponse,
)
from serhu_api.dependencies import create_being_orchestrator, get_orchestrator

from serhu_morphogenesis.engine import compute_visual_state

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/beings", tags=["beings"])


# -- helpers ----------------------------------------------------------------

def _being_response(orch) -> BeingResponse:
    """Build a ``BeingResponse`` from an Orchestrator."""
    p = orch.personality
    return BeingResponse(
        being_id=p.being_id,
        name=p.name,
        language=p.language,
        stage=p.development.stage,
        cognitive_age=p.development.cognitive_age,
        erikson_conflict=p.development.erikson_conflict,
        interaction_count=p.development.interaction_count,
        is_sleeping=orch.is_sleeping,
    )


def _get_orch(being_id: str):
    """Get an Orchestrator, raising 404 if not found."""
    try:
        return get_orchestrator(being_id)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# -- CRUD -------------------------------------------------------------------

@router.post("/", response_model=BeingResponse, status_code=201)
def create_being(body: CreateBeingRequest):
    """Create a new Being (tabula rasa)."""
    logger.info(f"📍 [POST /beings] Creating Being: name={body.name}, language={body.language}")
    orch = create_being_orchestrator(name=body.name, language=body.language)
    logger.info(f"✓ Being created: being_id={orch.being_id}")
    return _being_response(orch)


@router.get("/{being_id}", response_model=BeingResponse)
def get_being(being_id: str):
    """Get a Being's summary."""
    orch = _get_orch(being_id)
    return _being_response(orch)


@router.get("/{being_id}/personality", response_model=PersonalityResponse)
def get_personality(being_id: str):
    """Get the full personality ledger for a Being."""
    orch = _get_orch(being_id)
    p = orch.personality
    return PersonalityResponse(
        being_id=p.being_id,
        name=p.name,
        language=p.language,
        stage=p.development.stage,
        cognitive_age=p.development.cognitive_age,
        erikson_conflict=p.development.erikson_conflict,
        interaction_count=p.development.interaction_count,
        milestones_achieved=p.development.milestones_achieved,
        hexaco=p.hexaco.model_dump(),
        tci_temperament=p.tci_temperament.model_dump(),
        tci_character=p.tci_character.model_dump(),
        schwartz=p.schwartz.model_dump(),
        core_beliefs=p.core_beliefs,
        surface_beliefs=p.surface_beliefs,
    )


# -- Wakefulness: chat and process ------------------------------------------

@router.post("/{being_id}/chat", response_model=ChatResponse)
def chat(being_id: str, body: ChatRequest):
    """Chat with a Being (self-generated responses from learned patterns)."""
    logger.info(f"📍 [POST /beings/{being_id}/chat] User message: {body.message[:50]}...")
    orch = _get_orch(being_id)
    response_text, _ctx = orch.chat(
        body.message,
        auto_traits=body.auto_traits,
    )
    logger.info(f"✓ Response generated: {response_text[:50]}... (stage={orch.personality.development.stage})")

    p = orch.personality
    return ChatResponse(
        response=response_text,
        being_id=p.being_id,
        stage=p.development.stage,
        cognitive_age=p.development.cognitive_age,
    )


@router.post("/{being_id}/process", response_model=ContextWindowResponse)
def process_message(being_id: str, body: ProcessMessageRequest):
    """Process a message without LLM (manual mode)."""
    logger.info(f"📍 [POST /beings/{being_id}/process] Processing message from {body.role}: {body.content[:50]}...")
    orch = _get_orch(being_id)
    ctx = orch.process_message(
        role=body.role,
        content=body.content,
        metadata=body.metadata,
        trait_deltas=body.trait_deltas,
    )
    logger.info(f"✓ Message processed: working_memory={len(ctx.working)}, archival={len(ctx.archival_results)}, semantic_facts={len(ctx.semantic_facts)}")
    return ContextWindowResponse(
        working_memory_count=len(ctx.working),
        archival_count=len(ctx.archival_results),
        semantic_facts_count=len(ctx.semantic_facts),
    )


# -- Twilight: consolidation ------------------------------------------------

@router.post("/{being_id}/consolidate")
def consolidate(being_id: str):
    """Consolidate working memory to long-term storage."""
    logger.info(f"📍 [POST /beings/{being_id}/consolidate] Starting consolidation")
    orch = _get_orch(being_id)
    archived = orch.consolidate()
    logger.info(f"✓ Consolidation complete: {archived} entries archived")
    return {"archived": archived}


# -- Sleep ------------------------------------------------------------------

@router.post("/{being_id}/sleep", response_model=SleepResponse)
def sleep(being_id: str, body: SleepRequest):
    """Start continuous AIXI dreaming (runs until wake is called)."""
    logger.info(
        "📍 [POST /beings/%s/sleep] Starting sleep cycle: num_rollouts=%d, svd_rank=%d, cycle_interval_sec=%.3f",
        being_id,
        body.num_rollouts,
        body.svd_rank,
        body.cycle_interval_sec,
    )
    orch = _get_orch(being_id)
    try:
        orch.sleep(
            num_rollouts=body.num_rollouts,
            svd_rank=body.svd_rank,
            cycle_interval_sec=body.cycle_interval_sec,
            seed=body.seed,
        )
        logger.info(f"✓ Sleep cycle started (running in background)")
    except RuntimeError as exc:
        logger.error(f"✗ Sleep cycle error: {exc}")
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return SleepResponse(is_sleeping=True)


@router.post("/{being_id}/wake", response_model=WakeResponse)
def wake(being_id: str, body: WakeRequest = WakeRequest()):
    """Wake the Being from continuous sleep and retrieve results."""
    logger.info(f"📍 [POST /beings/{being_id}/wake] Waking Being from sleep (timeout={body.timeout}s)")
    orch = _get_orch(being_id)
    result = orch.wake(timeout=body.timeout)
    if result is None:
        logger.info(f"⏱️ Wake timeout: no results available")
        return WakeResponse(
            facts_extracted=0,
            beliefs_added=0,
            hypotheses_generated=0,
            cycles_completed=0,
        )
    if result.training_result is not None:
        logger.info(
            "✓ Being woken: facts_extracted=%d, beliefs_added=%d, hypotheses_generated=%d, cycles_completed=%d, training(vocab=%d, patterns=%d, entropy=%.4f)",
            len(result.facts_extracted),
            len(result.beliefs_added),
            len(result.hypotheses),
            result.cycles_completed,
            result.training_result.vocabulary_size,
            result.training_result.pattern_count,
            result.training_result.attention_entropy,
        )
    else:
        logger.info(
            "✓ Being woken: facts_extracted=%d, beliefs_added=%d, hypotheses_generated=%d, cycles_completed=%d",
            len(result.facts_extracted),
            len(result.beliefs_added),
            len(result.hypotheses),
            result.cycles_completed,
        )
    return WakeResponse(
        facts_extracted=len(result.facts_extracted),
        beliefs_added=len(result.beliefs_added),
        hypotheses_generated=len(result.hypotheses),
        cycles_completed=result.cycles_completed,
    )


@router.post("/{being_id}/sleep-once", response_model=SleepOnceResponse)
def sleep_once(being_id: str, body: SleepOnceRequest):
    """Trigger a single synchronous sleep cycle (backward-compatible)."""
    logger.info(f"📍 [POST /beings/{being_id}/sleep-once] Single sleep cycle: num_rollouts={body.num_rollouts}, svd_rank={body.svd_rank}")
    orch = _get_orch(being_id)
    result = orch.sleep_once(
        num_rollouts=body.num_rollouts,
        svd_rank=body.svd_rank,
        seed=body.seed,
    )
    logger.info(f"✓ Sleep cycle complete: facts_extracted={len(result.facts_extracted)}, beliefs_added={len(result.beliefs_added)}")
    return SleepOnceResponse(
        facts_extracted=len(result.facts_extracted),
        beliefs_added=len(result.beliefs_added),
        hypotheses_generated=len(result.hypotheses),
    )


# -- Retrieval --------------------------------------------------------------

@router.post("/{being_id}/recall", response_model=RecallResponse)
def recall(being_id: str, body: RecallRequest):
    """Recall memories relevant to a query."""
    logger.info(f"📍 [POST /beings/{being_id}/recall] Query: {body.query!r}, top_k={body.top_k}, type={body.memory_type}")
    orch = _get_orch(being_id)
    memories = orch.recall(
        query=body.query,
        top_k=body.top_k,
        memory_type=body.memory_type,
    )
    logger.info(f"✓ Recalled {len(memories)} memories")
    return RecallResponse(memories=memories)


@router.post("/{being_id}/learn", response_model=LearnFactResponse)
def learn_fact(being_id: str, body: LearnFactRequest):
    """Store a semantic fact."""
    logger.info(f"📍 [POST /beings/{being_id}/learn] Fact: {body.fact[:50]}...")
    orch = _get_orch(being_id)
    orch.learn_fact(body.fact)
    logger.info(f"✓ Fact learned")
    return LearnFactResponse(stored=True)


# -- Visual morphogenesis ---------------------------------------------------

@router.get("/{being_id}/visual", response_model=VisualStateResponse)
def get_visual_state(being_id: str):
    """Get the visual morphogenesis state for rendering."""
    logger.info(f"📍 [GET /beings/{being_id}/visual] Computing visual state")
    orch = _get_orch(being_id)
    vs = compute_visual_state(orch.personality)
    logger.info(f"✓ Visual state computed: color=HSL({vs.color.hue:.1f}, {vs.color.saturation:.1f}%, {vs.color.lightness:.1f}%)")
    return VisualStateResponse(
        being_id=vs.being_id,
        cognitive_stage=vs.cognitive_stage,
        cognitive_age=vs.cognitive_age,
        hue=vs.color.hue,
        saturation=vs.color.saturation,
        lightness=vs.color.lightness,
        alpha=vs.color.alpha,
        roundness=vs.geometry.roundness,
        complexity=vs.geometry.complexity,
        symmetry=vs.geometry.symmetry,
        scale=vs.geometry.scale,
        spikiness=vs.geometry.spikiness,
        organic_noise=vs.geometry.organic_noise,
        pulse_rate=vs.animation.pulse_rate,
        movement_speed=vs.animation.movement_speed,
        center_attraction=vs.animation.center_attraction,
        glow_intensity=vs.animation.glow_intensity,
        roughness=vs.animation.roughness,
    )
