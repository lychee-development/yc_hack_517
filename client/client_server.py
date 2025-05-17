from person import PersonV2
from mcp import ClientSession
from mcp.client.sse import sse_client
import concurrent.futures
import asyncio
from pydantic import AnyUrl
from contextlib import AsyncExitStack
import json
import random

# Global variables to store state
people = []
new_turn_ctx = None

async def initialize_people(mcp_session: ClientSession, num_people: int):
    """Initialize Person objects with sampled features."""
    global people
    
    features = await mcp_session.read_resource("resource://init")
    features_json = json.loads(features.contents[0].text)
    demographic_features = features_json['demographic_info']
    base_prompt = features_json['context']
    print(base_prompt)

    people = []
    for _ in range(num_people):
        # Sample a feature from each category based on probabilities
        sampled_features = []
        for feature_category in demographic_features:
            # Extract feature names and their probabilities
            feature_names = [item[0] for item in feature_category]
            probabilities = [item[1] for item in feature_category]
            
            # Normalize probabilities to ensure they sum to 100
            total = sum(probabilities)
            normalized_probs = [p/total for p in probabilities]
            
            # Sample one feature based on the probabilities
            selected_feature = random.choices(feature_names, weights=normalized_probs, k=1)[0]
            
            # Add to feature list
            sampled_features.append(selected_feature)
        
        # Create a person with the sampled features
        people.append(PersonV2(sampled_features))
        await people[-1].generate_sys_prompt(base_prompt, mcp_session)
    
    # Initialize the first turn context
    global new_turn_ctx
    next_turn_uri = "resource://next_timestep"
    new_turn_ctx = await mcp_session.read_resource(next_turn_uri)
    
    return people

async def run_turn(mcp_session: ClientSession):
    """Run a single turn for all people."""
    global people, new_turn_ctx
    
    # Create tasks for all persons
    tasks = [person.call_llm(mcp_session, new_turn_ctx.contents) for person in people]
    
    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks)
    
    print(results)
    
    # Get the next turn context
    next_turn_uri = "resource://next_timestep"
    new_turn_ctx = await mcp_session.read_resource(next_turn_uri)
    
    return results

async def run_client(mcp_session: ClientSession, num_people: int, num_turns: int):
    """Main function to run the client simulation."""
    # Initialize people
    await initialize_people(mcp_session, num_people)
    
    # Run turns
    for _ in range(num_turns):
        await run_turn(mcp_session)

async def start_client_server(host="127.0.0.1", port=8000, num_people=2, num_turns=1):
    """Start the client server with the given configuration."""
    exit_stack = AsyncExitStack()
    
    try:
        print("Starting SSE client...")
        sse_url = f"http://{host}:{port}/sse"
        sse_transport = await exit_stack.enter_async_context(sse_client(sse_url))
        read_stream, write_stream = sse_transport
        
        # Create a ClientSession with the streams
        mcp_session = await exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
        
        # Initialize the session
        await mcp_session.initialize()
        
        # Run the client with the session
        await run_client(mcp_session, num_people, num_turns)
    finally:
        await exit_stack.aclose()



from fastapi import FastAPI

app = FastAPI()

@app.get("/init")
async def init(num_people: int):
    # Initialize the client session
    exit_stack = AsyncExitStack()
    
    try:
        sse_url = "http://127.0.0.1:8000/sse"
        sse_transport = await exit_stack.enter_async_context(sse_client(sse_url))
        read_stream, write_stream = sse_transport
        
        # Create a ClientSession with the streams
        mcp_session = await exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
        
        # Initialize the session
        await mcp_session.initialize()
        
        # Initialize people
        await initialize_people(mcp_session, num_people)
        
        # Return list of tuples with person ID and features
        return [(str(person.id), person.features) for person in people]
    finally:
        await exit_stack.aclose()

@app.get("/run_turn")
async def run_turn_endpoint():
    # Initialize the client session
    exit_stack = AsyncExitStack()
    
    try:
        sse_url = "http://127.0.0.1:8000/sse"
        sse_transport = await exit_stack.enter_async_context(sse_client(sse_url))
        read_stream, write_stream = sse_transport
        
        # Create a ClientSession with the streams
        mcp_session = await exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
        
        # Initialize the session
        await mcp_session.initialize()
        
        # Run a turn and get results
        results = await run_turn(mcp_session)
        
        # Return the results as a list of tuples (id, decision, memory)
        return [(str(people[i].id), decision, memory) 
                for i, (decision, memory) in enumerate(results)]
    finally:
        await exit_stack.aclose()

@app.get("/people")
async def get_people():
    """Return the current state of all people."""
    return [
        {
            "id": str(person.id),
            "features": person.features,
            "decision": person.decision,
            "memory": person.memory
        }
        for person in people
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)