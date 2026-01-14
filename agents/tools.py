from agents.state import AgentState
from langchain_community.tools import DuckDuckGoSearchRun
from typing import List
from src.stagehand.get_image import get_image_link
import asyncio


# -------------------------
# Web search helper
# -------------------------
def web_search(query: str) -> str:
    search = DuckDuckGoSearchRun()
    return search.run(query)


# -------------------------
# Search tool node
# -------------------------
def search_tool(state: AgentState) -> AgentState:
    """
    Executes web search using the user's last query.
    If query contains 'image' or 'photo', it searches for images.
    """
    query = state["tool_input"][-1] if state.get("tool_input") else ""

    # Check if this is an image search request
    is_image_search = any(keyword in query.lower() for keyword in ['image', 'photo', 'picture', 'show me'])
    
    result = web_search(query)
    print(f"Search result: {result}")
    
    # Add metadata to help response generator format correctly
    if is_image_search:
        state["tool_output"].append(f"IMAGE_SEARCH: {query}\n{result}")
    else:
        state["tool_output"].append(f"{query}:\n{result}")
    
    return state


def fetch_images(query: str):
    """
    Fetches image URLs based on the query.
    """
    # Run in a separate thread to avoid signal handler issues with Streamlit
    import concurrent.futures
    import threading
    
    def run_async_in_thread():
        """Helper to run async code in a dedicated thread"""
        try:
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Run the async function
                result = loop.run_until_complete(get_image_link(query))
                return result
            finally:
                loop.close()
        except Exception as e:
            print(f"Error in async thread: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    try:
        # Execute in a separate thread to handle signal registration
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_async_in_thread)
            image_url = future.result(timeout=30)  # 30 second timeout
            return image_url
    except concurrent.futures.TimeoutError:
        print(f"Timeout fetching image for query: {query}")
        return None
    except Exception as e:
        print(f"Error fetching image: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def image_search_tool(state: AgentState) -> AgentState:
    """
    LangGraph tool node for image search.
    """
    query = state["tool_input"][-1] if state.get("tool_input") else ""

    image_result = fetch_images(query)
    # Handle both string URLs and ImageInfo objects
    if image_result:
        if isinstance(image_result, str):
            image_url = image_result
        elif hasattr(image_result, 'image_url'):
            image_url = image_result.image_url
        else:
            image_url = str(image_result)
        
        print(f"Fetched image URL: {image_url}")
        state["images"].append(image_url)
        state["tool_output"].append(f"Image search for '{query}': {image_url}")
    else:
        print(f"Failed to fetch image for query: {query}")
        state["tool_output"].append(f"Could not find image for '{query}'")

    return state
