package agentrpc

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"reflect"
	"strconv"
	"strings"
	"time"

	"github.com/invopop/jsonschema"

	"github.com/agentrpc/agentrpc/sdk-go/internal/client"
)

const (
	MaxConsecutivePollFailures = 50
	DefaultRetryAfter          = 0
)

type Tool struct {
	Name        string
	Description string
	schema      interface{}
	Config      interface{}
	Handler     interface{}
}

type pollingAgent struct {
	Tools      map[string]Tool
	inferable  *AgentRPC
	ctx        context.Context
	cancel     context.CancelFunc
	retryAfter int
}

type callMessage struct {
	Id       string      `json:"id"`
	Function string      `json:"function"`
	Input    interface{} `json:"input"`
}

type callResultMeta struct {
	FunctionExecutionTime int64 `json:"functionExecutionTime,omitempty"`
}

type callResult struct {
	Result     interface{}    `json:"result"`
	ResultType string         `json:"resultType"`
	Meta       callResultMeta `json:"meta"`
}

func (s *pollingAgent) Register(fn Tool) error {
	if s.isPolling() {
		return fmt.Errorf("tool must be registered before starting the service")
	}

	if _, exists := s.Tools[fn.Name]; exists {
		return fmt.Errorf("tool with name '%s' already registered", fn.Name)
	}

	// Validate that the function has exactly one argument and it's a struct
	fnType := reflect.TypeOf(fn.Handler)
	if fnType.NumIn() != 1 {
		return fmt.Errorf("tool '%s' must have exactly one argument", fn.Name)
	}
	arg1Type := fnType.In(0)

	// Set the argument type to the referenced type
	if arg1Type.Kind() == reflect.Ptr {
		arg1Type = arg1Type.Elem()
	}

	if arg1Type.Kind() != reflect.Struct {
		return fmt.Errorf("tool '%s' first argument must be a struct or a pointer to a struct", fn.Name)
	}

	// Get the schema for the input struct
	reflector := jsonschema.Reflector{DoNotReference: true, Anonymous: true, AllowAdditionalProperties: false}
	schema := reflector.Reflect(reflect.New(arg1Type).Interface())

	if schema == nil {
		return fmt.Errorf("failed to get schema for tool '%s'", fn.Name)
	}

	// Extract the relevant part of the schema
	defs, ok := schema.Definitions[arg1Type.Name()]

	// If the definition is not found, use the whole schema.
	// This tends to happen for inline structs.
	// For example: func(input struct { A int `json:"a"` }) int
	if !ok {
		defs = schema
	}

	defsString, err := json.Marshal(defs)
	if err != nil {
		return fmt.Errorf("failed to marshal schema for tool '%s': %v", fn.Name, err)
	}

	if strings.Contains(string(defsString), "\"$ref\":\"#/$defs") {
		return fmt.Errorf("schema for tool '%s' contains a $ref to an external definition. this is currently not supported. see https://go.inferable.ai/go-schema-limitation for details", fn.Name)
	}

	defs.AdditionalProperties = jsonschema.FalseSchema
	fn.schema = defs

	s.Tools[fn.Name] = fn
	return nil
}

// Start polling for jobs, registers the machine, and starts polling for messages
func (s *pollingAgent) Listen() error {
	_, err := s.inferable.registerMachine(s)
	if err != nil {
		return fmt.Errorf("failed to register machine: %v", err)
	}

	s.ctx, s.cancel = context.WithCancel(context.Background())
	s.retryAfter = DefaultRetryAfter

	go func() {
		failureCount := 0
		for {
			time.Sleep(time.Duration(s.retryAfter) * time.Second)

			select {
			case <-s.ctx.Done():
				return
			default:
				err := s.poll()

				if err != nil {
					failureCount++

					if failureCount > MaxConsecutivePollFailures {
						log.Printf("Too many consecutive poll failures, exiting service")
						s.Unlisten()
					}

					log.Printf("Failed to poll: %v", err)
				}
			}
		}
	}()

	log.Printf("started and polling for messages")
	return nil
}

// Stop stops the service and cancels the polling
func (s *pollingAgent) Unlisten() {
	if s.cancel != nil {
		s.cancel()
		log.Printf("stopped polling for messages")
	}
}

