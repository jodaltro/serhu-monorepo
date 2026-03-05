from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

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
