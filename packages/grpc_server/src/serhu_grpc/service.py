"""BeingService gRPC servicer implementation.

Implements the four RPCs defined in ``ser_identity.proto``:
  - GetLedger: retrieve the current personality ledger
  - RecordEvent: record a new event in the Being's life log
  - ReplayEvents: replay events to reconstruct state at a point in time
  - StreamEvents: server-side streaming for real-time event sync

Each servicer instance manages a collection of in-memory EventStores
keyed by ``ser_id``.  In production these would be backed by a durable
store (DynamoDB Streams, Kafka, etc.).

References:
    - Event Sourcing: https://martinfowler.com/eaaDev/EventSourcing.html
    - Proto definition: proto/ser_identity.proto
"""

from __future__ import annotations

import logging

import grpc

from serhu_orchestrator.personality.event_store import EventStore
from serhu_orchestrator.personality.proto_converter import personality_to_ledger
from serhu_orchestrator.proto.ser_identity_pb2 import (
    GetLedgerRequest,
    PersonalityEvent,
    PersonalityLedger,
    RecordEventResponse,
    ReplayEventsRequest,
    StreamEventsRequest,
)
from serhu_orchestrator.proto.ser_identity_pb2_grpc import BeingServiceServicer

logger = logging.getLogger(__name__)


class SerhuBeingServicer(BeingServiceServicer):
    """Concrete implementation of the BeingService gRPC service.

    Manages an in-memory collection of ``EventStore`` instances.

    Parameters
    ----------
    stores : dict[str, EventStore] | None
        Pre-populated event stores.  If ``None``, stores are created
        on demand when events are recorded.
    """

    def __init__(self, stores: dict[str, EventStore] | None = None) -> None:
        self._stores: dict[str, EventStore] = stores or {}

    def _get_or_create_store(self, ser_id: str) -> EventStore:
        """Return the EventStore for a Being, creating one if needed."""
        if ser_id not in self._stores:
            self._stores[ser_id] = EventStore(ser_id=ser_id)
        return self._stores[ser_id]

    # -- GetLedger -----------------------------------------------------------

    def GetLedger(self, request: GetLedgerRequest, context) -> PersonalityLedger:
        """Retrieve the current personality ledger for a Being.

        Replays all events in the Being's event log to reconstruct
        the current ``PersonalityState``, then converts it to a
        Protobuf ``PersonalityLedger``.
        """
        ser_id = request.ser_id
        if ser_id not in self._stores:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Being {ser_id!r} not found")
            return PersonalityLedger()

        store = self._stores[ser_id]
        state = store.replay()
        return personality_to_ledger(state)

    # -- RecordEvent ---------------------------------------------------------

    def RecordEvent(self, request: PersonalityEvent, context) -> RecordEventResponse:
        """Record a new event in the Being's life log.

        Appends the event to the Being's EventStore, assigns a sequence
        number, and returns the updated ledger snapshot.
        """
        ser_id = request.ser_id
        if not ser_id:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("ser_id is required")
            return RecordEventResponse()

        store = self._get_or_create_store(ser_id)
        recorded = store.append(request)
        state = store.replay()
        ledger = personality_to_ledger(state)

        return RecordEventResponse(
            sequence_number=recorded.sequence_number,
            ledger=ledger,
        )

    # -- ReplayEvents --------------------------------------------------------

    def ReplayEvents(self, request: ReplayEventsRequest, context) -> PersonalityLedger:
        """Replay events to reconstruct the ledger at a point in time.

        If ``up_to_sequence`` is 0, replays all events.
        """
        ser_id = request.ser_id
        if ser_id not in self._stores:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Being {ser_id!r} not found")
            return PersonalityLedger()

        store = self._stores[ser_id]
        state = store.replay(up_to_sequence=request.up_to_sequence)
        return personality_to_ledger(state)

    # -- StreamEvents --------------------------------------------------------

    def StreamEvents(self, request: StreamEventsRequest, context):
        """Stream events for a Being (server-side streaming).

        Yields events with sequence_number > ``from_sequence``.
        """
        ser_id = request.ser_id
        if ser_id not in self._stores:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Being {ser_id!r} not found")
            return

        store = self._stores[ser_id]
        events = store.get_events_since(request.from_sequence)
        for event in events:
            yield event
