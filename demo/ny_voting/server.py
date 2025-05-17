from fastmcp import FastMCP, Context
from fastmcp.prompts.prompt import Message

# Create the FastMCP server
mcp = FastMCP(name="NY Elections Server")

# Init resource function that returns a hardcoded JSON dictionary
@mcp.resource("resource://init")
def init() -> dict:
    """Initialize the NYC Mayoral Elections simulation with context and demographic data."""
    return {
        "context": "This is a simulation of the New York City mayoral elections. Candidates are competing for votes across different demographic groups in the five boroughs.",
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
        "options": ["Eric", "Curtis", "Maya"]
    }

# Next timestep resource
@mcp.resource("resource://next_timestep")
def next_timestep() -> str:
    """Advance the simulation to the next time step."""
    return "Hello world"

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

if __name__ == "__main__":
    # Run with Streamable HTTP transport instead of default STDIO
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",  # Allow connections from any IP
        port=8000,       # Use port 8000
        path="/mcp"      # Set the endpoint path
    )
