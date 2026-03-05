"""Unit tests for Event Sourcing: PersonalityEvent messages and EventStore."""

import math

import pytest

from serhu_orchestrator.proto.ser_identity_pb2 import (
    BeingCreatedPayload,
    BeliefPayload,
    EventType,
    FacetDeltas,
    GetLedgerRequest,
    InteractionPayload,
    MilestonePayload,
    PersonalityEvent,
    PersonalityLedger,
    RecordEventResponse,
    ReplayEventsRequest,
    SchwartzValue,
    SleepCyclePayload,
    StageTransitionPayload,
    StreamEventsRequest,
    TciSubscale,
    TraitUpdatePayload,
)
from serhu_orchestrator.personality.event_store import EventStore
from serhu_orchestrator.personality.types import PersonalityState


# ---------------------------------------------------------------------------
# Proto message construction (Event Sourcing types)
# ---------------------------------------------------------------------------


class TestEventTypeEnum:
    """Tests for the EventType enum."""

    def test_unspecified_is_zero(self):
        assert EventType.EVENT_TYPE_UNSPECIFIED == 0

    def test_all_event_types_exist(self):
        expected = [
            "EVENT_TYPE_UNSPECIFIED",
            "BEING_CREATED",
            "TRAIT_UPDATE",
            "MILESTONE_ACHIEVED",
            "STAGE_TRANSITION",
            "BELIEF_ADDED",
            "SLEEP_CYCLE_COMPLETED",
            "INTERACTION_PROCESSED",
        ]
        names = [name for name, _ in EventType.items()]
        for e in expected:
            assert e in names, f"Missing EventType: {e}"

    def test_event_type_count(self):
        assert len(EventType.items()) == 8


class TestPersonalityEventMessage:
    """Tests for the PersonalityEvent proto message."""

    def test_basic_construction(self):
        event = PersonalityEvent(
            event_id="evt-001",
            ser_id="being-001",
            event_type=EventType.BEING_CREATED,
            sequence_number=1,
        )
        assert event.event_id == "evt-001"
        assert event.ser_id == "being-001"
        assert event.event_type == EventType.BEING_CREATED
        assert event.sequence_number == 1

    def test_being_created_payload(self):
        event = PersonalityEvent(
            event_id="evt-002",
            ser_id="being-002",
            event_type=EventType.BEING_CREATED,
            being_created=BeingCreatedPayload(name="Luna", language="pt"),
        )
        assert event.being_created.name == "Luna"
        assert event.being_created.language == "pt"

    def test_trait_update_payload(self):
        fd = FacetDeltas()
        fd.values["sincerity"] = 0.05
        fd.values["creativity"] = -0.02
        payload = TraitUpdatePayload()
        payload.deltas["hexaco"].CopyFrom(fd)

        event = PersonalityEvent(
            event_id="evt-003",
            ser_id="being-003",
            event_type=EventType.TRAIT_UPDATE,
            trait_update=payload,
        )
        assert math.isclose(
            event.trait_update.deltas["hexaco"].values["sincerity"], 0.05, rel_tol=1e-5
        )
        assert math.isclose(
            event.trait_update.deltas["hexaco"].values["creativity"], -0.02, rel_tol=1e-5
        )

    def test_milestone_payload(self):
        event = PersonalityEvent(
            event_id="evt-004",
            ser_id="being-004",
            event_type=EventType.MILESTONE_ACHIEVED,
            milestone=MilestonePayload(
                milestone_id="object_permanence",
                new_cognitive_age=6.0,
            ),
        )
        assert event.milestone.milestone_id == "object_permanence"
        assert math.isclose(event.milestone.new_cognitive_age, 6.0, rel_tol=1e-5)

    def test_stage_transition_payload(self):
        event = PersonalityEvent(
            event_id="evt-005",
            ser_id="being-005",
            event_type=EventType.STAGE_TRANSITION,
            stage_transition=StageTransitionPayload(
                from_stage="sensorimotor",
                to_stage="preoperational",
                new_erikson_conflict="autonomy_vs_shame",
            ),
        )
        assert event.stage_transition.from_stage == "sensorimotor"
        assert event.stage_transition.to_stage == "preoperational"
        assert event.stage_transition.new_erikson_conflict == "autonomy_vs_shame"

    def test_belief_payload(self):
        event = PersonalityEvent(
            event_id="evt-006",
            ser_id="being-006",
            event_type=EventType.BELIEF_ADDED,
            belief=BeliefPayload(belief_type="core", content="The world is safe"),
        )
        assert event.belief.belief_type == "core"
        assert event.belief.content == "The world is safe"

    def test_sleep_cycle_payload(self):
        event = PersonalityEvent(
            event_id="evt-007",
            ser_id="being-007",
            event_type=EventType.SLEEP_CYCLE_COMPLETED,
            sleep_cycle=SleepCyclePayload(
                num_rollouts=1000,
                svd_rank=8,
                facts_extracted=5,
                beliefs_added=3,
            ),
        )
        assert event.sleep_cycle.num_rollouts == 1000
        assert event.sleep_cycle.svd_rank == 8
        assert event.sleep_cycle.facts_extracted == 5
        assert event.sleep_cycle.beliefs_added == 3

    def test_interaction_payload(self):
        event = PersonalityEvent(
            event_id="evt-008",
            ser_id="being-008",
            event_type=EventType.INTERACTION_PROCESSED,
            interaction=InteractionPayload(role="user", content="Hello!"),
        )
        assert event.interaction.role == "user"
        assert event.interaction.content == "Hello!"

    def test_binary_roundtrip(self):
        """PersonalityEvent survives binary serialization."""
        event = PersonalityEvent(
            event_id="evt-rt",
            ser_id="ser-rt",
            event_type=EventType.TRAIT_UPDATE,
            sequence_number=42,
        )
        fd = FacetDeltas()
        fd.values["sincerity"] = 0.1
        event.trait_update.deltas["hexaco"].CopyFrom(fd)

        data = event.SerializeToString()
        restored = PersonalityEvent()
        restored.ParseFromString(data)

        assert restored.event_id == "evt-rt"
        assert restored.ser_id == "ser-rt"
        assert restored.event_type == EventType.TRAIT_UPDATE
        assert restored.sequence_number == 42
        assert math.isclose(
            restored.trait_update.deltas["hexaco"].values["sincerity"], 0.1, rel_tol=1e-5
        )


