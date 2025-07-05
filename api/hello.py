# Step 1: Install required packages
# pip install python-dotenv langchain-openai
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_tavily import TavilySearch
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from tavily import TavilyClient

# Load environment variables from .env file
load_dotenv()
# Get API keys
tavily_api_key = os.getenv("TAVILY_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

# Quick validation
if not openai_api_key or not tavily_api_key:
    print("❌ Missing API keys in .env file!")
    exit(1)

# Initialize model and components
model = init_chat_model("openai:gpt-3.5-turbo")
memory = MemorySaver()

# Create factual quotes extraction tool
@tool
def extract_factual_quotes(content: str) -> str:
    """Extract quotes that contain information stated as a fact from the content."""
    
    # Truncate if too long
    if len(content) > 8000:
        content = content[:8000] + "... [truncated]"
    
    quote_extraction_prompt = f"""
    Find all quotes in this article that contain factual information. Look for:
    - Quotes with certain statements
    - Statements that provide concrete information
    - Quotes that describe experiences, situations, or conditions, numbers, people
    
    Return ONLY these factual style quotes, one per line. Do not add explanations or commentary.
    If no factual quotes exist, return only: "No factual quotes found"
    
    Content:
    {content}
    
    Factual quotes:
    """
    
    response = model.invoke([HumanMessage(content=quote_extraction_prompt)])
    return response.content

# Set up agent
tools = [extract_factual_quotes]
agent_executor = create_react_agent(model, tools, checkpointer=memory)

# Extract content and get quotes
url = "https://www.cbc.ca/news/canada/first-person-refugee-small-town-canada-1.7571127"
tavily_client = TavilyClient(api_key=tavily_api_key)

try:
    # Get article content
    response = tavily_client.extract(url)
    print("done extracting tavily response")
    # Extract quotes using agent
    config = {"configurable": {"thread_id": "quote_extraction_session"}}
    
    quote_extraction_request = f"""
    Find all quotes in this article that contain factual information and return only those quotes:
    
    {response}
    """
    
    agent_response = agent_executor.invoke(
        {"messages": [HumanMessage(content=quote_extraction_request)]},
        config=config
    )
    
    # Print just the quotes
    if agent_response and 'messages' in agent_response and len(agent_response['messages']) > 0:
        quotes = agent_response['messages'][-1].content
        print(quotes)
    else:
        print("No quotes could be extracted.")

except Exception as e:
    print(f"Error: {e}")