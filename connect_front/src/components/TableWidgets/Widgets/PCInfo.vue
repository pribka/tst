<template>
    <div :class="[textColor, ]">
        {{ getDisplayText() }}
    </div>
</template>

<script>
export default {
    props: {
        text: {
            type: String,
            default: ""
        },
    },
    data() {
        return {
            textColor: 'text-gray-300',
        }
    },
    methods: {
        getDisplayText() {
            if(this.text) {
                this.textColor = 'text-current'
                return this.text
            }
            return 'Не указан'
        },
    }
}
</script>