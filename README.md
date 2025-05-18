# 1000 minds: Simulating Societies with MCPs
## Inspiration
With MCP, we can give an agent access to shared resources and actions. But what if instead of one agent, we released a thousand, each interacting, reacting, and influencing one another? From elections and market dynamics to social media predictions, 1000minds can simulate entire societies responding realistically to any scenario you can imagine.


## What It Does
**1000 minds** simulates a society of 1000 agents with access to resources provided through an MCP server. Each agent is an LLM with:
- A unique prompt and temperature
- Access to shared resources
- The ability to call tools via the MCP interface

You define:
- A **simulation scenario**
- A **custom MCP server** exposing actions/tools/resources

We then:
1. Generate a diverse set of 1000 agents
2. Connect them to your MCP server
3. Let the agents reason, act, and evolve over time
4. Provide you with relevant data and visualizations via our frontend

This enables powerful simulations for **markets, political landscapes, and public sentiment**.

## How We Built It
![Architecture Diagram](https://i.ibb.co/5XyWyGW7/Structure.png)

Our stack includes:
- **FastMCP backend**: Handles agent initialization and tool calls
- **Typescript + Next frontend**

For example, in our NYC mayoral election simulation, one of the tools connected to our MCP server used the **Exa API** to fetch news in real-time. We could then observe how media shaped voter sentiment for every individual agent.

---

## Example: NYC Mayoral Election (2025)

![NYC Candidates](https://cdn.abcotvs.com/dip/images/15973530_030325-wabc-nyc-mayoral-candidates-img.jpg)

We modeled 1000 NYC citizens as agents with:
- Temperatures drawn from a normal distribution
- Demographics sampled to match NYC census data
- Access to daily news via Exa API (filtered by date for realism)

Each day:
1. Agents gather more news
2. Agents make a tool call to determine their political leanings

We ran this simulation for **10 days** for the purpose of demo brevity, but even short-term, we saw dynamic shifts in sentiment and trends over time.

---

## What's Next for 1000 minds

### Modular UI

We want to implement a completely modular ui, currently the frotned is optimized for time-series driven events. We want to make a ui that can also handle social media posts, live event attendance, and many other events.

### Agent-to-Agent (A2A) Communication
We’re exploring:
- **Vector embedding each agent’s memory**, then using k-nearest neighbors to simulate dialogue among like-minded individuals
- **Chat history fusion**: powerful—`union()` two agents’ histories and prompt them to "chat"

### More Tools, More Realism
- Financial APIs, social media feeds, and custom user actions
- Modeling trust, misinformation, and community formation

---
## MsCP 
We allow any types of society to be simulated if they follow our **Models Context Protocol**. 

```python
class MsCP: 
    @mcp.resource("resource://init")
    def init() -> dict:
        """
        initizes the demographic information about the 1000 people
        """

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
        }
    
    
    # Next timestep resource
    @mcp.resource("resource://next_timestep")
    def next_timestep() -> str:
        """Advance the simulation to the next time step."""
        global timestep
        timestep += 1
    
    # Add a list of actions as mcp tools
    @mcp.tool()
    async def search_for_news(query:str):
        """fetches relevant news articles"""
        return 
```


### Models Context Protocol (MsCP) for Society Simulation

The MsCP framework enables simulation of any society type by defining demographic distributions and temporal progression through two core methods: `init()` and `next_timestep()`.

### Core Methods

#### `@mcp.resource("resource://init")`

The `init()` method establishes the foundational demographic structure of the simulated population. It returns a dictionary containing:

**Purpose**: Initialize demographic information for the simulation population
**Returns**: Dictionary with context and demographic probability distributions

```python
{
    "context": "Simulation description and instructions",
    "demographic_info": [
        [category_distributions],
        [category_distributions],
        ...
    ]
}
```

#### `@mcp.resource("resource://next_timestep")`

The `next_timestep()` method advances the simulation forward in time, allowing for dynamic changes in the population's behavior, preferences, and circumstances.

**Purpose**: Progress the simulation to the next temporal unit
**Returns**: String confirmation of timestep advancement

### Demographic Probability Distribution System

#### Format: [Category: Probability]

Each demographic category follows the format `[category_name, probability_value]` where:

- **category_name**: String identifier for the demographic characteristic
- **probability_value**: Integer representing

## Open Source, Open Future
**1000 minds** is built with openness in mind. Anyone can plug in new prompts and MCP servers to simulate:
- Societies
- Economies
- Political systems
- Fictional universes

[1000 minds GitHub Repository](https://github.com/lychee-development/yc_hack_517)

Help us build better virtual societies - 1000 minds at a time
