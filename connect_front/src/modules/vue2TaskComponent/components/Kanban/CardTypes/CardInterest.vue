<template>
    <div :class="mainClass">
        <a-card
            style="border-radius: var(--borderRadius);"
            size="small"
            :bordered="false"
            v-touch:longtap="longtapHandler"
            :ref="`task_card_${item.id}`"
            :class="isMobile ? 'mmb mobile_card' : 'mb-2'"
            @click="openTask"
            class="kanban-card">
            <div class="mb-2 flex items-center justify-between">
                <TaskStatus 
                    class="mr-0"
                    :status="item.status" />
                <template v-if="canTakeAuction">
                    <a-popconfirm
                        class="ml-1"
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
            </div>
            <div class="mb-2">
                <div class="flex items-start justify-between leading-none ">
                    <div class="flex truncate max-w-full">
                        
                        <span
                            v-if="!item.rejected"
                            class="blue_color card_name truncate font-medium">
                            #{{item.counter}} {{ item.name }}
                        </span>
                        <a-tooltip
                            destroyTooltipOnHide
                            v-else
                            :title="$t('task.problem_task')">
                            <span
                                class="cursor-pointer blue_color font-medium">
                                <span class="counter_rejected"> #{{item.counter}}</span>
                                {{ item.name }}
                            </span>
                        </a-tooltip>
                        <CardPriority
                            class="ml-2"
                            :item="item"/>
                    </div>
                    <div class="act_btn flex items-center">
                        
                        <component
                            :is="actionsWidget"
                            :ref="`task_actions_${item.id}`"
                            :item="item"
                            :showButton="false"
                            :showStatus="true" />
                    </div>
                </div>
                
                <template v-if="clientName">
                    <div class="mt-1 text-xs font-light leading-none truncate">
                        {{ clientName }}
                    </div>
                </template>
                <template v-if="projectName || workgroupName">
                    <div class="mt-1 text-xs font-light leading-none truncate">
                        <span v-if="projectName">{{ projectName }}</span>
                        <span v-else-if="workgroupName">{{ workgroupName }}</span>
                    </div>
                </template>
            </div>
            <template v-if="isMobile || simplified">
                <template v-if="item.last_execution_time">
                    <div class="mb-2 text-xs font-light leading-none">
                        <span class="mr-1">
                            <i class="fi fi-rr-briefcase"></i>
                        </span>
                        <span>{{ item.last_execution_time }}</span>
                    </div>
                </template>
                <template v-if="nearestEvent">
                    <CardEvent 
                        class="mb-2" 
                        :event="nearestEvent"/>
                </template>
                <template v-if="showAnnotations">
                    <div class="mb-2 text-xs flex justify-between items-center">
                        <CardAnnotations :item="item" />
                    </div>
                </template>
                <!-- <template v-if="checkAllDates">
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
                            <DeadAndStart :task="item" />
                        </div>

                        <div
                            class="users_info flex items-center"
                            :ref="`kanban_card_${item.id}`">
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
                            <TaskStatus
                                v-if="showStatus"
                                class="mr-0"
                                :status="item.status" />
                        </div>
                    </div>
                </template> -->
            </template>
            <div class="flex items-center flex-wrap -mt-2">
                <CardDates 
                    class="text-xs mr-4 mt-2"
                    :task="item" />
                <div class="ml-auto mt-2">
                    <CardMembers 
                        :person="item.operator"
                        :participantCount="item.participants_count"/>
                </div>
            </div>
            <!-- <template v-else>
                <div 
                    v-if="item.project && item.project.name" 
                    class="task_project truncate">
                    {{ item.project.name }}
                </div>
                <div class="flex items-center justify-between mt-1">
                    <div class="flex items-center">
                        <DeadAndStart :task="item" />
                    </div>

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
            </template>
            

            <template v-if="selectingSubtask" >
                <a-button
                    
                    size="small"
                    class="mt-2"
                    @click="selectFunction(item)">
                    Выбрать
                </a-button>
            </template> -->
        </a-card>
    </div>
</template>

<script>
import TaskAction from '../../TaskActions/List.vue'
import DeadAndStart from "../../DeadAndStart.vue"
import TaskStatus from "../../TaskStatus.vue"
import taskHandler from '../../mixins/taskHandler.js'
import { mapState, mapGetters} from 'vuex'
import CardEvent from '../CardParts/CardEvent.vue'
import CardMembers from '../CardParts/CardMembers.vue'
import CardPriority from '../CardParts/CardPriority.vue'
import CardDates from '../CardParts/CardDates.vue'
import CardAnnotations from '../CardParts/CardAnnotations.vue'
export default {
    components: {
        TaskAction,
        DeadAndStart,
        TaskStatus,
        CardPriority,
        CardEvent,
        CardMembers,
        CardDates,
        CardAnnotations
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
        showAnnotations() {
            return this.item.children_count ||
                this.item.comments_count ||
                this.item.attachments_count ||
                this.item.has_description
        },
        clientName() {
            return this.item?.customer_card?.name ||
                this.item?.customer_name ||
                this.item?.contractor_name ||
                this.item?.potential_contractor?.company_name ||
                this.item?.potential_contractor?.name ||
                ''
        },
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
        },
        canTakeAuction() {
            return this.user && this.item.is_auction
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
    min-width: 100px;
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
    // .task_project{
    //     font-size: 13px;
    //     color: #656565;
    //     line-height: 15px;
    // }
    
    .act_btn{
        margin-right: -10px;
        margin-top: -5px;
        position: relative;
        z-index: 5;
    }
}
</style>
