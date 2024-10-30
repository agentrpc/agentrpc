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

Create a file named i.ts which will be used to initialize Inferable. This file will export the Inferable instance.

```typescript
// d.ts

import { Inferable } from "inferable";

// Initialize the Inferable client with your API secret.
// Get yours at https://console.inferable.ai.
export const d = new Inferable({
  apiSecret: "YOUR_API_SECRET",
});
```

### 2. Hello World Function

In a separate file, register a "sayHello" [function](https://docs.inferable.ai/pages/functions). This file will import the Inferable instance from `i.ts` and register the [function](https://docs.inferable.ai/pages/functions) with the [control-plane](https://docs.inferable.ai/pages/control-plane).

```typescript
// service.ts

import { i } from "./i";

// Define a simple function that returns "Hello, World!"
const sayHello = async ({ to }: { to: string }) => {
  return `Hello, ${to}!`;
};

// Register the service (using the 'default' service)
const sayHello = i.default.register({
  name: "sayHello",
  func: sayHello,
  schema: {
    input: z.object({
      to: z.string(),
    }),
  },
});

// Start the 'default' service
i.default.start();
```

### 3. Running the Service

To run the service, simply run the file with the [function](https://docs.inferable.ai/pages/functions) definition. This will start the `default` [service](https://docs.inferable.ai/pages/services) and make it available to the Inferable agent.

```bash
tsx service.ts
```

### 4. Trigger a run

The following code will create an [Inferable run](https://docs.inferable.ai/pages/runs) with the prompt "Say hello to John" and the `sayHello` function attached.

> You can inspect the progress of the run:
>
> - in the [playground UI](https://app.inferable.ai/) via `inf app`
> - in the [CLI](https://www.npmjs.com/package/@inferable/cli) via `inf runs list`

```typescript
const run = await i.run({
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

console.log("Started Run", {
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
