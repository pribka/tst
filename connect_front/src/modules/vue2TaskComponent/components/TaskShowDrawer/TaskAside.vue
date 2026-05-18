<template>
    <div class="task_sidebar_wrapper">
        <template v-if="task">
            <div 
                v-if="asideSetting" 
                class="task_sidebar sidebar_aside aside_item">
                <div v-if="isMobile" class="sidebar_item font-semibold">
                    {{task.name}}
                </div>
                <div class="sidebar_item flex items-center justify-between">
                    <template v-if="asideSetting.showStatus">
                        <TaskStatus :status="task.status" />
                    </template>
                    <TaskTimer
                        v-if="isMobile && !task.is_sign_task"
                        :task="task"
                        :dropActions="dropActions"
                        variant="aside" />
                </div>

                <div class="sidebar_item">
                    <div class="mb-1 opacity-60">
                        {{ $t('task.task_meeting') }}
                    </div>
                    <template v-if="task.meeting">
                        <div 
                            v-if="task.meeting.status" 
                            class="mb-2 flex items-center">
                            <span class="mr-2">{{ $t('task.status') }}:</span> <component :is="meetingStatus" :status="task.meeting.status" />
                        </div>
                        <div 
                            v-if="task.meeting.id" 
                            class="mb-2 cursor-pointer blue_color flex items-center"
                            @click="openMeeting()">
                            <i class="fi fi-rr-redo mr-1" />
                            {{ $t('task.open_meeting') }}
                        </div>
                        <div class="flex items-center gap-2">
                            <a-button 
                                v-if="task.meeting.url" 
                                block 
                                icon="fi-rr-video-camera-alt"
                                flaticon
                                :loading="meetingLoading"
                                type="flat_primary"
                                @click="openMeetingInviteModal()">
                                {{ task.meeting.status === 'online' ? $t('task.join_meeting') : (task.meeting.status === 'ended' ? $t('task.start_new_session') : $t('task.start_meeting'))  }}
                            </a-button>
                            <a-button 
                                v-if="task.meeting.url_external" 
                                icon="fi-rr-link-alt"
                                flaticon
                                v-tippy
                                :content="$t('copy_link')"
                                type="flat_primary"
                                @click="copyMeeting()" />
                        </div>
                    </template>
                    <div v-else class="mt-1">
                        <a-button 
                            block 
                            icon="fi-rr-video-camera-alt"
                            flaticon
                            :loading="meetingLoading"
                            type="flat_primary"
                            @click="openMeetingInviteModal()">
                            {{ $t('task.create_meeting') }} 
                        </a-button>
                    </div>
                </div>

                <!-- Project -->
                <div 
                    v-if="task.project && asideSetting.project" 
                    class="sidebar_item">
                    <div class="mb-1 opacity-60">
                        {{$t('task.project')}}
                    </div>
                    <div 
                        class="flex items-center cursor-pointer" 
                        @click="openProject('viewProject', task.project)">
                        <div>
                            <a-avatar 
                                :src="workgroupLogoPath(task.project)" 
                                icon="team" 
                                :size="32" />
                        </div>
                        <span class="ml-2">{{task.project.name}}</span>
                    </div>
                </div>

                <!-- Contract -->
                <div
                    v-if="task.contract"
                    class="sidebar_item">
                    <div class="mb-1 opacity-60">
                        {{ $t('task.contract') }}
                    </div>
                    <div class="break-words">
                        {{ task.contract.string_view || task.contract.name }}
                    </div>
                </div>
                <div
                    v-if="task.customer_card"
                    class="sidebar_item">
                    <div class="mb-1 opacity-60">
                        {{ $t('task.client') }}
                    </div>
                    <div class="break-words">
                        {{ task.customer_card.name }}
                    </div>
                </div>

                <!-- Blockers -->
                <div class="sidebar_item">
                    <div class="mb-1 opacity-60">
                        {{$t('task.blockers')}}
                    </div>
                    <Blockers
                        workplanUpdate
                        :task="task" />
                </div>

                <!-- Organization -->
                <div 
                    v-if="asideSetting.organization && task.organization" 
                    class="sidebar_item">
                    <div class="mb-1 opacity-60">
                        {{$t('task.organization')}}
                    </div>
                    <div 
                        class="flex items-center" >
                        <div>
                            <a-avatar 
                                :src="task.organization.logo" 
                                icon="team" 
                                :size="32" />
                        </div>
                        <span class="ml-2">{{task.organization.name}}</span>
                    </div>
                </div>
                
                <!-- Workgroup -->
                <div 
                    v-if="task.workgroup && asideSetting.workgroup" 
                    class="sidebar_item">
                    <div class="mb-1 opacity-60">
                        {{$t('task.workgroup')}}
                    </div>
                    <div 
                        class="flex items-center cursor-pointer" 
                        @click="openWorkgroup('viewGroup', task.workgroup)">
                        <div>
                            <a-avatar 
                                :src="workgroupLogoPath(task.workgroup)" 
                                icon="team" 
                                :size="32" />
                        </div>
                        <span class="ml-2">{{task.workgroup.name}}</span>
                    </div>
                </div>
                
                <!-- Sprint -->
                <div 
                    class="sidebar_item" 
                    v-if="task.sprint">
                    <div class="mb-1 opacity-60">
                        {{$t('task.participant_sprint')}}
                    </div>
                    <div
                        class="flex items-baseline cursor-pointer">
                        <div class="break-words" @click="openSprint(task.sprint.id)">
                            {{task.sprint.name }}
                        </div>
                        <a-button
                            v-if="dropActions && dropActions.unset_sprint && !task.is_sign_task"
                            type="ui"
                            flaticon
                            ghost
                            size="small"
                            :loading="sprintLoader"
                            class="ml-2"
                            shape="circle"
                            v-tippy="{ inertia : true, duration : '[600,300]'}"
                            :content="$t('task.remove_from_sprint')"
                            icon="fi-rr-cross-circle"
                            @click="removeToSprint()" />
                    </div>
                    <!--<div v-else-if="task.sprint_history.length > 0">
                        <div 
                            v-for="item in task.sprint_history" 
                            :key="item.id" 
                            class="flex items-baseline"
                            :class="!sprintOpen && 'cursor-pointer'">
                            <div class="break-words" @click="openSprint(item.id)">
                                {{item.name}}
                            </div>
                            <a-button
                                v-if="dropActions && dropActions.unset_sprint"
                                type="ui"
                                flaticon
                                ghost
                                :loading="sprintLoader"
                                size="small"
                                class="ml-2"
                                shape="circle"
                                v-tippy="{ inertia : true, duration : '[600,300]'}"
                                content="Убрать из спринта"
                                icon="fi-rr-cross-circle"
                                @click="removeToSprint()" />
                        </div>
                    </div>-->
                </div>

                <!-- Objectives -->
                <div 
                    v-if="objectives"
                    class="sidebar_item">
                    <div class="mb-1 opacity-60">
                        {{$t('task.goal')}}
                    </div>
                    <div>
                        {{ objectives }}
                    </div>
                </div>

                <!-- Key results -->
                <div 
                    v-if="keyResults"
                    class="sidebar_item">
                    <div class="mb-1 opacity-60">
                        {{$t('task.key_results')}}
                    </div>
                    <div>
                        {{ keyResults }}
                    </div>
                </div>
                
                <!-- Related objects -->
                <div 
                    v-if="task.reason && task.reason.type"
                    class="sidebar_item">
                    <div class="mb-1 opacity-60">
                        {{$t('task.related_objects')}}
                    </div>
                    <span v-if="task.reason.type === 'chat.MessageModel'" class="cursor-pointer blue_color" style="word-break: break-word;" @click="openMessage(task.reason)">
                        {{ $t('task.chat_message_reason') }}
                    </span>
                    <span v-if="task.reason.type === 'help_desk.HelpDeskTicketModel'" class="cursor-pointer blue_color" style="word-break: break-word;" @click="openTicket(task.reason.id)">
                        #{{ task.reason.number }} {{ task.reason.name }}
                    </span>
                    <template v-if="task.reason.type === 'comments.CommentModel'" >
                        <span 
                            class="cursor-pointer blue_color" 
                            style="word-break: break-word;"
                            @click="commentVisible = true">
                            {{ $t('task.comment') }}
                        </span>
                        <a-modal
                            :title="$t('task.comment')"
                            :visible="commentVisible"
                            @cancel="commentVisible = false">
                            <component 
                                :is="commentComponent" 
                                :user="user"
                                useShare
                                related_object="reason"
                                :item="task.reason" />
                            <template #footer>
                                <a-button size="large" ghost block type="ui" @click="commentVisible = false">
                                    {{ $t('close') }}
                                </a-button>
                            </template>
                        </a-modal>
                    </template>
                </div>

                <!-- Creation date -->
                <div 
                    v-if="asideSetting.showCreated" 
                    class="sidebar_item">
                    <div class="mb-1 opacity-60">
                        {{$t('task.created')}}
                    </div>
                    <div>{{$moment(task.created_at).format($t('task.date_format'))}}</div>
                </div>
                
                <!-- Start plan date -->
                <div 
                    v-if="asideSetting.date_start_plan && task.date_start_plan" 
                    class="sidebar_item">
                    <div class="mb-1 opacity-60">
                        {{ asideSetting.date_start_plan.label }}
                    </div>
                    <div>{{$moment(task.date_start_plan).format($t('task.date_format'))}}</div>
                </div>

                <!-- Start fact date -->
                <div 
                    v-if="task.date_start_fact" 
                    class="sidebar_item">
                    <div class="mb-1 opacity-60">
                        {{$t('task.date_start_fact')}}
                    </div>
                    <div>{{$moment(task.date_start_fact).format($t('task.date_format'))}}</div>
                </div>
                
                <div 
                    v-if="asideSetting.showDeadline" 
                    class="sidebar_item">
                    <div class="mb-1 opacity-60">
                        {{$t('task.dead_line')}}
                    </div>
                    <DeadLine 
                        :taskStatus="task.status" 
                        :date="task.dead_line" />
                </div>
                <div 
                    v-if="asideSetting.showPriority" 
                    class="sidebar_item">
                    <div class="mb-1 opacity-60">
                        {{$t('task.priority')}}
                    </div>
                    <div class="flex items-center">
                        <a-badge :color="priorityCheck.color" />
                        {{priorityCheck.name}}
                    </div>
                </div>

                <div 
                    v-if="task.funds && task.funds !== '0.00'" 
                    class="sidebar_item">
                    <div class="mb-1 opacity-60">
                        {{$t('task.cost')}}
                    </div>
                    <div class="flex items-center">
                        {{ task.funds }}
                    </div>
                </div>

                <div 
                    v-if="task.execution_time_plan && task.execution_time_plan !== '0.0'" 
                    class="sidebar_item">
                    <div class="mb-1 opacity-60">
                        {{$t('task.execution_time_plan')}}
                    </div>
                    <div class="flex items-center">
                        {{ task.execution_time_plan }}
                    </div>
                </div>

                <div 
                    v-if="task.contractor"
                    class="sidebar_item">
                    <div class="mb-1 opacity-60">
                        {{$t('task.contractor')}}
                    </div>
                    <span class="flex items-center">
                        {{task.contractor.name }}
                    </span>
                    <div v-if="task.contact_person" class="mt-1">
                        <Profiler 
                            :user="task.contact_person" 
                            initStatus
                            :getPopupContainer="trigger => trigger.parentNode"
                            :subtitle="{ text: $t('task.contact_user') }" />
                    </div>            
                </div>
                <div 
                    v-if="task.potential_contractor" 
                    class="sidebar_item">
                    <div class="mb-1 opacity-60">
                        {{$t('task.potential_contractor')}}
                    </div>
                    <span class="flex items-center">
                        {{task.potential_contractor.name}}
                    </span>
                </div>
                <div 
                    v-if="task.potential_contractor && task.potential_contractor.company_name" 
                    class="sidebar_item">
                    <div class="mb-1 opacity-60">
                        {{$t('task.potential_contractor_company_name')}}
                    </div>
                    <span class="flex items-center">
                        {{task.potential_contractor.company_name}}
                    </span>
                </div>
                <div 
                    v-if="task.potential_contractor && task.potential_contractor.business_region_name" 
                    class="sidebar_item">
                    <div class="mb-1 opacity-60">
                        {{$t('task.potential_contractor_region_name')}}
                    </div>
                    <span class="flex items-center">
                        {{task.potential_contractor.business_region_name}}
                    </span>
                </div>
                <div 
                    v-if="task.potential_contractor && task.potential_contractor.phone" 
                    class="sidebar_item">
                    <div class="mb-1 opacity-60">
                        {{$t('task.task_phone')}}
                    </div>
                    <span class="flex items-center">
                        <a :href="'tel:' + task.potential_contractor.phone">{{ task.potential_contractor.phone }}</a>
                    </span>
                </div>
                <div 
                    v-if="task.potential_contractor && task.potential_contractor.email" 
                    class="sidebar_item">
                    <div class="mb-1 opacity-60">
                        {{$t('task.email')}}
                    </div>
                    <span class="flex items-center">
                        <a :href="'mailto:' + task.potential_contractor.email">{{ task.potential_contractor.email }}</a>
                    </span>
                </div>
                <div 
                    v-if="asideSetting.owner" 
                    class="sidebar_item">
                    <div>
                        <Profiler 
                            :user="task.owner" 
                            initStatus
                            :getPopupContainer="trigger => trigger.parentNode"
                            :subtitle="{text: asideSetting.owner ? asideSetting.owner.label : $t('task.owner'), wrapClass: 'opacity-60'}" />
                    </div>
                </div>
                <div 
                    v-if="asideSetting.operator" 
                    class="sidebar_item">
                    <div>
                        <template v-if="user && task.is_auction">
                            <div class="text-gray mb-1">
                                {{ asideSetting.operator ? asideSetting.operator.label : $t('task.operator') }}
                            </div>
                            <a-popconfirm
                                :title="$t('task.handler.confirmTakeTask')"
                                :ok-text="$t('task.yes')"
                                :cancel-text="$t('task.no')"
                                @confirm="takeTask(task)">
                                <a-button
                                    type="primary"
                                    ghost
                                    class="flex items-center"
                                    :loading="takeLoader">
                                    <i class="fi fi-rr-user-add mr-2"></i>
                                    {{ $t('task.handler.ok') }}
                                </a-button>
                            </a-popconfirm>
                        </template>
                        <Profiler
                            v-else 
                            :user="task.operator" 
                            initStatus
                            :getPopupContainer="trigger => trigger.parentNode"
                            :subtitle="{
                                text: asideSetting.operator ? asideSetting.operator.label : $t('task.operator'), 
                                wrapClass: 'opacity-60'
                            }" />
                        <UserDrawer
                            v-if="canUpdateOperator && !task.is_auction"
                            :id="`task_operator_${task.id}`"
                            :value="editableOperator"
                            :taskId="task.id"
                            class="role_change_button"
                            buttonMode
                            buttonType="link"
                            buttonSize="small"
                            :buttonText="$t('task.change')"
                            :title="$t('task.select_performer')"
                            @input="onSingleRoleChange('operator', $event)" />
                    </div>
                </div>
                <!-- TODO: asideSetting.cooperators && task.cooperators.length -->
                <div class="sidebar_item" v-if="showCooperators">
                    <div 
                        v-for="cooperator in task.cooperators" 
                        :key="cooperator.id" 
                        class="visor_item">
                        <Profiler 
                            :user="cooperator.user"
                            initStatus
                            :getPopupContainer="trigger => trigger.parentNode"
                            :subtitle="{
                                text: asideSetting.cooperators ? asideSetting.cooperators.label : $t('Cooperator'),
                                wrapClass: 'opacity-60'
                            }" />
                        <div v-if="!task.is_sign_task" class="mt-2">
                            <template v-if="isOperator || isAuthor || (user.id === cooperator?.user?.id)">
                                <StatusesDropdown :item="task" :cooperator="cooperator">
                                </StatusesDropdown>
                            </template>
                            <template v-else>
                                <div>
                                    {{ $t('Status') }}: 
                                    <TypographyText :color="cooperator.status.color" underline class="ml-1">
                                        {{ cooperator.status.name }}
                                    </TypographyText>
                                </div>
                            </template>
                        </div>
                    </div>
                    <UserDrawer
                        v-if="canEditTaskUsers"
                        :id="`task_cooperators_${task.id}`"
                        :value="editableCooperators"
                        :taskId="task.id"
                        class="role_change_button"
                        multiple
                        buttonMode
                        buttonType="link"
                        buttonSize="small"
                        :buttonText="cooperatorsButtonText"
                        :buttonLoading="usersLoading.cooperators"
                        :title="$t('task.select_cooperators')"
                        @input="onMultipleRoleChange('cooperators', $event)" />
                </div>
                <div 
                    v-if="showVisors" 
                    class="sidebar_item">
                    <div 
                        v-for="user in task.visors" 
                        :key="user.id" 
                        class="visor_item">
                        <Profiler 
                            :user="user"
                            initStatus
                            :getPopupContainer="trigger => trigger.parentNode"
                            :subtitle="{
                                text: asideSetting.visors ? asideSetting.visors.label : $t('task.visor'),
                                wrapClass: 'opacity-60'
                            }" />
                    </div>
                    <UserDrawer
                        v-if="canEditTaskUsers"
                        :id="`task_visors_${task.id}`"
                        :value="editableVisors"
                        :taskId="task.id"
                        class="role_change_button"
                        multiple
                        buttonMode
                        buttonType="link"
                        buttonSize="small"
                        :buttonText="visorsButtonText"
                        :buttonLoading="usersLoading.visors"
                        :title="$t('task.select_observers')"
                        @input="onMultipleRoleChange('visors', $event)" />
                </div>
                <div 
                    v-if="task.owner && task.author && task.author.id !== task.owner.id" 
                    class="sidebar_item">
                    <div>
                        <Profiler 
                            :user="task.author" 
                            initStatus
                            :getPopupContainer="trigger => trigger.parentNode"
                            :subtitle="{text: $t('task.author'), wrapClass: 'opacity-60'}" />
                    </div>
                </div>
            </div>
            
            <StatSwitch 
                v-for="stat in asideStat" 
                :key="stat.key"
                class="aside_item"
                :task="task"
                :stat="stat" />

            <MeetingInviteModal
                :visible="inviteModalVisible"
                :users="taskUsers"
                :loading="meetingLoading"
                @cancel="inviteModalVisible = false"
                @invite="inviteAndStartMeeting" />
        </template>
        <template v-else>
            <a-skeleton 
                active 
                avatar 
                :paragraph="{ rows: 4 }" />
            <a-skeleton 
                active 
                avatar 
                :paragraph="{ rows: 4 }" />
        </template>
    </div>
