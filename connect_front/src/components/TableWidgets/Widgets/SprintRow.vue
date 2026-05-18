<template>
    <div
        v-if="text"
        type="link"
        @click="open"
        class="sprint_row truncate cursor-pointer">
        {{ text.name }}
    </div>
</template>
<script>
export default {
    props: {
        text: {
            type: Object,
            default: () => {}
        },
        startEdit: {
            type: Function,
            default: () => {}
        },
        deleteSprint: {
            type: Function,
            default: () => {}
        },
        updateStatus: {
            type: Function,
            default: () => {}
        },
    },
    methods: {
        open() {
            if (this.text) {
                if (this.$route.query.sprint !== this.text.id) {
                    const query = { 
                        ...this.$route.query,
                        sprint: this.text.id 
                    }
                    this.$router.replace({ query })
                }
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.sprint_row{
    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    &:hover{
        color: var(--blue);
    }
}
</style>