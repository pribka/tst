<template>
    <div 
        class="sprint_card" 
        ref="sprintCard"
        :class="visible && 'active'">
        <div class="sprint_card__header">
            <div class="card_top">
                <div 
                    class="card_name blue_color" 
                    :title="sprint.name"
                    @click="openSprint()">
                    {{ sprint.name }}
                </div>
                <div class="card_actions flex items-center justify-end gap-1">
                    <a-tag 
                        :color="statusColor">
                        {{ $t(`sprint.${sprint.status}`) }}
                    </a-tag>
                    <a-dropdown 
                        :trigger="['click']" 
                        :getPopupContainer="getPopupContainer"
                        placement="bottomRight"
                        @visibleChange="visibleChange">
                        <a-button 
                            size="small"
                            flaticon
                            shape="circle"
                            icon="fi fi-rr-menu-dots-vertical" />
                        <a-menu slot="overlay">
                            <template v-if="actions">
                                <a-menu-item 
                                    v-if="actions && actions.set_task && actions.set_task.availability && sprint.status !== 'completed'"
                                    key="add_task" 
                                    class="flex items-center"
                                    @click="addTask()">
                                    <i class="fi fi-rr-plus mr-2" /> {{ $t('task.add_task') }}
                                </a-menu-item>
                                <a-menu-item 
                                    v-if="windowWidth < 1500"
                                    key="open" 
                                    class="flex items-center"
                                    @click="openSprint()">
                                    <i class="fi fi-rr-zoom-in mr-2" /> {{ $t('sprint.open_sprint') }}
                                </a-menu-item>
                                <a-menu-item 
                                    key="share" 
                                    class="flex items-center"
                                    @click="share()">
                                    <i class="fi fi-rr-share mr-2" /> {{$t('task.share_to_chat')}}
                                </a-menu-item>
                                <a-menu-item 
                                    key="analytics" 
                                    class="flex items-center" 
                                    @click="openAnalytics()">
                                    <i class="fi fi-rr-chart-histogram mr-2" /> {{ $t('sprint.sprint_analytics') }}
                                </a-menu-item>
                                <a-menu-item 
                                    v-if="actions && actions.edit && actions.edit.availability"
                                    key="edit" 
                                    class="flex items-center" 
                                    @click="edit()">
                                    <i class="fi fi-rr-edit mr-2" /> {{$t('task.edit')}}
                                </a-menu-item>
                                <template v-if="actions && actions.delete && actions.delete.availability">
                                    <a-menu-divider />
                                    <a-menu-item 
                                        class="text-red-500 flex items-center" 
                                        key="delete" 
                                        @click="deleteSprint()">
                                        <i class="fi fi-rr-trash mr-2" /> {{$t('task.remove')}}
                                    </a-menu-item>
                                </template>
                            </template>
                            <template v-else>
                                <a-menu-item 
                                    class="flex justify-center"
                                    key="loader">
                                    <a-spin size="small" />
                                </a-menu-item>
                            </template>
                        </a-menu>
                    </a-dropdown>
                </div>
            </div>
            <div class="card_bottom">
                <div v-if="sprint.begin_date && sprint.dead_line" class="card_dates flex items-center" @click="openSprint()">
                    <i class="fi fi-rr-calendar mr-2" /> {{ $moment(sprint.begin_date).format('DD.MM.YY') }} - {{ $moment(sprint.dead_line).format('DD.MM.YY') }}
                </div>
                <div v-else class="card_dates"></div>
                <div class="count_stat">
                    <div 
                        v-tippy
                        :content="$t('task.new')"
                        class="count_stat__item new">
                        {{ sprint.new_task_count }}
                    </div>
                    <div 
                        v-tippy
                        :content="$t('task.in_work')"
                        class="count_stat__item process">
                        {{ sprint.in_work_task_count }}
                    </div>
                    <div 
                        v-tippy
                        :content="$t('task.completed')"
                        class="count_stat__item completed">
                        {{ sprint.completed_task_count }}
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { declOfNum } from '@/utils/utils.js'
export default {
    props: {
        sprint: {
            type: Object,
            required: true
        },
        inject: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            visible: false,
            sprintDetail: null,
            loading: false,
            taskList: [],
            count: 0,
            pageSize: 10,
            taskLoading: false,
            page: 1,
            empty: false,
            takeLoader: false,
            page_name: `sprint_tasks_${this.sprint.id}`,
            actions: null,
            actionsLoader: false
        }
    },
    computed: {
        statusColor() {
            switch (this.sprint.status) {
            case "new":
                return "blue";
                break;
            case "in_process":
                return "purple";
                break;
            case "completed":
                return "green";
                break;
            default:
                return "blue";
            }
        },
        isInject() {
            return this.inject ? `_inject` : ''
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        taskCount() {
            return `${this.sprint.task_count} ${declOfNum(this.sprint.task_count, [this.$t('task.task_singular'), this.$t('task.task_plural_2_4'), this.$t('task.task_plural_5_plus')])}`
        },
        user() {
            return this.$store.state.user.user
        },
        isAuthor() {
            if(this.$store.state.user.user?.id === this.sprint.author.id)
                return true
            else
                return false
        }
    },
    methods: {
        getPopupContainer() {
            return this.$refs.sprintCard
        },
        addTask() {
            eventBus.$emit('sprint_add_task', this.sprint.id)
        },
        visibleChange(vis) {
            if(vis && !this.actions) {
                this.getSprintActions()
            }
        },
        async getSprintActions(open = false) {
            try {
                this.actionsLoader = true
                const { data } = await this.$http.get(`/tasks/sprint/${this.sprint.id}/action_info/`)
                if(data) {
                    this.actions = data
                    if(open)
                        this.visible = true
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.actionsLoader = false
            }
        },
        openSprint() {
            const query = Object.assign({}, this.$route.query)
            if(query.sprint && Number(query.sprint) !== this.sprint.id || !query.sprint) {
                query.sprint = this.sprint.id
                this.$router.push({query})
            }
        },
        openAnalytics() {
            const query = Object.assign({}, this.$route.query)
            if(query.sprint && Number(query.sprint) !== this.sprint.id || !query.sprint) {
                query.sprint = this.sprint.id
                query.sptab = 'analytics'
                this.$router.push({query})
            }
        },
        showSprintInfo() {
            if(!this.actions) {
                this.getSprintActions(true)
            } else
                this.visible = !this.visible
        },
        share() {
            this.$store.commit('share/SET_SHARE_PARAMS', { 
                model: 'tasks.TaskModel',
                shareId: this.sprint.id,
                object: {...this.sprint,isSprint: true},
                shareUrl: `${window.location.origin}/ru/dashboard?sprint=${this.sprint.id}`,
                shareTitle: `${this.$t('task.sprint_menu')} - ${this.sprint.name}`
            })
        },
        async actionHandler() {
            if(this.sprint.status === 'new') {
                try {
                    this.loading = true
                    await this.$http.put(`tasks/sprint/${this.sprint.id}/update_status/`, {status: 'in_process'})
                    this.$message.success(this.$t('task.to_work'))
                    eventBus.$emit(`update_sprints_list${this.isInject}`)
                } catch(e) {
                    console.log(e)
                    this.$message.error(this.$t('error'))
                } finally {
                    this.loading = false
                }
            }
            if(this.sprint.status === 'in_process') {
                eventBus.$emit('end_sprint', this.sprint)
                /*try {
                    this.loading = true
                    await this.$http.put(`tasks/sprint/${this.sprint.id}/update_status/`, {status: 'completed'})
                    this.$message.success("Спринт завершен")
                    eventBus.$emit(`update_sprints_list${this.isInject}`)
                } catch(e) {
                    this.$message.error(this.$t('error'))
                } finally {
                    this.loading = false
                }*/
            }
        },
        edit() {
            eventBus.$emit('edit_sprint', {
                ...this.sprint,
                inject: this.inject
            })
        },
        deleteSprint() {
            this.$confirm({
                title: this.$t('task.delete_message'),
                closable: true,
                maskClosable: true,
                cancelText: this.$t('task.no'),
                okText: this.$t('task.remove'),
                okType: 'danger',
                zIndex: 99999,
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post('/table_actions/update_is_active/', [{ id: this.sprint.id, is_active: false }])
                            .then(() => {
                                this.$message.success(this.$t('task.remove'))
                                eventBus.$emit(`update_sprints_list${this.isInject}`)
                                resolve()
                            })
                            .catch((e) => {
                                console.log(e)
                                reject()
                            })
                    })
                }
            })
        }
    }
}
</script>

