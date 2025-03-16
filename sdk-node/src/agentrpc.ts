import debug from "debug";
import path from "path";
import { z } from "zod";
import { createApiClient } from "./create-client";
import { AgentRPCError } from "./errors";
import { machineId } from "./machine-id";
import { PollingAgent, registerMachine } from "./polling";
import { ToolRegistrationInput, JsonSchemaInput } from "./types";

// Custom json formatter
debug.formatters.J = (json) => {
  return JSON.stringify(json, null, 2);
};

export const log = debug("agentrpc:client");

/**
 * The AgentRPC client.
 *
 * ```ts
 * // create a new AngentRPC instance
 * const client = new AgentRPC({
 *  apiSecret: "API_SECRET",
 * });
 *
 *
 * // Register a tool
 * client.register("hello", z.object({name: z.string()}), async ({name}: {name: string}) => {
 *  return `Hello ${name}`;
 * })
 *
 * await client.listen();
 *
 * // stop the service on shutdown
 * process.on("beforeExit", async () => {
 *   await myService.stop();
 * });
 *
 * ```
 */
export class AgentRPC {
  static getVersion(): string {
    // eslint-disable-next-line @typescript-eslint/no-var-requires, @typescript-eslint/no-require-imports
    return require(path.join(__dirname, "..", "package.json")).version;
  }

  private clusterId?: string;

  private apiSecret: string;
  private endpoint: string;
  private machineId: string;

  private client: ReturnType<typeof createApiClient>;

  private pollingAgents: PollingAgent[] = [];

  private toolsRegistry: { [key: string]: ToolRegistrationInput<any> } = {};

  /**
   * Initializes a new AgentRPC instance.
   * @param apiSecret The API Secret for your AgentRPC cluster. If not provided, it will be read from the `INFERABLE_API_SECRET` environment variable.
   * @param options Additional options for the AgentRPC client.
   * @param options.endpoint The endpoint for the AgentRPC cluster. Defaults to https://api.agentrpc.com.
   *
   * @example
   * ```ts
   * // Basic usage
   * const client = new AgentRPC({
   *  apiSecret: "API_SECRET",
   * });
   * ```
   */
  constructor(options?: {
    apiSecret?: string;
    endpoint?: string;
    machineId?: string;
  }) {
    const apiSecret = options?.apiSecret;

    if (!apiSecret) {
      throw new AgentRPCError(`No API Secret provided.`);
    }

    if (!apiSecret.startsWith("sk_")) {
      throw new AgentRPCError(`Invalid API Secret.`);
    }

    this.apiSecret = apiSecret;

    this.endpoint = options?.endpoint || "https://api.agentrpc.com";

    this.machineId = options?.machineId || machineId();

    this.client = createApiClient({
      baseUrl: this.endpoint,
      machineId: this.machineId,
      apiSecret: this.apiSecret,
    });
  }

  public register<T extends z.ZodTypeAny | JsonSchemaInput>({
    name,
    handler,
    schema,
    config,
    description,
  }: ToolRegistrationInput<T>) {
    if (this.toolsRegistry[name]) {
      throw new AgentRPCError(`Tool name '${name}' is already registered.`);
    }

    const registration: ToolRegistrationInput<T> = {
      name,
      handler,
      schema: {
        input: schema.input,
      },
      config,
      description,
    };

    const existing = this.pollingAgents.length > 0;

    if (existing) {
      throw new AgentRPCError(
        `Tools must be registered before starting the listener.`,
      );
    }

    if (typeof registration.handler !== "function") {
      throw new AgentRPCError(`handler must be a function.`);
    }

    log(`Registering tool`, {
      name: registration.name,
    });

    this.toolsRegistry[registration.name] = registration;
  }

  public async listen() {
    if (this.pollingAgents.length > 0) {
      throw new AgentRPCError("Tools already listening");
    }

    // TODO: Create one polling agent per 10 tools
    const agent = new PollingAgent({
      endpoint: this.endpoint,
      machineId: this.machineId,
      apiSecret: this.apiSecret,
      clusterId: await this.getClusterId(),
      tools: Object.values(this.toolsRegistry),
    });

    this.pollingAgents.push(agent);
    await agent.start();
  }

  public async unlisten() {
    Promise.all(this.pollingAgents.map((agent) => agent.stop()));
  }

  private async getClusterId() {
    if (!this.clusterId) {
      // Call register machine without any services to test API key and get clusterId
      const registerResult = await registerMachine(this.client);
      this.clusterId = registerResult.clusterId;
    }

    return this.clusterId;
  }
}
