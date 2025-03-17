package main

import (
	"os"
	"os/signal"
	"syscall"

	"github.com/agentrpc/agentrpc/sdk-go"
)

func main() {
	client, _ := agentrpc.New(agentrpc.Options{
		APISecret: os.Getenv("AGENTRPC_API_SECRET"),
	})

	client.Register(agentrpc.Tool{
		Name:        "getWeather",
		Description: "Return weather information at a given location",
		Handler: func(input struct{ location string }) string {
			return "probably raining"
		},
	})

	go func() {
		client.Listen()
	}()

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)

	<-sigChan
	defer client.Unlisten()
}
