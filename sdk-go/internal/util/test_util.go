package util

import (
	"github.com/joho/godotenv"
	"os"
)

func GetTestVars() (string, string, string, string) {
	if os.Getenv("INFERABLE_MACHINE_SECRET") == "" {
		err := godotenv.Load("./.env")
		if err != nil {
			panic(err)
		}
	}
	machineSecret := os.Getenv("INFERABLE_MACHINE_SECRET")
	consumeSecret := os.Getenv("INFERABLE_CONSUME_SECRET")
	clusterId := os.Getenv("INFERABLE_CLUSTER_ID")
	apiEndpoint := os.Getenv("INFERABLE_API_ENDPOINT")

	if apiEndpoint == "" {
    panic("INFERABLE_API_ENDPOINT is not available")
	}
	if machineSecret == "" {
		panic("INFERABLE_MACHINE_SECRET is not available")
	}
	if consumeSecret == "" {
		panic("INFERABLE_CONSUME_SECRET is not available")
	}
	if clusterId == "" {
		panic("INFERABLE_CLUSTER_ID is not set in .env")
	}

	return machineSecret, consumeSecret, clusterId, apiEndpoint
}
