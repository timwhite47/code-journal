---
layout: post
title: "Taming the LLM Chaos: Building Actually Reliable APIs with LangChain Structured Outputs"
date: 2025-08-02
categories: [ai-coding, python]
tags: [langchain, fastapi, pydantic, openai, structured-outputs, llm]
excerpt: "So you asked an LLM for JSON and got a poem about JSON instead? Let's fix that with LangChain's structured outputs and build an animal joke API that actually behaves."
---

## The Problem: LLMs Are Magnificent Chaos Machines

So you asked an LLM for JSON and got a poem about JSON instead? Welcome to the club! 🎭

LLMs are brilliant at understanding context and generating creative responses, but they're absolutely terrible at following instructions when you need them to. Ask for a structured response and you might get:

- Perfect JSON (sometimes)
- Markdown with code blocks containing JSON (often)
- A philosophical essay about why JSON exists (surprisingly frequent)
- Complete nonsense that breaks your parser (always at the worst moment)

That moment when your frontend breaks because the AI decided to be creative with your API response format? Yeah, we've all been there. The question is: **How do you make LLMs behave in APIs without losing your sanity?**

Today we're building an animal joke API that ALWAYS returns the same structure, no matter how creative the LLM wants to get. We'll go from chaos to order, from broken parsing to type-safe responses, and from debugging nightmares to actually reliable code.

## Enter the Heroes: Our Toolkit

Before we dive into the carnage, let's meet our heroes:

**LangChain** - The AI orchestration framework that's actually useful. It gives us abstractions for working with LLMs without writing a million lines of boilerplate. More importantly, it has structured outputs that force LLMs to behave.

**Structured Outputs** - LangChain's "make the LLM behave" feature. Instead of hoping the LLM returns valid JSON, we define exactly what we want and LangChain makes it happen.

**FastAPI** - The Python API framework that doesn't hate you. Built-in type hints, automatic docs, async support, and plays beautifully with Pydantic.

**Pydantic** - Type validation that actually works. Define your data models once and get validation, serialization, and documentation for free.

The magic combo? These tools work together to eliminate the chaos. We define our response structure once in Pydantic, LangChain ensures the LLM follows it, and FastAPI serves it up with automatic validation and docs.

Here's a sneak peek at what we're building - a joke response that's guaranteed to have this exact structure:

```json
{
  "setup": "Why don't elephants use computers?",
  "punchline": "They're afraid of the mouse!",
  "rating": 7
}
```

Every. Single. Time.

## The "Aha!" Moment: Structured Outputs in Action

Let me show you the difference between chaos and order.

**Before** (the old way):
```python
# Pray to the LLM gods and hope for JSON
response = llm.invoke("Tell me a joke about cats in JSON format")
# Could be anything: {"joke": "..."} or "Here's a joke: ..." or pure chaos
```

**After** (with structured outputs):
```python
# From our models.py - this is what we're guaranteeing
class Joke(BaseModel):
    setup: str = Field(description="The setup/question part of the joke")
    punchline: str = Field(description="The punchline/answer of the joke")
    rating: Optional[int] = Field(
        default=None, 
        description="How funny the joke is on a scale of 1-10",
        ge=1, le=10
    )

# The magic happens here
structured_llm = llm.with_structured_output(Joke)
result = structured_llm.invoke("Tell me a joke about cats")
# ALWAYS returns a Joke object with setup, punchline, and rating
```

**The Magic**: `with_structured_output()` works under the hood by using OpenAI's function calling capabilities. Instead of asking the LLM to "please return JSON," it tells the LLM "you MUST call this function with these exact parameters." The LLM can't be creative with the format because it's literally calling a function.

**Why This Matters**: No more parsing nightmares. No more broken APIs. No more 3 AM debugging sessions because the LLM decided to write a haiku instead of JSON. Just guaranteed, type-safe responses.

## Building Our Joke Factory: Project Setup

**Getting Technical Now...**

Let's build something that actually works. Our project follows a clean separation of concerns that keeps us sane:

```
code/2025-08-02-langchain-structured-fastapi/
├── models.py      # Pydantic schemas (shared between LLM and API)
├── services.py    # LangChain service layer
├── main.py        # FastAPI routes and magic
└── test_api.py    # Make sure it actually works
```

