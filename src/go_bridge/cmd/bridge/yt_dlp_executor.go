package main

import (
	"fmt"
	"os"
	"os/exec"
	"go_bridge/internal/schema"
)

// runYtDlp executes the yt-dlp binary with the provided options.
func runYtDlp(opts schema.YtDlpOptions) (schema.YtDlpResult, error) {
	args := []string{
		opts.URL,
		"-o", fmt.Sprintf("%s/%s", opts.OutputDir, opts.OutputTemplate),
		"--format", "bestvideo+bestaudio/best",
		"--merge-output-format", "mp4",
		"--quiet",
	}

	if opts.UseAria2c {
		args = append(args, "--external-downloader", "aria2c", "--external-downloader-args", "-x 16 -k 1M")
	}

	if opts.CookieFile != "" {
		args = append(args, "--cookies", opts.CookieFile)
	}

	for k, v := range opts.ExtraArgs {
		args = append(args, "--"+k, v)
	}

	cmd := exec.Command("yt-dlp", args...)
	
	// DEBUG: Log the command and arguments
	fmt.Fprintf(os.Stderr, "DEBUG: Executing: %s %v\n", cmd.Path, cmd.Args)

	// Execute the command
	output, err := cmd.CombinedOutput()
	if err != nil {
		return schema.YtDlpResult{
			Status: "failed",
			Error:  fmt.Sprintf("Download failed: %v, Output: %s", err, string(output)),
		}, err
	}

	return schema.YtDlpResult{
		Status:   "completed",
		FilePath: "File saved (path resolution logic needs implementation)", // Simplified for now
	}, nil
}
