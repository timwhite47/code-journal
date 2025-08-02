#!/usr/bin/env python3
"""
Simple script to test the API manually.
Run this after starting the server to verify everything works.
"""

import asyncio
import aiohttp
import json


async def test_api():
    """Test the API endpoints manually."""
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        print("🧪 Testing LangChain FastAPI Demo")
        print("=" * 50)
        
        # Test root endpoint
        print("\n📋 Testing root endpoint...")
        async with session.get(f"{base_url}/") as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Root endpoint works: {data['message']}")
                print(f"📋 Available animals: {', '.join(data['available_animals'])}")
            else:
                print(f"❌ Root endpoint failed: {response.status}")
        
        # Test animals list
        print("\n🐾 Testing animals list...")
        async with session.get(f"{base_url}/animals") as response:
            if response.status == 200:
                animals = await response.json()
                print(f"✅ Animals endpoint works: {len(animals)} animals available")
            else:
                print(f"❌ Animals endpoint failed: {response.status}")
        
        # Test joke generation for each animal
        animals = ["cat", "dog", "elephant", "penguin", "monkey"]
        
        for animal in animals:
            print(f"\n😄 Testing joke for {animal}...")
            async with session.get(f"{base_url}/joke/{animal}") as response:
                if response.status == 200:
                    joke = await response.json()
                    print(f"✅ Joke generated successfully!")
                    print(f"   Setup: {joke['setup']}")
                    print(f"   Punchline: {joke['punchline']}")
                    print(f"   Rating: {joke.get('rating', 'N/A')}/10")
                else:
                    print(f"❌ Joke generation failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
        
        # Test invalid animal
        print(f"\n🚫 Testing invalid animal (unicorn)...")
        async with session.get(f"{base_url}/joke/unicorn") as response:
            if response.status == 422:
                print("✅ Invalid animal correctly rejected")
            else:
                print(f"❌ Expected 422, got {response.status}")
        
        print("\n🎉 API testing complete!")
        print("\n💡 Visit http://localhost:8000/docs for interactive documentation")


if __name__ == "__main__":
    try:
        asyncio.run(test_api())
    except KeyboardInterrupt:
        print("\n🛑 Testing interrupted by user")
    except Exception as e:
        print(f"❌ Testing failed: {e}")
        print("Make sure the server is running: poetry run uvicorn main:app --reload")
