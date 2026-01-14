import asyncio
import os
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from stagehand import StagehandConfig, Stagehand

# Load environment variables
load_dotenv()

class ImageInfo(BaseModel):
    image_url: str = Field(..., description="The direct URL to the source image file")
    alt_text: Optional[str] = Field(None, description="The descriptive text for the image")

async def get_image_link(query: str):
    """
    Uses Stagehand to find and extract the first image URL for a given query.
    """
    config = StagehandConfig(
        env="LOCAL", 
        model_name="google/gemini-2.5-flash", 
        model_api_key=os.getenv("GEMINI_API_KEY"),
    )

    stagehand = Stagehand(config)

    try:
        print(f"🔍 Searching for image: '{query}'...")
        await stagehand.init()
        page = stagehand.page

        # Navigate to Google Images
        search_url = f"https://www.google.com/search?q={query}&tbm=isch"
        await page.goto(search_url)

        # Extract using the schema
        result = await page.extract(
            instruction="Extract the URL of the first high-quality image result in the grid.",
            schema=ImageInfo
        )

        return result

    except Exception as e:
        print(f"❌ An error occurred: {str(e)}")
        return None
    finally:
        await stagehand.close()

async def main():
    # Example usage:
    search_query = input("Enter what you want an image of: ") or "apple"
    
    # FIX: We use 'await' here because get_image_link is async
    result = await get_image_link(search_query)

    if result and result.image_url:
        print("\n" + "="*50)
        print(f"✅ Found Image Link: {result.image_url}")
        if result.alt_text:
            print(f"📝 Description: {result.alt_text}")
        print("="*50)
    else:
        print("Could not find a valid image link.")

if __name__ == "__main__":
    # Start the event loop
    asyncio.run(main())