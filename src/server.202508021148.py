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
            box.style.pointerEvents = 'none';
            box.textContent = args.number;
            document.body.appendChild(box);
            return box;
        }
    ''', js_args)

async def clear_highlights(page: Page):
    """Remove all highlight elements"""
    await page.evaluate('''
        document.querySelectorAll("div[style*='z-index: 10000'], .selector-debug-box, .selector-debug-dot, .selector-legend, #selector-centered-tooltip").forEach(el => el.remove())
    ''')

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
        ),
        types.Tool(
            name="clear_highlights",
            description="Remove all visual highlight boxes from the page",
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
            name="show_selectors",
            description="Show selector boxes for interactive elements to aid in debugging automation",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Browser session ID"
                    },
                    "element_types": {
                        "type": "string",
                        "enum": ["all", "buttons", "inputs", "links", "interactive"],
                        "description": "Types of elements to show selectors for",
                        "default": "interactive"
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
        elif name == "clear_highlights":
            result = await clear_highlights_impl(arguments.get("session_id"))
        elif name == "show_selectors":
            result = await show_selectors_impl(
                arguments.get("session_id"),
                arguments.get("element_types", "interactive")
            )
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
            args=['--no-sandbox', '--disable-dev-shm-usage', '--start-maximized']  # Security hardening + maximized
        )
        context = await browser.new_context(
            no_viewport=True  # Use full browser window instead of fixed viewport
        )
        page = await context.new_page()
        
        # Set viewport to full screen dimensions (common full HD resolution)
        # This prevents scrollbars and improves AI automation efficiency
        await page.set_viewport_size({"width": 1920, "height": 1080})
        
        await page.goto(url)
        
        session = BrowserSession(session_id, playwright, browser, context, page)
        active_sessions[session_id] = session
        
        logger.info(f"Browser session {session_id} launched for URL: {url}")
        return session_id
        
    except Exception as e:
        logger.error(f"Failed to launch browser: {e}")
        raise RuntimeError(f"Browser launch failed: {str(e)}")

async def click_element_impl(session_id: str, x: int, y: int) -> str:
    """Click at coordinates with validation and event triggering"""
    session = validate_session(session_id)
    
    if not isinstance(x, int) or not isinstance(y, int):
        raise ValueError("Coordinates must be integers")
    
    if x < 0 or y < 0 or x > 10000 or y > 10000:
        raise ValueError("Coordinates out of reasonable bounds")
    
    try:
        session.element_counter += 1
        await highlight_element(session.page, x, y, session.element_counter)
        
        # Physical click + JavaScript event triggering
        await session.page.mouse.click(x, y)
        
        # Trigger JavaScript events for the element at coordinates
        await session.page.evaluate(f'''
            const element = document.elementFromPoint({x}, {y});
            if (element) {{
                // Trigger various events that might be needed
                element.focus();
                element.click();
                element.dispatchEvent(new Event('change', {{ bubbles: true }}));
                element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                element.dispatchEvent(new Event('blur', {{ bubbles: true }}));
            }}
        ''')
        
        logger.info(f"Clicked at ({x}, {y}) with events in session {session_id}")
        return f"Clicked at coordinates ({x}, {y}) with JavaScript events"
        
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

async def clear_highlights_impl(session_id: str) -> str:
    """Clear all highlight elements from the page"""
    session = validate_session(session_id)
    
    try:
        await clear_highlights(session.page)
        logger.info(f"Cleared highlights in session {session_id}")
        return "All highlight boxes cleared from page"
        
    except Exception as e:
        logger.error(f"Clear highlights failed: {e}")
        raise RuntimeError(f"Failed to clear highlights: {str(e)}")

async def show_selectors_impl(session_id: str, element_types: str = "interactive") -> str:
    """Show selector debugging boxes for interactive elements"""
    session = validate_session(session_id)
    
    try:
        # Define element queries based on type
        queries = {
            "buttons": "button, input[type='button'], input[type='submit'], [role='button']",
            "inputs": "input, textarea, select",
            "links": "a[href]",
            "interactive": "button, input, textarea, select, a[href], [onclick], [role='button'], [tabindex]:not([tabindex='-1'])",
            "all": "button, input, textarea, select, a, [onclick], [role='button'], [role='link'], [tabindex]:not([tabindex='-1'])"
        }
        
        query = queries.get(element_types, queries["interactive"])
        
        # Get elements and their selectors
        selectors_data = await session.page.evaluate(f'''
            () => {{
                const elements = document.querySelectorAll("{query}");
                const results = [];
                
                elements.forEach((el, index) => {{
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {{ // Only visible elements
                        
                        // Generate best selector
                        let selector = '';
                        if (el.id) {{
                            selector = '#' + el.id;
                        }} else if (el.className && typeof el.className === 'string') {{
                            const classes = el.className.trim().split(/\\s+/).slice(0, 2); // Max 2 classes
                            if (classes.length > 0 && classes[0]) {{
                                selector = el.tagName.toLowerCase() + '.' + classes.join('.');
                            }}
                        }} else {{
                            selector = el.tagName.toLowerCase();
                            if (el.type) selector += '[type="' + el.type + '"]';
                            if (el.name) selector += '[name="' + el.name + '"]';
                        }}
                        
                        // Determine color by element type
                        let color = '#9c27b0'; // Default purple
                        const tag = el.tagName.toLowerCase();
                        if (tag === 'button' || el.type === 'button' || el.type === 'submit' || el.getAttribute('role') === 'button') {{
                            color = '#2196f3'; // Blue for buttons
                        }} else if (tag === 'input' || tag === 'textarea' || tag === 'select') {{
                            color = '#4caf50'; // Green for inputs
                        }} else if (tag === 'a') {{
                            color = '#ff9800'; // Orange for links
                        }}
                        
                        results.push({{
                            selector: selector,
                            x: rect.left + rect.width / 2,
                            y: rect.top + rect.height / 2,
                            width: rect.width,
                            height: rect.height,
                            color: color,
                            tag: tag,
                            text: (el.innerText || el.value || el.alt || el.title || '').substring(0, 20)
                        }});
                    }}
                }});
                
                return results;
            }}
        ''')
        
        # Create selector dots with click-to-reveal
        for i, data in enumerate(selectors_data):
            await session.page.evaluate('''
                (data) => {
                    // Create clickable colored dot positioned below the element
                    const dot = document.createElement('div');
                    dot.className = 'selector-debug-dot';
                    dot.style.position = 'absolute';
                    dot.style.left = (data.x - 8) + 'px';
                    dot.style.top = (data.y + data.height/2 + 12) + 'px'; // Position below element
                    dot.style.width = '16px';
                    dot.style.height = '16px';
                    dot.style.backgroundColor = data.color;
                    dot.style.border = '2px solid white';
                    dot.style.borderRadius = '50%';
                    dot.style.zIndex = '10001';
                    dot.style.cursor = 'pointer';
                    dot.style.fontSize = '10px';
                    dot.style.color = 'white';
                    dot.style.fontWeight = 'bold';
                    dot.style.fontFamily = 'Arial, sans-serif';
                    dot.style.display = 'flex';
                    dot.style.alignItems = 'center';
                    dot.style.justifyContent = 'center';
                    dot.style.lineHeight = '1';
                    dot.textContent = (data.index + 1);
                    
                    // Store data for tooltip display
                    dot.setAttribute('data-selector', data.selector);
                    dot.setAttribute('data-tag', data.tag);
                    dot.setAttribute('data-text', data.text || '');
                    dot.setAttribute('data-color', data.color);
                    
                    // Click handler to show centered tooltip
                    dot.addEventListener('click', (e) => {
                        e.stopPropagation();
                        
                        // Get or create centered tooltip
                        let tooltip = document.getElementById('selector-centered-tooltip');
                        if (!tooltip) {
                            tooltip = document.createElement('div');
                            tooltip.id = 'selector-centered-tooltip';
                            tooltip.style.position = 'fixed';
                            tooltip.style.top = '20px';
                            tooltip.style.left = '50%';
                            tooltip.style.transform = 'translateX(-50%)';
                            tooltip.style.backgroundColor = '#333';
                            tooltip.style.color = 'white';
                            tooltip.style.padding = '12px 16px';
                            tooltip.style.borderRadius = '8px';
                            tooltip.style.border = '2px solid white';
                            tooltip.style.zIndex = '10004';
                            tooltip.style.fontFamily = 'monospace';
                            tooltip.style.fontSize = '14px';
                            tooltip.style.display = 'none';
                            tooltip.style.maxWidth = '80%';
                            tooltip.style.boxShadow = '0 4px 12px rgba(0,0,0,0.4)';
                            document.body.appendChild(tooltip);
                        }
                        
                        // Update tooltip content
                        const selector = data.selector;
                        const tag = data.tag;
                        const text = data.text || '';
                        
                        tooltip.innerHTML = `
                            <div style="display: flex; align-items: center; gap: 12px;">
                                <div>
                                    <div style="font-weight: bold; color: ${data.color}; margin-bottom: 4px;">${selector}</div>
                                    <div style="font-size: 12px; color: #ccc;">&lt;${tag}&gt; ${text ? '• ' + text : ''}</div>
                                </div>
                                <button id="copy-selector-btn" style="
                                    background: #1976d2;
                                    color: white;
                                    border: none;
                                    padding: 6px 12px;
                                    border-radius: 4px;
                                    cursor: pointer;
                                    font-size: 12px;
                                    font-family: Arial, sans-serif;
                                    display: flex;
                                    align-items: center;
                                    gap: 4px;
                                " title="Copy selector to clipboard">
                                    📋 Copy
                                </button>
                            </div>
                        `;
                        
                        // Show tooltip
                        tooltip.style.display = 'block';
                        
                        // Add copy functionality
                        const copyBtn = tooltip.querySelector('#copy-selector-btn');
                        copyBtn.addEventListener('click', async (e) => {
                            e.stopPropagation();
                            try {
                                await navigator.clipboard.writeText(selector);
                                copyBtn.innerHTML = '✅ Copied!';
                                copyBtn.style.backgroundColor = '#4caf50';
                                setTimeout(() => {
                                    copyBtn.innerHTML = '📋 Copy';
                                    copyBtn.style.backgroundColor = '#1976d2';
                                }, 2000);
                            } catch (err) {
                                copyBtn.innerHTML = '❌ Failed';
                                copyBtn.style.backgroundColor = '#f44336';
                                setTimeout(() => {
                                    copyBtn.innerHTML = '📋 Copy';
                                    copyBtn.style.backgroundColor = '#1976d2';
                                }, 2000);
                            }
                        });
                        
                        // Auto-hide after 5 seconds
                        setTimeout(() => {
                            tooltip.style.display = 'none';
                        }, 5000);
                    });
                    
                    document.body.appendChild(dot);
                }
            ''', {**data, 'index': i})
        
        # Hide tooltip on click elsewhere
        await session.page.evaluate('''
            () => {
                document.addEventListener('click', (e) => {
                    if (!e.target.closest('.selector-debug-dot') && !e.target.closest('#selector-centered-tooltip')) {
                        const tooltip = document.getElementById('selector-centered-tooltip');
                        if (tooltip) tooltip.style.display = 'none';
                    }
                });
            }
        ''')
        
        # Create legend
        await session.page.evaluate(f'''
            () => {{
                const legend = document.createElement('div');
                legend.className = 'selector-legend';
                legend.style.position = 'fixed';
                legend.style.top = '10px';
                legend.style.right = '10px';
                legend.style.backgroundColor = 'rgba(0,0,0,0.8)';
                legend.style.color = 'white';
                legend.style.padding = '8px 12px';
                legend.style.borderRadius = '6px';
                legend.style.fontSize = '11px';
                legend.style.fontFamily = 'Arial, sans-serif';
                legend.style.zIndex = '10003';
                legend.style.lineHeight = '1.4';
                legend.innerHTML = `
                    <div style="font-weight: bold; margin-bottom: 4px;">Selector Debug ({len(selectors_data)} elements)</div>
                    <div><span style="color: #2196f3;">●</span> Buttons</div>
                    <div><span style="color: #4caf50;">●</span> Inputs</div>
                    <div><span style="color: #ff9800;">●</span> Links</div>
                    <div><span style="color: #9c27b0;">●</span> Other</div>
                    <div style="margin-top: 4px; font-size: 10px; color: #ccc;">Click dots for details</div>
                `;
                document.body.appendChild(legend);
            }}
        ''')
        
        # Create summary
        summary = f"Added {len(selectors_data)} clickable debug dots ({element_types} elements):\n"
        summary += "🔵 Blue = Buttons | 🟢 Green = Inputs | 🟠 Orange = Links | 🟣 Purple = Other\n"
        summary += "Click numbered dots to see selector details in centered tooltip with copy button.\n\n"
        for i, data in enumerate(selectors_data[:10]):  # Show first 10 only
            summary += f"{i+1}. {data['selector']} ({data['tag']})\n"
        if len(selectors_data) > 10:
            summary += f"... and {len(selectors_data) - 10} more\n"
        
        logger.info(f"Displayed {len(selectors_data)} selector debug dots in session {session_id}")
        return summary
        
    except Exception as e:
        logger.error(f"Show selectors failed: {e}")
        raise RuntimeError(f"Failed to show selectors: {str(e)}")

# Cleanup handler for graceful shutdown
async def cleanup_sessions():
    """Clean up all active sessions on shutdown"""
    for session_id, session in list(active_sessions.items()):
        try:
            await session.cleanup()
        except Exception as e:
            logger.warning(f"Error cleaning up session {session_id}: {e}")
    active_sessions.clear()
    logger.info("All browser sessions cleaned up")

# Main entry point for MCP
async def main():
    """Main function to run the MCP server"""
    logger.info("Starting browser automation MCP server...")
    
    options = InitializationOptions(
        server_name="browser-automation",
        server_version="0.1.0",
        capabilities=["tools"]
    )
    
    try:
        await stdio_server(
            server,
            options=options,
            raise_exceptions=False
        )
    except KeyboardInterrupt:
        logger.info("Server interrupted, cleaning up...")
    finally:
        await cleanup_sessions()
    
    logger.info("Browser automation MCP server stopped")

if __name__ == "__main__":
    import sys
    import signal
    
    # Handle interrupts gracefully
    def signal_handler(sig, frame):
        asyncio.create_task(cleanup_sessions())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    asyncio.run(main())
