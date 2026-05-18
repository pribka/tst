import { createPopper } from '@popperjs/core'
export default {
    data() {
        return {
            placement: 'bottom'
        }
    },
    methods: {
        withPopper (dropdownList, component, {width}) {
            dropdownList.style.width = width

            const popper = createPopper(component.$refs.toggle, dropdownList, {
                placement: this.placement,
                modifiers: [
                    {
                        name: 'offset', options: {
                            offset: [0, -1]
                        }
                    },
                    {
                        name: 'toggleClass',
                        enabled: true,
                        phase: 'write',
                        fn ({state}) {
                            component.$el.classList.toggle('drop-up', state.placement === 'top')
                        }
                    }]
            })

            return () => popper.destroy()
        }
    }
}