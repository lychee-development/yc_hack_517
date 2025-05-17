from fastmcp import FastMCP, Context
from fastmcp.prompts.prompt import Message
from datetime import datetime, timedelta
import os

from dotenv import load_dotenv
import asyncio
from exa_py import Exa

# Create the FastMCP server
mcp = FastMCP(name="NY Elections Server")

timestep = 0
start_date = datetime(2025, 5, 10)  # May 10th, 2025

# Get API key from environment or use the provided key
# In production, this should be stored in an environment variable
load_dotenv()
EXA_API_KEY = os.environ.get("EXA_API_KEY")

# Initialize Exa client
exa = Exa(EXA_API_KEY)

@mcp.tool()
async def search_election_news(query: str, max_results: int = 5, ctx: Context = None) -> dict:
    """Search for relevant news and articles about NYC elections or related topics.

    Args:
        query: The search query to find news about NYC elections
        max_results: Maximum number of results to return

    Returns:
        A dictionary containing search results and snippets
    """
    global timestep

    # Calculate the current date based on the timestep
    current_date = start_date + timedelta(days=timestep - 1)

    # Format date for Exa API
    current_date_str = current_date.strftime("%Y-%m-%d")

    # Log the search if context is available
    if ctx:
        await ctx.info(f"Searching for news: '{query}' on {current_date_str}")

    # When calling the Exa API
    search_results = exa.search_and_contents(
        query,
        start_published_date=current_date_str,
        end_published_date=current_date_str,
        num_results=max_results,
        text=True
    )

    # Debug the structure of search_results
    if ctx:
        await ctx.info(f"Type of search_results: {type(search_results)}")
        await ctx.info(f"Dir of search_results: {dir(search_results)}")

    # Process results to include important info and limit content length
    processed_results = []

    # Try different ways of accessing the results
    results_list = []

    # Option 1: Try accessing as a dictionary
    try:
        if isinstance(search_results, dict) and "results" in search_results:
            results_list = search_results["results"]
            if ctx:
                await ctx.info("Accessed results as dictionary")
    except (TypeError, KeyError):
        pass

    # Option 2: Try accessing as an attribute
    if not results_list:
        try:
            if hasattr(search_results, "results"):
                results_list = search_results.results
                if ctx:
                    await ctx.info("Accessed results as attribute")
        except AttributeError:
            pass

    # Option 3: Try accessing as a method
    if not results_list:
        try:
            if callable(getattr(search_results, "results", None)):
                results_list = search_results.results()
                if ctx:
                    await ctx.info("Accessed results as method")
        except (AttributeError, TypeError):
            pass

    # Option 4: Check if search_results itself is iterable and treat it as the results
    if not results_list:
        try:
            # Check if it's iterable but not a string
            if hasattr(search_results, "__iter__") and not isinstance(search_results, (str, bytes)):
                results_list = list(search_results)
                if ctx:
                    await ctx.info("Treated search_results as iterable results")
        except (TypeError, ValueError):
            pass

    # If we couldn't determine the structure, log and return empty results
    if not results_list and ctx:
        await ctx.info(f"Unable to extract results from search_results")
        # Last resort: convert the entire object to a string for debugging
        await ctx.info(f"Search results content: {str(search_results)}")

    # Process each result with defensive programming
    for result in results_list:
        # Debug the first result structure
        if ctx and len(processed_results) == 0:
            if isinstance(result, dict):
                await ctx.info(f"Result is a dictionary with keys: {result.keys()}")
            else:
                await ctx.info(f"Result is of type {type(result)} with attributes: {dir(result)}")

        # Initialize the processed result
        processed_result = {"title": "No title", "url": "", "published_date": "", "source": "Unknown source", "snippet": ""}

        # Extract title
        if isinstance(result, dict):
            processed_result["title"] = result.get("title", "No title")
        elif hasattr(result, "title"):
            processed_result["title"] = result.title

        # Extract URL
        if isinstance(result, dict):
            processed_result["url"] = result.get("url", "")
        elif hasattr(result, "url"):
            processed_result["url"] = result.url

        # Extract published date (try different field names)
        if isinstance(result, dict):
            processed_result["published_date"] = result.get("publishedDate", result.get("published_date", ""))
        else:
            if hasattr(result, "publishedDate"):
                processed_result["published_date"] = result.publishedDate
            elif hasattr(result, "published_date"):
                processed_result["published_date"] = result.published_date

        # Extract source (which might be nested)
        if isinstance(result, dict):
            if "source" in result and isinstance(result["source"], dict) and "domain" in result["source"]:
                processed_result["source"] = result["source"]["domain"]
            elif "domain" in result:
                processed_result["source"] = result["domain"]
        else:
            if hasattr(result, "source") and hasattr(result.source, "domain"):
                processed_result["source"] = result.source.domain
            elif hasattr(result, "domain"):
                processed_result["source"] = result.domain

        # Extract text/snippet
        if isinstance(result, dict):
            text = result.get("text", "")
            processed_result["snippet"] = text[:500] + "..." if len(text) > 500 else text
        elif hasattr(result, "text"):
            text = result.text
            processed_result["snippet"] = text[:500] + "..." if len(text) > 500 else text

        processed_results.append(processed_result)

    return {
        "query": query,
        "date": current_date_str,
        "results_count": len(processed_results),
        "results": processed_results
    }

