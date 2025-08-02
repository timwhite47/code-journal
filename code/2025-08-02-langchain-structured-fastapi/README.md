# LangChain Structured FastAPI Demo

A demonstration of integrating LangChain's structured outputs with FastAPI to create reliable LLM-powered APIs.

## Features

- FastAPI endpoint with Pydantic models
- LangChain structured outputs using OpenAI
- Animal joke generation with structured responses
- Error handling and validation
- Type-safe API responses

## Setup

1. Install dependencies with Poetry:
```bash
poetry install
```

2. Create a `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

3. Run the development server:
```bash
poetry run uvicorn main:app --reload
```

4. Visit `http://localhost:8000/docs` to see the interactive API documentation.

## API Endpoints

### GET /joke/{animal}

Generate a structured joke about the specified animal.

**Path Parameters:**
- `animal`: One of: cat, dog, elephant, penguin, monkey

**Response:**
```json
{
  "setup": "Why don't elephants use computers?",
  "punchline": "They're afraid of the mouse!",
  "rating": 7
}
```

## Testing

Run tests with:
```bash
poetry run pytest
```

## Project Structure

- `main.py` - FastAPI application with endpoints
- `models.py` - Pydantic models for requests/responses
- `services.py` - LangChain service for LLM interactions
- `test_api.py` - API tests
