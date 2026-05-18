module.exports = {
    root: true,
    plugins: ['vue'],
    env: {
        node: true
    },
    extends: [
        'plugin:vue/essential'
    ],
    rules: {
        eqeqeq: [2, 'smart'],
        'no-console': 'off',
        'no-debugger': process.env.NODE_ENV !== 'production' ? 'off' : 'error',

        indent: ['error', 4, {
            ignoredNodes: ['TemplateLiteral']
        }],

        'template-curly-spacing': 'off',

        'vue/html-indent': 'off',
        'vue/script-indent': 'off',

        'vue/html-closing-bracket-newline': ['error', {
            singleline: 'never',
            multiline: 'never'
        }],
        'vue/attribute-hyphenation': 'off',
        'vue/max-attributes-per-line': 'off'
    },
    parser: 'vue-eslint-parser',
    parserOptions: {
        parser: 'babel-eslint',
        ecmaVersion: 2020,
        sourceType: 'module'
    }
}