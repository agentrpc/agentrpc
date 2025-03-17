package agentrpc

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNew(t *testing.T) {
	i, err := New(AgentRPCOptions{
		APIEndpoint: DefaultAPIEndpoint,
		APISecret:   "sk_secret_123",
	})
	require.NoError(t, err)
	assert.Equal(t, DefaultAPIEndpoint, i.apiEndpoint)
	assert.Equal(t, "sk_secret_123", i.apiSecret)
	assert.Equal(t, "secret", i.clusterID)
	assert.NotEmpty(t, i.machineID)
}

func TestCallFunc(t *testing.T) {
	i, _ := New(AgentRPCOptions{
		APIEndpoint: DefaultAPIEndpoint,
		APISecret:   "sk_secret_123",
	})

	type TestInput struct {
		A int `json:"a"`
		B int `json:"b"`
	}

	testFunc := func(input TestInput) int { return input.A + input.B }
	err := i.Register(Tool{
		Handler: testFunc,
		Name:    "TestCallFunc",
	})

	assert.NoError(t, err)

	result, err := i.callFunc("TestCallFunc", TestInput{A: 2, B: 3})
	require.NoError(t, err)
	assert.Equal(t, 5, result[0].Interface())

	// Test calling non-existent function
	_, err = i.callFunc("NonExistentFunc")
	assert.Error(t, err)
}

func TestServerOk(t *testing.T) {
	// Create a test server
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/live" {
			w.WriteHeader(http.StatusOK)
			w.Write([]byte(`{"status": "ok"}`))
		}
	}))
	defer server.Close()

	i, _ := New(AgentRPCOptions{
		APIEndpoint: server.URL,
		APISecret:   "sk_secret_123",
	})
	err := i.serverOk()
	assert.NoError(t, err)
}

func TestGetMachineID(t *testing.T) {
	i, _ := New(AgentRPCOptions{
		APIEndpoint: DefaultAPIEndpoint,
		APISecret:   "sk_secret_123",
	})
	machineID := i.machineID
	assert.NotEmpty(t, machineID)

	// Check if the machine ID is persistent
	i2, _ := New(AgentRPCOptions{
		APIEndpoint: DefaultAPIEndpoint,
		APISecret:   "sk_secret_123",
	})
	assert.Equal(t, machineID, i2.machineID)
}
