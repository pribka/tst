export default {
    name: 'Fragment',
    functional: true,
    render(h, context) {
        return context.children.length === 1 ? context.children[0] : h('div', context.children)
    }
}