package schema

// YtDlpOptions represents the configuration for a yt-dlp download task.
type YtDlpOptions struct {
	URL            string            `json:"url"`
	OutputDir      string            `json:"output_dir"`
	OutputTemplate string            `json:"output_template"`
	UseAria2c      bool              `json:"use_aria2c"`
	CookieFile     string            `json:"cookie_file,omitempty"`
	ExtraArgs      map[string]string `json:"extra_args,omitempty"`
}

// YtDlpResult represents the outcome of a download task.
type YtDlpResult struct {
	Status   string `json:"status"` // "completed" or "failed"
	FilePath string `json:"file_path,omitempty"`
	Error    string `json:"error,omitempty"`
}
