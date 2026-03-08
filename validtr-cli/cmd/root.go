package cmd

import (
	"fmt"
	"os"

	"validtr-cli/internal/config"

	"github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
	Use:   "validtr",
	Short: "validtr — agentic stack validation tool",
	Long: `validtr takes a natural language task description, recommends the optimal
agentic stack (LLM, agent framework, MCP servers, agent skills), provisions
that stack in Docker containers, executes the task, generates tests, and
scores the result.`,
	PersistentPreRunE: func(cmd *cobra.Command, args []string) error {
		configPath, err := cmd.Flags().GetString("config")
		if err != nil {
			return err
		}
		if configPath != "" {
			config.SetPath(configPath)
		}
		return nil
	},
}

func Execute() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func init() {
	rootCmd.PersistentFlags().StringP("config", "c", "", "config file (default is ~/.validtr/config.yaml)")
}
