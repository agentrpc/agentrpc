// Package agentrpc provides a client for interacting with the AgentRPC platform.
package agentrpc

import (
	"encoding/json"
	"fmt"
	"net/http"
	"reflect"
	"strings"

	"github.com/agentrpc/agentrpc/sdk-go/internal/client"
	"github.com/agentrpc/agentrpc/sdk-go/internal/util"
)

// Version of the AgentRPC package
const Version = "0.0.4"

const (
	// DefaultAPIEndpoint is the default endpoint for the AgentRPC API.
	DefaultAPIEndpoint = "https://api.agentrpc.com"
)

// AgentRPC is the main client for interacting with the AgentRPC platform.
type AgentRPC struct {
	client      *client.Client
	apiEndpoint string
	apiSecret   string
	machineID   string
	clusterID   string
	tools       *pollingAgent
}

type AgentRPCOptions struct {
	APIEndpoint string
	APISecret   string
	MachineID   string
}

// Initializes a new AgentRPC client.
//
// Parameters:
// 0 - options: The options for the AgentRPC client.
//
// Example:
//
//	// Create a new AgentRPC instance with an API secret
//	client := inferable.New(AgentRPCOptions{
//	    ApiSecret: "API_SECRET",
//	})
func New(options AgentRPCOptions) (*AgentRPC, error) {
	if options.APIEndpoint == "" {
		options.APIEndpoint = DefaultAPIEndpoint
	}

	machineID := options.MachineID
	if machineID == "" {
		machineID = util.GenerateMachineID(8)
	}

	parts := strings.Split(options.APISecret, "_")
	if len(parts) != 3 || parts[0] != "sk" {
		return nil, fmt.Errorf("invalid API secret")
	}

	client, err := client.NewClient(client.ClientOptions{
		Endpoint: options.APIEndpoint,
		Secret:   options.APISecret,
	})

	if err != nil {
		return nil, fmt.Errorf("error creating client: %v", err)
	}

	rpc := &AgentRPC{
		client:      client,
		apiEndpoint: options.APIEndpoint,
		apiSecret:   options.APISecret,
		clusterID:   parts[1],
		machineID:   machineID,
	}

	rpc.tools, err = rpc.createPollingAgent()
	if err != nil {
		return nil, fmt.Errorf("error creating polling agent: %v", err)
	}

	return rpc, nil
}

// Registers a Tool
//
// Parameters:
// - input: The Tool definition.
//
// Example:
//
//	// Create a new AgentRPC instance with an API secret
//	client := inferable.New(AgentRPCOptions{
//	    ApiSecret: "API_SECRET",
//	})
//
//	sayHello, err := client.Register(Tool{
//	  Handler:        func(input EchoInput) string {
//	    didCallSayHello = true
//	    return "Hello " + input.Input
//	  },
//	  Name:        "SayHello",
//	  Description: "A simple greeting function",
//	})
//
//	client.Listen()
//
//	defer client.Unlisten()
func (i *AgentRPC) Register(fn Tool) error {
	return i.tools.Register(fn)
}

func (i *AgentRPC) Listen() error {
	return i.tools.Listen()
}

func (i *AgentRPC) Unlisten() {
	i.tools.Unlisten()
}

func (i *AgentRPC) createPollingAgent() (*pollingAgent, error) {

	agent := &pollingAgent{
		Tools:     make(map[string]Tool),
		inferable: i, // Set the reference to the Inferable instance
	}
	return agent, nil
}

func (i *AgentRPC) callFunc(funcName string, args ...interface{}) ([]reflect.Value, error) {
	fn, exists := i.tools.Tools[funcName]
	if !exists {
		return nil, fmt.Errorf("function with name '%s' not found", funcName)
	}

	// Get the reflect.Value of the function
	fnValue := reflect.ValueOf(fn.Handler)

	// Check if the number of arguments is correct
	if len(args) != fnValue.Type().NumIn() {
		return nil, fmt.Errorf("invalid number of arguments for function '%s'", funcName)
	}

	// Prepare the arguments
	inArgs := make([]reflect.Value, len(args))
	for i, arg := range args {
		inArgs[i] = reflect.ValueOf(arg)
	}

	// Call the function
	return fnValue.Call(inArgs), nil
}

func (i *AgentRPC) fetchData(options client.FetchDataOptions) ([]byte, http.Header, error, int) {
	// Add default Content-Type header if not present
	if options.Headers == nil {
		options.Headers = make(map[string]string)
	}
	if _, exists := options.Headers["Content-Type"]; !exists && options.Body != "" {
		options.Headers["Content-Type"] = "application/json"
	}

	data, headers, err, status := i.client.FetchData(options)
	return []byte(data), headers, err, status
}

func (i *AgentRPC) serverOk() error {
	data, _, err, _ := i.client.FetchData(client.FetchDataOptions{
		Path:   "/live",
		Method: "GET",
	})
	if err != nil {
		return fmt.Errorf("error fetching data from /live: %v", err)
	}

	var response struct {
		Status string `json:"status"`
	}

	// Convert string to []byte before unmarshaling
	if err := json.Unmarshal([]byte(data), &response); err != nil {
		return fmt.Errorf("error unmarshaling response: %v", err)
	}

	if response.Status != "ok" {
		return fmt.Errorf("unexpected status from /live: %s", response.Status)
	}

	return nil
}

func (i *AgentRPC) registerMachine(s *pollingAgent) (string, error) {
	// Prepare the payload for registration
	payload := struct {
		Service string `json:"service,omitempty"`
		Tools   []struct {
			Name        string `json:"name"`
			Description string `json:"description,omitempty"`
			Schema      string `json:"schema,omitempty"`
		} `json:"tools,omitempty"`
	}{}

	if s != nil {
		// Check if there are any registered functions
		if len(s.Tools) == 0 {
			return "", fmt.Errorf("cannot register machine with no functions")
		}

		// Add registered functions to the payload
		for _, fn := range s.Tools {
			schemaJSON, err := json.Marshal(fn.schema)
			if err != nil {
				return "", fmt.Errorf("failed to marshal schema for function '%s': %v", fn.Name, err)
			}

			payload.Tools = append(payload.Tools, struct {
				Name        string `json:"name"`
				Description string `json:"description,omitempty"`
				Schema      string `json:"schema,omitempty"`
			}{
				Name:        fn.Name,
				Description: fn.Description,
				Schema:      string(schemaJSON),
			})
		}
	}

	// Marshal the payload to JSON
	jsonPayload, err := json.Marshal(payload)
	if err != nil {
		return "", fmt.Errorf("failed to marshal payload: %v", err)
	}

	// Prepare headers
	headers := map[string]string{
		"Authorization":          "Bearer " + i.apiSecret,
		"X-Machine-ID":           i.machineID,
		"X-Machine-SDK-Version":  Version,
		"X-Machine-SDK-Language": "go",
	}

	// Call the registerMachine endpoint
	options := client.FetchDataOptions{
		Path:    "/machines",
		Method:  "POST",
		Headers: headers,
		Body:    string(jsonPayload),
	}

	responseData, _, err, _ := i.fetchData(options)
	if err != nil {
		return "", fmt.Errorf("failed to register machine: %v", err)
	}

	// Parse the response
	var response struct {
		ClusterId string `json:"clusterId"`
	}

	err = json.Unmarshal(responseData, &response)
	if err != nil {
		return "", fmt.Errorf("failed to parse registration response: %v", err)
	}

	return response.ClusterId, nil
}
