from person import PersonV2
from mcp import ClientSession
from mcp.client.sse import sse_client
import concurrent.futures
import asyncio
from pydantic import AnyUrl
from contextlib import AsyncExitStack
import json
import random

async def run_client(mcp_session: ClientSession, num_people: int, num_turns: int):
    people = []
    features = await mcp_session.read_resource("resource://init")
    features = json.loads(features.contents[0].text)['demographic_info']
    
    for _ in range(num_people):
        # Sample a feature from each category based on probabilities
        sampled_features = []
        for feature_category in features:
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
        
        await people[-1].generate_sys_prompt(mcp_session)
    
    # Use the correct URI format for read_resource
    next_turn_uri = "resource://next_timestep"
    new_turn_ctx = await mcp_session.read_resource(next_turn_uri)

    for _ in range(num_turns):
        # Create tasks for all persons
        tasks = [person.call_llm(mcp_session, new_turn_ctx.contents) for person in people]
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks)

        print(results)
        # Call the next_turn resource
        new_turn_ctx = await mcp_session.read_resource(next_turn_uri)


async def main():
    exit_stack = AsyncExitStack()
    
    try:
        print("Starting SSE client...")
        sse_transport = await exit_stack.enter_async_context(sse_client("http://127.0.0.1:8000/sse"))
        read_stream, write_stream = sse_transport
        
        # Create a ClientSession with the streams
        mcp_session = await exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
        
        # Initialize the session
        await mcp_session.initialize()
        
        # Run the client with the session
        await run_client(mcp_session, 2, 1)
    finally:
        await exit_stack.aclose()

if __name__ == "__main__":
    asyncio.run(main())