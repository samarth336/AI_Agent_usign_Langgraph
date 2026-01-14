import asyncio
import os
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

try:
    from stagehand import StagehandConfig, Stagehand
except ImportError:
    try:
        from stagehand.stagehand import StagehandConfig, Stagehand
    except ImportError:
        print("Warning: Stagehand not properly installed")
        StagehandConfig = None
        Stagehand = None

# Load environment variables from .env if present
load_dotenv()

class ImageInfo(BaseModel):
    """Schema for the extracted image data."""
    image_url: str = Field(..., description="The direct, high-quality source URL of the image")
    alt_text: Optional[str] = Field(None, description="The descriptive text for the image")

async def get_image_link(query: str) -> Optional[str]:
    """
    Automates a browser using Stagehand to find a high-quality image link for a query.
    
    Args:
        query (str): The search term (e.g., "apple", "spacex starship")
        
    Returns:
        Optional[str]: The image URL string, or None if failed.
    """
    
    # Check if Stagehand is available
    if StagehandConfig is None or Stagehand is None:
        print("Stagehand not available, cannot fetch images")
        return None
    
    # Configure Stagehand. You can move these to your .env file.
    config = StagehandConfig(
        env="LOCAL", 
        model_name="google/gemini-2.5-flash", 
        model_api_key=os.getenv("GEMINI_API_KEY"),
    )

    stagehand = Stagehand(config)

    try:
        await stagehand.init()
        page = stagehand.page

        # 1. Direct navigation to Google Images
        search_url = f"https://www.google.com/search?q={query}&tbm=isch"
        await page.goto(search_url)

        # 2. Click the first result to reveal the source URL in the preview pane
        # This is required to get a real URL instead of a low-res data URI
        await page.act("Click the first image result in the grid.")
        
        # Short pause for the preview pane to load
        await asyncio.sleep(1.5)

        # 3. Extract the actual source URL
        result = await page.extract(
            instruction="Extract the direct source URL of the high-resolution image from the preview panel that opened. Do not return base64 or data:image links.",
            schema=ImageInfo
        )

        # Return just the URL string
        if result and hasattr(result, 'image_url'):
            return result.image_url
        return None

    except Exception as e:
        print(f"Error in Stagehand extraction: {str(e)}")
        return None
    finally:
        await stagehand.close()