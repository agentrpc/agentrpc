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

client = AgentRPC(
  api_secret="YOUR_API_SECRET"
)
```


## OpenAI Tools

AgentRPC provides integration with OpenAI's function calling capabilities, allowing you to expose your registered RPC functions as tools for OpenAI models to use.

### `client.openai.get_tools()`

The `get_tools()` method returns your registered AgentRPC functions formatted as OpenAI tools, ready to be passed to OpenAI's API.

```python
# First register your functions with AgentRPC (Locally or on another machine)

# Then get the tools formatted for OpenAI
tools = client.openai.get_tools()

# Pass these tools to OpenAI
chat_completion = openai.chat.completions.create(
  model="gpt-4-1106-preview",
  messages=messages,
  tools=tools,
  tool_choice="auto"
)
```

### `client.openai.execute_tool(tool_call)`

The `execute_tool()` method executes an OpenAI tool call against your registered AgentRPC functions.

```python
# Process tool calls from OpenAI's response
if chat_completion.choices[0].tool_calls:
  for tool_call in response_message.tool_calls:
    client.openai.execute_tool(tool_call)
```

## API

### `AgentRPC(options?)`

Creates a new AgentRPC client.

#### Options:

| Option       | Type   | Default                    | Description          |
| ------------ | ------ | -------------------------- | -------------------- |
| `api_secret` | str    | **Required**               | The API secret key.  |
| `endpoint`   | str    | `https://api.agentrpc.com` | Custom API endpoint. |
