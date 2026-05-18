<template>
    <div :class="mainClass">
        <a-card
            style="border-radius: var(--borderRadius);"
            size="small"
            v-touch:longtap="longtapHandler"
            :bordered="false"
            :ref="`task_card_${item.id}`"
            :class="isMobile ? 'mmb mobile_card' : 'mb-2'"
            class="kanban-card">
            <div class="card_title flex items-start justify-between truncate mb-2">
                <div class="flex truncate">
                    <a-checkbox class="mr-3" @change="changeCheckbox" />
                    <span
                        v-if="item.priority === 3"
                        class="priority">
                        <a-tooltip :title="$t('task.large_priority')" destroyTooltipOnHide>
                            <img src="../../../assets/images/fire.svg" />
                        </a-tooltip>
                    </span>
                    <span
                        v-if="item.priority === 4"
                        class="priority">
                        <a-tooltip :title="$t('task.very_large_priority')" destroyTooltipOnHide>
                            <img src="../../../assets/images/rocket.svg" />
                        </a-tooltip>
                    </span>
                    <span
                        v-if="item.priority === 0"
                        class="priority">
                        <a-tooltip :title="$t('task.very_low_priority')" destroyTooltipOnHide>
                            <img src="../../../assets/images/down-arrow.svg" />
                        </a-tooltip>
                    </span>
                    <span
                        v-if="!item.rejected"
                        class="blue_color card_name truncate font-medium"
                        @click="openTask">
                        #{{item.counter}} {{ item.name }}
                    </span>
                    <a-tooltip
                        v-else
                        destroyTooltipOnHide
                        :title="$t('task.problem_task')">
                        <span
                            class="cursor-pointer blue_color font-medium"
                            @click="openTask">
                            <span class="counter_rejected"> #{{item.counter}}</span>
                            {{ item.name }}
                        </span>
                    </a-tooltip>
                </div>
            </div>
            <template v-if="isMobile || simplified">
                <template v-if="checkAllDates">
                    <div 
                        v-if="item.project && item.project.name" 
                        class="task_project truncate">
                        {{ item.project.name }}
                    </div>
                    <div 
                        v-else-if="item.workgroup && item.workgroup.name" 
                        class="task_project truncate">
                        {{ item.workgroup.name }}
                    </div>
                    <div
                        class="flex items-center justify-between"
                        :class="isMobile && 'mt-2'">
                        <div class="flex items-center">
                            <DeadAndStart 
                                :task="item" 
                                :responsive="!isMobile" />
                        </div>

                        <div
                            class="users_info flex items-center"
                            :ref="`kanban_card_${item.id}`">
                            <template v-if="isMobile && user && item.is_auction">
                                <a-popconfirm
                                    :title="$t('task.handler.confirmTakeTask')"
                                    :ok-text="$t('task.yes')"
                                    :cancel-text="$t('task.no')"
                                    @confirm="takeTask(item)">
                                    <a-tag
                                        v-tippy="{ inertia : true}"
                                        :content="$t('task.handler.ok')"
                                        color="orange"
                                        class="mr-1 cursor-pointer">
                                        <i class="fi fi-rr-megaphone"></i>
                                    </a-tag>
                                </a-popconfirm>
                            </template>
                            <TaskStatus
                                v-if="showStatus"
                                class="mr-0"
                                :status="item.status" />
                        </div>
                    </div>
                </template>
                <template v-else>
                    <div class="flex items-center justify-between truncate" :class="isMobile && 'mt-2'">
                        <div 
                            v-if="item.project && item.project.name" 
                            class="task_project truncate">
                            {{ item.project.name }}
                        </div>
                        <div 
                            v-else-if="item.workgroup && item.workgroup.name" 
                            class="task_project truncate">
                            {{ item.workgroup.name }}
                        </div>
                        <div v-else></div>
                        <div
                            class="users_info flex items-center"
                            :ref="`kanban_card_${item.id}`">
                            <template v-if="isMobile && user && item.is_auction">
                                <a-popconfirm
                                    :title="$t('task.handler.confirmTakeTask')"
                                    :ok-text="$t('task.yes')"
                                    :cancel-text="$t('task.no')"
                                    @confirm="takeTask(item)">
                                    <a-tag
                                        v-tippy="{ inertia : true}"
                                        :content="$t('task.handler.ok')"
                                        color="orange"
                                        class="mr-1 cursor-pointer">
                                        <i class="fi fi-rr-megaphone"></i>
                                    </a-tag>
                                </a-popconfirm>
                            </template>
                            <TaskStatus
                                v-if="showStatus"
                                class="mr-0"
                                :status="item.status" />
                        </div>
                    </div>
                </template>
            </template>
            <template v-else>
                <div 
                    v-if="item.project && item.project.name" 
                    class="task_project truncate">
                    {{ item.project.name }}
                </div>
                <div class="flex items-center justify-between mt-1">
                    <DeadAndStart :task="item" :responsive="responsiveDeadline" />

                    <div class="flex items-center">
                        <TaskStatus
                            v-if="showStatus"
                            class="mr-2"
                            :status="item.status" />

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
                            <div v-if="item.operator && item.operator.id != 0" class="flex">
                                <Profiler
                                    :user="item.operator"
                                    :showUserName="false"
                                    :avatarSize="15"
                                    :getPopupContainer="getPopupContainer" />
                            </div>
                        </div>
                    </div>
                </div>
            </template>
            
            <div
                v-if="sprintId && showSprintButton"
                class="flex items-center justify-between mt-3">
                <a-button
                    v-if="!hasSprint"
                    type="primary"
                    block
                    @click="addToSprint(item)">
                    {{ $t('task.add_to_sprint') }}
                </a-button>
                <a-button
                    v-if="hasSprint"
                    block
                    @click="removeFromSprint(item)">
                    {{ $t('task.delete_to_sprint') }}
                </a-button>
            </div>

            <a-button
                v-if="selectingSubtask" 
                size="small"
                class="mt-2"
                @click="selectFunction(item)">
                {{ $t('task.select') }}
            </a-button>
        </a-card>
    </div>
