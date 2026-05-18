<template>
    <div class="task_sections">
        <TaskCardSection
            v-for="section in sectionList"
            :key="section.key"
            :sprint="sprint"
            :model="model"
            :title="section.title"
            :queryParams="{ display: section.key }"
            :pageName="page_name" />
        <TaskCardSection
            v-if="sprint.status === 'completed'"
            key="moved_to_sprint"
            :sprint="sprint"
            :model="model"
            :title="$t('sprint.moved_to_sprint')"
            :queryParams="{ display: 'moved_to_sprint' }"
            :pageName="page_name" />
    </div>
</template>

<script>
export default {
    components: {
        TaskCardSection: () => import('./TaskCardSection.vue')
    },
    props: {
        sprint: {
            type: Object,
            required: true
        },
        actions: {
            type: Object,
            required: true
        },
        page_name: {
            type: String,
            required: true
        },
        model: {
            type: String,
            required: true
        }
    },
    data() {
        return {
            sectionList: [
                {
                    key: 'opened',
                    title: this.$t('sprint.opened')
                },
                {
                    key: 'completed',
                    title: this.$t('sprint.completed')
                },
                {
                    key: 'after_start',
                    title: this.$t('sprint.after_start')
                },
                {
                    key: 'moved_to_backlog',
                    title: this.$t('sprint.moved_to_backlog')
                }
            ]
        }
    },
    methods: {
        tableReload() {
            this.$children.forEach(child => {
                if(typeof child.reload === 'function')
                    child.reload()
            })
        }
    }
}
</script>

<style lang="scss" scoped>
.task_sections{
    padding-top: 18px;
}
</style>
