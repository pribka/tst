<template>
    <div :class="mainClass">
        <a-card
            style="border-radius: var(--borderRadius);"
            size="small"
            v-touch:longtap="longtapHandler"
            :bordered="false"
            :ref="`task_card_${item.id}`"
            :class="[isMobile ? 'mmb mobile_card' : 'mb-2', bgInvert && 'bg_invert', bgWhite && 'bg_white']"
            class="kanban-card">
            <template v-if="item.blockers?.length">
                <div class="mb-2">
                    <div class="-m-0.5">
                        <a-tag 
                            v-for="blocker in item.blockers"
                            :key="blocker.id"
                            size="small"
                            class="m-0.5 card_tag"
                            :color="blocker.color">
                            {{ blocker.name }}
                        </a-tag>
                    </div>
                </div>
            </template>
            <div class="card_title flex items-start justify-between truncate mb-2">
                <div class="flex truncate">
                    <span
                        v-if="item.priority === 3"
                        class="priority priority_large"
                        :title="$t('task.large_priority')">
                        <i class="fi fi-rr-bolt" />
                    </span>
                    <span
                        v-if="item.priority === 4"
                        :title="$t('task.very_large_priority')"
                        class="priority priority_very_large">
                        <i class="fi fi-rr-flame" />
                    </span>
                    <span
                        v-if="item.priority === 0"
                        :title="$t('task.very_low_priority')"
                        class="priority priority_low">
                        <i class="fi fi-rr-hourglass-start" />
                    </span>
                    <span
                        class="blue_color card_name truncate font-medium"
                        @click="openTask">
                        #{{item.counter}} {{ item.name }}
                    </span>
                    <!--<a-tooltip
                        v-else
                        destroyTooltipOnHide
                        :title="$t('task.problem_task')">
                        <span
                            class="cursor-pointer blue_color font-medium"
                            @click="openTask">
                            <span class="counter_rejected"> #{{item.counter}}</span>
                            {{ item.name }}
                        </span>
                    </a-tooltip>-->
                </div>
                <div class="act_btn flex items-center">
                    <template v-if="!isMobile && user && item.is_auction">
                        <a-popconfirm
                            :title="$t('task.handler.confirmTakeTask')"
                            :ok-text="$t('task.yes')"
                            :cancel-text="$t('task.no')"
                            @confirm="takeTask(item)">
                            <a-tag
                                v-tippy="{ inertia : true}"
                                :content="$t('task.handler.ok')"
                                color="orange"
                                class="mx-0 cursor-pointer">
                                <i class="fi fi-rr-megaphone"></i>
                            </a-tag>
                        </a-popconfirm>
                    </template>
                    <component
                        v-if="useActions && !item.is_sign_task"
                        :is="actionsWidget"
                        :ref="`task_actions_${item.id}`"
                        :item="item"
                        btnSize="small"
                        btnClass="text_current"
                        btnType="link"
                        :btnGhost="false"
                        :showButton="false"
                        :showStatus="showStatus" />
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
                                class="mr-0 ml-2"
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
                                    :avatarSize="22"
                                    :getPopupContainer="getPopupContainer" />
                            </div>
                            <i class="fi fi-rr-angle-small-right mx-1 text-xs" />
                            <div v-if="item.operator && item.operator.id != 0" class="flex">
                                <Profiler
                                    :user="item.operator"
                                    :showUserName="false"
                                    :avatarSize="22"
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
                type="primary"
                ghost
                style="color: #000;"
                class="mt-2"
                @click="selectFunction(item)">
                {{ $t('task.select') }}
            </a-button>
        </a-card>
    </div>
</template>

<script>
import taskHandler from '../mixins/taskHandler.js'
import { mapState, mapGetters} from 'vuex'
export default {
    components: {
        TaskAction: () => import('../TaskActions/List.vue'),
        DeadAndStart: () => import("../DeadAndStart.vue"),
        TaskStatus: () => import("../TaskStatus.vue")
    },
    mixins: [
        taskHandler
    ],
    props: {
        item: [Object],
        bgInvert: {
            type: Boolean,
            default: false
        },
        bgWhite: {
            type: Boolean,
            default: false
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
        },
        responsiveDeadline: {
            type: Boolean,
            default: false
        },
        useActions: {
            type: Boolean,
            default: true
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
            else {
                if(!this.item.is_sign_task) {
                    if(this.item?.owner?.id === this.user?.id || this.item?.operator?.id === this.user?.id)
                        return 'active_task'
                    return this.item.can_update_status ? 'active_task' : 'not_active'
                }
                return 'not_active'
            }
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        actionsWidget() {
            if(this.isMobile || this.simplified)
                return () => import('../TaskActions/ListMobile.vue')
            return () => import('../TaskActions/List.vue')
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
        longtapHandler() {
            if(this.isMobile && !this.item.is_sign_task) {
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
.card_tag{
    &.ant-tag{
        line-height: 22px;
        padding: 0 8px;
        font-size: 12px;
    }
}
.counter_rejected{
    background: rgb(238, 42, 42);
    color: white;
    padding: 1px 2px;
    border-radius: 4px;
}
.not_active{
    .kanban-card{
        background: #edeff2;
        cursor: default;
    }
}
.active_task.drag-chosen,
.active_task.dragging-card{
    .kanban-card{
        box-shadow: 0 10px 24px rgba(21, 45, 89, 0.22) !important;
        transform-origin: center center;
    }
}
.active_task.drag-chosen{
    .kanban-card{
        transform: rotate(-1.4deg) scale(1.01);
    }
}
.active_task.dragging-card{
    .kanban-card{
        animation: cardDragWobble .9s ease-in-out infinite alternate;
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
    background: #f7f9fc;
    box-shadow: initial!important;
    border: 0px;
    &.bg_white{
        background: #fff;
    }
    &.bg_invert{
        background: #f7f9fc;
    }
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
        margin-right: 5px;
        &.priority_very_large{
            color: rgb(255, 92, 92);
        }
        &.priority_large{
            color: rgb(255, 154, 1);
        }
        &.priority_low{
            color: rgb(68, 70, 72);
        }
    }
    .act_btn{
        margin-right: -5px;
        margin-top: -2px;
        position: relative;
        z-index: 5;
    }
}

@keyframes cardDragWobble {
    0% {
        transform: rotate(-1.5deg) scale(1.01);
    }
    100% {
        transform: rotate(1.5deg) scale(1.02);
    }
}
</style>
