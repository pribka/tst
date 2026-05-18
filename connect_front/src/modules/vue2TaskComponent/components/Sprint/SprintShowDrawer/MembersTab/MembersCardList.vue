<template>
    <div>
        <a-spin :spinning="loading">
            <div
                v-for="member in list"
                :key="memberKey(member)"
                class="member_card"
                @click="onRowClicked({ data: member })">
                <div class="member_card__head">
                    <Profiler
                        v-if="member.user"
                        :avatarSize="28"
                        :user="member.user" />
                    <div v-else class="font-medium">
                        {{ value(member.name || member.full_name) }}
                    </div>
                </div>
                <div class="member_card__grid">
                    <div class="member_card__field">
                        <div class="label">{{ $t('table.is_scrum_master') }}</div>
                        <div>{{ sprintRole(member) }}</div>
                    </div>
                    <div class="member_card__field">
                        <div class="label">{{ $t('table.task_count') }}</div>
                        <div>{{ value(member.task_count) }}</div>
                    </div>
                    <div class="member_card__field">
                        <div class="label">{{ $t('table.completed_count') }}</div>
                        <div>{{ value(member.completed_count) }}</div>
                    </div>
                    <div class="member_card__field">
                        <div class="label">{{ $t('table.hours') }}</div>
                        <div>{{ value(member.hours) }}</div>
                    </div>
                    <div class="member_card__field">
                        <div class="label">{{ $t('table.last_activity') }}</div>
                        <div>{{ formatDate(member.last_activity) }}</div>
                    </div>
                    <div class="member_card__field">
                        <div class="label">{{ $t('table.need_help_tasks') }}</div>
                        <div>
                            <template v-if="member.need_help_tasks && member.need_help_tasks.length">
                                <span
                                    v-for="(task, index) in member.need_help_tasks"
                                    :key="task.id"
                                    class="task_link"
                                    @click.stop="openTask(task.id)">
                                    {{ task.counter }}<span v-if="index !== member.need_help_tasks.length - 1">, </span>
                                </span>
                            </template>
                            <template v-else>—</template>
                        </div>
                    </div>
                    <div class="member_card__field">
                        <div class="label">{{ $t('table.blocked_tasks') }}</div>
                        <div>
                            <template v-if="member.blocked_tasks && member.blocked_tasks.length">
                                <span
                                    v-for="(task, index) in member.blocked_tasks"
                                    :key="task.id"
                                    class="task_link text-danger"
                                    @click.stop="openTask(task.id)">
                                    {{ task.counter }}<span v-if="index !== member.blocked_tasks.length - 1">, </span>
                                </span>
                            </template>
                            <template v-else>—</template>
                        </div>
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
                @change="getMembers" />
        </div>
    </div>
</template>

<script>
export default {
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
        onRowClicked: {
            type: Function,
            default: () => {}
        },
        getDataHook: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            loading: false,
            list: [],
            count: 0,
            page: 1,
            pageSize: 15
        }
    },
    created() {
        this.getMembers()
    },
    methods: {
        memberKey(member) {
            return member.id || member.user?.id || `${member.user?.first_name}_${member.role}`
        },
        value(value) {
            if(value === undefined || value === null || value === '')
                return '—'
            return value
        },
        sprintRole(member) {
            if(typeof member.is_scrum_master === 'boolean')
                return member.is_scrum_master ? this.$t('sprint.scrum_master') : this.$t('sprint.sprint_member')
            return this.value(member.is_scrum_master)
        },
        formatDate(value) {
            if(!value)
                return '—'
            if(this.$moment(value).isValid())
                return this.$moment(value).format('DD.MM.YYYY HH:mm')
            return value
        },
        openTask(id) {
            const query = Object.assign({}, this.$route.query)
            if(query.task && Number(query.task) !== id || !query.task) {
                query.task = id
                this.$router.push({query})
            }
        },
        async getMembers() {
            try {
                this.loading = true
                const { data } = await this.$http.get(`tasks/sprint/${this.sprint.id}/members/`, {
                    params: {
                        page: this.page,
                        page_size: this.pageSize,
                        page_name: this.pageName
                    }
                })
                this.list = data?.results || []
                this.count = data?.count || 0
                this.getDataHook({
                    results: this.list,
                    count: this.count
                })
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        },
        tableReload() {
            this.page = 1
            this.getMembers()
        }
    }
}
</script>

<style lang="scss" scoped>
.member_card{
    background: #fff;
    border-bottom: 1px solid var(--borderColor);
    padding: 12px 0;
    color: #000;
    &__head{
        margin-bottom: 12px;
    }
    &__grid{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
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
    .task_link{
        color: var(--primaryColor);
        cursor: pointer;
    }
    .text-danger{
        color: var(--functional-text-danger);
    }
}
</style>
