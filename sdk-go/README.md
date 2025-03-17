# AgentRPC Go SDK

A universal RPC layer for AI agents. Connect to any function, any language, any framework, in minutes.

## Installation

```sh
go get github.com/agentrpc/go-sdk
```

## Registering Tools

### Creating an AgentRPC Client

```go
package main

import (
  "github.com/agentrpc/agentrpc/sdk-go"
)

func main() {
  client, err := agentrpc.New(agentrpc.Options{
    APISecret: "YOUR_API_SECRET",
  })
}
```

### Registering a Tool

```go
func main() {
  client, err := agentrpc.New(agentrpc.Options{
    APISecret: "YOUR_API_SECRET",
  })

  err = client.Register(agentrpc.Tool{
    Handler:     func(input EchoInput) string {
      return "Hello " + input.Input
    },
    Name:        "SayHello",
    Description: "A simple greeting function",
  })
}
```

### Starting the Listener

```go
err := client.Listen()
if err != nil {
  log.Fatal(err)
}
```

### Stopping the Listener

```go
client.Unlisten()
```

## API

### `agentrpc.NewClient(config AgentRPCOptions) -> *Client`

Creates a new AgentRPC client.

#### Config Options:

| Option       | Type   | Default                    | Description          |
|-------------|--------|----------------------------|----------------------|
| `APISecret` | string | **Required**               | The API secret key.  |
| `Endpoint`  | string | `https://api.agentrpc.com` | Custom API endpoint. |
| `MachineID` | string | Automatically generated    | Custom machine ID.   |

### `client.Register(tool Tool)`

Registers a tool.

- `Name`: Unique tool identifier.
- `Handler`: Function to process input.


### `client.Listen() error`

Starts listening for requests.

### `client.Unlisten() error`

Stops all running listeners.
```
