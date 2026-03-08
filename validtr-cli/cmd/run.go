package cmd

import (
	"fmt"
	"strings"

	"validtr-cli/internal/config"
	"validtr-cli/internal/engine"

	"github.com/spf13/cobra"
)

var (
	runProvider       string
	runCompare        string
	runDryRun         bool
	runModel          string
	runMaxRetries     int
	runScoreThreshold float64
	runTimeout        int
)

var runCmd = &cobra.Command{
	Use:   "run [task description]",
	Short: "Run a task and validate the agentic stack",
	Long: `Run a task with a single provider or compare across multiple providers.
The task is analyzed, a stack is recommended, containers are provisioned,
the task is executed, tests are generated, and results are scored.`,
	Args: cobra.MinimumNArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		task := strings.Join(args, " ")

		if runDryRun {
			return runDryRunMode(cmd, task)
		}

		if runCompare != "" {
			raw := strings.Split(runCompare, ",")
			providers := make([]string, 0, len(raw))
			for _, p := range raw {
				p = strings.TrimSpace(p)
				if p != "" {
					providers = append(providers, p)
				}
			}
			return runCompareMode(cmd, task, providers)
		}

		return runSingleMode(cmd, task)
	},
}

func init() {
	rootCmd.AddCommand(runCmd)

	runCmd.Flags().StringVar(&runProvider, "provider", "anthropic", "LLM provider (anthropic, openai, gemini)")
	runCmd.Flags().StringVar(&runCompare, "compare", "", "Compare across providers (comma-separated)")
	runCmd.Flags().BoolVar(&runDryRun, "dry-run", false, "Recommend a stack but don't execute")
	runCmd.Flags().StringVar(&runModel, "model", "", "Specific model to use")
	runCmd.Flags().IntVar(&runMaxRetries, "max-retries", 3, "Maximum retry attempts")
	runCmd.Flags().Float64Var(&runScoreThreshold, "score-threshold", 95.0, "Minimum passing score (0-100)")
	runCmd.Flags().IntVar(&runTimeout, "timeout", 300, "Execution timeout in seconds")
}

func loadRunConfig(cmd *cobra.Command) (*config.Config, error) {
	cfg, err := config.Load()
	if err != nil {
		return nil, fmt.Errorf("failed to load config: %w", err)
	}

	// Config values apply only when the CLI flag was NOT explicitly passed.
	if !cmd.Flags().Changed("provider") && cfg.Provider != "" {
		runProvider = cfg.Provider
	}
	if !cmd.Flags().Changed("max-retries") && cfg.MaxRetries > 0 {
		runMaxRetries = cfg.MaxRetries
	}
	if !cmd.Flags().Changed("score-threshold") && cfg.ScoreThreshold > 0 {
		runScoreThreshold = cfg.ScoreThreshold
	}
	if !cmd.Flags().Changed("timeout") && cfg.Timeout > 0 {
		runTimeout = cfg.Timeout
	}

	return cfg, nil
}

func runSingleMode(cmd *cobra.Command, task string) error {
	cfg, err := loadRunConfig(cmd)
	if err != nil {
		return err
	}

	apiKey := config.ResolveAPIKey(runProvider)
	if apiKey == "" {
		return fmt.Errorf("no API key found for provider %q — set %s environment variable",
			runProvider, config.ProviderEnvVars[runProvider])
	}

	client, err := engine.NewClient(cfg.EngineAddr)
	if err != nil {
		return fmt.Errorf("failed to connect to engine: %w", err)
	}
	defer client.Close()

	fmt.Println("╭──────────────────────────────────────────────────╮")
	fmt.Printf("│  validtr — Run                                   │\n")
	fmt.Printf("│  Task: %q\n", truncate(task, 40))
	fmt.Println("├──────────────────────────────────────────────────┤")

	searchKey := cfg.SearchAPIKey()
	result, err := client.RunTask(task, runProvider, runModel, apiKey, searchKey, runMaxRetries, runScoreThreshold, runTimeout)
	if err != nil {
		return fmt.Errorf("run failed: %w", err)
	}

	printResult(result)
	return nil
}

