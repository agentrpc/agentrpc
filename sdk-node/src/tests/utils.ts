import { AgentRPC } from "../agentrpc";
import { initClient } from "@ts-rest/core";
import { contract } from "../contract";

if (
  !process.env.INFERABLE_TEST_API_SECRET ||
  !process.env.INFERABLE_TEST_API_ENDPOINT ||
  !process.env.INFERABLE_TEST_CLUSTER_ID
) {
  throw new Error("Test environment variables not set");
}

export const TEST_ENDPOINT = process.env.INFERABLE_TEST_API_ENDPOINT;
export const TEST_CLUSTER_ID = process.env.INFERABLE_TEST_CLUSTER_ID;
export const TEST_API_SECRET = process.env.INFERABLE_TEST_API_SECRET;

console.log("Testing with", {
  TEST_ENDPOINT,
  TEST_CLUSTER_ID,
});

export const client = initClient(contract, {
  baseUrl: TEST_ENDPOINT,
  baseHeaders: {
    authorization: `${TEST_API_SECRET}`,
  },
});

export const testInstance = () =>
  new AgentRPC({
    apiSecret: TEST_API_SECRET,
    endpoint: TEST_ENDPOINT,
  });
