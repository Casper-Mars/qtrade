# Makefile for data-collector service

.PHONY: help build test lint clean run

# Default target
help:
	@echo "Available targets:"
	@echo "  build    - Build the application"
	@echo "  test     - Run tests"
	@echo "  lint     - Run linter checks"
	@echo "  clean    - Clean build artifacts"
	@echo "  run      - Run the application"
	@echo "  deps     - Download dependencies"

# Build the application
build:
	@echo "Building data-collector..."
	go build -o bin/data-collector cmd/main.go

# Run tests
test:
	@echo "Running tests..."
	go test -v ./...

# Run tests with coverage
test-coverage:
	@echo "Running tests with coverage..."
	go test -cover ./...
	go test -coverprofile=coverage.out ./...
	go tool cover -html=coverage.out -o coverage.html

# Run linter checks
lint:
	@echo "Running linter checks..."
	@if command -v golangci-lint >/dev/null 2>&1; then \
		golangci-lint run; \
	else \
		echo "golangci-lint not found, running basic checks..."; \
		go vet ./...; \
		go fmt ./...; \
	fi

# Clean build artifacts
clean:
	@echo "Cleaning..."
	rm -rf bin/
	rm -f coverage.out coverage.html

# Run the application
run:
	@echo "Running data-collector..."
	go run cmd/main.go

# Download dependencies
deps:
	@echo "Downloading dependencies..."
	go mod download
	go mod tidy

# Format code
fmt:
	@echo "Formatting code..."
	go fmt ./...

# Vet code
vet:
	@echo "Vetting code..."
	go vet ./...