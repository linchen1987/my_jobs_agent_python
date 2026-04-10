from abc import ABC, abstractmethod
from typing import Optional, TypedDict


class JobListItem(TypedDict):
    id: str
    source: str
    url: str
    title: str
    extra: dict


class JobDetail(TypedDict):
    id: str
    source: str
    url: str
    title: str
    content: str
    tags: list[dict]
    list_item: JobListItem
    extra: dict


class LLMAnalysis(TypedDict):
    is_qualified: bool
    analysis: dict
    extracted_info: dict


class AnalysisResult(TypedDict):
    id: str
    source: str
    url: str
    title: str
    detail: JobDetail
    llm_analysis: LLMAnalysis
    analyzed_at: str


class AnalyzedRecord(TypedDict):
    id: str
    source: str
    url: str
    is_qualified: bool
    analyzed_at: str
    reason: str


class BaseSource(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def fetch_list(self) -> list[JobListItem]: ...

    @abstractmethod
    def fetch_detail(self, item: JobListItem) -> Optional[JobDetail]: ...

    def global_id(self, item_id: str) -> str:
        return f"{self.name}:{item_id}"
