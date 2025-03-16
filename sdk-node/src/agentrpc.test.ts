import assert from "assert";
import { z } from "zod";
import { AgentRPC } from "./agentrpc";
import {
  TEST_CLUSTER_ID,
  TEST_API_SECRET,
  client,
  testInstance,
} from "./tests/utils";
import { setupServer } from "msw/node";
import { http, HttpResponse, passthrough } from "msw";

const testService = () => {
  const client = testInstance();
  const prefix = `test${Math.random().toString(36).substring(2, 15)}`;

  client.register({
    name: `${prefix}_echo`,
    handler: async (input: { text: string }) => {
      return { echo: input.text };
    },
    schema: {
      input: z.object({
        text: z.string(),
      }),
    },
  });

  client.register({
    name: `${prefix}_error`,
    handler: async (_input) => {
      throw new Error("This is an error");
    },
    schema: {
      input: z.object({
        text: z.string(),
      }),
    },
  });

  return {
    client,
    prefix,
  };
};

describe("AgentRPC", () => {
  const env = process.env;
  beforeEach(() => {
    delete process.env.INFERABLE_API_SECRET;
  });

  afterEach(() => {
    process.env = { ...env };
  });

  it("should initialize without optional args", () => {
    expect(() => new AgentRPC({ apiSecret: TEST_API_SECRET })).not.toThrow();
  });

  it("should throw if no API secret is provided", () => {
    expect(() => new AgentRPC()).toThrow();
  });

  it("should throw if invalid API secret is provided", () => {
    expect(() => new AgentRPC({ apiSecret: "invalid" })).toThrow();
  });
});

describe("Functions", () => {
  it("should handle successful function calls", async () => {
    const service = testService();

    await service.client.listen();

    const results = await Promise.all(
      Array.from({ length: 10 }).map(async (_, i) => {
        return client.createJob({
          query: {
            waitTime: 20,
          },
          params: {
            clusterId: TEST_CLUSTER_ID,
          },
          body: {
            tool: `${service.prefix}_echo`,
            input: { text: i.toString() },
          },
        });
      }),
    );

    results.forEach((result) => {
      expect(result.status).toBe(200);
      assert(result.status === 200);

      expect(result.body).toEqual(
        expect.objectContaining({
          status: "success",
          resultType: "resolution",
          result: {
            echo: expect.any(String),
          },
        }),
      );
    });

    await service.client.unlisten();
  });

  it("should recover from transient polling errors", async () => {
    // Fail the first 20 polls
    let count = 0;
    const server = setupServer(
      http.all("*/calls", async () => {
        if (count < 1) {
          count += 1;
          return new HttpResponse(null, { status: 500 });
        }
        return passthrough();
      }),
      http.all("*", async () => {
        return passthrough();
      }),
    );
    server.listen();

    const service = testService();
    await service.client.listen();

    const result = await client.createJob({
      query: {
        waitTime: 20,
      },
      params: {
        clusterId: TEST_CLUSTER_ID,
      },
      body: {
        tool: `${service.prefix}_echo`,
        input: { text: "foo" },
      },
    });

    expect(result.status).toEqual(200);
    assert(result.status === 200);
    expect(result.body.result).toEqual({ echo: "foo" });

    server.close();
  });

  it("should fail if machine registeration fails", async () => {
    const server = setupServer(
      http.all("*/machines", async () => {
        return new HttpResponse(null, { status: 500 });
      }),
      http.all("*", async () => {
        return passthrough();
      }),
    );
    server.listen();

    const service = testService();

    await expect(service.client.listen()).rejects.toThrow();

    server.close();
  });
});