class TestGrpcRequestResponseMessages:
    """Tests for the gRPC request/response messages."""

    def test_get_ledger_request(self):
        req = GetLedgerRequest(ser_id="ser-001")
        assert req.ser_id == "ser-001"

    def test_record_event_response(self):
        resp = RecordEventResponse(sequence_number=10)
        assert resp.sequence_number == 10

    def test_replay_events_request(self):
        req = ReplayEventsRequest(ser_id="ser-001", up_to_sequence=50)
        assert req.ser_id == "ser-001"
        assert req.up_to_sequence == 50

    def test_stream_events_request(self):
        req = StreamEventsRequest(ser_id="ser-001", from_sequence=5)
        assert req.ser_id == "ser-001"
        assert req.from_sequence == 5


# ---------------------------------------------------------------------------
# EventStore tests
# ---------------------------------------------------------------------------


class TestEventStoreCreation:
    """Tests for EventStore initialization and basic operations."""

    def test_new_store_is_empty(self):
        store = EventStore(ser_id="test-001")
        assert store.events == []
        assert store.last_sequence == 0

    def test_ser_id_stored(self):
        store = EventStore(ser_id="test-002")
        assert store.ser_id == "test-002"


class TestEventStoreRecording:
    """Tests for recording events."""

    def test_record_being_created(self):
        store = EventStore(ser_id="ser-001")
        event = store.record_being_created(name="Luna", language="pt")
        assert event.event_type == EventType.BEING_CREATED
        assert event.being_created.name == "Luna"
        assert event.being_created.language == "pt"
        assert event.sequence_number == 1
        assert event.ser_id == "ser-001"
        assert len(store.events) == 1

    def test_record_trait_update(self):
        store = EventStore(ser_id="ser-002")
        deltas = {"hexaco": {"sincerity": 0.05, "creativity": -0.02}}
        event = store.record_trait_update(deltas)
        assert event.event_type == EventType.TRAIT_UPDATE
        assert math.isclose(
            event.trait_update.deltas["hexaco"].values["sincerity"], 0.05, rel_tol=1e-5
        )

    def test_record_milestone(self):
        store = EventStore(ser_id="ser-003")
        event = store.record_milestone("object_permanence", 6.0)
        assert event.event_type == EventType.MILESTONE_ACHIEVED
        assert event.milestone.milestone_id == "object_permanence"
        assert math.isclose(event.milestone.new_cognitive_age, 6.0, rel_tol=1e-5)

    def test_record_stage_transition(self):
        store = EventStore(ser_id="ser-004")
        event = store.record_stage_transition(
            "sensorimotor", "preoperational", "autonomy_vs_shame"
        )
        assert event.event_type == EventType.STAGE_TRANSITION
        assert event.stage_transition.from_stage == "sensorimotor"
        assert event.stage_transition.to_stage == "preoperational"

    def test_record_belief(self):
        store = EventStore(ser_id="ser-005")
        event = store.record_belief("core", "The world is beautiful")
        assert event.event_type == EventType.BELIEF_ADDED
        assert event.belief.belief_type == "core"
        assert event.belief.content == "The world is beautiful"

    def test_record_sleep_cycle(self):
        store = EventStore(ser_id="ser-006")
        event = store.record_sleep_cycle(
            num_rollouts=1000, svd_rank=8, facts_extracted=5, beliefs_added=3
        )
        assert event.event_type == EventType.SLEEP_CYCLE_COMPLETED
        assert event.sleep_cycle.num_rollouts == 1000

    def test_record_interaction(self):
        store = EventStore(ser_id="ser-007")
        event = store.record_interaction("user", "Hello!")
        assert event.event_type == EventType.INTERACTION_PROCESSED
        assert event.interaction.role == "user"
        assert event.interaction.content == "Hello!"

    def test_sequence_numbers_increment(self):
        store = EventStore(ser_id="ser-008")
        e1 = store.record_being_created("Alpha")
        e2 = store.record_interaction("user", "Hi")
        e3 = store.record_trait_update({"hexaco": {"sincerity": 0.01}})
        assert e1.sequence_number == 1
        assert e2.sequence_number == 2
        assert e3.sequence_number == 3
        assert store.last_sequence == 3

    def test_events_have_unique_ids(self):
        store = EventStore(ser_id="ser-009")
        e1 = store.record_interaction("user", "Hi")
        e2 = store.record_interaction("user", "Bye")
        assert e1.event_id != e2.event_id

    def test_events_have_timestamps(self):
        store = EventStore(ser_id="ser-010")
        event = store.record_being_created("Test")
        assert event.timestamp.seconds > 0


