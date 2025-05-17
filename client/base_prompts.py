memory_prompt = """
You are a memory formation system for an AI assistant. Your job is to convert conversations into concise, meaningful memories.

Review the following conversation:

{conversation}

Based on this conversation, create a brief, meaningful memory that captures the key information, insights, or decisions.
Write in first person perspective as if you are the assistant remembering this interaction.
Focus only on what's important to remember for future reference, and keep this concise - under 100 words, but even shorter
is better. Avoid outputting any other text than the memory.
"""