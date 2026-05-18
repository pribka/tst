<template>
    <div class="task_card rounded-lg select-none" :class="[collapse && 'task_card_open', useInject && 'bg_invert']">
        <div class="task_card__wrapper cursor-pointer md:flex md:items-center" @click="collapseTask()">
            <div v-if="!isMobile" class="mr-4">
                <a-spin :spinning="pinnedLoading" size="small">
                    <div 
                        class="focus_btn select-none"
                        :class="task.pinned && 'active'"
                        v-tippy
                        :content="task.pinned ? $t('workplan.remove_from_focus') : mainDateStatus === 'today' ? $t('workplan.add_to_my_focus') : $t('workplan.add_to_current_day_focus')"
                        @click.stop="taskPinned()">
                        <i class="fi fi-rr-flag-alt" />
                    </div>
                    <!--<div v-else class="focus_btn select-none disabled" :class="task.pinned && 'active'" @click.stop="() => {}">
                        <i class="fi fi-rr-flag-alt" />
                    </div>-->
                </a-spin>
            </div>
            <div class="w-full truncate">
                <div class="flex items-start justify-between gap-5 mb-2">
                    <div class="flex items-center truncate min-w-0" @click.stop="openTask()">
                        <StatusDropdown :task="task" :storeKey="storeKey" :popupContainer="popupContainer" />
                        <span class="font-semibold truncate task_name" :title="task.name">
                            <span style="color: rgb(136, 136, 136);">#{{task.counter}}</span> {{ task.name }}
                        </span>
                    </div>
                    <div class="card_actions gap-2 md:gap-3">
                        <component
                            :is="timerButtonComp"
                            v-if="!isMobile && timerButtonComp"
                            :task="task" />
                        <a-spin v-if="loading" size="small" />
                        <i v-else class="fi fi-rr-angle-small-down card_arrow block" style="opacity: 0.5;font-size: 16px;" />
                    </div>
                </div>
                <div class="flex items-center flex-wrap gap-x-4 gap-y-1">
                    <component :is="relatedUsersComp" :relatedUsers="task.related_users" :storeKey="storeKey" />
                    <div class="flex items-center opacity-80">
                        <i class="fi fi-rr-clock mr-1" />
                        {{ $t('workplan.in_work') }} {{ actualDurationDays }}
                    </div>
                    <div class="flex items-center opacity-80">
                        {{ $t('workplan.today_short') }}:<span class="font-semibold ml-1">{{ secondsFormat(task.duration_total_range) }}</span>
                    </div>
                    <div class="flex items-center opacity-80">
                        {{ $t('workplan.total_short') }}:<span class="font-semibold ml-1">{{ secondsFormat(task.duration_total_all) }}</span>
                    </div>
                </div>
                <div v-if="isMobile" class="task_card__mobile_actions mt-2">
                    <component
                        :is="timerButtonComp"
                        v-if="timerButtonComp"
                        :task="task" />
                    <a-spin :spinning="pinnedLoading" size="small">
                        <div 
                            class="focus_btn select-none"
                            :class="task.pinned && 'active'"
                            @click.stop="taskPinned()">
                            <i class="fi fi-rr-flag-alt" />
                        </div>
                    </a-spin>
                </div>
                <div v-if="task.blockers && task.blockers.length || showNewComments" class="flex items-center flex-wrap gap-x-3 md:gap-x-4 gap-y-2 mt-2 text-xs">
                    <transition name="slowfade" appear :duration="{ enter: 600, leave: 300 }">
                        <div v-if="showNewComments" class="flex items-center blue_color" @click.stop="openTask(true)">
                            <i class="fi fi-rr-comment-dots mr-1" />
                            {{ $t('workplan.new_comments') }}
                        </div>
                    </transition>
                    <template v-if="task.blockers && task.blockers.length">
                        <div v-for="blocker in task.blockers" :key="blocker.id" :title="blocker.name" class="flex items-center" :style="`color: ${blocker.color};`">
                            <i class="fi fi-rr-exclamation mr-1" />
                            {{ blocker.name }}
                        </div>
                    </template>
                </div>
            </div>
        </div>
        <div v-if="collapse" class="collapse_wrapper">
            <div class="collapse_wrapper__divider" />
            <component 
                :is="accountingComp" 
                :task="task" />
        </div>
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
import { declOfNum } from '@/utils/utils.js'
import { secondsFormat } from '@/utils/utils.js'
export default {
    sockets: {
        notify({ data }) {
            if (
                data?.event_type === 'new_comment_from_object'
                && data?.obj === this.task?.id
            ) {
                if (this.isCurrentTaskOpen) {
                    this.hasSocketNewComment = false
                    return
                }
                this.hasSocketNewComment = true
            }
        }
    },
    components: {
        StatusDropdown: () => import('./StatusDropdown.vue')
    },
    props: {
        task: {
            type: Object,
            required: true
        },
        storeKey: {
            type: String,
            required: true
        },
        popupContainer: {
            type: Function,
            default: () => document.body
        },
        listType: {
            type: String,
            default: 'taskList'
        },
        hideReloadList: {
            type: Function,
            default: () => {}
        },
        useInject: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        mainDateRange() {
            return this.$store.state.workplan.mainDate?.[this.storeKey] || []
        },
        mainDateStatus() {
            const startRaw = this.mainDateRange[0]
            if (!startRaw) return null

            const start = new Date(startRaw)
            if (Number.isNaN(start.getTime())) return null

            const today = new Date()

            const startDay = new Date(start.getFullYear(), start.getMonth(), start.getDate()).getTime()
            const todayDay = new Date(today.getFullYear(), today.getMonth(), today.getDate()).getTime()

            if (startDay === todayDay) return 'today'
            if (startDay < todayDay) return 'past'
            return 'future'
        },
        isMobile() { 
            return this.$store.state.isMobile
        },
        project() {
            return this.$store.state.workplan.project?.[this.storeKey] || null
        },
        workgroup() {
            return this.$store.state.workplan.workgroup?.[this.storeKey] || null
        },
        user() {
            return this.$store.state.workplan.user?.[this.storeKey] || null
        },
        isActiveFilter() {
            return this.user?.length
        },
        relatedUsersComp() {
            if(this.task.related_users?.length)
                return () => import('../RelatedUsers.vue')
            return null
        },
        actualDurationDays() {
            return `${this.task.actual_duration_days} ${declOfNum(this.task.actual_duration_days, [this.$t('workplan.day_one'), this.$t('workplan.day_few'), this.$t('workplan.day_many')])}`
        },
        myTask() {
            return this.task.is_executor || this.task.is_owner
        },
        isCurrentTaskOpen() {
            return this.$route.query?.task === this.task?.id
        },
        showNewComments() {
            return !this.isCurrentTaskOpen
                && Boolean(this.task?.has_new_comments || this.hasSocketNewComment)
        },
        collapse: {
            get() {
                return this.task.collapse || false
            },
            set(value) {
                this.$store.commit('workplan/CHANGE_COLLAPSE', {
                    storeKey: this.storeKey,
                    value,
                    item: this.task,
                    list: this.listType
                })
            }
        },
        accountingComp() {
            if(this.collapse)
                return () => import('./Accounting.vue')
            return null
        },
        timerButtonComp() {
            return () => import('./TaskTimerButton.vue')
        }
    },
    data() {
        return {
            loading: false,
            pinnedLoading: false,
            hasSocketNewComment: false
        }
    },
    watch: {
        'task.id'() {
            this.hasSocketNewComment = false
        },
        isCurrentTaskOpen(value) {
            if (value) {
                this.hasSocketNewComment = false
            }
        }
    },
    methods: {
        secondsFormat,
        async taskPinned() {
            try {
                this.pinnedLoading = true
                await this.$store.dispatch('workplan/taskPinned', {
                    storeKey: this.storeKey,
                    item: this.task,
                    list: this.listType
                })
                if(this.mainDateStatus !== 'today') {
                    if(this.task.pinned)
                        this.$message.info(this.$t('workplan.task_removed_from_focus_day'))
                    else
                        this.$message.info(this.$t('workplan.task_added_to_focus_day'))
                }
                this.hideReloadList()
            } catch(error) {
                errorHandler({error})
            } finally {
                this.pinnedLoading = false
            }
        },
        formatHours(h) {
            const num = Number(h)
            if (!num) return `0 ${this.$t('workplan.hour_short')}`

            const val = Number(num.toFixed(2))
            const days = Math.floor(val / 24)
            const rem = +(val - days * 24).toFixed(2)

            const hoursStr = String(rem).replace(/\.?0+$/, '')

            if (days > 0 && rem > 0) return `${days} ${this.$t('workplan.day_short')} ${hoursStr} ${this.$t('workplan.hour_short')}`
            if (days > 0 && rem === 0) return `${days} ${this.$t('workplan.day_short')}`
            return `${hoursStr} ${this.$t('workplan.hour_short')}`
        },
        async getActions() {
            try {
                this.loading = true
                await this.$store.dispatch('workplan/getActions', {
                    storeKey: this.storeKey,
                    item: this.task,
                    list: this.listType
                })
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                this.loading = false
            }
        },
        async collapseTask() {
            if(!this.task.actions)
                await this.getActions()
            this.collapse = !this.collapse
        },
        openTask(comment = false) {
            const query = JSON.parse(JSON.stringify(this.$route.query))
            query.task = this.task.id
            if(comment) {
                this.hasSocketNewComment = false
                this.$store.commit('workplan/TOGGLE_NEW_COMMENT', {
                    item: this.task, 
                    value: null, 
                    storeKey: this.storeKey,
                    list: this.listType
                })
                query.comment = true
            }
            this.$router.replace({query})
        }
    }
}
</script>

