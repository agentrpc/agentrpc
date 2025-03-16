# AgentRPC TypeScript SDK

A universal RPC layer for AI agents. Connect to any function, any language, any framework, in minutes.

## Installation

```sh
npm install agentrpc
```

## Registering Tools

### Creating an AgentRPC Client

```ts
import { AgentRPC } from "agentrpc";

const client = new AgentRPC({
  apiSecret: "YOUR_API_SECRET",
});
```

### Registering a Tool

```ts
import { z } from "zod";

client.register({
  name: "hello",
  schema: {
    input: z.object({ name: z.string() }),
  },
  handler: async ({ name }) => `Hello ${name}`,
  // Optional
  config: {
    retryCountOnStall: 3,
    timeoutSeconds: 30,
  },
});
```

### Starting the Listener

```ts
await client.listen();
```

### Stopping the Listener

```ts
await client.unlisten();
```

## MCP Server

The AgentRPC TypeScript SDK includes an MCP (Model Context Protocol) server that can be started using:

```sh
npx agentrpc mcp <YOUR_API_SECRET>
```

This will launch an MCP-compliant server, allowing external AI models and applications to interact with your registered tools.

For more details on MCP, visit [Model Context Protocol](https://modelcontextprotocol.io/introduction).

### Claude Desktop Usage:

Add the following to your `claude_desktop_config.json`:

```
{
  "mcpServers": {
    "agentrpc": {
      "command": "npx",
      "args": [
        "-y",
        "agentrpc",
        "mcp"
      ],
      "env": {
        "AGENTRPC_API_SECRET": "<YOUR_API_SECRET>"
      }
    }
  }
}
```

[More Info](https://modelcontextprotocol.io/quickstart/user)

### Cursor

Add the following to your `~/.cursor/mcp.json`:

```
{
  "mcpServers": {
    "agentrpc": {
      "command": "npx",
      "args": ["-y", "agentrpc", "mcp"],
      "env": {
        "AGENTRPC_API_SECRET": "<YOUR_API_SECRET>"
      }
    }
  }
}
```

[More Info](https://docs.cursor.com/context/model-context-protocol#configuring-mcp-servers)

### Zed

[**Zed**](https://zed.dev/docs/assistant/model-context-protocol)

## OpenAI Tools

AgentRPC provides integration with OpenAI's function calling capabilities, allowing you to expose your registered RPC functions as tools for OpenAI models to use.

### `client.OpenAI.getTools()`

The `getTools()` method returns your registered AgentRPC functions formatted as OpenAI tools, ready to be passed to OpenAI's API.

```javascript
// First register your functions with AgentRPC (Locally or on another machine)

// Then get the tools formatted for OpenAI
const tools = await client.OpenAI.getTools();

// Pass these tools to OpenAI
const chatCompletion = await openai.chat.completions.create({
  model: "gpt-4-1106-preview",
  messages: messages,
  tools: tools,
  tool_choice: "auto",
});
```

### `client.OpenAI.executeTool(toolCall)`

The `executeTool()` method executes an OpenAI tool call against your registered AgentRPC functions.

```javascript
// Process tool calls from OpenAI's response
if (responseMessage.tool_calls && responseMessage.tool_calls.length > 0) {
  for (const toolCall of responseMessage.tool_calls) {
    try {
      // Execute the tool and add result to messages
      messages.push({
        role: "tool",
        tool_call_id: toolCall.id,
        content: await client.OpenAI.executeTool(toolCall),
      });
    } catch (error) {
      console.error(`Error executing tool ${toolCall.function.name}:`, error);
      messages.push({
        role: "tool",
        tool_call_id: toolCall.id,
        content: `Error: ${error.message}`,
      });
    }
  }
}
```

## API

### `new AgentRPC(options?)`

Creates a new AgentRPC client.

#### Options:

| Option      | Type   | Default                    | Description          |
| ----------- | ------ | -------------------------- | -------------------- |
| `apiSecret` | string | **Required**               | The API secret key.  |
| `endpoint`  | string | `https://api.agentrpc.com` | Custom API endpoint. |
| `machineId` | string | Automatically generated    | Custom machine ID.   |

### `register({ name, schema, handler, config })`

Registers a tool.

- `name`: Unique tool identifier.
- `schema`: Input validation schema (Zod or JSON schema).
- `handler`: Async function to process input.
- `config`: Optional tool configuration.

#### Tool Configuration Options:

| Option              | Type   | Default | Description                 |
| ------------------- | ------ | ------- | --------------------------- |
| `retryCountOnStall` | number | `null`  | Number of retries on stall. |
| `timeoutSeconds`    | number | `null`  | Request timeout in seconds. |

### `listen()`

Starts listening for requests.

### `unlisten()`

Stops all running listeners.
