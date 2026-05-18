<template>
    <div class="deal_tasks_tab">
        <div class="deal_tasks_tab__head">
            <div>
                <div class="deal_tasks_tab__title">Производственные задачи</div>
                <div class="deal_tasks_tab__subtitle">
                    Список подгружается по штатной связке задачи с причиной `reason = deal.id`.
                </div>
            </div>
            <a-button
                type="ui"
                ghost
                icon="fi-rr-refresh"
                flaticon
                :loading="loading"
                @click="loadTasks(page)">
                Обновить
            </a-button>
        </div>

        <a-table
            v-if="!isMobile"
            :columns="columns"
            :data-source="tasks"
            :loading="loading"
            :pagination="false"
            :row-key="record => record.id"
            class="deal_tasks_tab__table">
            <template slot="counter" slot-scope="text">
                <span class="text-slate-500">#{{ text }}</span>
            </template>
            <template slot="name" slot-scope="text, record">
                <div class="deal_tasks_tab__name" @click="$emit('open', record.id)">
                    {{ text }}
                </div>
            </template>
            <template slot="date" slot-scope="text">
                {{ formatDate(text) || '—' }}
            </template>
            <template slot="actions" slot-scope="text, record">
                <a-button type="link" class="px-0" @click="$emit('open', record.id)">
                    Открыть
                </a-button>
            </template>
        </a-table>

        <div v-else class="deal_tasks_tab__mobile">
            <template v-if="tasks.length">
                <div
                    v-for="task in tasks"
                    :key="task.id"
                    class="deal_tasks_tab__mobile_card">
                    <div class="deal_tasks_tab__mobile_top">
                        <span class="text-slate-500">#{{ task.counter }}</span>
                        <a-button type="link" class="px-0" @click="$emit('open', task.id)">
                            Открыть
                        </a-button>
                    </div>
                    <div class="deal_tasks_tab__name" @click="$emit('open', task.id)">
                        {{ task.name }}
                    </div>
                    <div class="deal_tasks_tab__dates">
                        <span>Старт: {{ formatDate(task.date_start_plan) || '—' }}</span>
                        <span>Срок: {{ formatDate(task.dead_line) || '—' }}</span>
                    </div>
                </div>
            </template>
            <a-empty v-else description="У этой сделки пока нет связанных задач." />
        </div>

        <div class="deal_tasks_tab__footer">
            <div class="deal_tasks_tab__count">Всего: {{ count }}</div>
            <a-pagination
                :current="page"
                :page-size="pageSize"
                :total="count"
                size="small"
                @change="changePage" />
        </div>
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'

export default {
    name: 'DealTasksTab',
    props: {
        dealId: {
            type: String,
            required: true
        }
    },
    data() {
        return {
            loading: false,
            tasks: [],
            count: 0,
            page: 1,
            pageSize: 10,
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        columns() {
            return [
                {
                    title: '№',
                    dataIndex: 'counter',
                    key: 'counter',
                    width: 110,
                    scopedSlots: { customRender: 'counter' }
                },
                {
                    title: 'Задача',
                    dataIndex: 'name',
                    key: 'name',
                    scopedSlots: { customRender: 'name' }
                },
                {
                    title: 'План старта',
                    dataIndex: 'date_start_plan',
                    key: 'date_start_plan',
                    width: 150,
                    scopedSlots: { customRender: 'date' }
                },
                {
                    title: 'Срок',
                    dataIndex: 'dead_line',
                    key: 'dead_line',
                    width: 150,
                    scopedSlots: { customRender: 'date' }
                },
                {
                    title: '',
                    key: 'actions',
                    width: 90,
                    scopedSlots: { customRender: 'actions' }
                }
            ]
        }
    },
    watch: {
        dealId: {
            immediate: true,
            handler() {
                this.page = 1
                this.loadTasks(1)
            }
        }
    },
    methods: {
        async loadTasks(page = 1) {
            if (!this.dealId) {
                this.tasks = []
                this.count = 0
                return
            }
            try {
                this.loading = true
                const { data } = await this.$http.get('/tasks/list_from_reason/', {
                    params: {
                        reason: this.dealId,
                        page,
                        page_size: this.pageSize,
                    }
                })
                this.page = page
                this.tasks = data?.results || []
                this.count = data?.count || 0
            } catch (error) {
                errorHandler({ error })
            } finally {
                this.loading = false
            }
        },
        changePage(page) {
            this.loadTasks(page)
        },
        formatDate(value) {
            if (!value) return ''
            const m = this.$moment(value)
            return m.isValid() ? m.format('DD.MM.YYYY') : ''
        }
    }
}
</script>

<style lang="scss" scoped>
.deal_tasks_tab__head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 16px;
}

.deal_tasks_tab__title {
    font-size: 16px;
    font-weight: 600;
    color: #111827;
}

.deal_tasks_tab__subtitle {
    margin-top: 4px;
    color: #6b7280;
    font-size: 13px;
}

.deal_tasks_tab__name {
    color: #1d4ed8;
    cursor: pointer;
    font-weight: 500;
}

.deal_tasks_tab__mobile {
    display: grid;
    gap: 12px;
}

.deal_tasks_tab__mobile_card {
    border: 1px solid var(--border2);
    border-radius: 14px;
    background: #fff;
    padding: 14px;
}

.deal_tasks_tab__mobile_top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 8px;
}

.deal_tasks_tab__dates {
    display: grid;
    gap: 4px;
    margin-top: 10px;
    color: #6b7280;
    font-size: 12px;
}

.deal_tasks_tab__footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    margin-top: 16px;
}

.deal_tasks_tab__count {
    color: #64748b;
    font-size: 13px;
}

@media (max-width: 767px) {
    .deal_tasks_tab__head,
    .deal_tasks_tab__footer {
        flex-direction: column;
        align-items: stretch;
    }
}
</style>
