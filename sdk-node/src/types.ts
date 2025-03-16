import { z } from "zod";
import { ToolConfigSchema } from "./contract";

export type ToolConfig = z.infer<typeof ToolConfigSchema>;

export type ToolInput<T extends z.ZodTypeAny | JsonSchemaInput> =
  T extends z.ZodObject<infer Input>
    ? {
        [K in keyof Input]: z.infer<Input[K]>;
      }
    : // eslint-disable-next-line @typescript-eslint/no-explicit-any
      any;

import type { JSONSchema4Type } from "json-schema";
import type { JsonSchema7Type } from "zod-to-json-schema";

export type JsonSchema = JSONSchema4Type | JsonSchema7Type;

export type JsonSchemaInput = {
  type: string;
  properties: Record<string, JsonSchema>;
  required: string[];
  $schema: string;
};

export type ToolSchema<T extends z.ZodTypeAny | JsonSchemaInput> = {
  input: T;
};

export type ToolRegistrationInput<T extends z.ZodTypeAny | JsonSchemaInput> = {
  name: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  handler: (input: ToolInput<T>) => Promise<any>;
  schema: ToolSchema<T>;
  config?: ToolConfig;
  description?: string;
};
