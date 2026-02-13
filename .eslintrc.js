module.exports = {
  env: {
    node: true,
    es2022: true,
    jest: true,
    browser: true
  },
  extends: [
    'eslint:recommended'
  ],
  parserOptions: {
    ecmaVersion: 2022,
    sourceType: 'module',
    ecmaFeatures: {
      jsx: true
    }
  },
  rules: {
    'indent': ['error', 2],
    'quotes': ['error', 'single'],
    'semi': ['error', 'always'],
    'max-len': ['warn', { code: 100 }],
    'no-console': ['warn', { allow: ['error', 'warn', 'info'] }],
    'no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    'no-trailing-spaces': 'error',
    'eol-last': ['error', 'always'],
    'object-curly-spacing': ['error', 'always'],
    'array-bracket-spacing': ['error', 'never'],
    'comma-dangle': ['error', 'never']
  },
  overrides: [
    {
      files: ['src/frontend/**/*.js', 'src/frontend/**/*.jsx'],
      env: {
        browser: true,
        node: false
      },
      globals: {
        React: 'readonly'
      }
    }
  ]
};
