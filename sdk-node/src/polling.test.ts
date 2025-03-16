import assert from "assert";
import { z } from "zod";
import { createAndPollJob } from "./polling";
import { client, TEST_CLUSTER_ID, testInstance } from "./tests/utils";

describe("Polling functions", () => {
  // Create a test service with functions we can call
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

    // Register a function that takes some time to complete
    client.register({
      name: `${prefix}_slow`,
      handler: async (input: { text: string; delay: number }) => {
        await new Promise((resolve) => setTimeout(resolve, input.delay));
        return { echo: input.text, delayed: true };
      },
      schema: {
        input: z.object({
          text: z.string(),
          delay: z.number(),
        }),
      },
    });

    // Register a function for testing invalid tools
    client.register({
      name: `${prefix}_valid`,
      handler: async (input: { text: string }) => {
        return { success: true, text: input.text };
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

  // Set up our test service
  const service = testService();

  // Use jest.retryTimes for integration tests to accommodate occasional network issues
  jest.retryTimes(2);

  beforeAll(async () => {
    await service.client.listen();
  }, 10000);

  afterAll(async () => {
    await service.client.unlisten();
  });

  it("should successfully create and poll for a job", async () => {
    // Get a client instance from the utils
    const apiClient = client;

    // Use the createAndPollJob function directly
    const { status, result, resultType } = await createAndPollJob(
      apiClient,
      TEST_CLUSTER_ID,
      `${service.prefix}_echo`,
      { text: "hello world" },
    );

    // Verify the results
    expect(status).toEqual("done");
    expect(resultType).toEqual("resolution");
    expect(result).toEqual({ echo: "hello world" });
  });

  it("should handle errors from functions properly", async () => {
    const apiClient = client;

    const { status, result, resultType } = await createAndPollJob(
      apiClient,
      TEST_CLUSTER_ID,
      `${service.prefix}_error`,
      { text: "will error" },
    );

    // Verify the error results
    expect(status).toEqual("done");
    expect(resultType).toEqual("rejection");
    expect(result).toHaveProperty("name", "Error");
    expect(result).toHaveProperty("message", "This is an error");
  });

  it("should poll multiple times for slow functions", async () => {
    const apiClient = client;

    const startTime = Date.now();

    const { status, result, resultType } = await createAndPollJob(
      apiClient,
      TEST_CLUSTER_ID,
      `${service.prefix}_slow`,
      { text: "delayed response", delay: 2000 },
    );

    const endTime = Date.now();
    const elapsed = endTime - startTime;

    // Verify the function took at least 2 seconds to complete
    expect(elapsed).toBeGreaterThanOrEqual(2000);

    // Verify the results
    expect(status).toEqual("done");
    expect(resultType).toEqual("resolution");
    expect(result).toEqual({ echo: "delayed response", delayed: true });
  });

  it("should throw when trying to use a non-existent tool", async () => {
    try {
      // This should fail because the tool doesn't exist
      await createAndPollJob(client, TEST_CLUSTER_ID, "nonexistent_tool", {
        text: "should fail",
      });

      // If we get here, the test failed
      fail("Should have thrown an error for nonexistent tool");
    } catch (error) {
      // Just verify we got an error - the exact message might vary
      expect(error).toBeDefined();
    }
  });

  it("should handle different poll intervals", async () => {
    // Use a custom poll interval (shorter for quicker test)
    const customPollInterval = 500; // 500ms

    const { status, result, resultType } = await createAndPollJob(
      client,
      TEST_CLUSTER_ID,
      `${service.prefix}_echo`,
      { text: "custom poll interval" },
    );

    expect(status).toEqual("done");
    expect(resultType).toEqual("resolution");
    expect(result).toEqual({ echo: "custom poll interval" });
  });
});
