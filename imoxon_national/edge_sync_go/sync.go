package main

import (
	"fmt"
	"time"
)

var localQueue []map[string]interface{}

func sendToCloud(tx map[string]interface{}) {
	fmt.Printf("[SYNC] Sending transaction %v to core...\n", tx["id"])
}

func syncToCloud() {
	for _, tx := range localQueue {
		sendToCloud(tx)
	}
	localQueue = []map[string]interface{}{}
}

func main() {
	fmt.Println("iMOXON Edge Sync Service: ACTIVE")
	// Background sync ticker
	ticker := time.NewTicker(10 * time.Second)
	for range ticker.C {
		if len(localQueue) > 0 {
			syncToCloud()
		}
	}
}
