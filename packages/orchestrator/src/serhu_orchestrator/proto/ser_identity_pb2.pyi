import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EventType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    EVENT_TYPE_UNSPECIFIED: _ClassVar[EventType]
    BEING_CREATED: _ClassVar[EventType]
    TRAIT_UPDATE: _ClassVar[EventType]
    MILESTONE_ACHIEVED: _ClassVar[EventType]
    STAGE_TRANSITION: _ClassVar[EventType]
    BELIEF_ADDED: _ClassVar[EventType]
    SLEEP_CYCLE_COMPLETED: _ClassVar[EventType]
    INTERACTION_PROCESSED: _ClassVar[EventType]
EVENT_TYPE_UNSPECIFIED: EventType
BEING_CREATED: EventType
TRAIT_UPDATE: EventType
MILESTONE_ACHIEVED: EventType
STAGE_TRANSITION: EventType
BELIEF_ADDED: EventType
SLEEP_CYCLE_COMPLETED: EventType
INTERACTION_PROCESSED: EventType

class HexacoFacet(_message.Message):
    __slots__ = ("score",)
    SCORE_FIELD_NUMBER: _ClassVar[int]
    score: float
    def __init__(self, score: _Optional[float] = ...) -> None: ...

class TciSubscale(_message.Message):
    __slots__ = ("score",)
    SCORE_FIELD_NUMBER: _ClassVar[int]
    score: float
    def __init__(self, score: _Optional[float] = ...) -> None: ...

class SchwartzValue(_message.Message):
    __slots__ = ("score",)
    SCORE_FIELD_NUMBER: _ClassVar[int]
    score: float
    def __init__(self, score: _Optional[float] = ...) -> None: ...

class DevelopmentStage(_message.Message):
    __slots__ = ("stage", "erikson_conflict", "cognitive_age", "interaction_count", "milestones_achieved")
    STAGE_FIELD_NUMBER: _ClassVar[int]
    ERIKSON_CONFLICT_FIELD_NUMBER: _ClassVar[int]
    COGNITIVE_AGE_FIELD_NUMBER: _ClassVar[int]
    INTERACTION_COUNT_FIELD_NUMBER: _ClassVar[int]
    MILESTONES_ACHIEVED_FIELD_NUMBER: _ClassVar[int]
    stage: str
    erikson_conflict: str
    cognitive_age: float
    interaction_count: int
    milestones_achieved: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, stage: _Optional[str] = ..., erikson_conflict: _Optional[str] = ..., cognitive_age: _Optional[float] = ..., interaction_count: _Optional[int] = ..., milestones_achieved: _Optional[_Iterable[str]] = ...) -> None: ...

class PersonalityLedger(_message.Message):
    __slots__ = ("ser_id", "cognitive_age_days", "piaget_stage", "hexaco", "tci_temperament", "tci_character", "schwartz", "development", "name", "language", "core_beliefs", "surface_beliefs")
    class HexacoEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: HexacoFacet
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[HexacoFacet, _Mapping]] = ...) -> None: ...
    class TciTemperamentEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: TciSubscale
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[TciSubscale, _Mapping]] = ...) -> None: ...
    class TciCharacterEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: TciSubscale
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[TciSubscale, _Mapping]] = ...) -> None: ...
    class SchwartzEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: SchwartzValue
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[SchwartzValue, _Mapping]] = ...) -> None: ...
    SER_ID_FIELD_NUMBER: _ClassVar[int]
    COGNITIVE_AGE_DAYS_FIELD_NUMBER: _ClassVar[int]
    PIAGET_STAGE_FIELD_NUMBER: _ClassVar[int]
    HEXACO_FIELD_NUMBER: _ClassVar[int]
    TCI_TEMPERAMENT_FIELD_NUMBER: _ClassVar[int]
    TCI_CHARACTER_FIELD_NUMBER: _ClassVar[int]
    SCHWARTZ_FIELD_NUMBER: _ClassVar[int]
    DEVELOPMENT_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    CORE_BELIEFS_FIELD_NUMBER: _ClassVar[int]
    SURFACE_BELIEFS_FIELD_NUMBER: _ClassVar[int]
    ser_id: str
    cognitive_age_days: int
    piaget_stage: str
    hexaco: _containers.MessageMap[str, HexacoFacet]
    tci_temperament: _containers.MessageMap[str, TciSubscale]
    tci_character: _containers.MessageMap[str, TciSubscale]
    schwartz: _containers.MessageMap[str, SchwartzValue]
    development: DevelopmentStage
    name: str
    language: str
    core_beliefs: _containers.RepeatedScalarFieldContainer[str]
    surface_beliefs: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, ser_id: _Optional[str] = ..., cognitive_age_days: _Optional[int] = ..., piaget_stage: _Optional[str] = ..., hexaco: _Optional[_Mapping[str, HexacoFacet]] = ..., tci_temperament: _Optional[_Mapping[str, TciSubscale]] = ..., tci_character: _Optional[_Mapping[str, TciSubscale]] = ..., schwartz: _Optional[_Mapping[str, SchwartzValue]] = ..., development: _Optional[_Union[DevelopmentStage, _Mapping]] = ..., name: _Optional[str] = ..., language: _Optional[str] = ..., core_beliefs: _Optional[_Iterable[str]] = ..., surface_beliefs: _Optional[_Iterable[str]] = ...) -> None: ...

