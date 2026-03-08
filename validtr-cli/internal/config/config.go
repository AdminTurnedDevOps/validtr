package config

import (
	"fmt"
	"os"
	"path/filepath"
	"strconv"

	"gopkg.in/yaml.v3"
)

// Config holds the validtr configuration.
// API keys and credentials are NEVER stored here — they come from environment variables only.
type Config struct {
	Provider       string  `yaml:"provider"`
	ScoreThreshold float64 `yaml:"score_threshold"`
	MaxRetries     int     `yaml:"max_retries"`
	Timeout        int     `yaml:"timeout"`
	EngineAddr     string  `yaml:"engine_addr"`

	path string
}

var configPathOverride string

// SetPath overrides the config file path used by Load and Save.
func SetPath(path string) {
	configPathOverride = path
}

func resolveConfigPath() (string, error) {
	if configPathOverride != "" {
		return configPathOverride, nil
	}

	home, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}

	return filepath.Join(home, ".validtr", "config.yaml"), nil
}

// DefaultConfig returns a config with sensible defaults.
func DefaultConfig() *Config {
	return &Config{
		Provider:       "anthropic",
		ScoreThreshold: 95.0,
		MaxRetries:     3,
		Timeout:        300,
		EngineAddr:     "http://127.0.0.1:4041",
	}
}

// SearchAPIKey returns the search API key from the environment.
func (c *Config) SearchAPIKey() string {
	return os.Getenv("TAVILY_API_KEY")
}

// Load reads the config from ~/.validtr/config.yaml.
func Load() (*Config, error) {
	configPath, err := resolveConfigPath()
	if err != nil {
		return DefaultConfig(), nil
	}

	data, err := os.ReadFile(configPath)
	if err != nil {
		// No config file — return defaults
		cfg := DefaultConfig()
		cfg.path = configPath
		return cfg, nil
	}

	cfg := DefaultConfig()
	cfg.path = configPath
	if err := yaml.Unmarshal(data, cfg); err != nil {
		return nil, fmt.Errorf("failed to parse config: %w", err)
	}

	return cfg, nil
}

// Save writes the config to disk.
func (c *Config) Save() error {
	if c.path == "" {
		configPath, err := resolveConfigPath()
		if err != nil {
			return err
		}
		c.path = configPath
	}

	// Ensure directory exists
	dir := filepath.Dir(c.path)
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return fmt.Errorf("failed to create config directory: %w", err)
	}

	data, err := yaml.Marshal(c)
	if err != nil {
		return fmt.Errorf("failed to marshal config: %w", err)
	}

	return os.WriteFile(c.path, data, 0o644)
}

// Set sets a configuration key. valueArgs contains the remaining args after the key.
//
// Examples:
//
//	Set("provider", ["anthropic"])
//	Set("score-threshold", ["90"])
//	Set("max-retries", ["5"])
//	Set("timeout", ["600"])
//	Set("engine-addr", ["http://127.0.0.1:4041"])
func (c *Config) Set(key string, valueArgs []string) error {
	if len(valueArgs) == 0 {
		return fmt.Errorf("no value provided for key %q", key)
	}

	switch key {
	case "provider":
		c.Provider = valueArgs[0]
	case "engine-addr":
		c.EngineAddr = valueArgs[0]
	case "score-threshold":
		v, err := strconv.ParseFloat(valueArgs[0], 64)
		if err != nil {
			return fmt.Errorf("invalid score-threshold: %s", valueArgs[0])
		}
		c.ScoreThreshold = v
	case "max-retries":
		v, err := strconv.Atoi(valueArgs[0])
		if err != nil {
			return fmt.Errorf("invalid max-retries: %s", valueArgs[0])
		}
		c.MaxRetries = v
	case "timeout":
		v, err := strconv.Atoi(valueArgs[0])
		if err != nil {
			return fmt.Errorf("invalid timeout: %s", valueArgs[0])
		}
		c.Timeout = v
	default:
		return fmt.Errorf("unknown config key: %s (valid keys: provider, engine-addr, score-threshold, max-retries, timeout)", key)
	}
	return nil
}
