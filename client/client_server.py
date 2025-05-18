from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Tuple, Dict, Any, Optional
import json
import random
import asyncio
from contextlib import AsyncExitStack
from mcp import ClientSession
from mcp.client.sse import sse_client
from person import PersonV2

app = FastAPI()


# monkey-patch immediately after you import ClientSession
from mcp.client.session import ClientSession as _CS
import traceback, sys, asyncio

# Global variables to store state
mcp_session = None
people = []
next_turn_uri = "resource://next_timestep"
exit_stack = None

class InitRequest(BaseModel):
    num_people: int

class InitResponse(BaseModel):
    people: List[Tuple[int, List[str]]]

class RunTurnResponse(BaseModel):
    updates: List[Tuple[int, Dict[str, Any], str]]

@app.on_event("startup")
async def startup_event():
    global mcp_session, exit_stack
    exit_stack = AsyncExitStack()
    
    try:
        print("Starting SSE client...")
        sse_transport = await exit_stack.enter_async_context(sse_client("http://127.0.0.1:8000/sse"))
        read_stream, write_stream = sse_transport
        
        # Create a ClientSession with the streams
        mcp_session = await exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
        
        # Initialize the session
        await mcp_session.initialize()
        print("MCP session initialized successfully")
    except Exception as e:
        print(f"Error initializing MCP session: {e}")
        if exit_stack:
            await exit_stack.aclose()
        raise HTTPException(status_code=500, detail=f"Failed to initialize MCP session: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    global exit_stack
    if exit_stack:
        await exit_stack.aclose()
        print("MCP session closed")

@app.get("/init", response_model=InitResponse)
async def init(request: InitRequest):
    global mcp_session, people
    
    if not mcp_session:
        raise HTTPException(status_code=500, detail="MCP session not initialized")
    
    try:
        # Clear existing people if any
        people = []
        
        # Get features from resource
        features = await mcp_session.read_resource("resource://init")
        features_json = json.loads(features.contents[0].text)
        demographic_features = features_json['demographic_info']
        base_prompt = features_json['context']
        
        for i in range(request.num_people):
            # Sample features for each person
            sampled_features = []
            for feature_category in demographic_features:
                feature_names = [item[0] for item in feature_category]
                probabilities = [item[1] for item in feature_category]
                
                # Normalize probabilities
                total = sum(probabilities)
                normalized_probs = [p/total for p in probabilities]
                
                # Sample one feature based on probabilities
                selected_feature = random.choices(feature_names, weights=normalized_probs, k=1)[0]
                sampled_features.append(selected_feature)
            
            # Create a new person with sampled features
            person = PersonV2(sampled_features)
            await person.generate_sys_prompt(base_prompt, mcp_session)
            people.append(person)
        
        # Prepare response with person IDs and their features
        response_data = [(i, person.features) for i, person in enumerate(people)]
        return InitResponse(people=response_data)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing people: {str(e)}")

@app.get("/run_turn", response_model=RunTurnResponse)
async def run_turn():
    global mcp_session, people, next_turn_uri
    
    if not mcp_session:
        raise HTTPException(status_code=500, detail="MCP session not initialized")
    
    if not people:
        raise HTTPException(status_code=400, detail="No people initialized. Call /init first.")
    
    # Get the next turn context
    new_turn_ctx = await mcp_session.read_resource(next_turn_uri)
    
    # Create tasks for all persons
    tasks = [person.call_llm(mcp_session, new_turn_ctx.contents) for person in people]
    
    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks)
    
    # Format the results as [(id, memory_update, decision)]
    formatted_results = []
    for i, result in enumerate(results):
        # PersonV2.call_llm returns a tuple of (decision, new_memory)
        person_id = i
        decision, memory_update = result
        formatted_results.append((person_id, {"memory": memory_update}, decision))
    
    return RunTurnResponse(updates=formatted_results)
    


if __name__ == "__main__":
    import uvicorn
    
    # Run the FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=3001)
    print("Server started at http://0.0.0.0:3001")