func (s *pollingAgent) poll() error {
	headers := map[string]string{
		"Authorization":          "Bearer " + s.inferable.apiSecret,
		"X-Machine-ID":           s.inferable.machineID,
		"X-Machine-SDK-Version":  Version,
		"X-Machine-SDK-Language": "go",
	}

	// Build comma-seperated tools list
	toolList := ""
	for _, tool := range s.Tools {
		toolList = toolList + tool.Name + ","
	}
	if len(toolList) > 0 {
		toolList = toolList[:len(toolList)-1]
	}

	options := client.FetchDataOptions{
		Path:    fmt.Sprintf("/clusters/%s/jobs?acknowledge=true&tools=%s&status=pending&limit=10&waitTime=20", s.inferable.clusterID, toolList),
		Method:  "GET",
		Headers: headers,
	}

	result, respHeaders, err, status := s.inferable.fetchData(options)

	if status == 410 {
		s.inferable.registerMachine(s)
	}

	if err != nil {
		return fmt.Errorf("failed to poll jobs: %v", err)
	}

	if retryAfter, ok := respHeaders["Retry-After"]; ok {
		for _, v := range retryAfter {
			if i, err := strconv.Atoi(v); err == nil {
				s.retryAfter = i
			}
		}
	}

	parsed := []callMessage{}

	err = json.Unmarshal(result, &parsed)
	if err != nil {
		return fmt.Errorf("failed to parse poll response: %v", err)
	}

	errors := []string{}
	for _, msg := range parsed {
		err := s.handleMessage(msg)
		if err != nil {
			errors = append(errors, err.Error())
		}
	}

	if len(errors) > 0 {
		return fmt.Errorf("failed to handle messages: %v", errors)
	}

	return nil
}

func (s *pollingAgent) handleMessage(msg callMessage) error {
	// Find the target function
	fn, ok := s.Tools[msg.Function]
	if !ok {
		log.Printf("Received call for unknown function: %s", msg.Function)
		return nil
	}

	// Create a new instance of the function's input type
	fnType := reflect.TypeOf(fn.Handler)
	argType := fnType.In(0)
	argPtr := reflect.New(argType)

	inputJson, err := json.Marshal(msg.Input)

	if err != nil {
		result := callResult{
			Result:     err.Error(),
			ResultType: "rejection",
		}

		// Persist the job result
		if err := s.persistJobResult(msg.Id, result); err != nil {
			return fmt.Errorf("failed to persist job result: %v", err)
		}
	}

	err = json.Unmarshal(inputJson, argPtr.Interface())
	if err != nil {
		result := callResult{
			Result:     err.Error(),
			ResultType: "rejection",
		}

		// Persist the job result
		if err := s.persistJobResult(msg.Id, result); err != nil {
			return fmt.Errorf("failed to persist job result: %v", err)
		}
	}

	start := time.Now()
	// Call the function with the unmarshaled argument
	fnValue := reflect.ValueOf(fn.Handler)
	returnValues := fnValue.Call([]reflect.Value{argPtr.Elem()})

	resultType := "resolution"
	resultValue := returnValues[0].Interface()

	for _, v := range returnValues {
		// Check if ANY of the return values is an error
		if v.Type().AssignableTo(reflect.TypeOf((*error)(nil)).Elem()) && v.Interface() != nil {
			resultType = "rejection"
			// Serialize the error
			resultValue = v.Interface().(error).Error()
			break
		}

		// Check if ANY of the return values is an interrupt
		if v.CanInterface() {
			val := v.Interface()
			switch t := val.(type) {
			case Interrupt:
				resultType = "interrupt"
				resultValue = t
			case *Interrupt:
				if t != nil {
					resultType = "interrupt"
					resultValue = *t
				}
			}
		}
	}

	result := callResult{
		Result:     resultValue,
		ResultType: resultType,
		Meta: callResultMeta{
			FunctionExecutionTime: int64(time.Since(start).Milliseconds()),
		},
	}

	// Persist the job result
	if err := s.persistJobResult(msg.Id, result); err != nil {
		return fmt.Errorf("failed to persist job result: %v", err)
	}

	return nil
}

func (s *pollingAgent) persistJobResult(jobID string, result callResult) error {
	payloadJSON, err := json.Marshal(result)
	if err != nil {
		return fmt.Errorf("failed to marshal payload for persistJobResult: %v", err)
	}

	headers := map[string]string{
		"Authorization":          "Bearer " + s.inferable.apiSecret,
		"X-Machine-ID":           s.inferable.machineID,
		"X-Machine-SDK-Version":  Version,
		"X-Machine-SDK-Language": "go",
	}

	options := client.FetchDataOptions{
		Path:    fmt.Sprintf("/clusters/%s/jobs/%s/result", s.inferable.clusterID, jobID),
		Method:  "POST",
		Headers: headers,
		Body:    string(payloadJSON),
	}

	_, _, err, _ = s.inferable.fetchData(options)
	if err != nil {
		return fmt.Errorf("failed to persist job result: %v", err)
	}

	return nil
}

func (s *pollingAgent) getSchema() (map[string]interface{}, error) {
	if len(s.Tools) == 0 {
		return nil, fmt.Errorf("no tools registered")
	}

	schema := make(map[string]interface{})

	for _, fn := range s.Tools {
		schema[fn.Name] = map[string]interface{}{
			"input": fn.schema,
			"name":  fn.Name,
		}
	}

	return schema, nil
}

func (s *pollingAgent) isPolling() bool {
	return s.cancel != nil
}
