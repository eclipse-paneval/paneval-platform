import js from '@eslint/js'
import pluginVue from 'eslint-plugin-vue'
import vueTs from '@vue/eslint-config-typescript'
import prettier from '@vue/eslint-config-prettier'

export default [
  {
    ignores: ['dist', 'coverage', 'node_modules']
  },
  js.configs.recommended,
  ...pluginVue.configs['flat/recommended'],
  ...vueTs(),
  prettier,
  {
    files: ['**/*.{ts,vue}'],
    rules: {
      'vue/multi-word-component-names': 'off'
    }
  }
]
