from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager

from models import Joke, Animal, ErrorResponse
from services import joke_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting up LangChain FastAPI service...")
    yield
    logger.info("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="LangChain Structured Output API",
    description="A demo API showing LangChain structured outputs with FastAPI",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "LangChain Structured Output API",
        "description": "Generate structured jokes about animals using LangChain and OpenAI",
        "docs": "/docs",
        "available_animals": [animal.value for animal in Animal]
    }


@app.get(
    "/joke/{animal}",
    response_model=Joke,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
    },
    summary="Generate an animal joke",
    description="Generate a structured joke about the specified animal using LangChain and OpenAI"
)
async def get_joke(animal: Animal) -> Joke:
    """
    Generate a structured joke about the specified animal.
    
    The API uses LangChain's structured output feature to ensure the LLM
    returns a properly formatted joke with setup, punchline, and rating.
    
    Args:
        animal: The animal to create a joke about (cat, dog, elephant, penguin, monkey)
        
    Returns:
        Joke: A structured joke with setup, punchline, and rating (1-10)
        
    Raises:
        HTTPException: If there's an error generating the joke
    """
    try:
        logger.info(f"Generating joke for animal: {animal.value}")
        joke = await joke_service.generate_joke(animal)
        logger.info(f"Successfully generated joke for {animal.value}")
        return joke
    
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
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


@app.get(
    "/animals",
    response_model=list[str],
    summary="List supported animals",
    description="Get a list of all animals supported by the joke API"
)
async def list_animals() -> list[str]:
    """Get a list of all supported animals."""
    return [animal.value for animal in Animal]


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unexpected errors."""
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "detail": "An unexpected error occurred"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