class PersonalityEvent(_message.Message):
    __slots__ = ("event_id", "ser_id", "event_type", "timestamp", "sequence_number", "trait_update", "milestone", "stage_transition", "belief", "sleep_cycle", "interaction", "being_created")
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    SER_ID_FIELD_NUMBER: _ClassVar[int]
    EVENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    SEQUENCE_NUMBER_FIELD_NUMBER: _ClassVar[int]
    TRAIT_UPDATE_FIELD_NUMBER: _ClassVar[int]
    MILESTONE_FIELD_NUMBER: _ClassVar[int]
    STAGE_TRANSITION_FIELD_NUMBER: _ClassVar[int]
    BELIEF_FIELD_NUMBER: _ClassVar[int]
    SLEEP_CYCLE_FIELD_NUMBER: _ClassVar[int]
    INTERACTION_FIELD_NUMBER: _ClassVar[int]
    BEING_CREATED_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    ser_id: str
    event_type: EventType
    timestamp: _timestamp_pb2.Timestamp
    sequence_number: int
    trait_update: TraitUpdatePayload
    milestone: MilestonePayload
    stage_transition: StageTransitionPayload
    belief: BeliefPayload
    sleep_cycle: SleepCyclePayload
    interaction: InteractionPayload
    being_created: BeingCreatedPayload
    def __init__(self, event_id: _Optional[str] = ..., ser_id: _Optional[str] = ..., event_type: _Optional[_Union[EventType, str]] = ..., timestamp: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., sequence_number: _Optional[int] = ..., trait_update: _Optional[_Union[TraitUpdatePayload, _Mapping]] = ..., milestone: _Optional[_Union[MilestonePayload, _Mapping]] = ..., stage_transition: _Optional[_Union[StageTransitionPayload, _Mapping]] = ..., belief: _Optional[_Union[BeliefPayload, _Mapping]] = ..., sleep_cycle: _Optional[_Union[SleepCyclePayload, _Mapping]] = ..., interaction: _Optional[_Union[InteractionPayload, _Mapping]] = ..., being_created: _Optional[_Union[BeingCreatedPayload, _Mapping]] = ...) -> None: ...

class TraitUpdatePayload(_message.Message):
    __slots__ = ("deltas",)
    class DeltasEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: FacetDeltas
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[FacetDeltas, _Mapping]] = ...) -> None: ...
    DELTAS_FIELD_NUMBER: _ClassVar[int]
    deltas: _containers.MessageMap[str, FacetDeltas]
    def __init__(self, deltas: _Optional[_Mapping[str, FacetDeltas]] = ...) -> None: ...

class FacetDeltas(_message.Message):
    __slots__ = ("values",)
    class ValuesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    VALUES_FIELD_NUMBER: _ClassVar[int]
    values: _containers.ScalarMap[str, float]
    def __init__(self, values: _Optional[_Mapping[str, float]] = ...) -> None: ...