class TestEventStoreReplay:
    """Tests for state reconstruction via event replay."""

    def test_replay_empty_store(self):
        store = EventStore(ser_id="ser-empty")
        state = store.replay()
        assert state.being_id == "ser-empty"
        assert state.name == ""
        assert state.development.stage == "sensorimotor"

    def test_replay_being_created(self):
        store = EventStore(ser_id="ser-001")
        store.record_being_created(name="Luna", language="pt")
        state = store.replay()
        assert state.name == "Luna"
        assert state.language == "pt"

    def test_replay_trait_update(self):
        store = EventStore(ser_id="ser-002")
        store.record_being_created("Alpha")
        store.record_trait_update({"hexaco": {"sincerity": 0.1}})
        state = store.replay()
        assert math.isclose(state.hexaco.sincerity, 0.6, rel_tol=1e-3)
        assert state.development.interaction_count == 1

    def test_replay_multiple_trait_updates(self):
        store = EventStore(ser_id="ser-003")
        store.record_being_created("Beta")
        store.record_trait_update({"hexaco": {"sincerity": 0.1}})
        store.record_trait_update({"hexaco": {"sincerity": 0.1}})
        store.record_trait_update({"tci_character": {"empathy": 0.3}})
        state = store.replay()
        assert math.isclose(state.hexaco.sincerity, 0.7, rel_tol=1e-3)
        assert math.isclose(state.tci_character.empathy, 0.3, rel_tol=1e-3)
        assert state.development.interaction_count == 3

    def test_replay_milestone(self):
        store = EventStore(ser_id="ser-004")
        store.record_being_created("Gamma")
        store.record_milestone("object_permanence", 6.0)
        state = store.replay()
        assert "object_permanence" in state.development.milestones_achieved
        assert math.isclose(state.development.cognitive_age, 6.0, rel_tol=1e-3)

    def test_replay_stage_transition(self):
        store = EventStore(ser_id="ser-005")
        store.record_being_created("Delta")
        store.record_stage_transition(
            "sensorimotor", "preoperational", "autonomy_vs_shame"
        )
        state = store.replay()
        assert state.development.stage == "preoperational"
        assert state.development.erikson_conflict == "autonomy_vs_shame"

    def test_replay_beliefs(self):
        store = EventStore(ser_id="ser-006")
        store.record_being_created("Echo")
        store.record_belief("core", "The world is safe")
        store.record_belief("surface", "Dogs are friendly")
        state = store.replay()
        assert "The world is safe" in state.core_beliefs
        assert "Dogs are friendly" in state.surface_beliefs

    def test_replay_up_to_sequence(self):
        store = EventStore(ser_id="ser-007")
        store.record_being_created("Zeta", language="es")  # seq 1
        store.record_trait_update({"hexaco": {"sincerity": 0.1}})  # seq 2
        store.record_trait_update({"hexaco": {"sincerity": 0.1}})  # seq 3

        # Replay only up to seq 2
        state = store.replay(up_to_sequence=2)
        assert state.name == "Zeta"
        assert state.language == "es"
        assert math.isclose(state.hexaco.sincerity, 0.6, rel_tol=1e-3)
        assert state.development.interaction_count == 1

    def test_replay_full_lifecycle(self):
        """Replay a full Being lifecycle: creation → interactions → sleep."""
        store = EventStore(ser_id="lifecycle-001")
        store.record_being_created("Nova", language="pt")
        store.record_interaction("user", "Hello Nova!")
        store.record_trait_update({"hexaco": {"sincerity": 0.05}})
        store.record_milestone("object_permanence", 6.0)
        store.record_milestone("circular_reactions", 12.0)
        store.record_belief("surface", "The user is kind")
        store.record_sleep_cycle(
            num_rollouts=100, svd_rank=8, facts_extracted=2, beliefs_added=1
        )
        store.record_belief("core", "Learned: kindness matters")

        state = store.replay()
        assert state.name == "Nova"
        assert state.language == "pt"
        assert math.isclose(state.hexaco.sincerity, 0.55, rel_tol=1e-3)
        assert "object_permanence" in state.development.milestones_achieved
        assert "circular_reactions" in state.development.milestones_achieved
        assert math.isclose(state.development.cognitive_age, 12.0, rel_tol=1e-3)
        assert "The user is kind" in state.surface_beliefs
        assert "Learned: kindness matters" in state.core_beliefs

    def test_trait_clamping_on_replay(self):
        """Trait values are clamped to [0.0, 1.0] during replay."""
        store = EventStore(ser_id="clamp-001")
        store.record_being_created("Clamp")
        store.record_trait_update({"hexaco": {"sincerity": 0.8}})  # 0.5 + 0.8 = 1.3 → 1.0
        state = store.replay()
        assert state.hexaco.sincerity == 1.0

    def test_trait_clamping_lower_bound(self):
        """Negative deltas are clamped to 0.0."""
        store = EventStore(ser_id="clamp-002")
        store.record_being_created("Floor")
        store.record_trait_update({"hexaco": {"sincerity": -0.8}})  # 0.5 - 0.8 = -0.3 → 0.0
        state = store.replay()
        assert state.hexaco.sincerity == 0.0


