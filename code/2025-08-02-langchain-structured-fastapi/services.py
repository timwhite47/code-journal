import os
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

from models import Joke, Animal

# Load environment variables
load_dotenv()


class JokeService:
    """Service for generating structured jokes using LangChain and OpenAI."""
    
    def __init__(self):
        """Initialize the service with OpenAI LLM."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Initialize the LLM
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",  # Using the efficient mini model
            temperature=0.7,      # Some creativity for humor
            api_key=api_key
        )
        
        # Configure structured output
        self.structured_llm = self.llm.with_structured_output(Joke)
        
        # Create the prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a comedian who creates family-friendly jokes about animals. 
            Generate a joke about the specified animal that follows this structure:
            - A setup (question or statement that leads to the punchline)
            - A punchline (the funny response/answer)
            - A rating from 1-10 for how funny you think the joke is
            
            Keep the jokes clean, clever, and suitable for all ages."""),
            ("user", "Create a joke about a {animal}")
        ])
        
        # Create the chain
        self.chain = self.prompt | self.structured_llm
    
    async def generate_joke(self, animal: Animal) -> Joke:
        """
        Generate a structured joke about the specified animal.
        
        Args:
            animal: The animal to create a joke about
            
        Returns:
            Joke: A structured joke with setup, punchline, and rating
            
        Raises:
            Exception: If the LLM request fails
        """
        try:
            # Invoke the chain with the animal
            result = await self.chain.ainvoke({"animal": animal.value})
            return result
        except Exception as e:
            raise Exception(f"Failed to generate joke: {str(e)}")


# Create a global instance for dependency injection
joke_service = JokeService()
