from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Animal(str, Enum):
    """Supported animals for joke generation."""
    CAT = "cat"
    DOG = "dog"
    ELEPHANT = "elephant"
    PENGUIN = "penguin"
    MONKEY = "monkey"


class Joke(BaseModel):
    """Structured joke response from the LLM."""
    setup: str = Field(description="The setup/question part of the joke")
    punchline: str = Field(description="The punchline/answer of the joke")
    rating: Optional[int] = Field(
        default=None, 
        description="How funny the joke is on a scale of 1-10",
        ge=1,
        le=10
    )


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(description="Error message")
    detail: Optional[str] = Field(default=None, description="Additional error details")
