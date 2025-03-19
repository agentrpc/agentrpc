import { initContract } from "@ts-rest/core";
import { z } from "zod";

const c = initContract();

const machineHeaders = {
  "x-machine-id": z.string().optional(),
  "x-machine-sdk-version": z.string().optional(),
  "x-machine-sdk-language": z.string().optional(),
  "x-forwarded-for": z.string().optional().optional(),
};

export const notificationSchema = z.object({
  destination: z
    .discriminatedUnion("type", [
      z.object({
        type: z.literal("slack"),
        channelId: z.string().optional(),
        threadId: z.string().optional(),
        userId: z.string().optional(),
        email: z.string().optional(),
      }),
      z.object({
        type: z.literal("email"),
        email: z.string(),
      }),
    ])
    .optional(),
  message: z.string().optional(),
});

export const interruptSchema = z.discriminatedUnion("type", [
  z.object({
    type: z.enum(["approval", "general"]),
    notification: notificationSchema.optional(),
  }),
]);

export const ToolConfigSchema = z.object({
  cache: z
    .object({
      keyPath: z.string(),
      ttlSeconds: z.number(),
    })
    .optional(),
  retryCountOnStall: z.number().optional(),
  timeoutSeconds: z.number().optional(),
  private: z.boolean().default(false).optional(),
});

