<p align="center">
  <img src="https://a.inferable.ai/logo.png?v=2" width="200" style="border-radius: 10px" />
</p>

# Typescript SDK

[![npm version](https://badge.fury.io/js/inferable.svg)](https://badge.fury.io/js/inferable)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/badge/docs-inferable.ai-brightgreen)](https://docs.inferable.ai/)
[![Downloads](https://img.shields.io/npm/dm/inferable)](https://www.npmjs.com/package/inferable)

This is the official Inferable AI SDK for Typescript.

## Installation

### npm

```bash
npm install inferable
```

### yarn

```bash
yarn add inferable
```

### pnpm

```bash
pnpm add inferable
```

## Quick Start

### 1. Initializing Inferable

```typescript
// d.ts

import { Inferable } from "inferable";

// Initialize the Inferable client with your API secret.
// Get yours at https://console.inferable.ai.
const client = new Inferable({
  apiSecret: "YOUR_API_SECRET",
});
```

If you don't provide an API key or base URL, it will attempt to read them from the following environment variables:

- `INFERABLE_API_SECRET`
- `INFERABLE_API_ENDPOINT`

### 2. Hello World Function

Register a "sayHello" [function](https://docs.inferable.ai/pages/functions). This file will register the function with the [control-plane](https://docs.inferable.ai/pages/control-plane).

```typescript
// Register a simple function (using the 'default' service)
const sayHello = client.default.register({
  name: "sayHello",
  func: async ({ to }: { to: string }) => {
    return `Hello, ${to}!`;
  },
  schema: {
    input: z.object({
      to: z.string(),
    }),
  },
});

// Start the 'default' service
client.default.start();
```

### 3. Trigger a run

The following code will create an [Inferable run](https://docs.inferable.ai/pages/runs) with the prompt "Say hello to John" and the `sayHello` function attached.

> You can inspect the progress of the run:
>
> - in the [playground UI](https://app.inferable.ai/) via `inf app`
> - in the [CLI](https://www.npmjs.com/package/@inferable/cli) via `inf runs list`

```typescript
const run = await client.run({
  message: "Say hello to John",
  // Optional: Explicitly attach the `sayHello` function (All functions attached by default)
  attachedFunctions: [{
    function: "sayHello",
    service: "default",
  }],
  // Optional: Define a schema for the result to conform to
  resultSchema: z.object({
    didSayHello: z.boolean()
  }),
  // Optional: Subscribe an Inferable function to receive notifications when the run status changes
  //onStatusChange: { function: { function: "handler", service: "default" } },
});

console.log("Run Started", {
  result: run.id,
});

// Wait for the run to complete and log.
console.log("Run result", {
  result: await run.poll(),
});
```

> Runs can also be triggered via the [API](https://docs.inferable.ai/pages/invoking-a-run-api), [CLI](https://www.npmjs.com/package/@inferable/cli) or [playground UI](https://app.inferable.ai/).

## Documentation

- [Inferable documentation](https://docs.inferable.ai/) contains all the information you need to get started with Inferable.

## Support

For support or questions, please [create an issue in the repository](https://github.com/inferablehq/inferable/issues) or [join the Discord](https://discord.gg/WHcTNeDP)

## Contributing

Contributions to the Inferable NodeJs Client are welcome. Please ensure that your code adheres to the existing style and includes appropriate tests.
