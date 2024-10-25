// Package inferable provides a client for interacting with the Inferable API.
package inferable

import (
	"encoding/json"
	"fmt"
	"net/http"
	"reflect"

	"github.com/inferablehq/inferable/sdk-go/internal/client"
	"github.com/inferablehq/inferable/sdk-go/internal/util"
)

// Version of the inferable package
const Version = "0.1.15"

const (
	DefaultAPIEndpoint = "https://api.inferable.ai"
)

type functionRegistry struct {
	services map[string]*service
}

type Inferable struct {
	client           *client.Client
	apiEndpoint      string
	apiSecret        string
	functionRegistry functionRegistry
	machineID        string
	clusterID        string
	Default          *service
}

type InferableOptions struct {
	APIEndpoint string
	APISecret   string
	MachineID   string
	ClusterID   string
}

// Input struct passed to a Run's result handler
type RunResultHandlerInput struct {
	Status   string      `json:"status"`
	RunId    string      `json:"runId"`
	Result   interface{} `json:"result"`
	Summary  string      `json:"summary"`
	Metadata interface{} `json:"metadata"`
}

type RunResult struct {
	Handler *FunctionHandle
	Schema  interface{}
}

type RunTemplate struct {
	ID    string
	Input map[string]interface{}
}

type Run struct {
	Functions []*FunctionHandle
	Message   string
	Result    *RunResult
	Metadata  map[string]string
	Template  *RunTemplate
}

type runHandle struct {
	ID string
}

type templateHandle struct {
	ID  string
	Run func(input *Run) (*runHandle, error)
}

func New(options InferableOptions) (*Inferable, error) {
	if options.APIEndpoint == "" {
		options.APIEndpoint = DefaultAPIEndpoint
	}
	client, err := client.NewClient(client.ClientOptions{
		Endpoint: options.APIEndpoint,
		Secret:   options.APISecret,
	})
	if err != nil {
		return nil, fmt.Errorf("error creating client: %v", err)
	}

	machineID := options.MachineID
	if machineID == "" {
		machineID = util.GenerateMachineID(8)
	}

	inferable := &Inferable{
		client:           client,
		apiEndpoint:      options.APIEndpoint,
		apiSecret:        options.APISecret,
		clusterID:        options.ClusterID,
		functionRegistry: functionRegistry{services: make(map[string]*service)},
		machineID:        machineID,
	}

	// Automatically register the default service
	inferable.Default, err = inferable.RegisterService("default")
	if err != nil {
		return nil, fmt.Errorf("error registering default service: %v", err)
	}

	return inferable, nil
}

func (i *Inferable) RegisterService(serviceName string) (*service, error) {
	if _, exists := i.functionRegistry.services[serviceName]; exists {
		return nil, fmt.Errorf("service with name '%s' already registered", serviceName)
	}
	service := &service{
		Name:      serviceName,
		Functions: make(map[string]Function),
		inferable: i, // Set the reference to the Inferable instance
	}
	i.functionRegistry.services[serviceName] = service
	return service, nil
}

func (i *Inferable) CreateRun(input *Run) (*runHandle, error) {
	if i.clusterID == "" {
		return nil, fmt.Errorf("cluster ID must be provided to manage runs")
	}

	var attachedFunctions []string
	for _, fn := range input.Functions {
		attachedFunctions = append(attachedFunctions, fmt.Sprintf("%s_%s", fn.Service, fn.Function))
	}

	payload := client.CreateRunInput{
		Message:           input.Message,
		AttachedFunctions: attachedFunctions,
		Metadata:          input.Metadata,
	}

	if input.Template != nil {
		payload.Template = &client.CreateRunTemplateInput{
			Input: input.Template.Input,
			ID:    input.Template.ID,
		}
	}

	if input.Result != nil {
		payload.Result = &client.CreateRunResultInput{}
		if input.Result.Handler != nil {
			payload.Result.Handler = &client.CreateRunResultHandlerInput{
				Service:  input.Result.Handler.Service,
				Function: input.Result.Handler.Function,
			}
		}
		if input.Result.Schema != nil {
			payload.Result.Schema = input.Result.Schema
		}
	}

	// Marshal the payload to JSON
	jsonPayload, err := json.Marshal(payload)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal payload: %v", err)
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
		Path:    fmt.Sprintf("/clusters/%s/runs", i.clusterID),
		Method:  "POST",
		Headers: headers,
		Body:    string(jsonPayload),
	}

	responseData, _, err, _ := i.fetchData(options)
	if err != nil {
		return nil, fmt.Errorf("failed to create run: %v", err)
	}

	// Parse the response
	var response struct {
		ID string `json:"id"`
	}

	err = json.Unmarshal(responseData, &response)
	if err != nil {
		return nil, fmt.Errorf("failed to parse run response: %v", err)
	}

	return &runHandle{ID: response.ID}, nil
}

func (i *Inferable) GetTemplate(id string) (*templateHandle, error) {
	if i.clusterID == "" {
		return nil, fmt.Errorf("cluster ID must be provided to manage runs")
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
		Path:    fmt.Sprintf("/clusters/%s/prompt-templates/%s", i.clusterID, id),
		Method:  "GET",
		Headers: headers,
	}

	responseData, _, err, _ := i.fetchData(options)
	if err != nil {
		return nil, fmt.Errorf("failed to get template: %v", err)
	}

	// Parse the response
	var response struct {
		ID string `json:"id"`
	}

	err = json.Unmarshal(responseData, &response)
	if err != nil {
		return nil, fmt.Errorf("failed to parse template response: %v", err)
	}

	return &templateHandle{
		ID: response.ID,
		Run: func(input *Run) (*runHandle, error) {
			// CLone the input
			inputCopy := *input

			// Set the template ID
			if inputCopy.Template == nil {
				inputCopy.Template = &RunTemplate{
					ID: response.ID,
				}
			} else {
				inputCopy.Template.ID = response.ID
			}

			fmt.Println(inputCopy)

			return i.CreateRun(&inputCopy)
		},
	}, nil
}

func (i *Inferable) callFunc(serviceName, funcName string, args ...interface{}) ([]reflect.Value, error) {
	service, exists := i.functionRegistry.services[serviceName]
	if !exists {
		return nil, fmt.Errorf("service with name '%s' not found", serviceName)
	}

	fn, exists := service.Functions[funcName]
	if !exists {
		return nil, fmt.Errorf("function with name '%s' not found in service '%s'", funcName, serviceName)
	}

	// Get the reflect.Value of the function
	fnValue := reflect.ValueOf(fn.Func)

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

func (i *Inferable) toJSONDefinition() ([]byte, error) {
	definitions := make([]map[string]interface{}, 0)

	for serviceName, service := range i.functionRegistry.services {
		serviceDef := make(map[string]interface{})
		functions := make([]map[string]interface{}, 0)

		for _, function := range service.Functions {
			funcDef := map[string]interface{}{
				"name":        function.Name,
				"description": function.Description,
				"schema":      function.schema,
			}
			functions = append(functions, funcDef)
		}

		serviceDef["service"] = serviceName
		serviceDef["functions"] = functions

		definitions = append(definitions, serviceDef)
	}

	return json.MarshalIndent(definitions, "", "  ")
}

func (i *Inferable) fetchData(options client.FetchDataOptions) ([]byte, http.Header, error, int) {
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

func (i *Inferable) serverOk() error {
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
