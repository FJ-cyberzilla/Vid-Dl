package schema

// AdapterRequest defines the contract for requests sent from Python to Go.
type AdapterRequest struct {
	Action string            `json:"action"`
	Params map[string]string `json:"params"`
}

// AdapterResponse defines the contract for responses sent from Go back to Python.
type AdapterResponse struct {
	Status string `json:"status"`
	Result any    `json:"result,omitempty"`
	Error  string `json:"error,omitempty"`
}
