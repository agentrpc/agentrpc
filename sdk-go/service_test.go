package agentrpc

import (
	"encoding/json"
	"fmt"
	"testing"

	"bytes"
	"net/http"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"github.com/agentrpc/agentrpc/sdk-go/internal/util"
)

func TestRegisterFunc(t *testing.T) {
	_, _, _, apiEndpoint := util.GetTestVars()

	i, _ := New(AgentRPCOptions{
		APIEndpoint: apiEndpoint,
		APISecret:   "sk_secret_123",
	})
	type TestInput struct {
		A int `json:"a"`
		B int `json:"b"`
	}

	testFunc := func(input TestInput) int { return input.A + input.B }
	err := i.Register(Tool{
		Handler:     testFunc,
		Name:        "TestFunc",
		Description: "Test function",
	})
	require.NoError(t, err)

	// Try to register the same function again
	err = i.Register(Tool{
		Handler: testFunc,
		Name:    "TestFunc",
	})
	assert.Error(t, err)

	// Try to register a function with invalid input
	invalidFunc := func(a, b int) int { return a + b }
	err = i.Register(Tool{
		Handler: invalidFunc,
		Name:    "InvalidFunc",
	})
	assert.Error(t, err)
}

func TestRegisterFuncWithInlineStruct(t *testing.T) {
	_, _, _, apiEndpoint := util.GetTestVars()

	i, _ := New(AgentRPCOptions{
		APIEndpoint: apiEndpoint,
		APISecret:   "sk_secret_123",
	})
	testFunc := func(input struct {
		A int `json:"a"`
		B int `json:"b"`
	}) int {
		return input.A + input.B
	}
	err := i.Register(Tool{
		Handler:     testFunc,
		Name:        "TestFunc",
		Description: "Test function",
	})
	require.NoError(t, err)

	// Try to register the same function again
	err = i.Register(Tool{
		Handler: testFunc,
		Name:    "TestFunc",
	})
	assert.Error(t, err)

	// Try to register a function with invalid input
	invalidFunc := func(a, b int) int { return a + b }
	err = i.Register(Tool{
		Handler: invalidFunc,
		Name:    "InvalidFunc",
	})
	assert.Error(t, err)
}

func TestRegistrationAndConfig(t *testing.T) {
	machineSecret, _, _, apiEndpoint := util.GetTestVars()

	machineID := "random-machine-id"

	// Create a new Inferable instance
	i, err := New(AgentRPCOptions{
		APIEndpoint: apiEndpoint,
		APISecret:   machineSecret,
		MachineID:   machineID,
	})
	require.NoError(t, err)

	// Register a service
	require.NoError(t, err)

	// Register a test function
	type TestInput struct {
		A int `json:"a"`
		B int `json:"b"`
		C []struct {
			D int           `json:"d"`
			E string        `json:"e"`
			F []interface{} `json:"f"`
		} `json:"c"`
	}

	testFunc := func(input TestInput) int { return input.A + input.B }

	err = i.Register(Tool{
		Handler:     testFunc,
		Name:        "TestFunc",
		Description: "Test function",
	})

	require.NoError(t, err)

	// Call Listen to trigger registration
	err = i.Listen()
	require.NoError(t, err)
}

func TestServiceStartAndReceiveMessage(t *testing.T) {
	machineSecret, consumeSecret, clusterId, apiEndpoint := util.GetTestVars()

	machineID := "random-machine-id"

	// Create a new Inferable instance
	i, err := New(AgentRPCOptions{
		APIEndpoint: apiEndpoint,
		APISecret:   machineSecret,
		MachineID:   machineID,
	})
	require.NoError(t, err)

	// Register a test function
	type TestInput struct {
		Message string `json:"message"`
	}

	testFunc := func(input TestInput) string { return "Received: " + input.Message }

	err = i.Register(Tool{
		Handler:     testFunc,
		Name:        "TestFunc",
		Description: "Test function",
	})
	require.NoError(t, err)

	// Start the service
	err = i.Listen()
	require.NoError(t, err)

	// Ensure the service is stopped at the end of the test
	defer i.Unlisten()

	// Use executeJobSync to invoke the function
	testMessage := "Hello, SQS!"
	executeCallUrl := fmt.Sprintf("%s/clusters/%s/jobs?waitTime=20", apiEndpoint, clusterId)
	payload := map[string]interface{}{
		"service":  "v2",
		"function": "TestFunc",
		"input": map[string]string{
			"message": testMessage,
		},
	}

	jsonPayload, err := json.Marshal(payload)
	require.NoError(t, err)

	req, err := http.NewRequest("POST", executeCallUrl, bytes.NewBuffer(jsonPayload))
	require.NoError(t, err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+consumeSecret)

	client := &http.Client{}
	resp, err := client.Do(req)
	require.NoError(t, err)
	defer resp.Body.Close()

	require.Equal(t, http.StatusOK, resp.StatusCode)

	var result map[string]interface{}
	err = json.NewDecoder(resp.Body).Decode(&result)
	require.NoError(t, err)

	// Print the response body for debugging
	resultBody, err := json.MarshalIndent(result, "", "    ")
	require.NoError(t, err)
	t.Logf("Response body: %s", string(resultBody))
	// Check if the job was executed successfully
	require.Equal(t, "resolution", result["resultType"])
	require.Equal(t, "done", result["status"])
	require.Equal(t, "Received: Hello, SQS!", result["result"])
}

func TestServiceStartAndReceiveFailingMessage(t *testing.T) {
	machineSecret, consumeSecret, clusterId, apiEndpoint := util.GetTestVars()

	machineID := "random-machine-id"

	// Create a new Inferable instance
	i, err := New(AgentRPCOptions{
		APIEndpoint: apiEndpoint,
		APISecret:   machineSecret,
		MachineID:   machineID,
	})
	require.NoError(t, err)

	// Register a test function
	type TestInput struct {
		Message string `json:"message"`
	}

	// Purposfuly failing function
	testFailingFunc := func(input TestInput) (*string, error) { return nil, fmt.Errorf("test error") }

	err = i.Register(Tool{
		Handler:     testFailingFunc,
		Name:        "FailingFunc",
		Description: "Test function",
	})
	require.NoError(t, err)

	// Start the service
	err = i.Listen()
	require.NoError(t, err)

	// Ensure the service is stopped at the end of the test
	defer i.Unlisten()

	// Use executeJobSync to invoke the function
	testMessage := "Hello, SQS!"
	executeCallUrl := fmt.Sprintf("%s/clusters/%s/jobs?waitTime=20", apiEndpoint, clusterId)
	payload := map[string]interface{}{
		"service":  "TestServiceFail",
		"function": "FailingFunc",
		"input": map[string]string{
			"message": testMessage,
		},
	}

	jsonPayload, err := json.Marshal(payload)
	require.NoError(t, err)

	req, err := http.NewRequest("POST", executeCallUrl, bytes.NewBuffer(jsonPayload))
	require.NoError(t, err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+consumeSecret)

	client := &http.Client{}
	resp, err := client.Do(req)
	require.NoError(t, err)
	defer resp.Body.Close()

	require.Equal(t, http.StatusOK, resp.StatusCode)

	var result map[string]interface{}
	err = json.NewDecoder(resp.Body).Decode(&result)
	require.NoError(t, err)

	// Check if the job was executed successfully
	require.Equal(t, "rejection", result["resultType"])
	require.Equal(t, "done", result["status"])
	require.Equal(t, "test error", result["result"])
}