<style lang="scss" scoped>
.info_card{
    background: #fff;
    padding: 15px;
    border-radius: 8px;
    color: #000;
    &__head{
        padding-bottom: 5px;
        min-height: 40px;
    }
    .h_label{
        opacity: 0.6;
    }
}
.task_table_name{
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    transition: color 0.3s;
    word-break: break-word;
}
.sprint_table{
    &::v-deep{
        .table_status{
            height: 30px;
            line-height: 30px;
            padding-left: 15px;
            padding-right: 15px;
            border-radius: 30px;
        }
        .ant-table-row{
            td{
                border-color: #ced3fb;
            }
        }
    }
}
.sprint_card{
    background: #fff;
    border-radius: 8px;
    padding: 14px;
    margin-bottom: 12px;
    color: #000;
    &.active{
        .card_arrow{
            transform: rotate(180deg);
        }
    }
    .sprint_target{
        &__item{
            opacity: 0.6;
            &:not(:last-child){
                margin-bottom: 5px;
            }
        }
    }
    &__body{
        border-top: 1px solid #afafaf;
        margin-top: 20px;
        padding-top: 20px;
        .sprint_info_grid{
            display: grid;
            gap: 15px;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            @media (min-width: 1350px) {
                grid-template-columns: repeat(4, minmax(0, 1fr));
            }
            @media (min-width: 1400px) {
                grid-template-columns: 190px 190px 1fr 1fr;
            }
        }
    }
    &__header{
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    .card_top,
    .card_bottom{
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 10px;
        min-width: 0;
    }
    .card_bottom{
        align-items: center;
    }
    .card_name{
        flex: 1 1 auto;
        min-width: 0;
        cursor: pointer;
        line-height: 20px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
        word-break: break-word;
    }
    .card_actions{
        flex: 0 0 auto;
        justify-content: flex-end;
    }
    .count_stat{
        display: flex;
        align-items: center;
        flex-shrink: 0;
        &__item{
            height: 32px;
            min-width: 32px;
            padding: 0 6px;
            color: #000;
            font-size: 14px;
            line-height: 32px;
            text-align: center;
            border-radius: 6px;
            &:not(:last-child) {
                margin-right: 5px;
            }
            &.new{
                background: #ced3fb;
            }
            &.process{
            background: #efbdbd;
            }
            &.completed{
                background: #bdf0cc;
            }
        }
    }
    .sprint_status{
        background: #1D65C0;
        border-radius: 30px;
        height: 30px;
        padding-left: 15px;
        padding-right: 15px;
        color: #fff;
        line-height: 30px;
        text-align: center;
        white-space: nowrap;
        font-size: 12px;
    }
    .card_dates{
        flex: 1 1 auto;
        opacity: 0.6;
        font-size: 14px;
        min-width: 0;
        word-break: break-word;
        line-height: 18px;
        cursor: pointer;
    }
    &::v-deep{
        .ant-tag{
            margin-right: 0;
            max-width: calc(100vw - 110px);
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .ant-btn-circle.ant-btn-sm{
            width: 32px!important;
            min-width: 32px!important;
            max-width: 32px!important;
            height: 32px!important;
            padding: 0!important;
            border-radius: 50%!important;
            flex: 0 0 32px;
        }
    }
    @media (max-width: 360px) {
        padding: 12px;
        .card_bottom{
            flex-direction: column;
        }
        .count_stat{
            margin-left: auto;
        }
    }
}
</style>