</template>

<script>
import taskHandler from '../mixins/taskHandler.js'
import {priorityList} from '../../utils'
import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'
import { errorHandler } from '@/utils/index.js'
export default {
    mixins: [
        taskHandler
    ],
    components: {
        DeadLine: () => import('../DeadLine'),
        TaskStatus: () => import('../TaskStatus'),
        TaskTimer: () => import('./TaskTimer.vue'),
        StatSwitch: () => import('./StatWidgets/StatSwitch.vue'),
        StatusesDropdown: () => import('../TaskActions/StatusesDropdown.vue'),
        TypographyText: () => import('@apps/UIModules/TypographyText.vue'),
        Blockers: () => import('../../components/Blockers.vue'),
        MeetingInviteModal: () => import('./MeetingInviteModal.vue'),
        UserDrawer: () => import('@apps/DrawerSelect/index.vue')
    },
    props: {
        dropActions: {
            type: Object,
            default: () => null
        },
        task: {
            type: Object,
            default: () => null
        },
        closeDrawerHan: {
            type: Function,
            default: () => {}
        },
        closeDrawer: {
            type: Function,
            default: () => {}
        },
        isMobile: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            commentVisible: false,
            priorityList,
            loading: false,
            sprintLoader: false,
            meetingLoading: false,
            inviteModalVisible: false,
            editableOperator: null,
            editableCooperators: [],
            editableVisors: [],
            usersLoading: {
                operator: false,
                cooperators: false,
                visors: false
            }
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user,
        }),
        commentComponent() {
            if(this.commentVisible)
                return () => import('@apps/vue2CommentsComponent/CommentItem.vue')
            return null
        },
        meetingStatus() {
            if(this.task.meeting)
                return () => import('@apps/vue2MeetingComponent/components/Status.vue')
            return null
        },
        objectives() {
            if (this.task?.key_results?.length) {
                return this.task.key_results
                    .filter(result => result.objective)
                    .map(result => result.objective.objective)
                    .join(', ')
            }
            return null
        },
        keyResults() {
            if (this.task?.key_results?.length) {
                return this.task.key_results
                    .map(result => result.description)
                    .join(', ')
            }
            return null
        },
        isAuthor() {
            return this.task?.owner?.id === this.user.id
        },
        isOperator() {
            return this.task?.operator?.id === this.user.id
        },
        sprintOpen() {
            const query = this.$route.query
            if(query?.sprint)
                return true
            return false
        },
        groupOpen() {
            const query = this.$route.query
            if(query?.viewGroup || query?.sprint) {
                return true
            }
            return false
        },
        projectOpen() {
            const query = this.$route.query
            if(query?.viewProject || query?.sprint) {
                return true
            }
            return false
        },
        asideSetting() {
            return this.task.aside_settings ? this.task.aside_settings : null 
        },
        priorityCheck() {
            const find = this.priorityList.find(item => item.value === this.task.priority)
            if(find)
                return find
            else
                return null
        },
        asideStat() {
            if(this.task.statWidgets?.length)
                return this.task.statWidgets
            else
                return []
        },
        canUpdateOperator() {
            return this.canEditTaskUsers
        },
        canEditTaskUsers() {
            return this.actionAvailable('edit') && !this.task?.is_sign_task
        },
        canEditCooperators() {
            return this.canEditTaskUsers && !['stage', 'milestone'].includes(this.task?.task_type)
        },
        hasCooperators() {
            return !!this.task?.cooperators?.length
        },
        hasVisors() {
            return !!this.task?.visors?.length
        },
        cooperatorsButtonText() {
            return this.hasCooperators ? this.$t('task.change') : this.$t('task.add_cooperators')
        },
        visorsButtonText() {
            return this.hasVisors ? this.$t('task.change') : this.$t('task.add_observers')
        },
        showCooperators() {
            return !!(this.hasCooperators || this.canEditCooperators)
        },
        showVisors() {
            return !!(this.asideSetting?.visors && (this.hasVisors || this.canEditTaskUsers))
        },
        taskUsers() {
            const list = []

            const pushUser = user => {
                if (user && user.id) list.push(user)
            }

            pushUser(this.task?.author)
            pushUser(this.task?.operator)
            pushUser(this.task?.owner)

            if (Array.isArray(this.task?.visors)) {
                this.task.visors.forEach(pushUser)
            }

            if (Array.isArray(this.task?.cooperators)) {
                this.task.cooperators.forEach(item => {
                    if (item?.user) pushUser(item.user)
                    else pushUser(item)
                })
            }

            const uniq = new Map()
            list.forEach(u => {
                const key = String(u.id)
                if (!uniq.has(key)) uniq.set(key, u)
            })

            const currentUserId = this.user?.id

            return Array
                .from(uniq.values())
                .filter(u => String(u.id) !== String(currentUserId))
        },
        user() {
            return this.$store.state.user.user
        }
    },
    watch: {
        task: {
            immediate: true,
            deep: true,
            handler() {
                this.syncEditableUsers()
            }
        }
    },
    methods: {
        actionAvailable(key) {
            const action = this.dropActions?.[key]
            if (!action) return false
            if (typeof action === 'boolean') return action
            return !!action.availability
        },
        syncEditableUsers() {
            this.editableOperator = this.task?.operator || null
            this.editableVisors = Array.isArray(this.task?.visors) ? [...this.task.visors] : []
            this.editableCooperators = Array.isArray(this.task?.cooperators)
                ? this.task.cooperators.map(item => item?.user || item).filter(Boolean)
                : []
        },
        idsFromUsers(users = []) {
            return users
                .map(user => user?.id)
                .filter(id => id !== undefined && id !== null)
        },
        async onSingleRoleChange(field, user) {
            if (!user?.id || this.usersLoading[field]) return

            const oldValue = this.task?.operator
            this.$set(this.usersLoading, field, true)

            try {
                const { data } = await this.$http.patch(`/tasks/task/${this.task.id}/update/`, { [field]: user.id })

                if (data) {
                    this.applyTaskUpdate(data)
                    this.$message.success(this.$t('task.task_updated'))
                }
            } catch(error) {
                if (field === 'operator') this.editableOperator = oldValue || null
                errorHandler({error})
            } finally {
                this.$set(this.usersLoading, field, false)
            }
        },
        async onMultipleRoleChange(field, users = []) {
            if (this.usersLoading[field]) return

            const oldValue = field === 'cooperators'
                ? [...this.editableCooperators]
                : [...this.editableVisors]
            this.$set(this.usersLoading, field, true)

            try {
                const payload = {
                    [field]: this.idsFromUsers(users)
                }
                const { data } = await this.$http.patch(`/tasks/task/${this.task.id}/update/`, payload)

                if (data) {
                    this.applyTaskUpdate(data)
                    this.$message.success(this.$t('task.task_updated'))
                }
            } catch(error) {
                if (field === 'cooperators') this.editableCooperators = oldValue
                if (field === 'visors') this.editableVisors = oldValue
                errorHandler({error})
            } finally {
                this.$set(this.usersLoading, field, false)
            }
        },
        applyTaskUpdate(task) {
            this.$store.commit('task/UPDATE_TASK', task)

            if (this.$store.hasModule('workplan')) {
                this.$store.dispatch('workplan/updateItem', {
                    item: task,
                    list: 'taskList'
                })
            }

            eventBus.$emit(`task_update_actions_${task.id}`)
            eventBus.$emit('update_task_data')
            eventBus.$emit('update_task_data_inject')
            eventBus.$emit('update_task_data_detail')
            eventBus.$emit('update_task_data_detail_inject')
        },
        openMeetingInviteModal() {
            if (this.task?.meeting?.status === 'online') {
                this.joinMeeting()
                return
            }
            if (!this.taskUsers.length) {
                this.startMeeting()
                return
            }
            this.inviteModalVisible = true
        },
        joinMeeting() {
            if (this.task?.meeting?.url) {
                window.open(this.task.meeting.url, '_blank', 'noopener,noreferrer');
            }
        },
        async inviteAndStartMeeting(notifyUserIds = []) {
            this.inviteModalVisible = false
            await this.startMeetingWithNotifyUsers(notifyUserIds)
        },
        async startMeetingWithNotifyUsers(notifyUserIds = []) {
            try {
                this.meetingLoading = true
                const payload = {
                    notify_user_ids: notifyUserIds
                }

                const { data } = await this.$http.post(`meetings/start-related/?related_object=${this.task.id}`, payload)
                this.$store.commit('task/TASK_CHANGE_FIELD', { key: 'meeting', value: data, task: this.task })
                window.open(data.url, '_blank', 'noopener,noreferrer');
            } catch(error) {
                errorHandler({error})
            } finally {
                this.meetingLoading = false
            }
        },
        openMeeting() {
            const query = JSON.parse(JSON.stringify(this.$route.query))
            if(!query?.meeting) {
                query.meeting = this.task.meeting.id
                this.$router.push({query})
            }
        },
        copyMeeting() {
            navigator.clipboard.writeText(this.task.meeting.url_external)
                .then(() => {
                    this.$message.success(this.$t('link_succes_copy'))
                })
                .catch(error => {
                    console.error(error)
                    this.$message.error(this.$t('copy_link_error'))
                })
        },
        async startMeeting() {
            try {
                this.meetingLoading = true
                const params = {related_object: this.task.id}
                const { data } = await this.$http.get('meetings/start-related/', { params })
                this.$store.commit('task/TASK_CHANGE_FIELD', { key: 'meeting', value: data, task: this.task })
                window.open(data.url, '_blank', 'noopener,noreferrer');
            } catch(error) {
                errorHandler({error})
            } finally {
                this.meetingLoading = false
            }
        },
        openMessage(message) {
            this.closeDrawerHan()
            setTimeout(() => {
                const chatId = message.chat
                const parseQuery = {
                    chat_id: chatId,
                    message_id: message.message_uid
                }
                if(this.isMobile)
                    delete message.chat
                if(this.$route.name === 'chat' && !this.isMobile) {
                    if(this.$route.query?.chat_id) {
                        if(this.$route.query?.chat_id === message.chat) {
                            const oQuery = JSON.parse(JSON.stringify(this.$route.query))
                            oQuery.message_id = message.message_uid
                            this.$router.replace({ query: oQuery })
                                .then(() => {
                                    eventBus.$emit('CHAT_SEARCH_USER_TAGS')
                                })
                        } else {
                            const oQuery = JSON.parse(JSON.stringify({
                                ...this.$route.query,
                                ...parseQuery
                            }))
                            this.$router.replace({ query: oQuery })
                                .then(() => {
                                    eventBus.$emit('CHAT_SEARCH_SELECT_CHAT')
                                })
                        }
                    } else {
                        const oQuery = JSON.parse(JSON.stringify({
                            ...this.$route.query,
                            ...parseQuery
                        }))
                        this.$router.replace({ query: oQuery })
                            .then(() => {
                                eventBus.$emit('CHAT_SEARCH_SELECT_CHAT')
                            })
                    }
                } else {
                    if(this.isMobile)
                        this.$router.push({ name: 'chat-body', params: { id: chatId }, query: parseQuery }).catch(e => {})
                    else
                        this.$router.push({ name: 'chat', query: parseQuery }).catch(e => {})
                }
            }, 500)
        },
        openTicket(id) {
            const query = this.$route.query
            this.$router.replace({ query: { ...query, ticketView: id }})
        },
        async removeToSprint() {
            try {
                this.sprintLoader = true
                const { data } = await this.$http.put(`tasks/task/${this.task.id}/set_sprint/`, {
                    sprint: null
                })
                if(data) { 
                    eventBus.$emit(`task_update_actions_${this.task.id}`)
                    eventBus.$emit('update_task_data')
                    eventBus.$emit('update_task_data_inject')
                    eventBus.$emit('update_task_data_detail')
                    eventBus.$emit('update_task_data_detail_inject')
                    this.$message.success(this.$t('task.task_removed_from_sprint'))
                }
            } catch(error) {
                errorHandler({error})
            } finally {
                this.sprintLoader = false
            }
        },
        async openSprint(id) {
            if(this.$route.query?.sprint) {
                const query = JSON.parse(JSON.stringify(this.$route.query))
                delete query.sprint
                this.$router.replace({query})
                await new Promise(resolve => setTimeout(resolve, 300))
            }
            this.closeDrawer({sprint: id})
        },
        async openProject(type, item) {
            if(this.$route.query?.viewProject) {
                const query = JSON.parse(JSON.stringify(this.$route.query))
                delete query.viewProject
                this.$router.replace({query})
                await new Promise(resolve => setTimeout(resolve, 300))
            }
            this.closeDrawer({[type]: item.id})
        },
        async openWorkgroup(type, item) {
            if(this.$route.query?.viewGroup) {
                const query = JSON.parse(JSON.stringify(this.$route.query))
                delete query.viewGroup
                this.$router.replace({query})
                await new Promise(resolve => setTimeout(resolve, 300))
            }
            this.closeDrawer({[type]: item.id})
        },
        workgroupLogoPath(workgroup) {
            return workgroup?.workgroup_logo?.path || ''
        }
    }
}
</script>

<style lang="scss" scoped>
.task_sidebar_wrapper{
    color: #000;
}
.aside_item{
    &:not(:last-child){
        margin-bottom: 15px;
    }
    .text-gray{
        color: var(--gray);
        font-size: 12px;
    }
}
::v-deep .role_change_button{
    .ant-btn-link{
        padding-left: 0;
        padding-right: 0;
    }
}


@keyframes pulse-red {
  0% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(255, 82, 82, 0.7);
  }
  
  70% {
    transform: scale(1);
    box-shadow: 0 0 0 10px rgba(255, 82, 82, 0);
  }
  
  100% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(255, 82, 82, 0);
  }
}
::v-deep .blob{
    display: inline-block;
    border-radius: 50%;
    height: 8px;
    width: 8px;
    transform: scale(1);
    background: rgba(255, 82, 82, 1);
    box-shadow: 0 0 0 0 rgba(255, 82, 82, 1);
    animation: pulse-red 2s infinite;
}
</style>
