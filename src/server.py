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
        "name": "click_selector",
        "description": "Click an element identified by a CSS selector",
        "input_schema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "The browser session ID"},
                "selector": {"type": "string", "description": "CSS selector to identify the element"}
            },
            "required": ["session_id", "selector"]
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
        "name": "get_page_content",
        "description": "Get the text content of the current page for analysis",
        "input_schema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "The browser session ID"}
            },
            "required": ["session_id"]
        }
    },
    {
        "name": "get_dom_structure",
        "description": "Get a simplified DOM structure of the current page",
        "input_schema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "The browser session ID"},
                "max_depth": {"type": "integer", "description": "Maximum depth of DOM tree to return", "default": 3}
            },
            "required": ["session_id"]
        }
    },
    {
        "name": "take_screenshot",
        "description": "Take a screenshot and return a description of the visual content",
        "input_schema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "The browser session ID"}
            },
            "required": ["session_id"]
        }
    },
    {
        "name": "extract_data",
        "description": "Extract structured data from the page based on a pattern",
        "input_schema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "The browser session ID"},
                "pattern": {"type": "string", "description": "Description of data to extract (e.g., 'product prices', 'article headlines')"}
            },
            "required": ["session_id", "pattern"]
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
async def click_selector(session_id: str, selector: str) -> str:
    """Click an element identified by a CSS selector.
    
    Args:
        session_id: The browser session ID
        selector: CSS selector to identify the element
    """
    session = active_browsers.get(session_id)
    if not session:
        raise ValueError(f"No browser session found with ID: {session_id}")
    
    try:
        page = session['page']
        # Wait for the selector to be available
        element = await page.wait_for_selector(selector, timeout=5000)
        if not element:
            return f"Element with selector '{selector}' not found"
        
        # Get element position for highlighting
        bounding_box = await element.bounding_box()
        if bounding_box:
            x = bounding_box['x'] + bounding_box['width'] / 2
            y = bounding_box['y'] + bounding_box['height'] / 2
            global element_counter
            element_counter += 1
            await highlight_element(page, x, y, element_counter)
        
        # Click the element
        await element.click()
        return f"Clicked element with selector: {selector}"
    except Exception as e:
        logger.error(f"Error clicking element with selector: {str(e)}", exc_info=True)
        return f"Error clicking element: {str(e)}"

@mcp.tool()
async def get_page_content(session_id: str) -> str:
    """Get the text content of the current page for analysis.
    
    Args:
        session_id: The browser session ID
    """
    session = active_browsers.get(session_id)
    if not session:
        raise ValueError(f"No browser session found with ID: {session_id}")
    
    try:
        page = session['page']
        # Extract text content from the page
        content = await page.evaluate('''
            () => {
                // Get all text nodes
                const textNodes = document.body.innerText;
                return textNodes;
            }
        ''')
        
        # Return a truncated version if it's too long
        if len(content) > 10000:
            return content[:10000] + "... (content truncated)"
        return content
    except Exception as e:
        logger.error(f"Error getting page content: {str(e)}", exc_info=True)
        return f"Error getting page content: {str(e)}"

