import os
import asyncio
import json
import re
from typing import List, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_tavily import TavilySearch
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from tavily import TavilyClient

# Load environment variables
load_dotenv()


@dataclass
class FactCheckResult:
    """Result of fact checking a single claim"""

    text: str
    truthfulness: str  # "TRUE" | "FALSE" | "SOMEWHAT TRUE"
    summary: str
    sources: List[Dict[str, str]]  # List of {"url": "...", "favicon": "..."}


class AsyncFactChecker:
    """Async fact checker using LangChain and Tavily"""

    def __init__(self):
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        if not self.openai_api_key or not self.tavily_api_key:
            raise ValueError("Missing TAVILY_API_KEY or OPENAI_API_KEY in environment")

        # Initialize components
        self.model = init_chat_model("openai:gpt-4o-mini")
        self.memory = MemorySaver()
        self.search = TavilySearch(max_results=3)
        self.tavily_client = TavilyClient(api_key=self.tavily_api_key)

        # Initialize fact collection list
        self.collected_facts = []

        # Set up agent with tools
        self.tools = [
            self._create_extract_quotes_tool(),
            self._create_verify_fact_tool(),
            self._create_add_fact_tool(),
        ]
        self.agent_executor = create_react_agent(
            self.model, self.tools, checkpointer=self.memory
        )

    def _create_extract_quotes_tool(self):
        """Create tool for extracting factual quotes"""

        @tool
        def extract_factual_quotes(content: str) -> str:
            """Extract statements that are presented as factual verbatim"""
            print(
                f"🔍 EXTRACT_QUOTES: Starting fact extraction from content ({len(content)} chars)"
            )

            if len(content) > 8000:
                content = content[:8000] + "... [truncated]"
                print(f"📏 EXTRACT_QUOTES: Truncated content to 8000 chars")

            print(f"📄 EXTRACT_QUOTES: Content preview: {content[:200]}...")

            quote_extraction_prompt = f"""
            Extract statements that are presented as factual verbatim. Look for:
            - Quotes with certain statements
            - Statements that provide concrete information
            - Quotes that describe experiences, situations, conditions, numbers, people
            
            Return ONLY these factual style quotes, one per line. Do not add explanations or commentary.
            If no factual quotes exist, return only: "No factual quotes found"
            
            Content:
            {content}
            
            Factual quotes:
            """

            print(f"🤖 EXTRACT_QUOTES: Sending prompt to OpenAI...")
            response = self.model.invoke(
                [HumanMessage(content=quote_extraction_prompt)]
            )

            print(f"✅ EXTRACT_QUOTES: Got response from OpenAI:")
            print(f"📝 EXTRACT_QUOTES: Response content: {response.content}")

            return response.content

        return extract_factual_quotes

    def _create_verify_fact_tool(self):
        """Create tool for verifying facts with sources"""

        @tool
        def verify_fact(fact: str) -> str:
            """Search for information about a fact using Tavily and determine truthfulness with sources."""
            print(f"🔍 VERIFY_FACT: Starting verification for fact: '{fact}'")

            try:
                # Use TavilySearch to find information about this fact
                print(f"🌐 VERIFY_FACT: Searching Tavily for: '{fact}'")
                search_results = self.search.run(fact)
                print(f"📊 VERIFY_FACT: Got search results from Tavily:")
                print(f"📄 VERIFY_FACT: Search results: {str(search_results)[:500]}...")

                verification_prompt = f"""
                You are a fact-checker. Based on the Tavily search results below, determine if the following fact is:
                - TRUE: Supported by reliable sources and evidence
                - SOMEWHAT TRUE: Partially correct but missing context or contains minor inaccuracies
                - FALSE: Contradicted by reliable sources or no credible evidence found
                
                Fact to verify: "{fact}"
                
                Tavily search results:
                {search_results}
                
                Instructions:
                - Analyze the search results carefully
                - Look for credible sources and evidence
                - Consider the reliability of the information
                - Provide your assessment as: TRUE, SOMEWHAT TRUE, or FALSE
                - Give a brief explanation (1-2 sentences) for your decision
                - Extract URLs from the search results as sources
                
                Format your response EXACTLY as:
                Status: [TRUE/SOMEWHAT TRUE/FALSE]
                Summary: [Your brief explanation]
                Sources: [Comma-separated list of URLs from search results]
                """

                print(f"🤖 VERIFY_FACT: Sending verification prompt to OpenAI...")
                response = self.model.invoke(
                    [HumanMessage(content=verification_prompt)]
                )

                print(f"✅ VERIFY_FACT: Got verification response from OpenAI:")
                print(f"📝 VERIFY_FACT: Response content: {response.content}")

                return response.content

            except Exception as e:
                print(f"❌ VERIFY_FACT: Error during verification: {str(e)}")
                return f"Status: FALSE\nSummary: Error during fact verification: {str(e)}\nSources: "

        return verify_fact

    def _create_add_fact_tool(self):
        """Create tool for adding verified facts to the collection"""

        @tool
        def add_fact(
            fact_text: str, truthfulness: str, summary: str, sources: str
        ) -> str:
            """Add a fact check result to the collection.

            Args:
                fact_text: The actual claim or statement being fact-checked
                truthfulness: Must be exactly "TRUE", "FALSE", or "SOMEWHAT TRUE"
                summary: Brief explanation of the fact check result (1-2 sentences)
                sources: Comma-separated list of URLs used as sources

            Returns:
                Confirmation message
            """
            print(f"📝 ADD_FACT: Adding fact to collection")
            print(f"   🎯 Fact: {fact_text}")
            print(f"   📊 Truthfulness: {truthfulness}")
            print(f"   💬 Summary: {summary}")
            print(f"   🔗 Sources: {sources}")

            # Clean up the fact text - remove quotes, escape characters, and extra whitespace
            clean_fact_text = fact_text.strip()
            # Remove outer quotes if they exist
            if clean_fact_text.startswith('"') and clean_fact_text.endswith('"'):
                clean_fact_text = clean_fact_text[1:-1]
            # Remove any remaining escaped quotes
            clean_fact_text = clean_fact_text.replace('\\"', '"')
            # Remove any extra whitespace
            clean_fact_text = clean_fact_text.strip()

            print(f"🧹 ADD_FACT: Cleaned fact text: '{clean_fact_text}'")

            # Validate truthfulness
            valid_truthfulness = ["TRUE", "FALSE", "SOMEWHAT TRUE"]
            if truthfulness not in valid_truthfulness:
                error_msg = f"Invalid truthfulness '{truthfulness}'. Must be one of: {valid_truthfulness}"
                print(f"❌ ADD_FACT: {error_msg}")
                return error_msg

            # Parse sources
            source_urls = []
            if sources and sources.strip():
                # Split by comma and clean up URLs
                for url in sources.split(","):
                    url = url.strip()
                    if url.startswith("http"):
                        source_urls.append(url)

            print(f"🌐 ADD_FACT: Parsed {len(source_urls)} source URLs")

            # Generate sources with favicons
            source_objects = []
            for url in source_urls[:3]:  # Limit to 3 sources
                try:
                    from urllib.parse import urlparse

                    domain = urlparse(url).netloc
                    favicon_url = f"https://{domain}/favicon.ico"
                    source_objects.append({"url": url, "favicon": favicon_url})
                except:
                    source_objects.append(
                        {
                            "url": url,
                            "favicon": "https://www.google.com/favicon.ico",
                        }
                    )

            # Add default source if none found
            if not source_objects:
                default_url = (
                    "https://www.google.com/search?q="
                    + clean_fact_text.replace(" ", "+")
                )
                source_objects = [
                    {
                        "url": default_url,
                        "favicon": "https://www.google.com/favicon.ico",
                    }
                ]
                print(f"🔗 ADD_FACT: Added default source")

            # Create fact result with cleaned text
            fact_result = FactCheckResult(
                text=clean_fact_text,
                truthfulness=truthfulness,
                summary=summary,
                sources=source_objects,
            )

            # Add to collection
            self.collected_facts.append(fact_result)

            success_msg = (
                f"Successfully added fact #{len(self.collected_facts)} to collection"
            )
            print(f"✅ ADD_FACT: {success_msg}")
            return success_msg

        return add_fact

    async def extract_content_from_url(self, url: str) -> str:
        """Extract content from URL using Tavily"""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, lambda: self.tavily_client.extract(url)
            )

            # Handle different response formats from Tavily
            if isinstance(response, dict):
                # Check if there are results
                if "results" in response and response["results"]:
                    # Extract content from first result
                    return response["results"][0].get("content", str(response))
                else:
                    # No results found or failed extraction
                    return f"No content extracted from {url}. Response: {str(response)}"
            elif isinstance(response, str):
                return response
            else:
                return str(response)

        except Exception as e:
            raise Exception(f"Failed to extract content from {url}: {str(e)}")

    async def analyze_facts_with_ai(self, content: str) -> List[FactCheckResult]:
        """Extract and verify facts from content using AI agent"""
        print(
            f"🚀 ANALYZE_FACTS: Starting AI analysis of content ({len(content)} chars)"
        )

        try:
            # Clear any previous facts
            self.collected_facts = []
            print(f"🔄 ANALYZE_FACTS: Cleared previous facts collection")

            config = {"configurable": {"thread_id": f"fact_check_{hash(content)}"}}
            print(
                f"⚙️ ANALYZE_FACTS: Config created with thread_id: fact_check_{hash(content)}"
            )

            fact_check_request = f"""
            You MUST fact-check this article using the available tools. Follow these steps EXACTLY:
            
            1. Use extract_factual_quotes to find factual statements
            2. For EACH factual statement you find:
               a) Use verify_fact to check truthfulness  
               b) IMMEDIATELY use add_fact to save the result
               c) USE THE EXACT TEXT OF THE FACT. DO NOT PARAPHRASE OR SUMMARIZE THE FACT. IT MUST BE VERBATIM OR IT WILL BE REJECTED.
                  IT MUST BE EXACTLY AS IT IS IN THE ORIGINAL SOURCE.
            
            CRITICAL: You MUST call add_fact for every single fact you verify. Do NOT just summarize - use the add_fact tool!
            
            Example of what you should do:
            - Call extract_factual_quotes
            - Find fact: "Vaccines cause autism"
            - Call verify_fact with "Vaccines cause autism"
            - Get result: Status: FALSE, Summary: No evidence..., Sources: url1,url2
            - Call add_fact("Vaccines cause autism", "FALSE", "No evidence supports this claim", "url1,url2")

            REMEMBER THAT THE TEXT OF THE FACT IS THE EXACT VERBATIM TEXT FROM THE ORIGINAL SOURCE.
            DO NOT PARAPHRASE OR SUMMARIZE THE FACT. IT MUST BE VERBATIM OR IT WILL BE REJECTED.
            IT MUST BE EXACTLY AS IT IS IN THE ORIGINAL SOURCE.
            
            Here is the article content:
            {content}
            
            Start by extracting quotes, then verify and add EACH fact using the tools.
            """

            print(f"📝 ANALYZE_FACTS: Created fact check request")
            print(f"📄 ANALYZE_FACTS: Request preview: {fact_check_request[:300]}...")

            # Run agent in thread pool to avoid blocking
            print(f"🔄 ANALYZE_FACTS: Starting agent execution in thread pool...")
            loop = asyncio.get_event_loop()
            agent_response = await loop.run_in_executor(
                None,
                lambda: self.agent_executor.invoke(
                    {"messages": [HumanMessage(content=fact_check_request)]},
                    config=config,
                ),
            )

            print(f"✅ ANALYZE_FACTS: Agent execution completed")
            print(
                f"📊 ANALYZE_FACTS: Collected {len(self.collected_facts)} facts using add_fact tool"
            )

            # Return the collected facts directly
            return self.collected_facts

        except Exception as e:
            print(f"❌ ANALYZE_FACTS: Error in analyze_facts_with_ai: {str(e)}")
            import traceback

            print(f"📊 ANALYZE_FACTS: Traceback: {traceback.format_exc()}")
            return []


# Global instance
_fact_checker = None


async def get_fact_checker() -> AsyncFactChecker:
    """Get or create fact checker instance"""
    global _fact_checker
    if _fact_checker is None:
        _fact_checker = AsyncFactChecker()
    return _fact_checker


async def extract_content_from_url_async(url: str) -> str:
    """Async wrapper for content extraction"""
    fact_checker = await get_fact_checker()
    return await fact_checker.extract_content_from_url(url)


async def analyze_facts_with_ai_async(content: str) -> List[FactCheckResult]:
    """Async wrapper for fact analysis"""
    fact_checker = await get_fact_checker()
    return await fact_checker.analyze_facts_with_ai(content)
