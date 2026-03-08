package cmd

import (
	"fmt"

	"validtr-cli/internal/config"

	"github.com/spf13/cobra"
)

var configCmd = &cobra.Command{
	Use:   "config",
	Short: "Manage validtr configuration",
}

var configSetCmd = &cobra.Command{
	Use:   "set [key] [value]",
	Short: "Set a configuration value",
	Long: `Set a configuration value. Examples:
  validtr config set provider anthropic
  validtr config set score-threshold 90
  validtr config set max-retries 5
  validtr config set timeout 600
  validtr config set engine-addr http://127.0.0.1:4041

API keys are set via environment variables, not config:
  export ANTHROPIC_API_KEY="sk-ant-..."
  export OPENAI_API_KEY="sk-..."
  export GOOGLE_API_KEY="..."
  export TAVILY_API_KEY="tvly-..."`,
	Args: cobra.ExactArgs(2),
	RunE: func(cmd *cobra.Command, args []string) error {
		key, value := args[0], args[1]

		cfg, err := config.Load()
		if err != nil {
			return fmt.Errorf("failed to load config: %w", err)
		}

		if err := cfg.Set(key, []string{value}); err != nil {
			return fmt.Errorf("failed to set %s: %w", key, err)
		}

		if err := cfg.Save(); err != nil {
			return fmt.Errorf("failed to save config: %w", err)
		}

		fmt.Printf("Set %s = %s\n", key, value)
		return nil
	},
}

var configShowCmd = &cobra.Command{
	Use:   "show",
	Short: "Show current configuration",
	RunE: func(cmd *cobra.Command, args []string) error {
		cfg, err := config.Load()
		if err != nil {
			return fmt.Errorf("failed to load config: %w", err)
		}

		fmt.Printf("Provider:         %s\n", cfg.Provider)
		fmt.Printf("Score Threshold:  %.0f\n", cfg.ScoreThreshold)
		fmt.Printf("Max Retries:      %d\n", cfg.MaxRetries)
		fmt.Printf("Timeout:          %ds\n", cfg.Timeout)
		fmt.Printf("Engine Address:   %s\n", cfg.EngineAddr)

		fmt.Println("\nAPI keys (from environment):")
		for provider, envVar := range config.ProviderEnvVars {
			if config.ResolveAPIKey(provider) != "" {
				fmt.Printf("  %s (%s): set\n", provider, envVar)
			} else {
				fmt.Printf("  %s (%s): not set\n", provider, envVar)
			}
		}

		return nil
	},
}

func init() {
	rootCmd.AddCommand(configCmd)
	configCmd.AddCommand(configSetCmd)
	configCmd.AddCommand(configShowCmd)
}
