import { z } from "zod";
import { testInstance } from "../utils";

const cache = new Map<string, any>();

export const getProduct = async ({
  id,
  random,
}: {
  id: string;
  random: string;
}) => {
  return {
    id,
    name: `Product ${id}`,
    random,
  };
};

export const succeedsOnSecondAttempt = async ({ id }: { id: string }) => {
  if (cache.has(id)) {
    return true;
  } else {
    cache.set(id, true);
    // wait 5s and time out
    await new Promise((resolve) => setTimeout(resolve, 5000));
  }
};

export const productService = () => {
  const prefix = `product${Math.random().toString(36).substring(2, 5)}`;
  const client = testInstance();

  client.register({
    name: `${prefix}_getProduct10sCache`,
    handler: getProduct,
    schema: z.object({
      id: z.string(),
      random: z.string(),
    }),
    config: {
      retryCountOnStall: 0,
      timeoutSeconds: 5,
      cache: {
        keyPath: "$.id",
        ttlSeconds: 10,
      },
    },
  });

  client.register({
    name: `${prefix}_getProduct1sCache`,
    handler: getProduct,
    schema: z.object({
      id: z.string(),
      random: z.string(),
    }),
    config: {
      retryCountOnStall: 0,
      timeoutSeconds: 5,
      cache: {
        keyPath: "$.id",
        ttlSeconds: 1,
      },
    },
  });

  let failingFunctionCount = 0;

  client.register({
    name: `${prefix}_failingFunction`,
    handler: async () => {
      await new Promise((resolve) => setTimeout(resolve, 5000));
      failingFunctionCount++;
      return failingFunctionCount;
    },
    schema: z.object({
      id: z.string(),
    }),
    config: {
      retryCountOnStall: 0,
      timeoutSeconds: 2,
    },
  });

  client.register({
    name: `${prefix}_succeedsOnSecondAttempt`,
    handler: succeedsOnSecondAttempt,
    schema: z.object({
      id: z.string(),
    }),
    config: {
      retryCountOnStall: 2,
      timeoutSeconds: 2,
    },
  });

  return {
    prefix,
    client,
  };
};
