.PHONY: test lint format build clean

test:
	go test -v ./...

lint:
	go fmt ./...

format:
	go fmt ./...
	go mod tidy

build:
	go build ./...

clean:
	go clean
	rm -rf bin/
	find . -type f -name '*.test' -delete
	find . -type f -name '*.out' -delete
