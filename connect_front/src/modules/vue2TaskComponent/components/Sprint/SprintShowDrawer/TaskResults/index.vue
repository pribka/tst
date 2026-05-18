<template>
    <div class="h-full flex flex-col min-h-0">
        <div class="mb-5 panel" v-if="sprint.expected_result?.length || sprint.target">
            <template v-if="sprint.target">
                <p class="text-muted">
                    {{ $t('sprint.spirnt_target') }}
                </p>
                <p class="mt-1">
                    {{ sprint.target }}
                </p>
            </template>
            <template v-if="sprint.expected_result">
                <p class="mt-2 text-muted">
                    {{ $t('sprint.expected_result') }}
                </p>
                <p class="mt-1">
                    {{ sprint.expected_result.join(', ') }}
                </p>
            </template>

        </div>
        <p class="mb-3 text-base">
            {{ $t('sprint.expected_sprint_results') }}
        </p>
        <component
            :is="resultsWidget"
            :sprint="sprint"
            model="tasks.TaskModel"
            pageName="expected_sprint_results" />
    </div>
</template>

<script>
export default {
    components: {
        Table: () => import('./Table')
    },
    props: {
        sprint: {
            type: Object,
            required: true
        }
    },
    computed: {
        resultsWidget() {
            if(this.isMobile)
                return () => import('./CardList.vue')
            return () => import('./Table.vue')
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    }
}
</script>

<style lang="scss" scoped>
.panel {
    padding: 12px 20px;
    background-color: #F8F9FD;
    border-radius: 12px;
}
.text-muted {
    color: #888888;
}
</style>