func runCompareMode(cmd *cobra.Command, task string, providers []string) error {
	cfg, err := loadRunConfig(cmd)
	if err != nil {
		return err
	}

	client, err := engine.NewClient(cfg.EngineAddr)
	if err != nil {
		return fmt.Errorf("failed to connect to engine: %w", err)
	}
	defer client.Close()

	fmt.Printf("Comparing across providers: %s\n", strings.Join(providers, ", "))

	searchKey := cfg.SearchAPIKey()
	for _, provider := range providers {
		apiKey := config.ResolveAPIKey(provider)
		if apiKey == "" {
			fmt.Printf("\n--- %s --- SKIPPED (no API key)\n", provider)
			continue
		}

		fmt.Printf("\n--- %s ---\n", provider)
		result, err := client.RunTask(task, provider, "", apiKey, searchKey, runMaxRetries, runScoreThreshold, runTimeout)
		if err != nil {
			fmt.Printf("  Error: %v\n", err)
			continue
		}
		printResult(result)
	}

	return nil
}

func runDryRunMode(cmd *cobra.Command, task string) error {
	cfg, err := loadRunConfig(cmd)
	if err != nil {
		return err
	}

	apiKey := config.ResolveAPIKey(runProvider)
	if apiKey == "" {
		return fmt.Errorf("no API key found for provider %q — set %s environment variable",
			runProvider, config.ProviderEnvVars[runProvider])
	}

	client, err := engine.NewClient(cfg.EngineAddr)
	if err != nil {
		return fmt.Errorf("failed to connect to engine: %w", err)
	}
	defer client.Close()

	fmt.Println("Dry run — recommending stack without execution...")

	searchKey := cfg.SearchAPIKey()
	recommendation, err := client.DryRun(task, runProvider, apiKey, searchKey)
	if err != nil {
		return fmt.Errorf("dry run failed: %w", err)
	}

	fmt.Println(recommendation)
	return nil
}

func printResult(result *engine.RunResult) {
	// Best stack recommendation — the whole point of the tool
	fmt.Println("│")
	fmt.Println("│  Best Stack Found")
	fmt.Printf("│    Provider:  %s\n", result.Stack.Provider)
	fmt.Printf("│    Model:     %s\n", result.Stack.Model)
	if result.Stack.Framework != nil && *result.Stack.Framework != "" {
		fmt.Printf("│    Framework: %s\n", *result.Stack.Framework)
	}
	if len(result.Stack.MCPServers) > 0 {
		fmt.Printf("│    MCP:       %s\n", strings.Join(result.Stack.MCPServers, ", "))
	}
	if len(result.Stack.Skills) > 0 {
		fmt.Printf("│    Skills:    %s\n", strings.Join(result.Stack.Skills, ", "))
	}
	if result.Stack.PromptStrategy != "" {
		fmt.Println("│")
		fmt.Println("│  Prompt Strategy")
		fmt.Printf("│    %s\n", truncate(result.Stack.PromptStrategy, 96))
	}

	// Validation score with breakdown
	fmt.Println("│")
	fmt.Printf("│  Validation Score: %.0f/100\n", result.Score)
	if len(result.Dimensions) > 0 {
		for _, d := range result.Dimensions {
			bar := scoreBar(d.Score, d.MaxScore)
			fmt.Printf("│    %-20s %s  %.0f/%.0f\n", d.Name, bar, d.Score, d.MaxScore)
		}
	}

	// Attempt history — show how the stack was refined
	if result.TotalAttempts > 1 {
		fmt.Println("│")
		fmt.Printf("│  Explored %d configurations (best: #%d)\n", result.TotalAttempts, result.BestAttempt)
		for _, a := range result.Attempts {
			marker := " "
			if a.AttemptNumber == result.BestAttempt {
				marker = "*"
			}
			fmt.Printf("│   %s #%d  %.0f/100  %s/%s\n", marker, a.AttemptNumber, a.Score, a.Stack.Provider, a.Stack.Model)
			if len(a.Stack.MCPServers) > 0 {
				fmt.Printf("│          MCP: %s\n", strings.Join(a.Stack.MCPServers, ", "))
			}
			if len(a.Stack.Skills) > 0 {
				fmt.Printf("│          Skills: %s\n", strings.Join(a.Stack.Skills, ", "))
			}
			for _, note := range a.AdjustmentNotes {
				fmt.Printf("│          -> %s\n", note)
			}
		}
	} else {
		fmt.Println("│")
		fmt.Printf("│  Validated in %d attempt\n", result.TotalAttempts)
	}

	fmt.Printf("│  Artifacts: %d files\n", result.ArtifactCount)
	fmt.Println("╰──────────────────────────────────────────────────╯")
}

func scoreBar(score, max float64) string {
	if max <= 0 {
		return "          "
	}
	filled := int((score / max) * 10)
	if filled > 10 {
		filled = 10
	}
	bar := ""
	for i := 0; i < filled; i++ {
		bar += "█"
	}
	for i := filled; i < 10; i++ {
		bar += "░"
	}
	return bar
}

func truncate(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen-3] + "..."
}
