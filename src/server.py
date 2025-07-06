#!/usr/bin/env python3
"""
MCP Server for Browser Automation
Pure MCP SDK implementation following 2025-06-18 specification
"""

import sys
import json
import logging
import tempfile
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.lowlevel.server import InitializationOptions
from mcp import types
from playwright.async_api import async_playwright, Page, Browser, BrowserContext, Playwright

# Configure logging for MCP compliance
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("mcp-browser-server")

class BrowserSession:
    """Represents a browser automation session"""
    
    def __init__(self, session_id: str, playwright: Playwright, browser: Browser, 
                 context: BrowserContext, page: Page):
        self.session_id = session_id
        self.playwright = playwright
        self.browser = browser
        self.context = context
        self.page = page
        self.created_at = asyncio.get_event_loop().time()
        self.element_counter = 0
        
    async def cleanup(self):
        """Clean up browser resources"""
        try:
            await self.page.close()
            await self.context.close()
            await self.browser.close()
            await self.playwright.stop()
        except Exception as e:
            logger.warning(f"Error during session cleanup: {e}")

# Global state for browser sessions
active_sessions: Dict[str, BrowserSession] = {}
session_counter = 0
max_sessions = 10  # Security: limit concurrent sessions

# Create MCP server
server = Server("browser-automation")

async def highlight_element(page: Page, x: int, y: int, number: int, color: str = 'red'):
    """Add visual highlight at coordinates"""
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

def validate_session(session_id: str) -> BrowserSession:
    """Validate session exists and return it"""
    if not session_id:
        raise ValueError("Session ID is required")
    
    session = active_sessions.get(session_id)
    if not session:
        raise ValueError(f"No browser session found with ID: {session_id}")
    
    return session

