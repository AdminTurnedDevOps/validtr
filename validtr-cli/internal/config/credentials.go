package config

import "os"

// ProviderEnvVars maps provider names to their API key environment variables.
var ProviderEnvVars = map[string]string{
	"anthropic": "ANTHROPIC_API_KEY",
	"openai":    "OPENAI_API_KEY",
	"gemini":    "GOOGLE_API_KEY",
}

// ResolveAPIKey resolves the API key for a provider from environment variables.
func ResolveAPIKey(provider string) string {
	if envVar, ok := ProviderEnvVars[provider]; ok {
		return os.Getenv(envVar)
	}
	return ""
}
