import { defineConfig } from 'vitepress'

export default defineConfig({
  base: '/validtr/',
  title: 'validtr',
  description: 'Natural language in. Production-grade agentic stack out.',
  cleanUrls: true,
  srcExclude: ['README.md'],
  themeConfig: {
    logo: '/validtr-logo.png',
    nav: [
      { text: 'Guide', link: '/getting-started/overview' },
      { text: 'Concepts', link: '/concepts/architecture' },
      { text: 'Reference', link: '/reference/cli' },
      { text: 'Operations', link: '/operations/troubleshooting' },
      { text: 'Releases', link: '/releases/changelog' },
      { text: 'Roadmap', link: '/roadmap/implemented-vs-roadmap' },
      { text: 'GitHub', link: 'https://github.com/AdminTurnedDevOps/validtr' }
    ],
    search: {
      provider: 'local'
    },
    sidebar: {
      '/getting-started/': [
        {
          text: 'Getting Started',
          items: [
            { text: 'Overview', link: '/getting-started/overview' },
            { text: 'Install', link: '/getting-started/install' },
            { text: 'Quickstart', link: '/getting-started/quickstart' },
            { text: 'Project Layout', link: '/getting-started/project-layout' }
          ]
        }
      ],
      '/concepts/': [
        {
          text: 'Concepts',
          items: [
            { text: 'Architecture', link: '/concepts/architecture' },
            { text: 'Pipeline', link: '/concepts/pipeline' },
            { text: 'Scoring', link: '/concepts/scoring' },
            { text: 'Task Lifecycle', link: '/concepts/task-lifecycle' }
          ]
        }
      ],
      '/reference/': [
        {
          text: 'Reference',
          items: [
            { text: 'CLI', link: '/reference/cli' },
            { text: 'Engine API', link: '/reference/api' },
            { text: 'Configuration', link: '/reference/configuration' },
            { text: 'Providers', link: '/reference/providers' },
            { text: 'Data Models', link: '/reference/models' },
            { text: 'Recommendation Engine', link: '/reference/recommendation' },
            { text: 'MCP Registry', link: '/reference/mcp-registry' },
            { text: 'Skills Registry', link: '/reference/skills-registry' },
            { text: 'Execution Runtime', link: '/reference/execution-runtime' },
            { text: 'Testing and Validation', link: '/reference/testing-validation' },
            { text: 'Retry Strategy', link: '/reference/retry-strategy' },
            { text: 'Prompts and Contracts', link: '/reference/prompts-contracts' }
          ]
        }
      ],
      '/operations/': [
        {
          text: 'Operations',
          items: [
            { text: 'Troubleshooting', link: '/operations/troubleshooting' },
            { text: 'Current Limitations', link: '/operations/limitations' }
          ]
        }
      ],
      '/releases/': [
        {
          text: 'Releases',
          items: [
            { text: 'Changelog', link: '/releases/changelog' },
            { text: 'Versioning Strategy', link: '/releases/versioning' }
          ]
        }
      ],
      '/roadmap/': [
        {
          text: 'Roadmap',
          items: [
            { text: 'Implemented vs Roadmap', link: '/roadmap/implemented-vs-roadmap' }
          ]
        }
      ]
    },
    socialLinks: [{ icon: 'github', link: 'https://github.com/AdminTurnedDevOps/validtr' }],
    footer: {
      message: 'MIT Licensed',
      copyright: 'Copyright 2026 validtr'
    }
  }
})
