package main

import (
	"os"
	"os/signal"
	"syscall"

	"github.com/agentrpc/agentrpc/sdk-go"
)

func main() {
	client, _ := agentrpc.New(agentrpc.Options{
		APISecret: "",
	})

	client.Register(agentrpc.Tool{
		Handler:        func(input struct{ Input string }) string {
			return "Hello " + input.Input
		},
		Name:        "SayHello",
		Description: "A simple greeting function",
	})

	go func() {
		client.Listen()
	}()

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)

	<-sigChan
	defer client.Unlisten()
}

