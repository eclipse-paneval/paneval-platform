import { defineConfig } from 'vitepress'
import mathjax3 from 'markdown-it-mathjax3'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  srcDir: 'src',
  title: "PanEval Docs",
  description: "PanEval Platform User Manual",
  base: '/documents/',
  markdown: {
    config(md) {
      md.use(mathjax3)
    }
  },
  themeConfig: {
    logoLink: 'https://paneval.eclipse.org',
    siteTitle: '<span class="paneval-brand"><span class="paneval-brand-mark">PE</span><span class="paneval-brand-name">PanEval</span></span>',
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: 'Manual', link: '/manual/platform-overview' }
    ],

    sidebar: [
      {
        text: 'Manual',
        items: [
          { text: 'Platform Overview', link: '/manual/platform-overview' },
          { text: 'Basic Concepts', link: '/manual/basic-concepts' },
          { text: 'Quick Start', link: '/manual/quick-start' },
          { text: 'Evaluation Operation Process', link: '/manual/evaluation-operation-process' },
          { text: 'FAQ', link: '/manual/faq' },
          { text: 'Contact Us', link: '/manual/contact-us' }
        ]
      }
    ]
  }
})