# Init resource function that returns a hardcoded JSON dictionary
@mcp.resource("resource://init")
def init() -> dict:
    """Initialize the NYC Mayoral Elections simulation with context and demographic data."""
    return {
        "context": "This is a simulation of the New York City mayoral elections. You are going to pretend to be a person, whose demographics will be given to you. Each day, you will have the option to make a decision or read the news. Based on this, make a decision for the New York city mayoral election.",
        "demographic_info": [
            [
                ["Democrat", 68],
                ["Republican", 12],
                ["Independent", 20]
            ],
            [
                ["White", 32],
                ["Black", 24],
                ["Hispanic", 29],
                ["Asian", 14],
                ["Other", 1]
            ],
            [
                ["Manhattan", 19],
                ["Brooklyn", 31],
                ["Queens", 27],
                ["Bronx", 17],
                ["Staten Island", 6]
            ]
        ],
        "options": ["Andrew Cuomo", "Zohran Mamdani", "Eric Adams", "Curtis Sliwa"]
    }

# Next timestep resource
@mcp.resource("resource://next_timestep")
def next_timestep() -> str:
    """Advance the simulation to the next time step."""
    global timestep

    # Increment timestep first
    timestep += 1

    # Calculate the current date based on the timestep
    date = (start_date + timedelta(days=timestep - 1)).strftime("%Y-%m-%d")

    res = f"The current day is {date}, news searches will be for this specific date."
    return res

# Prompts to explain demographic info - names match exactly with demographics
@mcp.prompt(name="Democrat")
def democrat() -> str:
    """Explain the Democrat demographic."""
    return """Democrats in New York City make up about 68% of registered voters.
    They typically support:
    - Progressive policies
    - Expanded social services
    - Housing affordability initiatives
    - Public transportation improvements
    - Police reform and criminal justice reform
    Democrats dominate NYC politics and have won most recent mayoral elections."""

@mcp.prompt(name="Republican")
def republican() -> str:
    """Explain the Republican demographic."""
    return """Republicans in New York City make up about 12% of registered voters.
    They typically support:
    - Tougher approaches to crime and public safety
    - Lower taxes and business-friendly policies
    - Less regulation on real estate development
    - Support for police departments
    Republicans have stronger representation in Staten Island and parts of Queens."""

@mcp.prompt(name="Independent")
def independent() -> str:
    """Explain the Independent demographic."""
    return """Independents in New York City make up about 20% of voters.
    They have diverse political views and tend to:
    - Vote based on candidate qualifications rather than party
    - Focus on quality-of-life issues in the city
    - Cross party lines depending on the election
    - Care about pragmatic solutions to city problems
    Independents can be crucial swing voters in competitive elections."""

@mcp.prompt(name="White")
def white() -> str:
    """Explain the White demographic."""
    return """White voters make up about 32% of the New York City electorate.
    This demographic:
    - Is concentrated in Manhattan, parts of Brooklyn, Queens, and Staten Island
    - Has varying voting patterns depending on neighborhood and income level
    - Includes diverse ethnic backgrounds with different voting tendencies
    - Often splits between progressive and moderate candidates"""

