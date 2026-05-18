<template>
    <div v-if="relatedType" class="flex items-center mt-2 blue_color" @click.stop="openTask()">
        <i class="fi fi-rr-link-alt mr-1" />
        {{ relatedType }}
    </div>
</template>

<script>
export default {
    props: {
        related_object: {
            type: Object,
            default: () => null
        }
    },
    computed: {
        relatedType() {
            if(this.related_object?.type === 'tasks.TaskModel')
                return this.$t('workplan.related_to_task', { name: this.related_object.name })
            return null
        }
    },
    methods: {
        openTask() {
            const query = JSON.parse(JSON.stringify(this.$route.query))
            query.task = this.related_object.id
            this.$router.replace({query})
        }
    }
}
</script>