@mcp.tool()
async def get_dom_structure(session_id: str, max_depth: int = 3) -> str:
    """Get a simplified DOM structure of the current page.
    
    Args:
        session_id: The browser session ID
        max_depth: Maximum depth of DOM tree to return
    """
    session = active_browsers.get(session_id)
    if not session:
        raise ValueError(f"No browser session found with ID: {session_id}")
    
    try:
        page = session['page']
        # Extract DOM structure using JavaScript
        dom_structure = await page.evaluate(f'''
            () => {{
                function extractDomNode(node, depth = 0, maxDepth = {max_depth}) {{
                    if (depth > maxDepth) return "...";
                    
                    // Skip comment nodes and script tags
                    if (node.nodeType === 8 || 
                        (node.tagName && node.tagName.toLowerCase() === 'script')) {{
                        return null;
                    }}
                    
                    // Text node
                    if (node.nodeType === 3) {{
                        const text = node.textContent.trim();
                        return text ? text.substring(0, 50) + (text.length > 50 ? "..." : "") : null;
                    }}
                    
                    // Element node
                    if (node.nodeType === 1) {{
                        const result = {{
                            tag: node.tagName.toLowerCase(),
                            id: node.id || undefined,
                            classes: node.className ? Array.from(node.classList) : undefined,
                        }};
                        
                        // Add important attributes
                        if (node.hasAttribute('href')) result.href = node.getAttribute('href');
                        if (node.hasAttribute('src')) result.src = node.getAttribute('src');
                        if (node.hasAttribute('alt')) result.alt = node.getAttribute('alt');
                        if (node.hasAttribute('title')) result.title = node.getAttribute('title');
                        
                        // Add children if not at max depth
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
        
        return json.dumps(dom_structure, indent=2)
    except Exception as e:
        logger.error(f"Error getting DOM structure: {str(e)}", exc_info=True)
        return f"Error getting DOM structure: {str(e)}"

@mcp.tool()
async def take_screenshot(session_id: str) -> str:
    """Take a screenshot and return a description of the visual content.
    
    Args:
        session_id: The browser session ID
    """
    session = active_browsers.get(session_id)
    if not session:
        raise ValueError(f"No browser session found with ID: {session_id}")
    
    try:
        page = session['page']
        # Take a screenshot
        screenshot_path = f"screenshot_{session_id}.png"
        await page.screenshot(path=screenshot_path)
        
        # Return a message with the path
        return f"Screenshot saved to {screenshot_path}. The image shows the current state of the browser window."
    except Exception as e:
        logger.error(f"Error taking screenshot: {str(e)}", exc_info=True)
        return f"Error taking screenshot: {str(e)}"

@mcp.tool()
async def extract_data(session_id: str, pattern: str) -> str:
    """Extract structured data from the page based on a pattern.
    
    Args:
        session_id: The browser session ID
        pattern: Description of data to extract (e.g., 'product prices', 'article headlines')
    """
    session = active_browsers.get(session_id)
    if not session:
        raise ValueError(f"No browser session found with ID: {session_id}")
    
    try:
        page = session['page']
        
        # Define extraction strategies based on common patterns
        extraction_strategies = {
            "product prices": '''
                () => {
                    const prices = [];
                    // Look for common price selectors
                    const priceElements = document.querySelectorAll('.price, [class*="price"], [id*="price"], .product-price, .amount');
                    priceElements.forEach(el => {
                        prices.push({
                            text: el.innerText.trim(),
                            location: el.getBoundingClientRect()
                        });
                    });
                    return prices;
                }
            ''',
            "article headlines": '''
                () => {
                    const headlines = [];
                    // Look for heading elements
                    const headingElements = document.querySelectorAll('h1, h2, h3, .headline, .title, article h2, article h3');
                    headingElements.forEach(el => {
                        headlines.push({
                            text: el.innerText.trim(),
                            tag: el.tagName.toLowerCase()
                        });
                    });
                    return headlines;
                }
            ''',
            "navigation links": '''
                () => {
                    const links = [];
                    // Look for navigation links
                    const navLinks = document.querySelectorAll('nav a, header a, .navigation a, .menu a');
                    navLinks.forEach(el => {
                        links.push({
                            text: el.innerText.trim(),
                            href: el.getAttribute('href')
                        });
                    });
                    return links;
                }
            ''',
            "form fields": '''
                () => {
                    const fields = [];
                    // Look for form fields
                    const formElements = document.querySelectorAll('input, textarea, select');
                    formElements.forEach(el => {
                        fields.push({
                            type: el.type || el.tagName.toLowerCase(),
                            name: el.name || '',
                            id: el.id || '',
                            placeholder: el.placeholder || ''
                        });
                    });
                    return fields;
                }
            '''
        }
        
        # Use a generic extraction if pattern doesn't match predefined strategies
        pattern_lower = pattern.lower()
        if pattern_lower not in extraction_strategies:
            # Try to infer what to extract based on the pattern
            extraction_js = f'''
                () => {{
                    // Generic extraction based on pattern: "{pattern}"
                    const elements = [];
                    // Try to find elements that might match the pattern
                    const allElements = document.querySelectorAll('*');
                    const patternLower = "{pattern}".toLowerCase();
                    
                    for (const el of allElements) {{
                        const text = el.innerText?.trim();
                        const id = el.id?.toLowerCase();
                        const className = el.className?.toLowerCase();
                        const tagName = el.tagName?.toLowerCase();
                        
                        // Check if element might be relevant to the pattern
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
                            
                            // Limit to 20 elements to avoid overwhelming results
                            if (elements.length >= 20) break;
                        }}
                    }}
                    
                    return elements;
                }}
            '''
        else:
            extraction_js = extraction_strategies[pattern_lower]
        
        # Execute the extraction
        extracted_data = await page.evaluate(extraction_js)
        
        return json.dumps(extracted_data, indent=2)
    except Exception as e:
        logger.error(f"Error extracting data: {str(e)}", exc_info=True)
        return f"Error extracting data: {str(e)}"

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
