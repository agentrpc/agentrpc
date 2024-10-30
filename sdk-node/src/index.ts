/**
 * # inferable
 *
 * ## Installation
 *
 * ```bash
 * npm install inferable
 * ```
 *
 * ```bash
 * yarn add inferable
 * ```
 *
 * ```bash
 * pnpm add inferable
 * ```
 */

export { Inferable } from "./Inferable";
export const masked = () => {
  throw new Error("masked is not implemented");
};

export * as InferablePromptfooProvider from "./eval/promptfoo";
export { statusChangeSchema } from "./types";

export {
  validateDescription,
  validateServiceName,
  validateFunctionName,
  validateFunctionSchema,
  blob,
} from "./util";

export { createApiClient } from "./create-client";
