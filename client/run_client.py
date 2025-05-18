from person import PersonV2
from mcp import ClientSession
from mcp.client.sse import sse_client
import concurrent.futures
import asyncio
from pydantic import AnyUrl
from contextlib import AsyncExitStack
import json
import random
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def run_client(mcp_session: ClientSession, num_people: int, num_turns: int):
    people = []
    try:
        logger.info("Reading initial resource")
        features = await mcp_session.read_resource("resource://init")
        features_json = json.loads(features.contents[0].text)
        features = features_json['demographic_info']
        base_prompt= features_json['context']

        logger.info("Creating people")
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
            logger.info(f"Creating person with features: {sampled_features}")
            people.append(PersonV2(sampled_features))
            
            await people[-1].generate_sys_prompt(base_prompt, mcp_session)
        
        # Use the correct URI format for read_resource
        next_turn_uri = "resource://next_timestep"
        logger.info(f"Getting next turn context from {next_turn_uri}")
        new_turn_ctx = await mcp_session.read_resource(next_turn_uri)

        for turn in range(num_turns):
            logger.info(f"Starting turn {turn+1}/{num_turns}")
            # Create tasks for all persons
            tasks = []
            for i, person in enumerate(people):
                logger.info(f"Creating task for person {i+1}")
                tasks.append(person.call_llm(mcp_session, new_turn_ctx.contents))
            
            # Wait for all tasks to complete with error handling
            try:
                logger.info("Waiting for all tasks to complete")
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Check for exceptions in results
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(f"Error in person {i+1} task: {result}")
                    else:
                        logger.info(f"Person {i+1} task completed successfully")
                
                print(results)
                
                # Call the next_turn resource
                logger.info("Getting next turn context")
                new_turn_ctx = await mcp_session.read_resource(next_turn_uri)
            except Exception as e:
                logger.error(f"Error during task execution: {e}")
                raise
    except Exception as e:
        logger.error(f"Error in run_client: {e}")
        raise
    
    return results


async def main():
    exit_stack = AsyncExitStack()
    
    try:
        print("Starting SSE client...")
        # Increase timeouts for SSE connection
        sse_transport = await exit_stack.enter_async_context(
            sse_client("http://127.0.0.1:8000/sse", 
                      timeout=30,  # Increase connection timeout
                      sse_read_timeout=300)  # Increase read timeout to 5 minutes
        )
        read_stream, write_stream = sse_transport
        
        # Create a ClientSession with the streams
        logger.info("Creating client session")
        mcp_session = await exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
        
        # Initialize the session
        logger.info("Initializing session")
        await mcp_session.initialize()
        
        # Run the client with the session
        logger.info("Running client")
        await run_client(mcp_session, 2, 1)
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise
    finally:
        logger.info("Closing resources")
        await exit_stack.aclose()

if __name__ == "__main__":
    asyncio.run(main())