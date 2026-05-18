<template>
    <a-tag 
        :color="tagColor" 
        class="mr-0">
        {{ user.work_status.name }}
    </a-tag>
</template>

<script>
export default {
    props: {
        user: {
            type: Object,
            required: true
        }
    },
    computed: {
        tagColor() {
            return this.user.work_status.color || 'geekblue'
        }
    }
}
</script>