export const definition = {
  // Misc Endpoints
  live: {
    method: "GET",
    path: "/live",
    responses: {
      200: z.object({
        status: z.string(),
      }),
    },
  },
  createEphemeralSetup: {
    method: "POST",
    path: "/ephemeral-setup",
    responses: {
      200: z.object({
        clusterId: z.string(),
        apiKey: z.string(),
      }),
    },
    body: z.undefined(),
  },
  getContract: {
    method: "GET",
    path: "/contract",
    responses: {
      200: z.object({
        contract: z.string(),
      }),
    },
  },

  // Job Endpoints
  getJob: {
    method: "GET",
    path: "/clusters/:clusterId/jobs/:jobId",
    headers: z.object({ authorization: z.string() }),
    pathParams: z.object({
      clusterId: z.string(),
      jobId: z.string(),
    }),
    query: z.object({
      waitTime: z.coerce
        .number()
        .min(0)
        .max(20)
        .default(0)
        .describe(
          "Time in seconds to keep the request open waiting for a response",
        ),
    }),
    responses: {
      200: z.object({
        id: z.string(),
        status: z.string(),
        targetFn: z.string(),
        executingMachineId: z.string().nullable(),
        targetArgs: z.string(),
        result: z.any().nullable(),
        resultType: z.string().nullable(),
        createdAt: z.date(),
        approved: z.boolean().nullable(),
        approvalRequested: z.boolean().nullable(),
      }),
    },
  },
  getJobListing: {
    method: "GET",
    path: "/clusters/:clusterId/job-listing",
    headers: z.object({ authorization: z.string() }),
    pathParams: z.object({
      clusterId: z.string(),
    }),
    query: z.object({
      limit: z.string(),
      status: z
        .enum([
          "pending",
          "running",
          "done",
          "failure",
          "stalled",
          "interrupted",
        ])
        .optional(),
      targetFn: z.string().optional(),
      after: z.string().optional(),
    }),
    responses: {
      200: z.array(
        z.object({
          id: z.string(),
          status: z.string(),
          targetFn: z.string(),
          executingMachineId: z.string().nullable(),
          createdAt: z.date(),
          approved: z.boolean().nullable(),
        }),
      ),
    },
  },
  createJob: {
    method: "POST",
    path: "/clusters/:clusterId/jobs",
    query: z.object({
      waitTime: z.coerce
        .number()
        .min(0)
        .max(20)
        .default(0)
        .describe(
          "Time in seconds to keep the request open waiting for a response",
        ),
    }),
    headers: z.object({
      authorization: z.string(),
    }),
    body: z.object({
      function: z.string().optional(),
      tool: z.string().optional(),
      input: z.object({}).passthrough(),
    }),
    responses: {
      401: z.undefined(),
      200: z.object({
        id: z.string(),
        result: z.any().nullable(),
        resultType: z.enum(["resolution", "rejection", "interrupt"]).nullable(),
        status: z.enum([
          "pending",
          "running",
          "done",
          "failure",
          "stalled",
          "interrupted",
        ]),
      }),
    },
  },
  cancelJob: {
    method: "POST",
    path: "/clusters/:clusterId/jobs/:jobId/cancel",
    headers: z.object({
      authorization: z.string(),
    }),
    pathParams: z.object({
      clusterId: z.string(),
      jobId: z.string(),
    }),
    responses: {
      204: z.undefined(),
      401: z.undefined(),
    },
    body: z.undefined(),
  },
  createJobResult: {
    method: "POST",
    path: "/clusters/:clusterId/jobs/:jobId/result",
    headers: z.object({
      authorization: z.string(),
      ...machineHeaders,
    }),
    pathParams: z.object({
      clusterId: z.string(),
      jobId: z.string(),
    }),
    responses: {
      204: z.undefined(),
      401: z.undefined(),
    },
    body: z.object({
      result: z.any(),
      resultType: z.enum(["resolution", "rejection", "interrupt"]),
      meta: z.object({
        functionExecutionTime: z.number().optional(),
      }),
    }),
  },
  listJobs: {
    method: "GET",
    path: "/clusters/:clusterId/jobs",
    query: z.object({
      tools: z
        .string()
        .optional()
        .describe("Comma-separated list of tools to poll"),
      status: z
        .enum(["pending", "running", "paused", "done", "failed"])
        .default("pending"),
      limit: z.coerce.number().min(1).max(20).default(10),
      acknowledge: z.coerce
        .boolean()
        .default(false)
        .describe("Should retrieved Jobs be marked as running"),
      waitTime: z.coerce
        .number()
        .min(0)
        .max(20)
        .default(0)
        .describe(
          "Time in seconds to keep the request open waiting for a response",
        ),
    }),
    pathParams: z.object({
      clusterId: z.string(),
    }),
    headers: z.object({
      authorization: z.string(),
      ...machineHeaders,
    }),
    responses: {
      401: z.undefined(),
      410: z.object({
        message: z.string(),
      }),
      200: z.array(
        z.object({
          id: z.string(),
          function: z.string(),
          input: z.any(),
          authContext: z.any().nullable(),
          runContext: z.any().nullable(),
          approved: z.boolean(),
        }),
      ),
    },
  },
  createJobApproval: {
    method: "POST",
    path: "/clusters/:clusterId/jobs/:jobId/approval",
    headers: z.object({
      authorization: z.string(),
    }),
    pathParams: z.object({
      clusterId: z.string(),
      jobId: z.string(),
    }),
    responses: {
      204: z.undefined(),
      404: z.object({
        message: z.string(),
      }),
    },
    body: z.object({
      approved: z.boolean(),
    }),
  },

  createMachine: {
    method: "POST",
    path: "/machines",
    headers: z.object({
      authorization: z.string(),
      ...machineHeaders,
    }),
    body: z.object({
      functions: z
        .array(
          z.object({
            name: z.string(),
            description: z.string().optional(),
            schema: z.string().optional(),
            config: ToolConfigSchema.optional(),
          }),
        )
        .optional(),
      tools: z
        .array(
          z.object({
            name: z.string(),
            description: z.string().optional(),
            schema: z.string().optional(),
            config: ToolConfigSchema.optional(),
          }),
        )
        .optional(),
    }),
    responses: {
      200: z.object({
        clusterId: z.string(),
      }),
      204: z.undefined(),
    },
  },

  // Cluster Endpoints
  createCluster: {
    method: "POST",
    path: "/clusters",
    headers: z.object({
      authorization: z.string(),
    }),
    responses: {
      204: z.undefined(),
    },
    body: z.object({
      description: z
        .string()
        .describe("Human readable description of the cluster"),
      name: z
        .string()
        .optional()
        .describe("Human readable name of the cluster"),
      isDemo: z
        .boolean()
        .optional()
        .default(false)
        .describe("Whether the cluster is a demo cluster"),
    }),
  },
  deleteCluster: {
    method: "DELETE",
    path: "/clusters/:clusterId",
    headers: z.object({
      authorization: z.string(),
    }),
    body: z.undefined(),
    responses: {
      204: z.undefined(),
    },
  },
  updateCluster: {
    method: "PUT",
    path: "/clusters/:clusterId",
    headers: z.object({
      authorization: z.string(),
    }),
    responses: {
      204: z.undefined(),
      401: z.undefined(),
    },
    body: z.object({
      name: z.string().optional(),
      description: z.string().optional(),
      debug: z
        .boolean()
        .optional()
        .describe(
          "Enable additional logging (Including prompts and results) for use by Inferable support",
        ),
      enableCustomAuth: z.boolean().optional(),
      enableKnowledgebase: z.boolean().optional(),
      handleCustomAuthFunction: z.string().optional(),
    }),
  },
  getCluster: {
    method: "GET",
    path: "/clusters/:clusterId",
    headers: z.object({
      authorization: z.string(),
    }),
    responses: {
      200: z.object({
        id: z.string(),
        name: z.string(),
        description: z.string().nullable(),
        createdAt: z.number(),
        debug: z.boolean(),
        enableCustomAuth: z.boolean(),
        handleCustomAuthFunction: z.string().nullable(),
        isDemo: z.boolean(),
        machines: z.array(
          z.object({
            id: z.string(),
            lastPingAt: z.number().nullable(),
            ip: z.string().nullable(),
            sdkVersion: z.string().nullable(),
            sdkLanguage: z.string().nullable(),
          }),
        ),
        tools: z.array(
          z.object({
            name: z.string(),
            description: z.string().nullable(),
            schema: z.unknown().nullable(),
            config: z.unknown().nullable(),
            shouldExpire: z.boolean(),
            createdAt: z.number(),
            lastPingAt: z.number().nullable(),
          }),
        ),
      }),
      401: z.undefined(),
      404: z.undefined(),
    },
    pathParams: z.object({
      clusterId: z.string(),
    }),
  },
  listClusters: {
    method: "GET",
    path: "/clusters",
    headers: z.object({
      authorization: z.string(),
    }),
    responses: {
      200: z.array(
        z.object({
          id: z.string(),
          name: z.string(),
          createdAt: z.date(),
          description: z.string().nullable(),
        }),
      ),
      401: z.undefined(),
    },
  },

  // Event Endpoints
  listEvents: {
    method: "GET",
    path: "/clusters/:clusterId/events",
    headers: z.object({
      authorization: z.string(),
    }),
    responses: {
      200: z.array(
        z.object({
          type: z.string(),
          machineId: z.string().nullable(),
          createdAt: z.date(),
          jobId: z.string().nullable(),
          targetFn: z.string().nullable(),
          resultType: z.string().nullable(),
          status: z.string().nullable(),
          runId: z.string().nullable(),
          meta: z.any().nullable(),
          id: z.string(),
        }),
      ),
      401: z.undefined(),
      404: z.undefined(),
    },
    query: z.object({
      type: z.string().optional(),
      jobId: z.string().optional(),
      machineId: z.string().optional(),
      runId: z.string().optional(),
      includeMeta: z.string().optional(),
    }),
  },
  getEventMeta: {
    method: "GET",
    path: "/clusters/:clusterId/events/:eventId/meta",
    headers: z.object({
      authorization: z.string(),
    }),
    responses: {
      200: z.object({
        type: z.string(),
        machineId: z.string().nullable(),
        createdAt: z.date(),
        jobId: z.string().nullable(),
        targetFn: z.string().nullable(),
        resultType: z.string().nullable(),
        status: z.string().nullable(),
        meta: z.unknown(),
        id: z.string(),
      }),
      401: z.undefined(),
      404: z.undefined(),
    },
  },
  oas: {
    method: "GET",
    path: "/public/oas.json",
    responses: {
      200: z.unknown(),
    },
  },

  // API Key Endpoints
  createApiKey: {
    method: "POST",
    path: "/clusters/:clusterId/api-keys",
    headers: z.object({ authorization: z.string() }),
    pathParams: z.object({
      clusterId: z.string(),
    }),
    body: z.object({
      name: z.string(),
    }),
    responses: {
      200: z.object({
        id: z.string(),
        key: z.string(),
      }),
    },
  },
  listApiKeys: {
    method: "GET",
    path: "/clusters/:clusterId/api-keys",
    headers: z.object({ authorization: z.string() }),
    pathParams: z.object({
      clusterId: z.string(),
    }),
    responses: {
      200: z.array(
        z.object({
          id: z.string(),
          name: z.string(),
          createdAt: z.date(),
          createdBy: z.string(),
          revokedAt: z.date().nullable(),
        }),
      ),
    },
  },
  revokeApiKey: {
    method: "DELETE",
    path: "/clusters/:clusterId/api-keys/:keyId",
    headers: z.object({ authorization: z.string() }),
    pathParams: z.object({
      clusterId: z.string(),
      keyId: z.string(),
    }),
    body: z.undefined(),
    responses: {
      204: z.undefined(),
    },
  },

  listMachines: {
    method: "GET",
    path: "/clusters/:clusterId/machines",
    headers: z.object({
      authorization: z.string(),
    }),
    query: z.object({
      limit: z.coerce.number().min(10).max(50).default(50),
    }),
    responses: {
      200: z.array(
        z.object({
          id: z.string(),
          lastPingAt: z.date(),
          ip: z.string(),
        }),
      ),
    },
    pathParams: z.object({
      clusterId: z.string(),
    }),
  },

  // Tool Endpoints
  listTools: {
    method: "GET",
    path: "/clusters/:clusterId/tools",
    headers: z.object({
      authorization: z.string(),
    }),
    pathParams: z.object({
      clusterId: z.string(),
    }),
    responses: {
      200: z.array(
        z.object({
          name: z.string(),
          description: z.string().nullable(),
          schema: z.string().nullable(),
          config: ToolConfigSchema.nullable(),
          shouldExpire: z.boolean(),
          lastPingAt: z.date().nullable(),
          createdAt: z.date(),
        }),
      ),
      401: z.undefined(),
    },
  },
} as const;

export const contract = c.router(definition);
