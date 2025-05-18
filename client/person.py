import uuid
import numpy as np
import logging
from anthropic import AsyncAnthropic
from dotenv import load_dotenv
from base_prompts import memory_prompt
from mcp import ClientSession

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# TODO should be accessing resources?

class PersonV2:
    def __init__(self, features, model="claude-3-5-haiku-latest", memory_model = "claude-3-5-haiku-latest", temp=0.7, max_tokens=2048):
        self.features = features
        self.model = model
        self.memory_model = memory_model
        self.temp = temp
        self.max_tokens = max_tokens
        self.anthropic = AsyncAnthropic()
        self.decision = "Undecided"
        self.sys_prompt = ""
        self.memory = ""  # Initialize memory as empty string
        self.options = []
        self.id = uuid.uuid4()  # Add id for consistency with Person class

    async def generate_sys_prompt(self, base_prompt, mcp_session: ClientSession, options):
        self.options = options
        prompt = base_prompt
        base_prompt += f"\n You have the following options: {options}"
        for f in self.features:
            feature_prompt = await mcp_session.get_prompt(f)
            prompt += str(feature_prompt.messages[0].content.text)
            prompt += "\n"

        self.sys_prompt = prompt 

    async def call_llm(self, mcp_session: ClientSession, ctx):
        """ Makes an LLM call with the mcp server and context.
            Loops until there are no more tool calls, then updates memory.
        """

        # Convert ctx to string if it's a list
        ctx_str = ctx if isinstance(ctx, str) else str(ctx)
        
        prompt = self.sys_prompt + "\n\n Here's all the memories you've retained up to this point. \n\n" + self.memory+ "\n\n Here's some updated context \n\n" + ctx_str
        print("here")
        messages = [{
            "role": "user", # TODO should we be using user here?
            "content": prompt
        }]

        # Get available tools
        tools_response = await mcp_session.list_tools()
        available_tools = []
        
        for tool in tools_response.tools:
            tool_schema = {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            }
            available_tools.append(tool_schema)

        available_tools.append({
            "name": "make_decision", 
            "description": "Make or change your decision based on the available options.", 
            "input_schema": {
                "type": "object",
                "properties": {
                    "decision": {"type": "string"}
                },
                "required": ["decision"]
            }
        })
        # Track the full conversation history
        conversation_history = messages.copy()
        
        # Add loop counter to limit iterations
        loop_count = 0
        max_loops = 4
        
        while loop_count < max_loops:
            # Increment loop counter
            loop_count += 1
            
            # Make API call to Claude
            response = await self.anthropic.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=messages,
                tools=available_tools,
                temperature=self.temp
            )
            
            # Process and store assistant response
            assistant_message_content = []
            has_tool_calls = False
            
            for content in response.content:
                if content.type == 'text':
                    assistant_message_content.append(content)
                elif content.type == 'tool_use':
                    has_tool_calls = True
                    assistant_message_content.append(content)
                    
                    # Execute tool call
                    tool_name = content.name
                    # Handle both dictionary and object formats for tool arguments
                    if hasattr(content.input, '__getitem__'):
                        tool_args = content.input  # Already a dict-like object
                    else:
                        # Convert object to dict if it has attributes but not dict access
                        tool_args = vars(content.input) if hasattr(content.input, '__dict__') else content.input

                    print(tool_name)
                    print(tool_args)
                    if tool_name == "make_decision":
                        if tool_args["decision"] not in self.options:
                            result_content = f"Not a valid decision. Valid decisions are {self.options}"
                        else:
                            self.decision = tool_args["decision"]
                            result_content = "Decision made: " + self.decision
                    else:
                        try:
                            result = await mcp_session.call_tool(tool_name, tool_args)
                            result_content = result.content
                        except:
                            result_content = "Tool call failed. Don't try again."
                      
                    # Add assistant message with tool call to messages
                    messages.append({
                        "role": "assistant",
                        "content": assistant_message_content
                    })
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": content.id,
                                "content": result_content 
                            }
                        ]
                    })
                    
                    # Update conversation history
                    conversation_history.extend(messages[-2:])
                    break
            
            # If no tool calls, we're done with the loop
            if not has_tool_calls:
                # Add final assistant message to conversation history
                conversation_history.append({
                    "role": "assistant",
                    "content": assistant_message_content
                })
                break
                
        # If we reached the maximum number of loops, add a note about it
        if loop_count >= max_loops and has_tool_calls:
            logger.warning(f"Maximum number of tool call loops ({max_loops}) reached for person {self.id}")
            # Add the last assistant message to conversation history if it wasn't added
            conversation_history.append({
                "role": "assistant",
                "content": assistant_message_content
            })
        
        # Update memory with the conversation history
        new_memory = await self.update(conversation_history)
        
        return (self.decision, new_memory)

    async def update(self, llm_call_sequence):
        """ Updates the person's memory. This function should parse the LLM call result,
        and update the history instance attribute.

        Args:
            llm_call_result: the sequence of the LLM loop that we are adding to the history.
        """
        # Convert the conversation history to a string format for the memory prompt
        conversation_text = ""
        for message in llm_call_sequence:
            role = message["role"]
            content = message["content"]
            
            # Process content based on its type
            if isinstance(content, list):
                # Handle content that is a list of blocks
                for block in content:
                    if hasattr(block, "type"):
                        # Handle Anthropic API objects with attributes
                        if block.type == "text":
                            conversation_text += f"{role.capitalize()}: {block.text}\n\n"
                        elif block.type == "tool_use":
                            conversation_text += f"{role.capitalize()} used tool: {block.name}\n"
                        elif block.type == "tool_result":
                            conversation_text += f"Tool result: {block.content}\n\n"
                    elif isinstance(block, dict):
                        # Handle dictionary blocks
                        if block.get("type") == "text":
                            conversation_text += f"{role.capitalize()}: {block.get('text', '')}\n\n"
                        elif block.get("type") == "tool_use":
                            conversation_text += f"{role.capitalize()} used tool: {block.get('name', '')}\n"
                        elif block.get("type") == "tool_result":
                            conversation_text += f"Tool result: {block.get('content', '')}\n\n"
            else:
                # Handle content that is a string
                conversation_text += f"{role.capitalize()}: {content}\n\n"
        
        # Use the memory model to generate a memory from the conversation
        memory_response = await self.anthropic.messages.create(
            model=self.memory_model,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": memory_prompt.format(conversation=conversation_text)
                }
            ],
            temperature=0.7
        )
        
        # Extract the memory from the response
        new_memory = "\n\n" + memory_response.content[0].text
        self.memory += new_memory

        return new_memory

        
