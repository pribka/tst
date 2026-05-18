<template>
    <div :class="[textColor, ]">
        <a-badge 
            v-if="text && text.color !== 'default'" 
            :color="text.color" />
        {{ getSource() }}
    </div>
</template>

<script>
export default {
    props: {
        text: {
            type: Object,
            default: () => null
        },
    },
    data() {
        return {
            textColor: 'text-gray-300',
        }
    },
    methods: {
        getSource() {
            if(this.text) {
                this.textColor = 'text-current'
                return this.text.name
            }
            return 'Не указан' 
        },
    }
}
</script>