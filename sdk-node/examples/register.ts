import { AgentRPC } from "../src";
import { z } from "zod";

const rpc = new AgentRPC({
  apiSecret: process.env.AGENTRPC_API_SECRET!,
});

client.register({
  name: "getWeather",
  description: "Return weather information at a given location",
  schema: z.object({ location: z.string() }),
  handler: async ({ location }) => {
    return {
      location: location,
      temperature: "variable",
      parcipitation: "probably",
    };
  }
});

client.listen();
