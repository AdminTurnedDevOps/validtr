package cmd

import (
	"fmt"

	"validtr-cli/internal/config"
	"validtr-cli/internal/engine"

	"github.com/spf13/cobra"
)

func newEngineClient() (*engine.Client, error) {
	cfg, err := config.Load()
	if err != nil {
		return nil, err
	}
	return engine.NewClient(cfg.EngineAddr)
}

var mcpCmd = &cobra.Command{
	Use:   "mcp",
	Short: "MCP server discovery and management",
}

var mcpListCmd = &cobra.Command{
	Use:   "list",
	Short: "List known MCP servers",
	RunE: func(cmd *cobra.Command, args []string) error {
		client, err := newEngineClient()
		if err != nil {
			return err
		}
		defer client.Close()

		servers, err := client.ListMCPServers()
		if err != nil {
			return err
		}

		fmt.Printf("%-20s %-12s %s\n", "NAME", "TRANSPORT", "DESCRIPTION")
		fmt.Println("────────────────────────────────────────────────────────────")
		for _, s := range servers {
			fmt.Printf("%-20s %-12s %s\n", s.Name, s.Transport, s.Description)
		}

		return nil
	},
}

var mcpSearchCmd = &cobra.Command{
	Use:   "search [query]",
	Short: "Search for MCP servers",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		client, err := newEngineClient()
		if err != nil {
			return err
		}
		defer client.Close()

		servers, err := client.SearchMCPServers(args[0])
		if err != nil {
			return err
		}

		if len(servers) == 0 {
			fmt.Println("No servers found.")
			return nil
		}

		for _, s := range servers {
			fmt.Printf("%s (%s)\n  %s\n  Install: %s\n\n", s.Name, s.Transport, s.Description, s.Install)
		}

		return nil
	},
}

var mcpInfoCmd = &cobra.Command{
	Use:   "info [server-name]",
	Short: "Show details about an MCP server",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		client, err := newEngineClient()
		if err != nil {
			return err
		}
		defer client.Close()

		info, err := client.GetMCPServerInfo(args[0])
		if err != nil {
			return err
		}

		fmt.Printf("Name:        %s\n", info.Name)
		fmt.Printf("Transport:   %s\n", info.Transport)
		fmt.Printf("Description: %s\n", info.Description)
		fmt.Printf("Install:     %s\n", info.Install)
		fmt.Printf("Credentials: %s\n", info.Credentials)

		return nil
	},
}

func init() {
	rootCmd.AddCommand(mcpCmd)
	mcpCmd.AddCommand(mcpListCmd)
	mcpCmd.AddCommand(mcpSearchCmd)
	mcpCmd.AddCommand(mcpInfoCmd)
}
