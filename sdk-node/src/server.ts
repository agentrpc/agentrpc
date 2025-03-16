import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z, ZodRawShape, ZodTypeAny } from "zod";
import { createApiClient } from "./create-client";

// Firt arg
const apiSecret = process.argv[2];

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
  version: "1.0.0",
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
      "Failed to get Cluster Id:",
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
      "Failed to list tools:",
      toolResponse.status,
      toolResponse.body,
    );

    return;
  }

  for (const tool of toolResponse.body) {
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
  console.error("MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error in main():", error);
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
