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
            { text: 'Quickstart', link: '/getting-started/quickstart' }
          ]
        }
      ],
      '/concepts/': [
        {
          text: 'Concepts',
          items: [
            { text: 'Architecture', link: '/concepts/architecture' },
            { text: 'Pipeline', link: '/concepts/pipeline' },
            { text: 'Scoring', link: '/concepts/scoring' }
          ]
        }
      ],
      '/reference/': [
        {
          text: 'Reference',
          items: [
            { text: 'CLI', link: '/reference/cli' },
            { text: 'Engine API', link: '/reference/api' },
            { text: 'Configuration', link: '/reference/configuration' }
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
