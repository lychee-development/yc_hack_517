from fastmcp import FastMCP, Context
from fastmcp.prompts.prompt import Message

# Create the FastMCP server
mcp = FastMCP(name="NY Elections Server")

# Init resource function that returns a hardcoded JSON dictionary
@mcp.resource("resource://init")
def init() -> dict:
    """Initialize the NY Elections simulation with context and demographic data."""
    return {
        "context": "This is a simulation of the New York state elections. Candidates are competing for votes across different demographic groups.",
        "demographic_info": [
            [
                ["Republican", 25],
                ["Democrat", 45],
                ["Independent", 30]
            ],
            [
                ["White", 60],
                ["Black", 20],
                ["Hispanic", 20]
            ]
        ],
        "options": ["Gavin", "Donald", "Mike"]
    }

# Next timestep resource
@mcp.resource("resource://next_timestep")
def next_timestep() -> str:
    """Advance the simulation to the next time step."""
    return "Hello world"

# Prompts to explain demographic info
@mcp.prompt()
def explain_republican() -> str:
    """Explain the Republican demographic."""
    return """Republicans in New York make up about 25% of the voting population.
    They typically support:
    - Lower taxes
    - Smaller government
    - Conservative social policies
    - Strong national defense
    Republicans tend to be strong in upstate and rural areas of New York."""

@mcp.prompt()
def explain_democrat() -> str:
    """Explain the Democrat demographic."""
    return """Democrats in New York make up about 45% of the voting population.
    They typically support:
    - Progressive taxation
    - Expanded social services
    - Environmental regulations
    - Urban development
    Democrats have strongholds in New York City and other urban centers."""

@mcp.prompt()
def explain_independent() -> str:
    """Explain the Independent demographic."""
    return """Independents in New York make up about 30% of the voting population.
    They have diverse political views and tend to:
    - Vote based on candidate rather than party
    - Focus on specific issues rather than party platforms
    - Swing elections in competitive districts
    Independents are distributed throughout the state."""

@mcp.prompt()
def explain_white() -> str:
    """Explain the White demographic."""
    return """White voters make up about 60% of the New York electorate.
    This demographic:
    - Lives throughout the state with concentrations in suburbs and rural areas
    - Has diverse political views with regional differences
    - Tends to have higher voter turnout rates
    - Includes various ethnic backgrounds with different voting patterns"""

@mcp.prompt()
def explain_black() -> str:
    """Explain the Black demographic."""
    return """Black voters make up about 20% of the New York electorate.
    This demographic:
    - Is concentrated in urban areas, particularly in NYC
    - Historically votes Democratic by significant margins
    - Has increasing political representation
    - Focuses on issues like economic opportunity, criminal justice reform, and civil rights"""

@mcp.prompt()
def explain_hispanic() -> str:
    """Explain the Hispanic demographic."""
    return """Hispanic voters make up about 20% of the New York electorate.
    This demographic:
    - Includes diverse communities (Puerto Rican, Dominican, Mexican, and others)
    - Is growing in electoral importance
    - Tends to vote Democratic but with regional and generational variations
    - Prioritizes issues like immigration reform, education, and economic opportunity"""

if __name__ == "__main__":
    mcp.run()
