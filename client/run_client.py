from person import PersonV2
from mcp import ClientSession
from mcp.client.sse import sse_client
import concurrent.futures
import asyncio
from pydantic import AnyUrl
from contextlib import AsyncExitStack

async def run_client(mcp_session: ClientSession, features: list[list[str]], num_turns: int):
    people = []
    for feature_set in features:
        people.append(PersonV2(feature_set))
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
        await run_client(mcp_session, [["Democrat"]], 2)
    finally:
        await exit_stack.aclose()

if __name__ == "__main__":
    asyncio.run(main())