@mcp.prompt(name="Black")
def black() -> str:
    """Explain the Black demographic."""
    return """Black voters make up about 24% of the New York City electorate.
    This demographic:
    - Has strong representation in parts of Brooklyn, Queens, and the Bronx
    - Historically votes Democratic by significant margins
    - Represents a crucial voting bloc in citywide elections
    - Focuses on issues like affordable housing, policing, education, and economic opportunity"""

@mcp.prompt(name="Hispanic")
def hispanic() -> str:
    """Explain the Hispanic demographic."""
    return """Hispanic voters make up about 29% of the New York City electorate.
    This demographic:
    - Includes diverse communities (Puerto Rican, Dominican, Mexican, and others)
    - Has strong presence in the Bronx, parts of Queens, and Brooklyn
    - Tends to vote Democratic but with varying turnout rates
    - Prioritizes issues like affordable housing, education, immigration, and economic mobility"""

@mcp.prompt(name="Asian")
def asian() -> str:
    """Explain the Asian demographic."""
    return """Asian voters make up about 14% of the New York City electorate.
    This demographic:
    - Is the fastest-growing demographic group in NYC
    - Has strong presence in Queens, Brooklyn, and Manhattan
    - Includes diverse communities (Chinese, South Asian, Korean, Filipino, and others)
    - Shows increasing political engagement and representation
    - Focuses on issues like public safety, education, small business support, and anti-discrimination"""

@mcp.prompt(name="Other")
def other() -> str:
    """Explain the Other demographic category."""
    return """Other demographic groups make up about 1% of the New York City electorate.
    This category:
    - Includes Native American, Pacific Islander, multiracial, and other voters
    - Has diverse political perspectives and concerns
    - Often focuses on representation and inclusion in city policies"""

@mcp.prompt(name="Manhattan")
def manhattan() -> str:
    """Explain the Manhattan borough demographic."""
    return """Manhattan represents about 19% of NYC voters.
    This borough:
    - Has the highest income and education levels in the city
    - Features stark economic contrasts between neighborhoods
    - Tends to support progressive candidates on social issues but sometimes moderate/centrist on economic policy
    - Prioritizes issues like housing affordability, transportation, and quality of life
    - Has high voter turnout compared to other boroughs"""

@mcp.prompt(name="Brooklyn")
def brooklyn() -> str:
    """Explain the Brooklyn borough demographic."""
    return """Brooklyn represents about 31% of NYC voters, the largest borough by population.
    This borough:
    - Has undergone significant gentrification in many neighborhoods
    - Features highly diverse communities and voting patterns
    - Contains both progressive strongholds and more moderate/conservative areas
    - Shows increasing political activism and engagement
    - Prioritizes housing affordability, education, and community development"""

@mcp.prompt(name="Queens")
def queens() -> str:
    """Explain the Queens borough demographic."""
    return """Queens represents about 27% of NYC voters.
    This borough:
    - Is the most ethnically diverse county in the United States
    - Has strong immigrant communities with growing political influence
    - Features a mix of urban and suburban neighborhoods
    - Tends to be more moderate than Brooklyn or Manhattan
    - Focuses on issues like transportation, education, and small business support"""

@mcp.prompt(name="Bronx")
def bronx() -> str:
    """Explain the Bronx borough demographic."""
    return """The Bronx represents about 17% of NYC voters.
    This borough:
    - Has the lowest median income in the city
    - Contains predominantly Black and Hispanic communities
    - Strongly supports Democratic candidates
    - Prioritizes affordable housing, jobs, healthcare access, and economic development
    - Historically has lower voter turnout than other boroughs"""

@mcp.prompt(name="Staten Island")
def staten_island() -> str:
    """Explain the Staten Island borough demographic."""
    return """Staten Island represents about 6% of NYC voters, the smallest borough by population.
    This borough:
    - Is the most conservative borough in NYC
    - Has elected Republican officials more frequently than other boroughs
    - Contains a higher percentage of white voters than other boroughs
    - Often feels disconnected from the rest of NYC
    - Focuses on transportation, property taxes, and maintaining neighborhood character"""
