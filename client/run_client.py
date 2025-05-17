from client.person import Person, PersonV2
from mcp import ClientSession
import concurrent.futures

mcp_session = ClientSession()

def run_client(features: list[list[str]], num_turns: int):

    people = []
    for feature_set in features:
        people.append(PersonV2(feature_set))
        people[-1].generate_sys_prompt(mcp_session)
    
    new_turn_ctx = mcp_session.call_resource("next_turn", {})

    for _ in range(num_turns):
        # Run call_llm in parallel for all persons using ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(person.call_llm, mcp_session, new_turn_ctx) for person in people]
            # Wait for all futures to complete and collect results if needed
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        new_turn_ctx = mcp_session.call_resource("next_turn", {})