class TestEventStoreGetEventsSince:
    """Tests for fetching events since a given sequence number."""

    def test_get_all_from_zero(self):
        store = EventStore(ser_id="since-001")
        store.record_being_created("Test")
        store.record_interaction("user", "Hi")
        events = store.get_events_since(0)
        assert len(events) == 2

    def test_get_from_middle(self):
        store = EventStore(ser_id="since-002")
        store.record_being_created("Test")   # seq 1
        store.record_interaction("user", "A")  # seq 2
        store.record_interaction("user", "B")  # seq 3
        events = store.get_events_since(1)
        assert len(events) == 2
        assert events[0].sequence_number == 2
        assert events[1].sequence_number == 3

    def test_get_from_end_returns_empty(self):
        store = EventStore(ser_id="since-003")
        store.record_being_created("Test")
        events = store.get_events_since(1)
        assert events == []


class TestEventStoreBinarySerialization:
    """Tests for binary serialization of events."""

    def test_event_survives_binary_roundtrip(self):
        store = EventStore(ser_id="bin-001")
        original = store.record_trait_update({"hexaco": {"sincerity": 0.05}})
        data = original.SerializeToString()
        restored = PersonalityEvent()
        restored.ParseFromString(data)
        assert restored.event_id == original.event_id
        assert restored.sequence_number == original.sequence_number
        assert math.isclose(
            restored.trait_update.deltas["hexaco"].values["sincerity"],
            0.05,
            rel_tol=1e-5,
        )

    def test_full_lifecycle_events_survive_roundtrip(self):
        """All events in a lifecycle survive serialization."""
        store = EventStore(ser_id="bin-002")
        store.record_being_created("Test", "en")
        store.record_trait_update({"hexaco": {"sincerity": 0.1}})
        store.record_milestone("object_permanence", 6.0)
        store.record_stage_transition(
            "sensorimotor", "preoperational", "autonomy_vs_shame"
        )
        store.record_belief("core", "Test belief")
        store.record_sleep_cycle(100, 8, 2, 1)

        for event in store.events:
            data = event.SerializeToString()
            restored = PersonalityEvent()
            restored.ParseFromString(data)
            assert restored.event_id == event.event_id
            assert restored.ser_id == event.ser_id
            assert restored.event_type == event.event_type
            assert restored.sequence_number == event.sequence_number
