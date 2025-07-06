"""
Tests for the MCP server implementation.
"""
import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Import server module
import server


class TestServerTools:
    """Test the MCP server tools."""
    
    @pytest.mark.asyncio
    async def test_server_has_mcp_instance(self):
        """Test that server has an MCP instance."""
        assert hasattr(server, 'mcp')
        assert server.mcp is not None
    
    @pytest.mark.asyncio
    async def test_launch_browser_tool_exists(self):
        """Test that launch_browser tool is registered."""
        # The tool should be decorated with @mcp.tool()
        assert hasattr(server, 'launch_browser')
        assert callable(server.launch_browser)
    
    @pytest.mark.asyncio
    async def test_click_element_tool_exists(self):
        """Test that click_element tool is registered."""
        assert hasattr(server, 'click_element')
        assert callable(server.click_element)
    
    @pytest.mark.asyncio
    async def test_type_text_tool_exists(self):
        """Test that type_text tool is registered."""
        assert hasattr(server, 'type_text')
        assert callable(server.type_text)
    
    @pytest.mark.asyncio
    async def test_all_required_tools_exist(self):
        """Test that all required tools exist in the server module."""
        required_tools = [
            'launch_browser',
            'click_element',
            'click_selector',
            'type_text',
            'scroll_page',
            'get_page_content',
            'get_dom_structure',
            'take_screenshot',
            'extract_data',
            'close_browser'
        ]
        
        for tool in required_tools:
            assert hasattr(server, tool), f"Tool {tool} not found in server module"
            assert callable(getattr(server, tool)), f"Tool {tool} is not callable"
    
    @pytest.mark.asyncio
    async def test_launch_browser_with_mock(self):
        """Test launch_browser function with mocked playwright."""
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        
        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        
        with patch('server.async_playwright') as mock_async_playwright:
            mock_async_playwright.return_value.start = AsyncMock(return_value=mock_playwright_instance)
            
            # Call launch_browser (no headless parameter)
            result = await server.launch_browser(url="https://example.com")
            
            # FastMCP returns strings
            assert isinstance(result, str)
            assert result.isdigit()  # Should be session ID
    
    @pytest.mark.asyncio
    async def test_error_handling_no_session(self):
        """Test error handling when session doesn't exist."""
        # Most tools require a session_id that doesn't exist
        with pytest.raises(ValueError) as exc_info:
            await server.click_element(session_id="nonexistent", x=100, y=100)
        
        assert "No browser session found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_close_browser_nonexistent_session(self):
        """Test closing a browser session that doesn't exist."""
        with pytest.raises(ValueError) as exc_info:
            await server.close_browser(session_id="nonexistent")
        
        assert "No browser session found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_screenshot_output_format(self):
        """Test that screenshot raises error when session doesn't exist."""
        # This will fail with no session
        with pytest.raises(ValueError) as exc_info:
            await server.take_screenshot(session_id="test")
        
        assert "No browser session found" in str(exc_info.value)
    
    def test_tool_descriptions_exist(self):
        """Test that tool descriptions are properly defined."""
        # Check that the tools list exists in the module
        assert hasattr(server, 'tools')
        assert isinstance(server.tools, list)
        assert len(server.tools) > 0
        
        # Check each tool has required fields
        for tool in server.tools:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool


class TestServerIntegration:
    """Integration tests for server functionality."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_browser_lifecycle(self):
        """Test a complete browser lifecycle with mocked components."""
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value="Test page content")
        mock_page.close = AsyncMock()
        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()
        
        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        
        with patch('server.async_playwright') as mock_async_playwright:
            mock_async_playwright.return_value.start = AsyncMock(return_value=mock_playwright_instance)
            
            # Launch browser
            launch_result = await server.launch_browser(url="https://example.com")
            session_id = launch_result  # FastMCP returns string session ID
            
            assert session_id is not None
            assert session_id.isdigit()
            
            # Get page content - this will be a string
            content_result = await server.get_page_content(session_id=session_id)
            assert isinstance(content_result, str)
            
            # Close browser - this will be a string  
            close_result = await server.close_browser(session_id=session_id)
            assert isinstance(close_result, str)