# AgentRPC Python SDK

A universal RPC layer for AI agents. Connect to any function, any language, any framework, in minutes.

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

### Registering Tools

There are two ways to register tools with AgentRPC:

#### Using the Decorator Syntax

```python
# Register a tool using decorator syntax
@agentrpc.register(name="greet", description="Greet a person by name")
def greet(name: str) -> str:
    """Return a greeting for the given name."""
    return f"Hello, {name}!"

# You can also use the decorator without arguments
# In this case, the function name is used as the tool name
@agentrpc.register
def calculate_sum(a: int, b: int) -> int:
    """Calculate the sum of two numbers."""
    return a + b
```

#### Using Direct Function Calls

```python
# Define a function
def process_order(order_id: str, items: list) -> dict:
    """Process an order with the given items."""
    # Process the order...
    return {"status": "success", "order_id": order_id}

# Register it directly
agentrpc.register(
    process_order,
    name="process_order",
    description="Process a new order with items"
)
```

### Listening for Tool Invocations

After registering your tools, you need to start listening for invocations:

```python
# Start listening for tool invocations (blocking call)
agentrpc.listen()

# When your application is shutting down, stop listening
agentrpc.unlisten()
```

For a complete example, see the [tool registration example](./examples/tool_registration.py).

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

| Option       | Type   | Default                    | Description                                 |
| ------------ | ------ | -------------------------- | ------------------------------------------- |
| `api_secret` | str    | **Required**               | The API secret key.                         |
| `endpoint`   | str    | `https://api.agentrpc.com` | Custom API endpoint.                        |
| `machine_id` | str    | *auto-generated*           | Custom machine ID for registration.         |

### `AgentRPC.register(func=None, *, name=None, description=None, schema=None)`

Registers a function as a tool. Can be used as a decorator or as a function.

#### Parameters:

| Parameter    | Type     | Default               | Description                                   |
| ------------ | -------- | --------------------- | --------------------------------------------- |
| `func`       | callable | None                  | The function to register.                     |
| `name`       | str      | *function name*       | Custom name for the tool.                     |
| `description`| str      | *function docstring*  | Description of what the tool does.            |
| `schema`     | dict     | *auto-generated*      | Custom JSON schema for the tool's input.      |

### `AgentRPC.listen()`

Start listening for tool invocations. This is a blocking call that will register the machine and start polling for jobs.

### `AgentRPC.unlisten()`

Stop listening for tool invocations.
