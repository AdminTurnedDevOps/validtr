package engine

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"time"
)

// Client communicates with the Python engine via HTTP (gRPC in future).
type Client struct {
	httpClient *http.Client
	baseURL    string
}

// RunResult holds the result of a task run.
type RunResult struct {
	RunID         string  `json:"run_id"`
	Score         float64 `json:"score"`
	Passed        bool    `json:"passed"`
	TotalAttempts int     `json:"total_attempts"`
	ArtifactCount int     `json:"artifact_count"`
	Artifacts     map[string]string `json:"artifacts"`
}

// MCPServer holds MCP server information.
type MCPServer struct {
	Name        string `json:"name"`
	Transport   string `json:"transport"`
	Description string `json:"description"`
	Install     string `json:"install"`
	Credentials string `json:"credentials"`
}

// NewClient creates a new engine client. Uses the provided address or defaults to localhost:4041.
func NewClient(addr string) (*Client, error) {
	if addr == "" {
		addr = "http://127.0.0.1:4041"
	}
	return &Client{
		httpClient: &http.Client{Timeout: 10 * time.Minute},
		baseURL:    addr,
	}, nil
}

// Close cleans up the client.
func (c *Client) Close() {
	// Nothing to clean up for HTTP client
}

// RunTask sends a task to the engine and returns the result.
func (c *Client) RunTask(task, provider, model, apiKey, searchAPIKey string, maxRetries int, threshold float64, timeout int) (*RunResult, error) {
	payload := map[string]interface{}{
		"task":            task,
		"provider":        provider,
		"model":           model,
		"api_key":         apiKey,
		"search_api_key":  searchAPIKey,
		"max_retries":     maxRetries,
		"score_threshold": threshold,
		"timeout":         timeout,
	}

	body, err := json.Marshal(payload)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	resp, err := c.httpClient.Post(c.baseURL+"/api/run", "application/json", bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("engine request failed: %w", err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("engine returned %d: %s", resp.StatusCode, string(respBody))
	}

	var result RunResult
	if err := json.Unmarshal(respBody, &result); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	return &result, nil
}

// DryRun requests a stack recommendation without execution.
func (c *Client) DryRun(task, provider, apiKey, searchAPIKey string) (string, error) {
	payload := map[string]interface{}{
		"task":           task,
		"provider":       provider,
		"api_key":        apiKey,
		"search_api_key": searchAPIKey,
		"dry_run":        true,
	}

	body, err := json.Marshal(payload)
	if err != nil {
		return "", err
	}

	resp, err := c.httpClient.Post(c.baseURL+"/api/run", "application/json", bytes.NewReader(body))
	if err != nil {
		return "", fmt.Errorf("engine request failed: %w", err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("engine returned %d: %s", resp.StatusCode, string(respBody))
	}

	return string(respBody), nil
}

// ListMCPServers lists all known MCP servers.
func (c *Client) ListMCPServers() ([]MCPServer, error) {
	resp, err := c.httpClient.Get(c.baseURL + "/api/mcp/servers")
	if err != nil {
		return nil, fmt.Errorf("engine request failed: %w", err)
	}
	defer resp.Body.Close()

	var servers []MCPServer
	if err := json.NewDecoder(resp.Body).Decode(&servers); err != nil {
		return nil, err
	}

	return servers, nil
}

// SearchMCPServers searches for MCP servers.
func (c *Client) SearchMCPServers(query string) ([]MCPServer, error) {
	resp, err := c.httpClient.Get(c.baseURL + "/api/mcp/search?q=" + url.QueryEscape(query))
	if err != nil {
		return nil, fmt.Errorf("engine request failed: %w", err)
	}
	defer resp.Body.Close()

	var servers []MCPServer
	if err := json.NewDecoder(resp.Body).Decode(&servers); err != nil {
		return nil, err
	}

	return servers, nil
}

// GetMCPServerInfo returns details about a specific MCP server.
func (c *Client) GetMCPServerInfo(name string) (*MCPServer, error) {
	resp, err := c.httpClient.Get(c.baseURL + "/api/mcp/servers/" + name)
	if err != nil {
		return nil, fmt.Errorf("engine request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return nil, fmt.Errorf("MCP server %q not found", name)
	}
	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("engine returned %d: %s", resp.StatusCode, string(body))
	}

	var server MCPServer
	if err := json.NewDecoder(resp.Body).Decode(&server); err != nil {
		return nil, err
	}

	return &server, nil
}
