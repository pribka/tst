<template>
    <div :class="mainClass">
        <a-card
            style="border-radius: var(--borderRadius);"
            size="small"
            :bordered="false"
            :ref="`task_card_${item.id}`"
            :class="isMobile ? 'mmb' : 'mb-2'"
            class="kanban-card">
            <div class="mb-2">
                <div class="flex items-start justify-between leading-none ">
                    <div class="flex items-center justify-between w-full max-w-full">
                        <div
                            class="flex items-center truncate"
                            @click="openTask()">
                            <CardPriority
                                class="mr-1"
                                :item="item"/>
                            <span
                                v-if="!item.rejected"
                                class="blue_color card_name truncate font-medium">
                                #{{item.counter}} {{ item.name }}
                            </span>
                            <a-tooltip
                                v-else
                                destroyTooltipOnHide
                                :title="$t('task.problem_task')">
                                <span
                                    class="cursor-pointer blue_color font-medium">
                                    <span class="counter_rejected"> #{{item.counter}}</span>
                                    {{ item.name }}
                                </span>
                            </a-tooltip>
                        </div>
                        <!-- user && item.is_auction -->
                        <template v-if="user && item.is_auction">
                            <a-popconfirm
                                :title="$t('task.handler.confirmTakeTask')"
                                :ok-text="$t('task.yes')"
                                :cancel-text="$t('task.no')"
                                @confirm="takeTask(item)">
                                <a-tag
                                    v-tippy="{ inertia : true}"
                                    :content="$t('task.handler.ok')"
                                    color="orange"
                                    class="ml-2 mr-0 cursor-pointer">
                                    <i class="fi fi-rr-megaphone"></i>
                                </a-tag>
                            </a-popconfirm>
                        </template>
                    </div>
                    <div class="flex items-center">
                        <component
                            :is="actionsWidget"
                            :ref="`task_actions_${item.id}`"
                            :item="item"
                            :showButton="false"
                            :showStatus="true" />
                    </div>
                </div>
                
                <template v-if="projectName || workgroupName">
                    <div class="mt-1 text-xs font-light leading-none truncate" @click="openTask()">
                        <span v-if="projectName">{{ projectName }}</span>
                        <span v-else-if="workgroupName">{{ workgroupName }}</span>
                    </div>
                </template>
            </div>
            <template v-if="isMobile || simplified">
                <template v-if="item.last_execution_time">
                    <div class="mb-2 text-xs font-light leading-none" @click="openTask()">
                        <span class="mr-1">
                            <i class="fi fi-rr-briefcase"></i>
                        </span>
                        <span>{{ item.last_execution_time }}</span>
                    </div>
                </template>
            </template>
            <div @click="openTask()">
                <CardDates
                    class="text-xs"
                    hideNoDates
                    :task="item" />
            </div>
            <div class="flex justify-end">
                <div
                    class="users_info flex items-center"
                    :ref="`kanban_card_${item.id}`">
                    <div class="flex">
                        <Profiler
                            :user="item.owner"
                            :showUserName="false"
                            :avatarSize="15"
                            :getPopupContainer="getPopupContainer" />
                    </div>
                    <a-icon
                        type="right"
                        class="mx-1 text-xs" />
                    <div 
                        v-if="item.operator && item.operator.id != 0" 
                        class="flex">
                        <Profiler
                            :user="item.operator"
                            :showUserName="false"
                            :avatarSize="15"
                            :getPopupContainer="getPopupContainer" />
                    </div>
                </div>
            </div>
        </a-card>
    </div>
</template>