</template>

<script>
import taskHandler from '../../mixins/taskHandler.js'
import { mapState, mapGetters} from 'vuex'
export default {
    components: {
        DeadAndStart: () => import("../../DeadAndStart.vue"),
        TaskStatus: () => import("../../TaskStatus.vue")
    },
    mixins: [
        taskHandler
    ],
    props: {
        item: [Object],
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
        },
        responsiveDeadline: {
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
        dropActions() {
            const actions = this.taskActions(this.item.task_type)
            if(actions)
                return actions.actions
            else
                return null
        },
        checkAllDates() {
            return this.item.dead_line || this.item.date_start_plan ? true : false
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
        }
    },
    created() {
        if (!this.item.operator){this.item.operator={id:0}} // Костыль требует переосмысления. В самом темплейте такой оператор не отрисовывается и совт не падает при рендеринге
    },
    watch: {
        'item.status'(){
            this.$emit('statusChanged', this.item)
        }
    },
    methods: {
        changeCheckbox() {
            this.$emit('rowSelected', {
                data: this.item
            })
        },
        longtapHandler() {
            if(this.isMobile) {
                this.$refs[`task_actions_${this.item.id}`].openDrawer()
            }
        },
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
    &.mobile_card{
        transition: all 0.5s cubic-bezier(0.645, 0.045, 0.355, 1);
        &.touch{
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
            transform: scale(0.97);
        }
    }
    &.mmb{
        margin-bottom: 10px;
    }
    .card_title{
        cursor: pointer;
    }
    .task_project{
        font-size: 13px;
        color: #656565;
        line-height: 15px;
    }
    .priority{
        display: block;
        min-width: 14px;
        min-height: 14px;
        margin-right: 0.15rem;
        img{
            width: 14px;
            height: 14px;
        }
    }
    .act_btn{
        margin-right: -10px;
        margin-top: -5px;
        position: relative;
        z-index: 5;
    }
}
</style>