class MilestonePayload(_message.Message):
    __slots__ = ("milestone_id", "new_cognitive_age")
    MILESTONE_ID_FIELD_NUMBER: _ClassVar[int]
    NEW_COGNITIVE_AGE_FIELD_NUMBER: _ClassVar[int]
    milestone_id: str
    new_cognitive_age: float
    def __init__(self, milestone_id: _Optional[str] = ..., new_cognitive_age: _Optional[float] = ...) -> None: ...

class StageTransitionPayload(_message.Message):
    __slots__ = ("from_stage", "to_stage", "new_erikson_conflict")
    FROM_STAGE_FIELD_NUMBER: _ClassVar[int]
    TO_STAGE_FIELD_NUMBER: _ClassVar[int]
    NEW_ERIKSON_CONFLICT_FIELD_NUMBER: _ClassVar[int]
    from_stage: str
    to_stage: str
    new_erikson_conflict: str
    def __init__(self, from_stage: _Optional[str] = ..., to_stage: _Optional[str] = ..., new_erikson_conflict: _Optional[str] = ...) -> None: ...

class BeliefPayload(_message.Message):
    __slots__ = ("belief_type", "content")
    BELIEF_TYPE_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    belief_type: str
    content: str
    def __init__(self, belief_type: _Optional[str] = ..., content: _Optional[str] = ...) -> None: ...

class SleepCyclePayload(_message.Message):
    __slots__ = ("num_rollouts", "svd_rank", "facts_extracted", "beliefs_added")
    NUM_ROLLOUTS_FIELD_NUMBER: _ClassVar[int]
    SVD_RANK_FIELD_NUMBER: _ClassVar[int]
    FACTS_EXTRACTED_FIELD_NUMBER: _ClassVar[int]
    BELIEFS_ADDED_FIELD_NUMBER: _ClassVar[int]
    num_rollouts: int
    svd_rank: int
    facts_extracted: int
    beliefs_added: int
    def __init__(self, num_rollouts: _Optional[int] = ..., svd_rank: _Optional[int] = ..., facts_extracted: _Optional[int] = ..., beliefs_added: _Optional[int] = ...) -> None: ...

class InteractionPayload(_message.Message):
    __slots__ = ("role", "content")
    ROLE_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    role: str
    content: str
    def __init__(self, role: _Optional[str] = ..., content: _Optional[str] = ...) -> None: ...

class BeingCreatedPayload(_message.Message):
    __slots__ = ("name", "language")
    NAME_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    name: str
    language: str
    def __init__(self, name: _Optional[str] = ..., language: _Optional[str] = ...) -> None: ...

class GetLedgerRequest(_message.Message):
    __slots__ = ("ser_id",)
    SER_ID_FIELD_NUMBER: _ClassVar[int]
    ser_id: str
    def __init__(self, ser_id: _Optional[str] = ...) -> None: ...

class RecordEventResponse(_message.Message):
    __slots__ = ("sequence_number", "ledger")
    SEQUENCE_NUMBER_FIELD_NUMBER: _ClassVar[int]
    LEDGER_FIELD_NUMBER: _ClassVar[int]
    sequence_number: int
    ledger: PersonalityLedger
    def __init__(self, sequence_number: _Optional[int] = ..., ledger: _Optional[_Union[PersonalityLedger, _Mapping]] = ...) -> None: ...

class ReplayEventsRequest(_message.Message):
    __slots__ = ("ser_id", "up_to_sequence")
    SER_ID_FIELD_NUMBER: _ClassVar[int]
    UP_TO_SEQUENCE_FIELD_NUMBER: _ClassVar[int]
    ser_id: str
    up_to_sequence: int
    def __init__(self, ser_id: _Optional[str] = ..., up_to_sequence: _Optional[int] = ...) -> None: ...

class StreamEventsRequest(_message.Message):
    __slots__ = ("ser_id", "from_sequence")
    SER_ID_FIELD_NUMBER: _ClassVar[int]
    FROM_SEQUENCE_FIELD_NUMBER: _ClassVar[int]
    ser_id: str
    from_sequence: int
    def __init__(self, ser_id: _Optional[str] = ..., from_sequence: _Optional[int] = ...) -> None: ...
