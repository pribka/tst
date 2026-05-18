<template>
    <div>
        <a-spin :spinning="loading">
            <div
                v-for="task in list"
                :key="task.id"
                class="labor_card">
                <div class="labor_card__title blue_color" @click="openTask(task)">
                    #{{ task.counter }} {{ task.name }}
                </div>
                <div
                    v-for="(time, index) in task.time_tracking"
                    :key="index"
                    class="labor_card__time">
                    <div class="labor_card__field">
                        <div class="label">{{ $t('table.user') }}</div>
                        <Profiler
                            v-if="time.user"
                            :avatarSize="20"
                            :user="time.user" />
                    </div>
                    <div class="labor_card__field">
                        <div class="label">{{ $t('table.role') }}</div>
                        <div>{{ time.role || '—' }}</div>
                    </div>
                    <div class="labor_card__field">
                        <div class="label">{{ $t('table.work_log_duration') }}</div>
                        <div>{{ time.hours_sum || time.hours || task.hours || 0 }}</div>
                    </div>
                </div>
                <div class="labor_card__footer">
                    <div class="labor_card__field">
                        <div class="label">{{ $t('table.status_task') }}</div>
                        <TaskStatus v-if="task.status" :status="task.status" />
                    </div>
                    <div class="labor_card__field">
                        <div class="label">{{ $t('table.excluded') }}</div>
                        <a-tag v-if="task.excluded" color="purple" class="m-0">
                            {{ $t('task.returned') }}
                        </a-tag>
                        <span v-else>—</span>
                    </div>
                </div>
            </div>
        </a-spin>
        <div
            v-if="!loading && !list.length"
            class="pt-6">
            <a-empty :description="$t('no_data')" />
        </div>
        <div class="mt-3 flex justify-end">
            <a-pagination
                v-model="page"
                size="small"
                :total="count"
                :pageSize="pageSize"
                hideOnSinglePage
                show-less-items
                @change="getTasks" />
        </div>
    </div>
</template>

<script>
import TaskStatus from '../../../TaskStatus.vue'
export default {
    components: {
        TaskStatus
    },
    props: {
        sprint: {
            type: Object,
            required: true
        },
        pageName: {
            type: String,
            required: true
        },
        model: {
            type: String,
            required: true
        },
        queryParams: {
            type: Object,
            default: () => ({})
        }
    },
    data() {
        return {
            loading: false,
            list: [],
            count: 0,
            page: 1,
            pageSize: 5
        }
    },
    watch: {
        queryParams: {
            deep: true,
            handler() {
                this.reload()
            }
        }
    },
    created() {
        this.getTasks()
    },
    methods: {
        openTask(task) {
            const query = Object.assign({}, this.$route.query)
            if(query.task && Number(query.task) !== task.id || !query.task) {
                query.task = task.id
                this.$router.push({query})
            }
        },
        reload() {
            this.page = 1
            this.getTasks()
        },
        async getTasks() {
            try {
                this.loading = true
                const params = {
                    ...this.queryParams,
                    page: this.page,
                    page_size: this.pageSize,
                    page_name: this.pageName
                }
                const { data } = await this.$http.get(`/tasks/sprint/${this.sprint.id}/report/tasks/`, { params })
                this.list = data?.results || []
                this.count = data?.count || 0
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.labor_card{
    background: #fff;
    border-bottom: 1px solid var(--borderColor);
    padding: 12px 0;
    color: #000;
    &__title{
        font-weight: 500;
        margin-bottom: 10px;
        word-break: break-word;
    }
    &__time{
        display: grid;
        grid-template-columns: minmax(0, 1fr);
        gap: 10px;
        padding: 10px 0;
        &:not(:last-child){
            border-bottom: 1px solid var(--borderColor);
        }
    }
    &__field{
        min-width: 0;
        word-break: break-word;
        .label{
            color: var(--functional-text-muted);
            font-size: 12px;
            margin-bottom: 3px;
        }
    }
    &__footer{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
        margin-top: 10px;
    }
}
</style>
