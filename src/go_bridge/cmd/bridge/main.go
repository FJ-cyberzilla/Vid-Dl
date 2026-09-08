package main

import (
	"encoding/json"
	"fmt"
	"os"
	"go_bridge/internal/schema"
)

// Simplified validation logic ported from Python
func isYouTubeURL(url string) bool {
    // Basic check for now; real implementation would use urlparse logic
    return len(url) > 0 // Placeholder
}

func main() {
	var req schema.AdapterRequest
	if err := json.NewDecoder(os.Stdin).Decode(&req); err != nil {
		fmt.Fprintf(os.Stderr, "Error decoding request: %v\n", err)
		os.Exit(1)
	}

	var res schema.AdapterResponse
	switch req.Action {
	case "ping":
		res = schema.AdapterResponse{Status: "ok", Result: "pong"}
	case "validate_url":
        url := req.Params["url"]
        if isYouTubeURL(url) {
            res = schema.AdapterResponse{Status: "ok", Result: "true"}
        } else {
            res = schema.AdapterResponse{Status: "ok", Result: "false"}
        }
    case "download_yt_dlp":
        var opts schema.YtDlpOptions
        // Need to parse params into opts
        data, _ := json.Marshal(req.Params)
        json.Unmarshal(data, &opts)
        
        result, err := runYtDlp(opts)
        if err != nil {
            res = schema.AdapterResponse{Status: "error", Error: result.Error}
        } else {
            res = schema.AdapterResponse{Status: "ok", Result: result}
        }
	default:
		res = schema.AdapterResponse{Status: "error", Error: "unknown action"}
	}

	json.NewEncoder(os.Stdout).Encode(res)
}
