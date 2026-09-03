from typing import Generic, TypeVar, Optional
from pydantic import BaseModel, Field

T = TypeVar("T")


class FieldWithConfidence(BaseModel, Generic[T]):
    """Wrapper encapsulating an extracted value alongside its OCR inference confidence score."""
    value: Optional[T] = None
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score from 0.0 to 1.0",
    )
    raw_snippet: Optional[str] = Field(
        default=None,
        description="Bounding box or verbatim snippet from raw prescription",
    )

    def __bool__(self) -> bool:
        return self.value is not None