<script>
import TaskAction from '../../TaskActions/List.vue'
import taskHandler from '../../mixins/taskHandler.js'
import { mapState, mapGetters} from 'vuex'
import { onLongPress } from '@vueuse/core'
import CardPriority from '../CardParts/CardPriority.vue'
import CardDates from '../CardParts/CardDates.vue'
export default {
    components: {
        TaskAction,
        CardPriority,
        CardDates,
    },
    mixins: [
        taskHandler
    ],
    props: {
        item: {
            type: Object,
            required: true
        },
        active: {
            type: Boolean,
            default: true
        },
        myTaskEnabled: {
            type: Boolean,
            default: true
        },
        hideDeadline: {
            type: Boolean,
            default: false
        },
        showStatus: {
            type: Boolean,
            default: false
        },
        sprintId: {
            type: String,
            default: ""
        },
        belongSprint: {
            type: Boolean,
            default: false
        },
        addToSprint: {
            type: Function
        },
        removeFromSprint: {
            type: Function
        },
        showSprintButton: {
            type: Boolean,
            default: false
        },
        isScrolling: {
            type: Boolean,
            default: false
        },
        actionsEnabled: {
            type: Boolean,
            default: true
        },
        reloadTask: {
            type: Function,
            default: () => null
        },
        simplified: {
            type: Boolean,
            default: false
        },
        selectingSubtask: {
            type: Boolean,
            default: false
        },
        selectFunction: {
            type: Function
        },
        activeMobile: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        ...mapGetters({
            taskActions: 'task/taskActions'
        }),
        projectName() {
            return this.item?.project?.name
        },
        workgroupName() {
            return this.item?.workgroup?.name
        },
        nearestEvent() {
            return this.item.nearest_event
        },
        dropActions() {
            const actions = this.taskActions(this.item.task_type)
            if(actions)
                return actions.actions
            else
                return null
        },
        checkAllDates() {
            return this.item.dead_line && this.item.date_start_plan ? true : false
        },
        mainClass() {
            if(this.activeMobile)
                return 'active_task'
            else
                return this.item.can_update_status ? 'active_task' : 'not_active'
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        actionsWidget() {
            if(this.isMobile || this.simplified)
                return () => import('../../TaskActions/ListMobile.vue')
            return () => import('../../TaskActions/List.vue')
        },
        hasSprint() {
            return this.item.sprint?.id
        },
        isInterest() {
            return this.item.task_type === 'interest'
        }
    },
    data(){
        return {
            // workType: null
        }
    },
    async created() {
        // const { data } = await this.$http.get('/tasks/time_tracking/', {
        //     params: {
        //         task: this.item.id,
        //         page: 1,
        //         page_size: 1,
        //         ordering: 'date'
        //     }
        // })
        // this.workType = data
        if (!this.item.operator){this.item.operator={id:0}} // Костыль требует переосмысления. В самом темплейте такой оператор не отрисовывается и совт не падает при рендеринге
    },
    watch: {
        'item.status'(){
            this.$emit('statusChanged', this.item)
        }
    },
    methods: {
        getPopupContainer() {
            return this.$refs[`kanban_card_${this.item.id}`]
        },
        filter(data) {
            // this.$emit("filter", data)
        },
        async openTask() {
            let query = Object.assign({}, this.$route.query)
            query.task = this.item.id
            if(!this.$route.query.task) 
                this.$router.push({query})
            else if(this.$route.query.task !== this.item.id)
                this.reloadTask(this.item)
        },
    },
    mounted() {
        if(this.actionsEnabled && this.isMobile) {
            this.$nextTick(() => {
                onLongPress(this.$refs[`task_card_${this.item.id}`], event => {
                    if(!this.isScrolling) {
                        event.preventDefault()
                        event.stopPropagation()
                        event.stopImmediatePropagation()
                        this.$refs[`task_actions_${this.item.id}`].openDrawer()
                    }
                }, { modifiers: { prevent: true } })
            })
        }
    }
}
</script>

<style lang="scss" scoped>
.counter_rejected{
    background: rgb(238, 42, 42);
    color: white;
    padding: 1px 2px;
    border-radius: 4px;
}
.not_active{
    .kanban-card{
        background: #ebebeb;
        cursor: default;
    }
}
.kanban-card{
    min-width: 270px;
    cursor: move;
    -webkit-user-select: none; 
    -khtml-user-select: none; 
    -moz-user-select: none; 
    -ms-user-select: none; 
    user-select: none;
    &.mmb{
        margin-bottom: 10px;
    }
    .card_title{
        cursor: pointer;
    }
    // .task_project{
    //     font-size: 13px;
    //     color: #656565;
    //     line-height: 15px;
    // }
    
    .act_btn{
        margin-right: -10px;
        margin-top: -13px;
        position: relative;
        z-index: 5;
    }
}
</style>