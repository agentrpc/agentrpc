# AgentRPC Python SDK

A universal RPC layer for AI agents. Connect to any function, any language, any framework, in minutes.

> ⚠️ The AgentRPC Python SDK does **not** currently support registering tools.

## Installation

```sh
pip install agentrpc
```

## Registering Tools

### Creating an AgentRPC Client

```python
from agentrpc import AgentRPC

agentrpc = AgentRPC(
  # Get your API secret from https://app.agentrpc.com
  api_secret="YOUR_API_SECRET"
)
```


## OpenAI Tools

AgentRPC provides integration with OpenAI's function calling capabilities, allowing you to expose your registered RPC functions as tools for OpenAI models to use.

### Agents SDK

#### `rpc.OpenAI.agents.get_tools()`

The `get_tools()` method returns your registered AgentRPC functions as OpenAI Agent tools.

```python
# First register your functions with AgentRPC (Locally or on another machine)

# Attach the tools to the Agent
agent = Agent(name="AgentRPC Agent", tools=agentrpc.openai.agents.get_tools())

result = await Runner.run(
    agent,
    input="What is the weather in Melbourne?",
)

print(result.final_output)

```

### Completions SDK
#### `rpc.OpenAI.completions.get_tools()`

The `get_tools()` method returns your registered AgentRPC functions formatted as OpenAI tools, ready to be passed to OpenAI's API.

```python
# First register your functions with AgentRPC (Locally or on another machine)

# Then get the tools formatted for OpenAI
tools = agentrpc.openai.get_tools()

# Pass these tools to OpenAI
chat_completion = openai.chat.completions.create(
  model="gpt-4-1106-preview",
  messages=messages,
  tools=tools,
  tool_choice="auto"
)
```

#### `rpc.OpenAI.completions.execute_tool(tool_call)`

The `execute_tool()` method executes an OpenAI tool call against your registered AgentRPC functions.

```python
# Process tool calls from OpenAI's response
if chat_completion.choices[0].tool_calls:
  for tool_call in response_message.tool_calls:
    rpc.OpenAI.execute_tool(tool_call)
```

## API

### `AgentRPC(options?)`

Creates a new AgentRPC client.

#### Options:

| Option       | Type   | Default                    | Description          |
| ------------ | ------ | -------------------------- | -------------------- |
| `api_secret` | str    | **Required**               | The API secret key.  |
| `endpoint`   | str    | `https://api.agentrpc.com` | Custom API endpoint. |