<style lang="scss" scoped>
.slowfade-enter-active,
.slowfade-leave-active {
  transition: opacity .4s ease, transform .4s ease;
}
.slowfade-enter,
.slowfade-leave-to {
  opacity: 0;
  transform: translateX(8px);
}
.focus_btn{
    border-radius: 50%;
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid var(--borderColor);
    cursor: pointer;
    color: #888888;
    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    &.disabled{
        cursor: not-allowed;
    }
    &.active{
        border-color: #ee560e;
        color: #ee560e;
    }
    &:not(.disabled){
        &:hover{
            border-color: #ee560e;
            color: #ee560e;
        }
    }
}
.task_name{
    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    &:hover{
        color: var(--blue);
    }
}
.collapse_wrapper{
    padding-left: 15px;
    padding-right: 15px;
    padding-bottom: 15px;
    @media (min-width: 768px) {
        padding-left: 20px;
        padding-right: 20px;
        padding-bottom: 20px;
    }
    &__divider{
        margin-bottom: 15px;
        height: 1px;
        background: #e8e8e8;
        @media (min-width: 768px) {
            margin-bottom: 20px;
        }
    }
}
.task_card{
    background: #fff;
    &__mobile_actions{
        display: flex;
        align-items: center;
        gap: 12px;
    }
    &.bg_invert{
        background: #f7f9fc;
    }
    .card_actions{
        display: flex;
        align-items: center;
        flex-shrink: 0;
    }
    .card_arrow{
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    }
    &__wrapper{
        padding: 15px;
        @media (min-width: 768px) {
            padding: 20px;
        }
    }
    &:not(:last-child){
        margin-bottom: 10px;
        @media (min-width: 768px) {
            margin-bottom: 15px;
        }
    }
    &.task_card_open{
        .card_arrow{
            transform: rotate(180deg);
        }
    }
}
</style>
