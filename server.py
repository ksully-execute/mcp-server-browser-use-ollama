#!/usr/bin/env python
import sys
import json
import logging
from fastmcp import FastMCP
from typing import Dict, Any
from playwright.async_api import async_playwright, Page

# Configure logging to use stderr
logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
logger = logging.getLogger(__name__)

async def highlight_element(page: Page, x: int, y: int, number: int, color: str = 'red'):
    """Add a numbered highlight box at the specified coordinates"""
    js_args = {'x': x - 15, 'y': y - 15, 'number': number, 'color': color}
    await page.evaluate('''
        args => {
            const box = document.createElement('div');
            box.style.position = 'absolute';
            box.style.left = args.x + 'px';
            box.style.top = args.y + 'px';
            box.style.width = '30px';
            box.style.height = '30px';
            box.style.backgroundColor = args.color;
            box.style.opacity = '0.5';
            box.style.border = '2px solid ' + args.color;
            box.style.borderRadius = '5px';
            box.style.display = 'flex';
            box.style.alignItems = 'center';
            box.style.justifyContent = 'center';
            box.style.color = 'white';
            box.style.fontWeight = 'bold';
            box.style.zIndex = '10000';
            box.textContent = args.number;
            document.body.appendChild(box);
            return box;
        }
    ''', js_args)

# Define tool descriptions
tools = [
    {
        "name": "launch_browser",
        "description": "Launch a new browser session and navigate to the specified URL",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL to navigate to"}
            },
            "required": ["url"]
        }
    },
    {
        "name": "click_element",
        "description": "Click at specific coordinates in the browser window",
        "input_schema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "The browser session ID"},
                "x": {"type": "integer", "description": "X coordinate to click"},
                "y": {"type": "integer", "description": "Y coordinate to click"}
            },
            "required": ["session_id", "x", "y"]
        }
    },
    {
        "name": "type_text",
        "description": "Type text into the currently focused element",
        "input_schema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "The browser session ID"},
                "text": {"type": "string", "description": "The text to type"}
            },
            "required": ["session_id", "text"]
        }
    },
    {
        "name": "scroll_page",
        "description": "Scroll the page up or down",
        "input_schema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "The browser session ID"},
                "direction": {
                    "type": "string",
                    "description": "Either 'up' or 'down'",
                    "enum": ["up", "down"],
                    "default": "down"
                }
            },
            "required": ["session_id"]
        }
    },
    {
        "name": "close_browser",
        "description": "Close a browser session",
        "input_schema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "The browser session ID to close"}
            },
            "required": ["session_id"]
        }
    }
]

# Initialize FastMCP server with debug disabled
mcp = FastMCP(
    "browser-use",
    debug=False,
    tool_descriptions=tools
)

# Store active browser sessions
active_browsers: Dict[str, Any] = {}
session_counter = 0
element_counter = 0

@mcp.tool()
async def launch_browser(url: str) -> str:
    """Launch a new browser session and navigate to the specified URL.
    
    Args:
        url: The URL to navigate to
    """
    global session_counter, element_counter
    session_id = str(session_counter)
    session_counter += 1
    element_counter = 0
    
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 900, 'height': 600})
        page = await context.new_page()
        await page.goto(url)
        
        active_browsers[session_id] = {
            'playwright': playwright,
            'browser': browser,
            'context': context,
            'page': page,
            'elements': {}  # Store highlighted elements
        }
        return session_id
    except Exception as e:
        logger.error(f"Error launching browser: {str(e)}", exc_info=True)
        raise

@mcp.tool()
async def click_element(session_id: str, x: int, y: int) -> str:
    """Click at specific coordinates in the browser window.
    
    Args:
        session_id: The browser session ID
        x: X coordinate to click
        y: Y coordinate to click
    """
    global element_counter
    session = active_browsers.get(session_id)
    if not session:
        raise ValueError(f"No browser session found with ID: {session_id}")
    
    try:
        page = session['page']
        element_counter += 1
        await highlight_element(page, x, y, element_counter)
        await page.mouse.click(x, y)
        return f"Clicked at coordinates ({x}, {y})"
    except Exception as e:
        logger.error(f"Error clicking element: {str(e)}", exc_info=True)
        raise

@mcp.tool()
async def type_text(session_id: str, text: str) -> str:
    """Type text into the currently focused element.
    
    Args:
        session_id: The browser session ID
        text: The text to type
    """
    session = active_browsers.get(session_id)
    if not session:
        raise ValueError(f"No browser session found with ID: {session_id}")
    
    try:
        page = session['page']
        await page.keyboard.type(text)
        return f"Typed text: {text}"
    except Exception as e:
        logger.error(f"Error typing text: {str(e)}", exc_info=True)
        raise

@mcp.tool()
async def scroll_page(session_id: str, direction: str = "down") -> str:
    """Scroll the page up or down.
    
    Args:
        session_id: The browser session ID
        direction: Either "up" or "down"
    """
    session = active_browsers.get(session_id)
    if not session:
        raise ValueError(f"No browser session found with ID: {session_id}")
    
    try:
        page = session['page']
        if direction.lower() == "down":
            await page.evaluate('window.scrollBy(0, window.innerHeight)')
        elif direction.lower() == "up":
            await page.evaluate('window.scrollBy(0, -window.innerHeight)')
        else:
            raise ValueError("Invalid direction. Use 'up' or 'down'.")
        return f"Scrolled {direction}"
    except Exception as e:
        logger.error(f"Error scrolling page: {str(e)}", exc_info=True)
        raise

@mcp.tool()
async def close_browser(session_id: str) -> str:
    """Close a browser session.
    
    Args:
        session_id: The browser session ID to close
    """
    session = active_browsers.get(session_id)
    if not session:
        raise ValueError(f"No browser session found with ID: {session_id}")
    
    try:
        await session['page'].close()
        await session['context'].close()
        await session['browser'].close()
        await session['playwright'].stop()
        del active_browsers[session_id]
        return f"Browser session {session_id} closed successfully"
    except Exception as e:
        logger.error(f"Error closing browser: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    mcp.run()
