# AgentRPC

![NPM Version](https://img.shields.io/npm/v/agentrpc?color=32CD32) ![GitHub go.mod Go version](https://img.shields.io/github/go-mod/go-version/agentrpc/agentrpc?filename=sdk-go%2Fgo.mod&color=32CD32) ![PyPI - Python Version](https://img.shields.io/pypi/v/agentrpc?color=32CD32) ![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)

> Universal RPC layer for AI agents across network boundaries and languages

## Overview

AgentRPC allows you to connect to any function, in any language, across network boundaries. It's ideal when you have services deployed in:
- Private VPCs
- Kubernetes clusters
- Multiple cloud environments

AgentRPC wraps your functions in a universal RPC interface, connecting them to a hosted RPC server accessible through open standards:

- Model Context Protocol (MCP)
- OpenAI-compatible tool definitions (OpenAI, Anthropic, LiteLLM, OpenRouter, etc.)

<div align="center" style="width: 500px; margin: 0 auto;">

![deployment](./assets/deployment.png)

</div>

## How It Works

1. **Registration**: Use our SDK to register functions and APIs in any language
2. **Management**: The AgentRPC platform (api.agentrpc.com) registers the function and monitors its health
3. **Access**: Receive OpenAPI SDK compatible tool definitions and a hosted MCP server for connecting to compatible agents

## Key Features

| Feature | Description |
|---------|-------------|
| **Multi-language Support** | Connect to tools in TypeScript, Go, Python and .NET (coming soon) |
| **Private Network Support** | Register functions in private VPCs with no open ports required |
| **Long-running Functions** | Long polling SDKs allow function calls beyond HTTP timeout limits |
| **Full Observability** | Comprehensive tracing, metrics, and events for complete visibility |
| **Automatic Failover** | Intelligent health tracking with automatic failover and retries |
| **Framework Compatibility** | Out-of-the-box support for MCP and OpenAI SDK compatible agents |

## Getting Started

### Quick Installation

1. [Get your API key](https://app.agentrpc.com)
2. Choose your preferred SDK:
   - [Go SDK](sdk-go/README.md)
   - [Node.js SDK](sdk-node/README.md)
   - [Python SDK](sdk-python/README.md)
3. Explore working examples in the [examples](./examples) directory

## Integration Guides

### MCP Server

The AgentRPC TypeScript SDK includes an MCP (Model Context Protocol) server:

```sh
ANGENTRPC_API_SECRET=YOUR_API_SECRET npx agentrpc mcp
```

This launches an MCP-compliant server for external AI models to interact with your registered tools.

For more details on MCP, visit [Model Context Protocol](https://modelcontextprotocol.io/introduction).

### Claude Desktop Integration

Add to your `claude_desktop_config.json`:

```json
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

### Cursor Integration

Add to your `~/.cursor/mcp.json`:

```json
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

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

This repository contains all the open-source components and SDKs for AgentRPC.
