"""Event Store – Append-only log of personality life events.

Implements the Event Sourcing pattern for the Being's life record.
Every mutation to the PersonalityLedger is captured as an immutable
``PersonalityEvent``, enabling full audit trails and state reconstruction
via replay.

The current ``PersonalityState`` is derived by replaying the event log
rather than being the single source of truth.  This allows:
- Time-travel debugging (reconstruct state at any point)
- Complete audit trail of the Being's evolution
- Reliable transmission between Lambda (vigília) and Fargate (sono)

References:
    - Event Sourcing: https://martinfowler.com/eaaDev/EventSourcing.html
    - CQRS + Event Sourcing: https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing
"""

from __future__ import annotations

import time
import uuid

from google.protobuf.timestamp_pb2 import Timestamp

from serhu_orchestrator.personality.types import (
    DevelopmentStage,
    ERIKSON_CONFLICTS,
    HexacoFacets,
    PersonalityState,
    SchwartzValues,
    STAGE_AGE_RANGES,
    STAGE_MILESTONES,
    STAGE_ORDER,
    TciCharacter,
    TciTemperament,
)
from serhu_orchestrator.proto.ser_identity_pb2 import (
    BeingCreatedPayload,
    BeliefPayload,
    EventType,
    FacetDeltas,
    InteractionPayload,
    MilestonePayload,
    PersonalityEvent,
    SleepCyclePayload,
    StageTransitionPayload,
    TraitUpdatePayload,
)


def _now_timestamp() -> Timestamp:
    """Create a protobuf Timestamp for the current time."""
    ts = Timestamp()
    ts.FromSeconds(int(time.time()))
    return ts


class EventStore:
    """Append-only event log for a Being's life record.

    Stores ``PersonalityEvent`` messages in memory.  In production this
    would be backed by a durable store (e.g. DynamoDB Stream, Kafka).

    Parameters
    ----------
    ser_id : str
        Identifier of the Being this store belongs to.
    """

    def __init__(self, ser_id: str) -> None:
        self.ser_id = ser_id
        self._events: list[PersonalityEvent] = []
        self._sequence: int = 0

    # -- public API ----------------------------------------------------------

    @property
    def events(self) -> list[PersonalityEvent]:
        """Return a copy of the event log."""
        return list(self._events)

    @property
    def last_sequence(self) -> int:
        """Return the last assigned sequence number."""
        return self._sequence

    def append(self, event: PersonalityEvent) -> PersonalityEvent:
        """Append a pre-built event, assigning sequence number and timestamp.

        Returns the event with sequence number and timestamp populated.
        """
        self._sequence += 1
        event.sequence_number = self._sequence
        if not event.timestamp.seconds:
            event.timestamp.CopyFrom(_now_timestamp())
        self._events.append(event)
        return event

    # -- convenience event builders ------------------------------------------

    def record_being_created(
        self,
        name: str = "",
        language: str = "en",
    ) -> PersonalityEvent:
        """Record a BEING_CREATED event."""
        event = PersonalityEvent(
            event_id=uuid.uuid4().hex,
            ser_id=self.ser_id,
            event_type=EventType.BEING_CREATED,
            being_created=BeingCreatedPayload(name=name, language=language),
        )
        return self.append(event)

    def record_trait_update(
        self,
        deltas: dict[str, dict[str, float]],
    ) -> PersonalityEvent:
        """Record a TRAIT_UPDATE event.

        Parameters
        ----------
        deltas : dict[str, dict[str, float]]
            Nested dict: model_name → {facet_name: delta_value}.
        """
        proto_deltas: dict[str, FacetDeltas] = {}
        for model_name, facet_map in deltas.items():
            fd = FacetDeltas()
            for facet_name, delta in facet_map.items():
                fd.values[facet_name] = delta
            proto_deltas[model_name] = fd

        payload = TraitUpdatePayload()
        for k, v in proto_deltas.items():
            payload.deltas[k].CopyFrom(v)

        event = PersonalityEvent(
            event_id=uuid.uuid4().hex,
            ser_id=self.ser_id,
            event_type=EventType.TRAIT_UPDATE,
            trait_update=payload,
        )
        return self.append(event)

    def record_milestone(
        self,
        milestone_id: str,
        new_cognitive_age: float,
    ) -> PersonalityEvent:
        """Record a MILESTONE_ACHIEVED event."""
        event = PersonalityEvent(
            event_id=uuid.uuid4().hex,
            ser_id=self.ser_id,
            event_type=EventType.MILESTONE_ACHIEVED,
            milestone=MilestonePayload(
                milestone_id=milestone_id,
                new_cognitive_age=new_cognitive_age,
            ),
        )
        return self.append(event)

    def record_stage_transition(
        self,
        from_stage: str,
        to_stage: str,
        new_erikson_conflict: str,
    ) -> PersonalityEvent:
        """Record a STAGE_TRANSITION event."""
        event = PersonalityEvent(
            event_id=uuid.uuid4().hex,
            ser_id=self.ser_id,
            event_type=EventType.STAGE_TRANSITION,
            stage_transition=StageTransitionPayload(
                from_stage=from_stage,
                to_stage=to_stage,
                new_erikson_conflict=new_erikson_conflict,
            ),
        )
        return self.append(event)

    def record_belief(
        self,
        belief_type: str,
        content: str,
    ) -> PersonalityEvent:
        """Record a BELIEF_ADDED event."""
        event = PersonalityEvent(
            event_id=uuid.uuid4().hex,
            ser_id=self.ser_id,
            event_type=EventType.BELIEF_ADDED,
            belief=BeliefPayload(belief_type=belief_type, content=content),
        )
        return self.append(event)

    def record_sleep_cycle(
        self,
        num_rollouts: int,
        svd_rank: int,
        facts_extracted: int,
        beliefs_added: int,
    ) -> PersonalityEvent:
        """Record a SLEEP_CYCLE_COMPLETED event."""
        event = PersonalityEvent(
            event_id=uuid.uuid4().hex,
            ser_id=self.ser_id,
            event_type=EventType.SLEEP_CYCLE_COMPLETED,
            sleep_cycle=SleepCyclePayload(
                num_rollouts=num_rollouts,
                svd_rank=svd_rank,
                facts_extracted=facts_extracted,
                beliefs_added=beliefs_added,
            ),
        )
        return self.append(event)

    def record_interaction(
        self,
        role: str,
        content: str,
    ) -> PersonalityEvent:
        """Record an INTERACTION_PROCESSED event."""
        event = PersonalityEvent(
            event_id=uuid.uuid4().hex,
            ser_id=self.ser_id,
            event_type=EventType.INTERACTION_PROCESSED,
            interaction=InteractionPayload(role=role, content=content),
        )
        return self.append(event)

    # -- replay / projection -------------------------------------------------

    def replay(self, up_to_sequence: int = 0) -> PersonalityState:
        """Reconstruct a PersonalityState by replaying events.

        Parameters
        ----------
        up_to_sequence : int
            Replay up to this sequence number.  0 means replay all events.

        Returns
        -------
        PersonalityState
            The projected state after applying events in order.
        """
        state = PersonalityState(being_id=self.ser_id)

        for event in self._events:
            if up_to_sequence and event.sequence_number > up_to_sequence:
                break
            state = _apply_event(state, event)

        return state

    def get_events_since(self, from_sequence: int) -> list[PersonalityEvent]:
        """Return events with sequence_number > from_sequence."""
        return [e for e in self._events if e.sequence_number > from_sequence]


