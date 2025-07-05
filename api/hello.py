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
search = TavilySearch(max_results=3)  # Now we're using this for fact-checking

# Create factual quotes extraction tool
@tool
def extract_factual_quotes(content: str) -> str:
    """Extract statements that are presented as factual verbatim"""
    if len(content) > 8000:
        content = content[:8000] + "... [truncated]"
    
    quote_extraction_prompt = f"""
    Extract statements that are presented as factual verbatim. Look for:
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

# Create fact verification tool using TavilySearch
@tool
def verify_fact(fact: str) -> str:
    """Search for information about a fact using Tavily and determine if it's truthful, somewhat truthful, or false."""
    
    try:
        # Use TavilySearch to find information about this fact
        print(f"🔍 Searching for: {fact}")
        search_results = search.run(fact)
        print(f"✅ Search completed, analyzing results...")
        
        verification_prompt = f"""
        You are a fact-checker. Based on the Tavily search results below, determine if the following fact is:
        - TRUTHFUL: Supported by reliable sources and evidence
        - SOMEWHAT TRUTHFUL: Partially correct but missing context or contains minor inaccuracies
        - FALSE: Contradicted by reliable sources or no credible evidence found
        
        Fact to verify: "{fact}"
        
        Tavily search results:
        {search_results}
        
        Instructions:
        - Analyze the search results carefully
        - Look for credible sources and evidence
        - Consider the reliability of the information
        - Provide your assessment as: TRUTHFUL, SOMEWHAT TRUTHFUL, or FALSE
        - Give a brief explanation (1-2 sentences) for your decision
        
        Format your response as:
        Status: [TRUTHFUL/SOMEWHAT TRUTHFUL/FALSE]
        Explanation: [Your brief explanation]
        """
        
        response = model.invoke([HumanMessage(content=verification_prompt)])
        return response.content
        
    except Exception as e:
        return f"Error during fact verification: {str(e)}"

# Set up agent with both tools
tools = [extract_factual_quotes, verify_fact]
agent_executor = create_react_agent(model, tools, checkpointer=memory)

# Extract content and get quotes
url = "https://www.cbc.ca/news/canada/first-person-refugee-small-town-canada-1.7571127"
tavily_client = TavilyClient(api_key=tavily_api_key)

try:
    # Get article content
    response = tavily_client.extract(url)
    print("✅ Done extracting Tavily response")
    # Extract and verify quotes using agent
    config = {"configurable": {"thread_id": "fact_check_session"}}
    
    fact_check_request = f"""
    Please do the following:
    
    1. First, use the extract_factual_quotes tool to find all factual statements in this article
    2. Then, for EACH factual statement you found, use the verify_fact tool to check if it's truthful
    
    Here is the article content:
    {response}
    
    Please extract the facts and then verify each one.
    """
    
    print("🤖 Agent is extracting facts and verifying them...")
    print("⏳ This will take a moment as each fact needs to be searched...")
    
    agent_response = agent_executor.invoke(
        {"messages": [HumanMessage(content=fact_check_request)]},
        config=config
    )
    
    # Print the results
    if agent_response and 'messages' in agent_response and len(agent_response['messages']) > 0:
        results = agent_response['messages'][-1].content
        print("\n📊 FACT EXTRACTION AND VERIFICATION RESULTS:")
        print("="*60)
        print(results)
    else:
        print("❌ No results could be generated.")

except Exception as e:
    print(f"❌ Error: {e}")