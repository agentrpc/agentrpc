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
  schema: z.object({ name: z.string() }),
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
npx AgentRPC server <YOUR_API_SECRET>
```

This will launch an MCP-compliant server, allowing external AI models and applications to interact with your registered tools.

For more details on MCP, visit [Model Context Protocol](https://modelcontextprotocol.io/introduction).

### Supported Applications

AgentRPC’s MCP server can be used with various applications that support the Model Context Protocol, such as:

- [**Cursor**](https://docs.cursor.com/context/model-context-protocol#configuring-mcp-servers)
- [**Claude Desktop**](https://modelcontextprotocol.io/quickstart/user)
- [**Zed**](https://zed.dev/docs/assistant/model-context-protocol)

For a quickstart guide on MCP, refer to the [Model Context Protocol Quickstart](https://modelcontextprotocol.io/quickstart/user).

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