# ---------------------------------------------------------------------------
# Event application (projection)
# ---------------------------------------------------------------------------


def _apply_event(state: PersonalityState, event: PersonalityEvent) -> PersonalityState:
    """Apply a single event to a PersonalityState, returning the updated state."""
    etype = event.event_type

    if etype == EventType.BEING_CREATED:
        payload = event.being_created
        state.name = payload.name
        state.language = payload.language if payload.language else "en"

    elif etype == EventType.TRAIT_UPDATE:
        payload = event.trait_update
        model_map = {
            "hexaco": state.hexaco,
            "tci_temperament": state.tci_temperament,
            "tci_character": state.tci_character,
            "schwartz": state.schwartz,
        }
        for model_name, facet_deltas in payload.deltas.items():
            model = model_map.get(model_name)
            if model is None:
                continue
            for facet_name, delta in facet_deltas.values.items():
                if hasattr(model, facet_name):
                    current = getattr(model, facet_name)
                    setattr(model, facet_name, max(0.0, min(1.0, current + delta)))
        state.development.interaction_count += 1

    elif etype == EventType.MILESTONE_ACHIEVED:
        payload = event.milestone
        if payload.milestone_id not in state.development.milestones_achieved:
            state.development.milestones_achieved.append(payload.milestone_id)
        state.development.cognitive_age = payload.new_cognitive_age

    elif etype == EventType.STAGE_TRANSITION:
        payload = event.stage_transition
        state.development.stage = payload.to_stage
        state.development.erikson_conflict = payload.new_erikson_conflict

    elif etype == EventType.BELIEF_ADDED:
        payload = event.belief
        if payload.belief_type == "core":
            state.core_beliefs.append(payload.content)
        elif payload.belief_type == "surface":
            state.surface_beliefs.append(payload.content)

    elif etype == EventType.INTERACTION_PROCESSED:
        pass  # Informational event; no state mutation beyond what TRAIT_UPDATE does

    elif etype == EventType.SLEEP_CYCLE_COMPLETED:
        pass  # Informational event; actual changes are in TRAIT_UPDATE / BELIEF_ADDED

    return state
