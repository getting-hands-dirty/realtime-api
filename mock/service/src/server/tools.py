from langchain_core.tools import tool


@tool
def add(a: int, b: int):
    """Add two numbers. Please let the user know that you're adding the numbers BEFORE you call the tool"""
    return a + b

@tool
def rag_query(rag_query: str):
    """Query the RAG model with the given text, Usual User Queries should get redirected here."""
    return rag_query

TOOLS = []
