"""Unit tests for the gRPC BeingService implementation.

Tests the SerhuBeingServicer directly (without a running gRPC server)
using mock contexts, and also via a real in-process gRPC channel.
"""

from __future__ import annotations

import uuid

import grpc
import pytest

from serhu_orchestrator.personality.event_store import EventStore
from serhu_orchestrator.proto.ser_identity_pb2 import (
    BeingCreatedPayload,
    BeliefPayload,
    EventType,
    FacetDeltas,
    GetLedgerRequest,
    InteractionPayload,
    MilestonePayload,
    PersonalityEvent,
    ReplayEventsRequest,
    StageTransitionPayload,
    StreamEventsRequest,
    TraitUpdatePayload,
)
from serhu_orchestrator.proto.ser_identity_pb2_grpc import BeingServiceStub
from serhu_grpc.service import SerhuBeingServicer
from serhu_grpc.server import create_server


# -- helpers ----------------------------------------------------------------

class MockContext:
    """Simple mock for a gRPC context in direct servicer tests."""

    def __init__(self):
        self.code = None
        self.details = None

    def set_code(self, code):
        self.code = code

    def set_details(self, details):
        self.details = details


def _create_being_event(ser_id: str, name: str = "TestBeing", language: str = "en") -> PersonalityEvent:
    return PersonalityEvent(
        event_id=uuid.uuid4().hex,
        ser_id=ser_id,
        event_type=EventType.BEING_CREATED,
        being_created=BeingCreatedPayload(name=name, language=language),
    )


def _trait_update_event(ser_id: str) -> PersonalityEvent:
    payload = TraitUpdatePayload()
    fd = FacetDeltas()
    fd.values["sincerity"] = 0.05
    payload.deltas["hexaco"].CopyFrom(fd)
    return PersonalityEvent(
        event_id=uuid.uuid4().hex,
        ser_id=ser_id,
        event_type=EventType.TRAIT_UPDATE,
        trait_update=payload,
    )


def _milestone_event(ser_id: str) -> PersonalityEvent:
    return PersonalityEvent(
        event_id=uuid.uuid4().hex,
        ser_id=ser_id,
        event_type=EventType.MILESTONE_ACHIEVED,
        milestone=MilestonePayload(
            milestone_id="object_permanence",
            new_cognitive_age=6.0,
        ),
    )


def _belief_event(ser_id: str) -> PersonalityEvent:
    return PersonalityEvent(
        event_id=uuid.uuid4().hex,
        ser_id=ser_id,
        event_type=EventType.BELIEF_ADDED,
        belief=BeliefPayload(belief_type="core", content="Trust is earned"),
    )


# -- direct servicer tests --------------------------------------------------

class TestSerhuBeingServicerDirect:
    """Test the servicer without gRPC infrastructure."""

    def test_record_event_creates_store(self):
        servicer = SerhuBeingServicer()
        ctx = MockContext()
        ser_id = uuid.uuid4().hex

        event = _create_being_event(ser_id)
        resp = servicer.RecordEvent(event, ctx)

        assert resp.sequence_number == 1
        assert resp.ledger.ser_id == ser_id
        assert resp.ledger.name == "TestBeing"

    def test_get_ledger_returns_state(self):
        servicer = SerhuBeingServicer()
        ctx = MockContext()
        ser_id = uuid.uuid4().hex

        # Record creation
        servicer.RecordEvent(_create_being_event(ser_id, name="Luna", language="pt"), ctx)

        # Get ledger
        req = GetLedgerRequest(ser_id=ser_id)
        ledger = servicer.GetLedger(req, ctx)

        assert ledger.ser_id == ser_id
        assert ledger.name == "Luna"
        assert ledger.language == "pt"

    def test_get_ledger_not_found(self):
        servicer = SerhuBeingServicer()
        ctx = MockContext()

        servicer.GetLedger(GetLedgerRequest(ser_id="nonexistent"), ctx)
        assert ctx.code == grpc.StatusCode.NOT_FOUND

    def test_trait_update_applies_delta(self):
        servicer = SerhuBeingServicer()
        ctx = MockContext()
        ser_id = uuid.uuid4().hex

        # Create and update
        servicer.RecordEvent(_create_being_event(ser_id), ctx)
        resp = servicer.RecordEvent(_trait_update_event(ser_id), ctx)

        assert resp.sequence_number == 2
        # HEXACO sincerity should be 0.5 + 0.05 = 0.55
        assert abs(resp.ledger.hexaco["sincerity"].score - 0.55) < 1e-4

    def test_milestone_updates_cognitive_age(self):
        servicer = SerhuBeingServicer()
        ctx = MockContext()
        ser_id = uuid.uuid4().hex

        servicer.RecordEvent(_create_being_event(ser_id), ctx)
        resp = servicer.RecordEvent(_milestone_event(ser_id), ctx)

        assert abs(resp.ledger.development.cognitive_age - 6.0) < 1e-4
        assert "object_permanence" in resp.ledger.development.milestones_achieved

    def test_belief_added_to_ledger(self):
        servicer = SerhuBeingServicer()
        ctx = MockContext()
        ser_id = uuid.uuid4().hex

        servicer.RecordEvent(_create_being_event(ser_id), ctx)
        resp = servicer.RecordEvent(_belief_event(ser_id), ctx)

        assert "Trust is earned" in resp.ledger.core_beliefs

    def test_replay_partial(self):
        servicer = SerhuBeingServicer()
        ctx = MockContext()
        ser_id = uuid.uuid4().hex

        # Record 3 events
        servicer.RecordEvent(_create_being_event(ser_id), ctx)
        servicer.RecordEvent(_trait_update_event(ser_id), ctx)
        servicer.RecordEvent(_milestone_event(ser_id), ctx)

        # Replay only first 2 events
        req = ReplayEventsRequest(ser_id=ser_id, up_to_sequence=2)
        ledger = servicer.ReplayEvents(req, ctx)

        # Should have trait update but NOT milestone
        assert abs(ledger.hexaco["sincerity"].score - 0.55) < 1e-4
        assert ledger.development.cognitive_age == 0.0

    def test_replay_not_found(self):
        servicer = SerhuBeingServicer()
        ctx = MockContext()

        servicer.ReplayEvents(ReplayEventsRequest(ser_id="nonexistent"), ctx)
        assert ctx.code == grpc.StatusCode.NOT_FOUND

    def test_stream_events(self):
        servicer = SerhuBeingServicer()
        ctx = MockContext()
        ser_id = uuid.uuid4().hex

        # Record 3 events
        servicer.RecordEvent(_create_being_event(ser_id), ctx)
        servicer.RecordEvent(_trait_update_event(ser_id), ctx)
        servicer.RecordEvent(_milestone_event(ser_id), ctx)

        # Stream from sequence 1 (skip creation)
        req = StreamEventsRequest(ser_id=ser_id, from_sequence=1)
        events = list(servicer.StreamEvents(req, ctx))

        assert len(events) == 2
        assert events[0].event_type == EventType.TRAIT_UPDATE
        assert events[1].event_type == EventType.MILESTONE_ACHIEVED

    def test_stream_events_not_found(self):
        servicer = SerhuBeingServicer()
        ctx = MockContext()

        events = list(servicer.StreamEvents(StreamEventsRequest(ser_id="nonexistent"), ctx))
        assert len(events) == 0
        assert ctx.code == grpc.StatusCode.NOT_FOUND

    def test_record_event_requires_ser_id(self):
        servicer = SerhuBeingServicer()
        ctx = MockContext()

        event = PersonalityEvent(
            event_id=uuid.uuid4().hex,
            event_type=EventType.BEING_CREATED,
            being_created=BeingCreatedPayload(name="X"),
        )
        servicer.RecordEvent(event, ctx)
        assert ctx.code == grpc.StatusCode.INVALID_ARGUMENT

    def test_multiple_beings(self):
        servicer = SerhuBeingServicer()
        ctx = MockContext()
        id1, id2 = uuid.uuid4().hex, uuid.uuid4().hex

        servicer.RecordEvent(_create_being_event(id1, name="Alpha"), ctx)
        servicer.RecordEvent(_create_being_event(id2, name="Beta"), ctx)

        l1 = servicer.GetLedger(GetLedgerRequest(ser_id=id1), MockContext())
        l2 = servicer.GetLedger(GetLedgerRequest(ser_id=id2), MockContext())

        assert l1.name == "Alpha"
        assert l2.name == "Beta"


