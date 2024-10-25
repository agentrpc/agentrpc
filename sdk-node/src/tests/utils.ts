import { Inferable } from "../Inferable";
import { initClient } from "@ts-rest/core";
import { contract } from "../contract";

if (
  !process.env.INFERABLE_MACHINE_SECRET ||
  !process.env.INFERABLE_CONSUME_SECRET ||
  !process.env.INFERABLE_API_ENDPOINT ||
  !process.env.INFERABLE_CLUSTER_ID
) {
  throw new Error("Test environment variables not set");
}

export const TEST_ENDPOINT = process.env.INFERABLE_API_ENDPOINT;
export const TEST_CLUSTER_ID = process.env.INFERABLE_CLUSTER_ID;

export const TEST_MACHINE_SECRET = process.env.INFERABLE_MACHINE_SECRET;
export const TEST_CONSUME_SECRET = process.env.INFERABLE_CONSUME_SECRET;

console.log("Testing with", {
  TEST_ENDPOINT,
  TEST_CLUSTER_ID,
});

export const client = initClient(contract, {
  baseUrl: TEST_ENDPOINT,
  baseHeaders: {
    authorization: `${TEST_CONSUME_SECRET}`,
  },
});

export const inferableInstance = () =>
  new Inferable({
    apiSecret: TEST_MACHINE_SECRET,
    endpoint: TEST_ENDPOINT,
    jobPollWaitTime: 5000,
  });
