<template>
    <div :title="projectsList" class="two_rows">{{ projectsList }}</div>
</template>
<script>
export default {
    props: {
        record: {
            type: Object,
            required: true
        }
    },
    computed: {
        projectsList() {
            if(this.record?.projects?.length)
                return this.record.projects.map(item => item.name).join(', ')
            return ''
        }
    }
}
</script>