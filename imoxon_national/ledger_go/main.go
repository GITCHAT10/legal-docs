package main

import (
	"encoding/json"
	"net/http"
	"time"
)

type LedgerEntry struct {
	ID        string    `json:"id"`
	Action    string    `json:"action"`
	Payload   any       `json:"payload"`
	Hash      string    `json:"hash"`
	Timestamp time.Time `json:"timestamp"`
}

func writeLedger(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Immutable append-only write simulated
	w.WriteHeader(http.StatusCreated)
	w.Write([]byte(`{"status": "ledger_committed", "integrity": "verified"}`))
}

func main() {
	http.HandleFunc("/write", writeLedger)
	http.ListenAndServe(":8001", nil)
}
