package config

import (
	"os"
	"path/filepath"
	"testing"

	"gopkg.in/yaml.v3"
)

func TestDefaultConfig(t *testing.T) {
	cfg := DefaultConfig()

	if cfg.Provider != "anthropic" {
		t.Errorf("expected default provider %q, got %q", "anthropic", cfg.Provider)
	}
	if cfg.ScoreThreshold != 95.0 {
		t.Errorf("expected default score threshold 95.0, got %f", cfg.ScoreThreshold)
	}
	if cfg.MaxRetries != 3 {
		t.Errorf("expected default max retries 3, got %d", cfg.MaxRetries)
	}
	if cfg.Timeout != 300 {
		t.Errorf("expected default timeout 300, got %d", cfg.Timeout)
	}
	if cfg.EngineAddr != "http://127.0.0.1:4041" {
		t.Errorf("expected default engine addr %q, got %q", "http://127.0.0.1:4041", cfg.EngineAddr)
	}
}

func TestLoad_NoFile(t *testing.T) {
	cfg, err := Load()
	if err != nil {
		t.Fatalf("Load() returned unexpected error: %v", err)
	}
	if cfg == nil {
		t.Fatal("Load() returned nil config")
	}
	if cfg.Provider == "" {
		t.Error("expected a non-empty default provider from Load()")
	}
}

func TestSaveAndLoad_Roundtrip(t *testing.T) {
	tmpDir := t.TempDir()
	configPath := filepath.Join(tmpDir, "config.yaml")

	original := DefaultConfig()
	original.path = configPath
	original.Provider = "openai"
	original.ScoreThreshold = 88.5
	original.MaxRetries = 5
	original.Timeout = 600
	original.EngineAddr = "http://localhost:9090"

	if err := original.Save(); err != nil {
		t.Fatalf("Save() returned error: %v", err)
	}

	if _, err := os.Stat(configPath); os.IsNotExist(err) {
		t.Fatal("expected config file to exist after Save()")
	}

	loaded := DefaultConfig()
	loaded.path = configPath
	data, err := os.ReadFile(configPath)
	if err != nil {
		t.Fatalf("failed to read saved config: %v", err)
	}

	if err := yaml.Unmarshal(data, loaded); err != nil {
		t.Fatalf("failed to unmarshal saved config: %v", err)
	}

	if loaded.Provider != "openai" {
		t.Errorf("provider: want %q, got %q", "openai", loaded.Provider)
	}
	if loaded.ScoreThreshold != 88.5 {
		t.Errorf("score threshold: want 88.5, got %f", loaded.ScoreThreshold)
	}
	if loaded.MaxRetries != 5 {
		t.Errorf("max retries: want 5, got %d", loaded.MaxRetries)
	}
	if loaded.Timeout != 600 {
		t.Errorf("timeout: want 600, got %d", loaded.Timeout)
	}
	if loaded.EngineAddr != "http://localhost:9090" {
		t.Errorf("engine addr: want %q, got %q", "http://localhost:9090", loaded.EngineAddr)
	}
}

func TestSet_Provider(t *testing.T) {
	cfg := DefaultConfig()
	if err := cfg.Set("provider", []string{"openai"}); err != nil {
		t.Fatalf("Set provider: %v", err)
	}
	if cfg.Provider != "openai" {
		t.Errorf("expected provider %q, got %q", "openai", cfg.Provider)
	}
}

func TestSet_ScoreThreshold(t *testing.T) {
	cfg := DefaultConfig()
	if err := cfg.Set("score-threshold", []string{"90"}); err != nil {
		t.Fatalf("Set score-threshold: %v", err)
	}
	if cfg.ScoreThreshold != 90.0 {
		t.Errorf("expected score threshold 90.0, got %f", cfg.ScoreThreshold)
	}
}

func TestSet_ScoreThreshold_Invalid(t *testing.T) {
	cfg := DefaultConfig()
	err := cfg.Set("score-threshold", []string{"not-a-number"})
	if err == nil {
		t.Fatal("expected error for invalid score-threshold")
	}
}

func TestSet_ScoreThreshold_PartialNumber(t *testing.T) {
	cfg := DefaultConfig()
	err := cfg.Set("score-threshold", []string{"90abc"})
	if err == nil {
		t.Fatal("expected error for partial numeric value like 90abc")
	}
}

func TestSet_MaxRetries(t *testing.T) {
	cfg := DefaultConfig()
	if err := cfg.Set("max-retries", []string{"5"}); err != nil {
		t.Fatalf("Set max-retries: %v", err)
	}
	if cfg.MaxRetries != 5 {
		t.Errorf("expected max retries 5, got %d", cfg.MaxRetries)
	}
}

func TestSet_Timeout(t *testing.T) {
	cfg := DefaultConfig()
	if err := cfg.Set("timeout", []string{"600"}); err != nil {
		t.Fatalf("Set timeout: %v", err)
	}
	if cfg.Timeout != 600 {
		t.Errorf("expected timeout 600, got %d", cfg.Timeout)
	}
}

func TestSet_EngineAddr(t *testing.T) {
	cfg := DefaultConfig()
	if err := cfg.Set("engine-addr", []string{"http://remote:4041"}); err != nil {
		t.Fatalf("Set engine-addr: %v", err)
	}
	if cfg.EngineAddr != "http://remote:4041" {
		t.Errorf("expected engine addr %q, got %q", "http://remote:4041", cfg.EngineAddr)
	}
}

func TestSet_InvalidKey(t *testing.T) {
	cfg := DefaultConfig()
	err := cfg.Set("nonexistent-key", []string{"value"})
	if err == nil {
		t.Fatal("expected error for unknown config key")
	}
}

func TestSet_APIKey_Rejected(t *testing.T) {
	cfg := DefaultConfig()
	err := cfg.Set("api-key", []string{"sk-ant-123"})
	if err == nil {
		t.Fatal("expected error — api-key should not be stored in config")
	}
}

func TestSet_NoValue(t *testing.T) {
	cfg := DefaultConfig()
	err := cfg.Set("provider", []string{})
	if err == nil {
		t.Fatal("expected error when no value is provided")
	}
}

func TestSearchAPIKey_FromEnv(t *testing.T) {
	cfg := DefaultConfig()
	t.Setenv("TAVILY_API_KEY", "tvly-from-env")

	got := cfg.SearchAPIKey()
	if got != "tvly-from-env" {
		t.Errorf("expected %q, got %q", "tvly-from-env", got)
	}
}

func TestSearchAPIKey_NotSet(t *testing.T) {
	cfg := DefaultConfig()
	t.Setenv("TAVILY_API_KEY", "")

	got := cfg.SearchAPIKey()
	if got != "" {
		t.Errorf("expected empty, got %q", got)
	}
}

func TestResolveAPIKey_FromEnv(t *testing.T) {
	t.Setenv("ANTHROPIC_API_KEY", "sk-ant-test")
	got := ResolveAPIKey("anthropic")
	if got != "sk-ant-test" {
		t.Errorf("expected %q, got %q", "sk-ant-test", got)
	}
}

func TestResolveAPIKey_NotSet(t *testing.T) {
	t.Setenv("ANTHROPIC_API_KEY", "")
	got := ResolveAPIKey("anthropic")
	if got != "" {
		t.Errorf("expected empty, got %q", got)
	}
}

func TestResolveAPIKey_UnknownProvider(t *testing.T) {
	got := ResolveAPIKey("unknown-provider")
	if got != "" {
		t.Errorf("expected empty for unknown provider, got %q", got)
	}
}
