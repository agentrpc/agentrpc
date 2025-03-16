#!/usr/bin/env node

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z, ZodRawShape, ZodTypeAny } from "zod";
import { createApiClient } from "./create-client";

// Firt arg Command name
const commandName = process.argv[2];

// Second arg API Secret
const apiSecret = process.argv[3];

if (!commandName || commandName !== "mcp") {
  console.error("Invalid command. Supported commands: mcp");
  process.exit(1);
}

if (!apiSecret) {
  console.error("No API Secret provided");
  process.exit(1);
}

const client = createApiClient({
  apiSecret,
});

// Create server instance
const server = new McpServer({
  name: "agentrpc",
  // Read from package.json
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  version: require("../package.json").version,
});

async function main() {
  const clusterResult = await client.createMachine({
    headers: {
      "x-machine-id": crypto.randomUUID(),
    },
    body: {
      tools: [],
    },
  });

  if (clusterResult.status !== 200) {
    console.error(
      "Failed to get AgentRPC Cluster ID",
      clusterResult.status,
      clusterResult.body,
    );

    return;
  }

  const clusterId = clusterResult.body.clusterId;

  const toolResponse = await client.listTools({
    params: {
      clusterId,
    },
  });

  if (toolResponse.status !== 200) {
    console.error(
      "Failed to list AgentRPC tools:",
      toolResponse.status,
      toolResponse.body,
    );

    return;
  }

  for (const tool of toolResponse.body) {
    console.info("Registering tool:", {
      name: tool.name,
    });
    server.tool(
      tool.name,
      tool.description ?? "",
      buildZodObject(JSON.parse(tool.schema!)),
      async (i) => {
        const createResult = await client.createJob({
          body: {
            tool: tool.name,
            input: i,
          },
          params: {
            clusterId,
          },
          query: {
            waitTime: 20,
          },
        });

        if (createResult.status !== 200) {
          return {
            content: [
              {
                type: "text",
                text: `Failed to run tool: ${createResult.status}`,
              },
            ],
          };
        }

        let status: string = createResult.body.status;
        let result: string = createResult.body.result ?? "";
        let resultType: string = createResult.body.resultType ?? "rejection";

        while (!["failure", "success"].includes(status)) {
          await new Promise((resolve) => setTimeout(resolve, 1000));

          const details = await client.getJob({
            params: {
              clusterId,
              jobId: createResult.body.id,
            },
          });

          if (details.status !== 200) {
            return {
              content: [
                {
                  type: "text",
                  text: `Failed to run tool: ${details.status}`,
                },
              ],
            };
          }

          status = details.body.status;
          result = details.body.result ?? "";
          resultType = details.body.resultType ?? "rejection";
        }

        return {
          content: [
            {
              type: "text",
              text: `${resultType}: ${JSON.stringify(result)}`,
            },
          ],
        };
      },
    );
  }

  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.info("AgentRPC MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Failed to start AgentRPC MCP Server", error);
  process.exit(1);
});

// @eslint-disable-next-line
const buildZodObject = (schema: any): ZodRawShape => {
  const result: Record<string, ZodTypeAny> = {};

  for (const [k, v] of Object.entries(schema.properties)) {
    // @eslint-disable-next-line
    result[k] = buildZodProp(v, k);
  }

  return result;
};

// @eslint-disable-next-line
const buildZodProp = (prop: any, key: string): ZodTypeAny => {
  if (prop.type === "string") {
    return z.string();
  } else if (prop.type === "number") {
    return z.number();
  } else if (prop.type === "boolean") {
    return z.boolean();
  } else if (prop.type === "object") {
    return z.object(buildZodObject(prop));
  } else if (prop.type === "array") {
    return z.array(buildZodProp(prop.items, key));
  } else {
    return z.any();
  }
};
