<template>
    <div>
        <a-spin :spinning="loading">
            <div
                v-for="item in list"
                :key="item.id"
                class="result_card">
                <div class="result_card__top">
                    <div class="result_card__task blue_color" @click="openTask(item)">
                        {{ taskTitle(item) }}
                    </div>
                    <div class="result_card__status">
                        <TaskStatus v-if="item.status" :status="item.status" />
                    </div>
                </div>
                <div class="result_card__field">
                    <div class="label">{{ $t('table.result') }}</div>
                    <div>{{ item.result || '—' }}</div>
                </div>
                <div class="result_card__field">
                    <div class="label">{{ $t('table.operator') }}</div>
                    <Profiler
                        v-if="item.operator"
                        :avatarSize="20"
                        :user="item.operator" />
                    <span v-else>—</span>
                </div>
                <div class="result_card__grid">
                    <div class="result_card__field">
                        <div class="label">{{ $t('table.dead_line') }}</div>
                        <DeadLine
                            v-if="item.dead_line"
                            :taskStatus="item.status"
                            :date="item.dead_line" />
                        <span v-else>—</span>
                    </div>
                    <div class="result_card__field">
                        <div class="label">{{ $t('task.result_approving') }}</div>
                        <template v-if="item.excluded">
                            <i
                                v-tippy="{ inertia : true, duration : '[600,300]'}"
                                :content="$t('task.removed_from_sprint')"
                                class="fi fi-rr-cross"></i>
                        </template>
                        <a-checkbox
                            v-else
                            :checked="item.approved"
                            :disabled="approvedLoading === item.id"
                            @change="changeApproved(item, $event.target.checked)" />
                    </div>
                </div>
                <div class="result_card__field">
                    <div class="label">{{ $t('table.comment') }}</div>
                    <a-input
                        inputType="ghost"
                        :value="item.comment"
                        :placeholder="$t('task.add_comment')"
                        @change="changeCommentLocal(item, $event.target.value)"
                        @blur="saveComment(item)"
                        @keyup.enter="saveComment(item)" />
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
                @change="getResults" />
        </div>
    </div>
</template>

<script>
import TaskStatus from '../../../TaskStatus.vue'
export default {
    components: {
        TaskStatus,
        DeadLine: () => import('@apps/vue2TaskComponent/components/DeadLine')
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
        }
    },
    data() {
        return {
            loading: false,
            approvedLoading: null,
            list: [],
            count: 0,
            page: 1,
            pageSize: 15
        }
    },
    created() {
        this.getResults()
    },
    methods: {
        taskCounter(item) {
            return item.task?.counter || item.task_counter || item.counter || item.id
        },
        taskTitle(item) {
            const counter = this.taskCounter(item)
            const name = item.task?.name || item.task_name || item.name || ''
            return name ? `#${counter} ${name}` : `#${counter}`
        },
        openTask(item) {
            const taskId = item.task?.id || item.task || item.task_id
            if(!taskId)
                return
            const query = Object.assign({}, this.$route.query)
            if(query.task && Number(query.task) !== taskId || !query.task) {
                query.task = taskId
                this.$router.push({query})
            }
        },
        async getResults() {
            try {
                this.loading = true
                const { data } = await this.$http.get(`/tasks/sprint/${this.sprint.id}/expected_results/`, {
                    params: {
                        page: this.page,
                        page_size: this.pageSize,
                        page_name: this.pageName
                    }
                })
                this.list = data?.results || []
                this.count = data?.count || 0
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        },
        async changeApproved(item, value) {
            try {
                this.approvedLoading = item.id
                this.$set(item, 'approved', value)
                await this.$http.patch(`/tasks/sprint/expected_results/${item.id}/update/`, {
                    approved: value
                })
            } catch(e) {
                console.log(e)
                this.$message.error('Не удалось совершить изменения')
            } finally {
                this.approvedLoading = null
            }
        },
        changeCommentLocal(item, value) {
            this.$set(item, 'comment', value)
        },
        async saveComment(item) {
            try {
                await this.$http.patch(`/tasks/sprint/expected_results/${item.id}/update/`, {
                    comment: item.comment
                })
            } catch(e) {
                console.log(e)
                this.$message.error('Не удалось совершить изменения')
            }
        },
        tableReload() {
            this.page = 1
            this.getResults()
        }
    }
}
</script>

<style lang="scss" scoped>
.result_card{
    background: #fff;
    border-bottom: 1px solid var(--borderColor);
    padding: 12px 0;
    color: #000;
    &__top{
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        align-items: center;
        gap: 10px;
        margin-bottom: 10px;
    }
    &__task{
        min-width: 0;
        font-weight: 500;
        cursor: pointer;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    &__status{
        flex: 0 0 auto;
        min-width: 0;
    }
    &__grid{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
    }
    &__field{
        min-width: 0;
        word-break: break-word;
        &:not(:last-child){
            margin-bottom: 10px;
        }
        .label{
            color: var(--functional-text-muted);
            font-size: 12px;
            margin-bottom: 3px;
        }
    }
}
</style>