**Step 1: The Data Models**

Here's our foundation from `models.py` - the contracts that everything else builds on:

```python
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
        ge=1, le=10
    )
```

Notice how we're using Pydantic's validation features? The `ge=1, le=10` ensures our rating is always between 1 and 10. The `Animal` enum means our API can only accept valid animals - no more "tell me a joke about a unicorn" requests breaking things.

**Step 2: The LangChain Service**

The service layer in `services.py` is where the LangChain magic happens:

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

class JokeService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",  # Efficient and cheap
            temperature=0.7,      # Some creativity for humor
        )
        
        # This is the key line - structured output guarantee
        self.structured_llm = self.llm.with_structured_output(Joke)
        
        # Prompt engineering for reliable jokes
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a comedian who creates family-friendly jokes about animals. 
            Generate a joke about the specified animal that follows this structure:
            - A setup (question or statement that leads to the punchline)
            - A punchline (the funny response/answer)
            - A rating from 1-10 for how funny you think the joke is
            
            Keep the jokes clean, clever, and suitable for all ages."""),
            ("user", "Create a joke about a {animal}")
        ])
        
        # Chain it all together
        self.chain = self.prompt | self.structured_llm
```

**Key Insight**: We use the same `Joke` Pydantic model for both the LLM output AND the API response. This isn't just convenient - it's the secret sauce that makes everything type-safe from end to end.

## The Implementation Deep Dive

**Now We Get Serious...**

Let's walk through how this all comes together in practice.

**The Service Layer Magic**

The real power is in how the chain works:

```python
# From services.py
async def generate_joke(self, animal: Animal) -> Joke:
    try:
        # This ALWAYS returns a Joke object, never raw text
        result = await self.chain.ainvoke({"animal": animal.value})
        return result
    except Exception as e:
        raise Exception(f"Failed to generate joke: {str(e)}")
```

When we call `self.chain.ainvoke()`, here's what happens:
1. The prompt gets formatted with our animal
2. LangChain sends it to OpenAI with function calling enabled
3. OpenAI MUST respond by calling our `Joke` function
4. LangChain automatically validates and creates the Pydantic object
5. We get back a guaranteed `Joke` instance

No parsing. No validation. No hoping. Just structured data.

**The FastAPI Integration**

Now for the API layer in `main.py`:

```python
@app.get(
    "/joke/{animal}",
    response_model=Joke,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
    },
)
async def get_joke(animal: Animal) -> Joke:
    """Generate a structured joke about the specified animal."""
    try:
        logger.info(f"Generating joke for animal: {animal.value}")
        joke = await joke_service.generate_joke(animal)
        logger.info(f"Successfully generated joke for {animal.value}")
        return joke
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    
    except Exception as e:
        logger.error(f"Error generating joke for {animal.value}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate joke. Please try again."
        )
```

**The Beautiful Parts**:

1. **Path Parameter Validation**: `animal: Animal` means FastAPI automatically validates the path parameter against our enum. Invalid animals get rejected before they hit our code.

2. **Response Model Declaration**: `response_model=Joke` tells FastAPI exactly what to expect and automatically generates OpenAPI docs.

3. **Type Safety Throughout**: From the path parameter to the LLM service to the response, everything is typed and validated.

4. **Error Handling Hierarchy**: Different exception types get different HTTP status codes. The API consumers get meaningful error messages instead of generic failures.

**The Validation Layer**

The most elegant part? Pydantic handles validation at every layer:

- **Input**: The `Animal` enum validates path parameters
- **Output**: The `Joke` model validates LLM responses
- **API**: FastAPI validates everything automatically and generates docs

If the LLM somehow returns an invalid rating (say, 15), Pydantic catches it before it leaves our service. If someone tries to request a joke about a "unicorn," the enum validation rejects it before we waste an API call.

This is defensive programming that actually works - we validate at the boundaries and trust the types in between.

## Testing Our Creation: Does It Actually Work?

**The Moment of Truth...**

Let's fire this thing up and see what happens:

```bash
# From our project directory
poetry run uvicorn main:app --reload
```

The server starts up and FastAPI automatically generates interactive docs at `http://localhost:8000/docs`. This isn't just a nice-to-have - it's a full testing interface where you can try different animals and see the structured responses.

**Manual Testing**

I included a `test_manual.py` script that hits all our endpoints:

```python
# Test each animal
for animal in ["cat", "dog", "elephant", "penguin", "monkey"]:
    async with session.get(f"{base_url}/joke/{animal}") as response:
        if response.status == 200:
            joke = await response.json()
            print(f"✅ Joke generated successfully!")
            print(f"   Setup: {joke['setup']}")
            print(f"   Punchline: {joke['punchline']}")
            print(f"   Rating: {joke.get('rating', 'N/A')}/10")
```

**What Could Go Wrong?**

The beauty of structured outputs is that most things CAN'T go wrong:

- **OpenAI API failures**: We catch and return proper HTTP 500 errors
- **Invalid animals**: FastAPI rejects them with HTTP 422 before we process them
- **Malformed LLM responses**: Impossible - Pydantic validation happens in LangChain
- **Missing fields**: The LLM is forced to provide setup and punchline (rating is optional)

**Automated Testing**

Our `test_api.py` includes proper unit tests:

```python
@patch('services.joke_service.generate_joke')
def test_get_joke_success(self, mock_generate_joke, client, mock_joke):
    """Test successful joke generation."""
    mock_generate_joke.return_value = mock_joke
    
    response = client.get("/joke/cat")
    assert response.status_code == 200
    
    data = response.json()
    assert data["setup"] == mock_joke.setup
    assert data["punchline"] == mock_joke.punchline
    assert data["rating"] == mock_joke.rating
```

We mock the LLM service for consistent testing, but the integration test validates the entire request/response cycle.

## The Payoff: What We Actually Built

**Victory Lap Time...**

Let's appreciate what we accomplished here. We started with the fundamental problem of LLM unpredictability and built a completely reliable API that:

✅ **Always returns the same JSON structure**  
✅ **Validates inputs before making expensive API calls**  
✅ **Handles errors gracefully with proper HTTP status codes**  
✅ **Generates interactive documentation automatically**  
✅ **Is fully type-safe from request to response**  

**Before vs After**:
- **Before**: Pray the LLM returns valid JSON, write brittle parsing code, debug mysterious failures
- **After**: Define your structure once, get guaranteed compliance, sleep peacefully

**What We Learned**:

1. **Structured outputs eliminate LLM unpredictability** - The LLM literally cannot return invalid data because it's calling a function, not generating free text.

2. **Shared Pydantic models create type safety throughout the stack** - One definition, validation everywhere.

3. **FastAPI + LangChain is a surprisingly smooth combo** - They both embrace Python type hints and async programming.

4. **Good architecture makes debugging actually possible** - When something breaks, you know exactly where and why.

**When to Use This Pattern**:

- Any time you need predictable LLM responses in an API
- Building services that other systems will consume
- When type safety matters more than creative freedom
- APIs that need to be reliable, not just functional

## Next Steps: Where to Go From Here

**The Adventure Continues...**

You've got a solid foundation now. Here's where you could take this:

**Extensions You Could Try**:
- **More complex response structures**: Nested objects, lists, unions
- **Multiple LLM providers**: Anthropic, local models, different endpoints  
- **Caching**: Redis integration for repeated queries (cat jokes are probably pretty similar)
- **Batch processing**: Generate jokes for multiple animals in one request

**The Code**: Everything we built is available in the `{{ site.baseurl }}/code/2025-08-02-langchain-structured-fastapi/` directory. Clone it, modify it, break it, fix it.

**Your Turn**: What will you build with structured outputs? A product description generator? A code review summarizer? A data analysis API? The pattern is the same - define your structure, let LangChain enforce it, and serve it up with FastAPI.

The chaos is tamed. The LLMs are behaving. Your APIs are reliable.

Now go build something awesome! 🚀

---

*Want to see more AI coding tutorials? Follow along as we explore the wild world of building reliable systems with unpredictable AI. Next up: streaming responses, because sometimes you want the chaos back (but controlled chaos).*
