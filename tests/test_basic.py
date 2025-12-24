"""
Basic tests for Liangent.
"""



def test_import_liangent():
    """Test that liangent can be imported."""
    from liangent import Liangent, tool
    assert Liangent is not None
    assert tool is not None


def test_tool_decorator():
    """Test the @tool decorator works."""
    from liangent import tool
    
    @tool
    def example_tool(x: int, y: int) -> int:
        """
        Add two numbers.
        
        Args:
            x: First number.
            y: Second number.
        """
        return x + y
    
    assert example_tool(2, 3) == 5


def test_sandbox_execute():
    """Test sandbox code execution."""
    from liangent.tools.sandbox import sandbox
    
    result = sandbox.execute("3 * 2")
    assert result["success"] is True
    assert "6" in result["output"]


def test_sandbox_security():
    """Test sandbox blocks dangerous operations."""
    from liangent.tools.sandbox import sandbox
    
    # Should block os module
    result = sandbox.execute("import os")
    assert result["success"] is False
    assert "not allowed" in result["error"]