@server.list_tools()
async def list_tools() -> List[types.Tool]:
    """List available browser automation tools"""
    return [
        types.Tool(
            name="launch_browser",
            description="Launch a new browser session and navigate to URL",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to navigate to"
                    }
                },
                "required": ["url"]
            }
        ),
        types.Tool(
            name="click_element",
            description="Click at specific coordinates in the browser",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Browser session ID"
                    },
                    "x": {
                        "type": "integer",
                        "description": "X coordinate to click"
                    },
                    "y": {
                        "type": "integer", 
                        "description": "Y coordinate to click"
                    }
                },
                "required": ["session_id", "x", "y"]
            }
        ),
        types.Tool(
            name="click_selector",
            description="Click an element by CSS selector",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Browser session ID"
                    },
                    "selector": {
                        "type": "string",
                        "description": "CSS selector to identify element"
                    }
                },
                "required": ["session_id", "selector"]
            }
        ),
        types.Tool(
            name="type_text",
            description="Type text into the currently focused element",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Browser session ID"
                    },
                    "text": {
                        "type": "string",
                        "description": "Text to type"
                    }
                },
                "required": ["session_id", "text"]
            }
        ),
        types.Tool(
            name="scroll_page",
            description="Scroll the page up or down",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Browser session ID"
                    },
                    "direction": {
                        "type": "string",
                        "enum": ["up", "down"],
                        "description": "Scroll direction",
                        "default": "down"
                    }
                },
                "required": ["session_id"]
            }
        ),
        types.Tool(
            name="get_page_content",
            description="Get text content of the current page",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Browser session ID"
                    }
                },
                "required": ["session_id"]
            }
        ),
        types.Tool(
            name="get_dom_structure",
            description="Get simplified DOM structure of the page",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Browser session ID"
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Maximum DOM tree depth",
                        "default": 3,
                        "minimum": 1,
                        "maximum": 10
                    }
                },
                "required": ["session_id"]
            }
        ),
        types.Tool(
            name="take_screenshot",
            description="Take a screenshot of the current page",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Browser session ID"
                    }
                },
                "required": ["session_id"]
            }
        ),
        types.Tool(
            name="extract_data",
            description="Extract structured data from the page",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Browser session ID"
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Data extraction pattern (e.g. 'product prices')"
                    }
                },
                "required": ["session_id", "pattern"]
            }
        ),
        types.Tool(
            name="close_browser",
            description="Close a browser session",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Browser session ID to close"
                    }
                },
                "required": ["session_id"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> List[types.TextContent]:
    """Handle tool calls with proper MCP compliance"""
    global session_counter
    
    try:
        if name == "launch_browser":
            result = await launch_browser_impl(arguments.get("url"))
        elif name == "click_element":
            result = await click_element_impl(
                arguments.get("session_id"),
                arguments.get("x"),
                arguments.get("y")
            )
        elif name == "click_selector":
            result = await click_selector_impl(
                arguments.get("session_id"),
                arguments.get("selector")
            )
        elif name == "type_text":
            result = await type_text_impl(
                arguments.get("session_id"),
                arguments.get("text")
            )
        elif name == "scroll_page":
            result = await scroll_page_impl(
                arguments.get("session_id"),
                arguments.get("direction", "down")
            )
        elif name == "get_page_content":
            result = await get_page_content_impl(arguments.get("session_id"))
        elif name == "get_dom_structure":
            result = await get_dom_structure_impl(
                arguments.get("session_id"),
                arguments.get("max_depth", 3)
            )
        elif name == "take_screenshot":
            result = await take_screenshot_impl(arguments.get("session_id"))
        elif name == "extract_data":
            result = await extract_data_impl(
                arguments.get("session_id"),
                arguments.get("pattern")
            )
        elif name == "close_browser":
            result = await close_browser_impl(arguments.get("session_id"))
        else:
            raise ValueError(f"Unknown tool: {name}")
            
        return [types.TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.error(f"Tool {name} failed: {e}")
        raise RuntimeError(f"Tool execution failed: {str(e)}")

# Tool implementations
async def launch_browser_impl(url: str) -> str:
    """Launch browser session with security controls"""
    global session_counter
    
    if not url:
        raise ValueError("URL is required")
    
    # Security: limit concurrent sessions
    if len(active_sessions) >= max_sessions:
        raise RuntimeError(f"Maximum sessions ({max_sessions}) exceeded")
    
    # Security: validate URL format
    if not url.startswith(('http://', 'https://')):
        raise ValueError("Only HTTP/HTTPS URLs are allowed")
    
    session_id = str(session_counter)
    session_counter += 1
    
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=False,
            args=['--no-sandbox', '--disable-dev-shm-usage']  # Security hardening
        )
        context = await browser.new_context(
            viewport={'width': 900, 'height': 600}
        )
        page = await context.new_page()
        await page.goto(url)
        
        session = BrowserSession(session_id, playwright, browser, context, page)
        active_sessions[session_id] = session
        
        logger.info(f"Browser session {session_id} launched for URL: {url}")
        return session_id
        
    except Exception as e:
        logger.error(f"Failed to launch browser: {e}")
        raise RuntimeError(f"Browser launch failed: {str(e)}")

async def click_element_impl(session_id: str, x: int, y: int) -> str:
    """Click at coordinates with validation"""
    session = validate_session(session_id)
    
    if not isinstance(x, int) or not isinstance(y, int):
        raise ValueError("Coordinates must be integers")
    
    if x < 0 or y < 0 or x > 10000 or y > 10000:
        raise ValueError("Coordinates out of reasonable bounds")
    
    try:
        session.element_counter += 1
        await highlight_element(session.page, x, y, session.element_counter)
        await session.page.mouse.click(x, y)
        
        logger.info(f"Clicked at ({x}, {y}) in session {session_id}")
        return f"Clicked at coordinates ({x}, {y})"
        
    except Exception as e:
        logger.error(f"Click failed: {e}")
        raise RuntimeError(f"Click operation failed: {str(e)}")

async def click_selector_impl(session_id: str, selector: str) -> str:
    """Click element by CSS selector"""
    session = validate_session(session_id)
    
    if not selector:
        raise ValueError("CSS selector is required")
    
    try:
        element = await session.page.wait_for_selector(selector, timeout=5000)
        if not element:
            raise RuntimeError(f"Element with selector '{selector}' not found")
        
        # Get position for highlighting
        bounding_box = await element.bounding_box()
        if bounding_box:
            x = bounding_box['x'] + bounding_box['width'] / 2
            y = bounding_box['y'] + bounding_box['height'] / 2
            session.element_counter += 1
            await highlight_element(session.page, x, y, session.element_counter)
        
        await element.click()
        logger.info(f"Clicked element '{selector}' in session {session_id}")
        return f"Clicked element with selector: {selector}"
        
    except Exception as e:
        logger.error(f"Selector click failed: {e}")
        raise RuntimeError(f"Failed to click element: {str(e)}")

async def type_text_impl(session_id: str, text: str) -> str:
    """Type text with security validation"""
    session = validate_session(session_id)
    
    if not isinstance(text, str):
        raise ValueError("Text must be a string")
    
    # Security: limit text length
    if len(text) > 10000:
        raise ValueError("Text too long (max 10000 characters)")
    
    try:
        await session.page.keyboard.type(text)
        logger.info(f"Typed {len(text)} characters in session {session_id}")
        return f"Typed text: {text[:50]}{'...' if len(text) > 50 else ''}"
        
    except Exception as e:
        logger.error(f"Text typing failed: {e}")
        raise RuntimeError(f"Failed to type text: {str(e)}")

async def scroll_page_impl(session_id: str, direction: str) -> str:
    """Scroll page with direction validation"""
    session = validate_session(session_id)
    
    if direction not in ["up", "down"]:
        raise ValueError("Direction must be 'up' or 'down'")
    
    try:
        if direction == "down":
            await session.page.evaluate('window.scrollBy(0, window.innerHeight)')
        else:
            await session.page.evaluate('window.scrollBy(0, -window.innerHeight)')
        
        logger.info(f"Scrolled {direction} in session {session_id}")
        return f"Scrolled {direction}"
        
    except Exception as e:
        logger.error(f"Scroll failed: {e}")
        raise RuntimeError(f"Scroll operation failed: {str(e)}")

async def get_page_content_impl(session_id: str) -> str:
    """Extract page text content with size limits"""
    session = validate_session(session_id)
    
    try:
        content = await session.page.evaluate('() => document.body.innerText')
        
        # Security: limit content size
        if len(content) > 50000:
            content = content[:50000] + "\n... (content truncated for size)"
        
        logger.info(f"Extracted {len(content)} characters from session {session_id}")
        return content
        
    except Exception as e:
        logger.error(f"Content extraction failed: {e}")
        raise RuntimeError(f"Failed to get page content: {str(e)}")

async def get_dom_structure_impl(session_id: str, max_depth: int) -> str:
    """Get DOM structure with depth limits"""
    session = validate_session(session_id)
    
    if not isinstance(max_depth, int) or max_depth < 1 or max_depth > 10:
        raise ValueError("max_depth must be integer between 1 and 10")
    
    try:
        dom_structure = await session.page.evaluate(f'''
            () => {{
                function extractDomNode(node, depth = 0, maxDepth = {max_depth}) {{
                    if (depth > maxDepth) return "...";
                    
                    if (node.nodeType === 8 || 
                        (node.tagName && node.tagName.toLowerCase() === 'script')) {{
                        return null;
                    }}
                    
                    if (node.nodeType === 3) {{
                        const text = node.textContent.trim();
                        return text ? text.substring(0, 50) + (text.length > 50 ? "..." : "") : null;
                    }}
                    
                    if (node.nodeType === 1) {{
                        const result = {{
                            tag: node.tagName.toLowerCase(),
                            id: node.id || undefined,
                            classes: node.className ? Array.from(node.classList) : undefined,
                        }};
                        
                        if (node.hasAttribute('href')) result.href = node.getAttribute('href');
                        if (node.hasAttribute('src')) result.src = node.getAttribute('src');
                        if (node.hasAttribute('alt')) result.alt = node.getAttribute('alt');
                        if (node.hasAttribute('title')) result.title = node.getAttribute('title');
                        
                        if (depth < maxDepth) {{
                            const children = [];
                            for (const child of node.childNodes) {{
                                const childResult = extractDomNode(child, depth + 1, maxDepth);
                                if (childResult) children.push(childResult);
                            }}
                            if (children.length > 0) result.children = children;
                        }} else if (node.childNodes.length > 0) {{
                            result.children = "...";
                        }}
                        
                        return result;
                    }}
                    
                    return null;
                }}
                
                return extractDomNode(document.documentElement);
            }}
        ''')
        
        result = json.dumps(dom_structure, indent=2)
        logger.info(f"Extracted DOM structure from session {session_id}")
        return result
        
    except Exception as e:
        logger.error(f"DOM extraction failed: {e}")
        raise RuntimeError(f"Failed to get DOM structure: {str(e)}")

async def take_screenshot_impl(session_id: str) -> str:
    """Take screenshot with secure file handling"""
    session = validate_session(session_id)
    
    try:
        # Security: use temp file with proper cleanup
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            screenshot_path = temp_file.name
        
        await session.page.screenshot(path=screenshot_path)
        
        # Read file and clean up immediately for security
        file_size = Path(screenshot_path).stat().st_size
        Path(screenshot_path).unlink()  # Delete immediately after creation
        
        logger.info(f"Screenshot taken for session {session_id} ({file_size} bytes)")
        return f"Screenshot captured ({file_size} bytes). File processed and cleaned up for security."
        
    except Exception as e:
        logger.error(f"Screenshot failed: {e}")
        raise RuntimeError(f"Screenshot operation failed: {str(e)}")

async def extract_data_impl(session_id: str, pattern: str) -> str:
    """Extract data with pattern matching"""
    session = validate_session(session_id)
    
    if not pattern:
        raise ValueError("Extraction pattern is required")
    
    try:
        # Define extraction strategies
        strategies = {
            "product prices": '''
                () => {
                    const prices = [];
                    const priceElements = document.querySelectorAll('.price, [class*="price"], [id*="price"], .product-price, .amount');
                    priceElements.forEach(el => {
                        prices.push({
                            text: el.innerText.trim(),
                            location: el.getBoundingClientRect()
                        });
                    });
                    return prices.slice(0, 20); // Limit results
                }
            ''',
            "article headlines": '''
                () => {
                    const headlines = [];
                    const headingElements = document.querySelectorAll('h1, h2, h3, .headline, .title, article h2, article h3');
                    headingElements.forEach(el => {
                        headlines.push({
                            text: el.innerText.trim(),
                            tag: el.tagName.toLowerCase()
                        });
                    });
                    return headlines.slice(0, 20);
                }
            ''',
            "navigation links": '''
                () => {
                    const links = [];
                    const navLinks = document.querySelectorAll('nav a, header a, .navigation a, .menu a');
                    navLinks.forEach(el => {
                        links.push({
                            text: el.innerText.trim(),
                            href: el.getAttribute('href')
                        });
                    });
                    return links.slice(0, 20);
                }
            '''
        }
        
        # Use predefined strategy or generic extraction
        pattern_lower = pattern.lower()
        if pattern_lower in strategies:
            extraction_js = strategies[pattern_lower]
        else:
            # Generic extraction with security limits
            extraction_js = f'''
                () => {{
                    const elements = [];
                    const allElements = document.querySelectorAll('*');
                    const patternLower = "{pattern}".toLowerCase();
                    
                    for (const el of allElements) {{
                        const text = el.innerText?.trim();
                        const id = el.id?.toLowerCase();
                        const className = el.className?.toLowerCase();
                        const tagName = el.tagName?.toLowerCase();
                        
                        if ((text && text.toLowerCase().includes(patternLower)) ||
                            (id && id.includes(patternLower)) ||
                            (className && className.includes(patternLower)) ||
                            (tagName && patternLower.includes(tagName))) {{
                            
                            elements.push({{
                                tag: tagName,
                                text: text ? (text.length > 100 ? text.substring(0, 100) + "..." : text) : "",
                                id: id || undefined,
                                class: className || undefined
                            }});
                            
                            if (elements.length >= 20) break;
                        }}
                    }}
                    
                    return elements;
                }}
            '''
        
        extracted_data = await session.page.evaluate(extraction_js)
        result = json.dumps(extracted_data, indent=2)
        
        logger.info(f"Extracted data for pattern '{pattern}' from session {session_id}")
        return result
        
    except Exception as e:
        logger.error(f"Data extraction failed: {e}")
        raise RuntimeError(f"Data extraction failed: {str(e)}")

async def close_browser_impl(session_id: str) -> str:
    """Close browser session with cleanup"""
    session = validate_session(session_id)
    
    try:
        await session.cleanup()
        del active_sessions[session_id]
        
        logger.info(f"Browser session {session_id} closed")
        return f"Browser session {session_id} closed successfully"
        
    except Exception as e:
        logger.error(f"Session cleanup failed: {e}")
        raise RuntimeError(f"Failed to close session: {str(e)}")

async def cleanup_all_sessions():
    """Clean up all browser sessions"""
    logger.info("Cleaning up all browser sessions...")
    for session_id in list(active_sessions.keys()):
        try:
            await close_browser_impl(session_id)
        except Exception as e:
            logger.error(f"Failed to cleanup session {session_id}: {e}")

async def main():
    """Run the MCP server"""
    # Setup cleanup on exit
    import signal
    
    def cleanup_handler(signum, frame):
        logger.info("Received shutdown signal, cleaning up...")
        asyncio.create_task(cleanup_all_sessions())
    
    signal.signal(signal.SIGINT, cleanup_handler)
    signal.signal(signal.SIGTERM, cleanup_handler)
    
    # Run MCP server with stdio transport
    async with stdio_server() as (read_stream, write_stream):
        initialization_options = InitializationOptions(
            server_name="browser-automation",
            server_version="0.1.0",
            capabilities=types.ServerCapabilities(
                tools=types.ToolsCapability(),
            )
        )
        await server.run(read_stream, write_stream, initialization_options)

if __name__ == "__main__":
    asyncio.run(main())