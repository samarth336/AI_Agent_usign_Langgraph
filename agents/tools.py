from agents.state import AgentState
from langchain_community.tools import DuckDuckGoSearchRun
from typing import Any, List
from src.stagehand.get_image import get_image_link
import asyncio
import re
import json

from plugins.mcp_plugin import mcp_plugin


# -------------------------
# Web search helper
# -------------------------
def web_search(query: str) -> str:
    search = DuckDuckGoSearchRun()
    return search.run(query)


def _tool_result_to_text(result: Any) -> str:
    content = getattr(result, "content", result)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif hasattr(item, "text"):
                parts.append(str(item.text))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content)


def _extract_url(text: str) -> str | None:
    match = re.search(r"https?://[^\s]+", text)
    if not match:
        return None
    return match.group(0).rstrip(")]}.>,")


def _extract_github_username(text: str) -> str | None:
    match = re.search(r"github\.com/([^/?#\s]+)", text)
    if not match:
        return None
    return match.group(1)


def _extract_page_info(snapshot_text: str) -> tuple[str | None, str | None]:
    title_match = re.search(r"Page Title:\s*(.+)", snapshot_text)
    url_match = re.search(r"Page URL:\s*(.+)", snapshot_text)
    title = title_match.group(1).strip() if title_match else None
    url = url_match.group(1).strip() if url_match else None
    return title, url


def _extract_file_path(text: str) -> str | None:
    windows_match = re.search(r"[A-Za-z]:\\[^\s\"'<>|]+", text)
    if windows_match:
        return windows_match.group(0).rstrip(".,)\"]}>")

    unix_match = re.search(r"/[^\s\"'<>|]+", text)
    if unix_match:
        return unix_match.group(0).rstrip(".,)\"]}>")

    return None


def _format_file_read_result(path: str, content: str) -> str:
    return f"File: {path}\n\n{content}"


async def _open_and_capture_browser(query: str) -> str:
    session = await mcp_plugin.create_session("playwright")

    try:
        url = _extract_url(query)
        username = _extract_github_username(query) or (_extract_github_username(url) if url else None)

        if url:
            await session.call_tool("browser_navigate", {"url": url})

        snapshot = await session.call_tool("browser_snapshot", {})
        snapshot_text = _tool_result_to_text(snapshot)
        title, current_url = _extract_page_info(snapshot_text)

        if username and any(keyword in query.lower() for keyword in ["repo", "repository", "any repo", "go to repo"]):
            repo_page = f"https://github.com/{username}?tab=repositories"
            await session.call_tool("browser_navigate", {"url": repo_page})
            repos_snapshot = await session.call_tool("browser_snapshot", {})
            repos_text = _tool_result_to_text(repos_snapshot)

            reserved = {
                "repositories",
                "followers",
                "following",
                "stars",
                "sponsors",
                "packages",
                "projects",
                "activity",
                "orgs",
            }
            repo_match = re.search(
                rf'- link "([^"]+)" \[ref=[^\]]+\].*?- /url: (/{re.escape(username)}/[^\s\]"]+)',
                repos_text,
                re.S,
            )
            if repo_match:
                repo_href = repo_match.group(2).rstrip(")]}.>,")
                repo_name = repo_href.rsplit("/", 1)[-1]
                if repo_name not in reserved:
                    repo_url = f"https://github.com{repo_href}"
                    await session.call_tool("browser_navigate", {"url": repo_url})
                    final_snapshot = await session.call_tool("browser_snapshot", {})
                    final_text = _tool_result_to_text(final_snapshot)
                    final_title, final_url = _extract_page_info(final_text)
                    return f"Opened GitHub repo: {final_title or repo_name} ({final_url or repo_url})"

            return f"Opened GitHub repositories page for {username}: {title or 'GitHub'} ({current_url or repo_page})"

        return f"Opened page: {title or 'unknown title'} ({current_url or url or 'unknown url'})"
    finally:
        await mcp_plugin.close_session(session)


async def _read_and_capture_file(query: str) -> str:
    session = await mcp_plugin.create_session("filesystem")

    try:
        path = _extract_file_path(query)
        if not path:
            return "I could not find a file path in the request. Please provide an absolute path."

        result = await session.call_tool("read_text_file", {"path": path})
        text = _tool_result_to_text(result)

        try:
            payload = json.loads(text)
            if isinstance(payload, dict) and "content" in payload:
                text = str(payload["content"])
        except json.JSONDecodeError:
            pass

        if not text.strip():
            return f"I found the file path {path}, but the file appears empty or unreadable."

        return _format_file_read_result(path, text)
    finally:
        await mcp_plugin.close_session(session)


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


def browser_tool(state: AgentState) -> AgentState:
    """
    Opens or navigates a browser page using the Playwright MCP server.
    """
    query = state["tool_input"][-1] if state.get("tool_input") else state["task"]

    try:
        result = asyncio.run(_open_and_capture_browser(query))
        state["tool_output"].append(result)
        print(f"Browser result: {result}")
    except Exception as e:
        error_message = f"Browser action failed for '{query}': {str(e)}"
        print(error_message)
        state["tool_output"].append(error_message)

    return state


def filesystem_tool(state: AgentState) -> AgentState:
    """
    Reads a local file using the filesystem MCP server.
    """
    query = state["tool_input"][-1] if state.get("tool_input") else state["task"]

    try:
        result = asyncio.run(_read_and_capture_file(query))
        state["tool_output"].append(result)
        state["output"] = result
        print(f"Filesystem result: {result}")
    except Exception as e:
        error_message = f"Filesystem action failed for '{query}': {str(e)}"
        print(error_message)
        state["tool_output"].append(error_message)

    return state
