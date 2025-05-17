from client.person import Person

def run_client(mcp_session, prompts, num_turns):
    people = [Person(sys_prompt=p) for p in prompts]
    for person in people:
        for _ in range(num_turns):
            person.call_llm(mcp_session)
            person.update(mcp_session)