# -- in-process gRPC server tests -------------------------------------------

class TestGrpcInProcess:
    """Test using a real in-process gRPC channel."""

    @pytest.fixture()
    def channel(self):
        """Create an in-process gRPC server and channel."""
        servicer = SerhuBeingServicer()
        server = create_server(port=0, servicer=servicer)
        port = server.add_insecure_port("[::]:0")
        server.start()
        ch = grpc.insecure_channel(f"localhost:{port}")
        yield ch, servicer
        ch.close()
        server.stop(grace=0)

    def test_get_ledger_via_grpc(self, channel):
        ch, servicer = channel
        stub = BeingServiceStub(ch)
        ser_id = uuid.uuid4().hex

        # Record directly on the servicer
        ctx = MockContext()
        servicer.RecordEvent(_create_being_event(ser_id, name="Luna"), ctx)

        # Query via gRPC
        ledger = stub.GetLedger(GetLedgerRequest(ser_id=ser_id))
        assert ledger.name == "Luna"
        assert ledger.ser_id == ser_id

    def test_record_event_via_grpc(self, channel):
        ch, _ = channel
        stub = BeingServiceStub(ch)
        ser_id = uuid.uuid4().hex

        resp = stub.RecordEvent(_create_being_event(ser_id, name="Sol"))
        assert resp.sequence_number == 1
        assert resp.ledger.name == "Sol"

    def test_full_lifecycle_via_grpc(self, channel):
        ch, _ = channel
        stub = BeingServiceStub(ch)
        ser_id = uuid.uuid4().hex

        # Create
        stub.RecordEvent(_create_being_event(ser_id, name="Cosmos", language="es"))
        # Trait update
        stub.RecordEvent(_trait_update_event(ser_id))
        # Milestone
        stub.RecordEvent(_milestone_event(ser_id))
        # Belief
        resp = stub.RecordEvent(_belief_event(ser_id))

        assert resp.sequence_number == 4
        assert resp.ledger.name == "Cosmos"
        assert resp.ledger.language == "es"
        assert abs(resp.ledger.hexaco["sincerity"].score - 0.55) < 1e-4
        assert abs(resp.ledger.development.cognitive_age - 6.0) < 1e-4
        assert "Trust is earned" in resp.ledger.core_beliefs

    def test_stream_via_grpc(self, channel):
        ch, servicer = channel
        stub = BeingServiceStub(ch)
        ser_id = uuid.uuid4().hex

        ctx = MockContext()
        servicer.RecordEvent(_create_being_event(ser_id), ctx)
        servicer.RecordEvent(_trait_update_event(ser_id), ctx)

        events = list(stub.StreamEvents(StreamEventsRequest(ser_id=ser_id, from_sequence=0)))
        assert len(events) == 2
