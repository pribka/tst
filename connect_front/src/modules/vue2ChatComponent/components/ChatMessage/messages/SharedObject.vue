<template>
    <div>
        <component v-if="isConference" :is="compConference" :messageItem="message" :message="message" />
        <component v-if="isWorkgroup" :is="compWorkgroup" :messageItem="message" :message="message" />
        <component v-if="isTask" :is="compTask" :messageItem="message" :message="message" :myMessage="myMessage" />
        <component v-if="isFile" :is="compFile" :message="message" :messageItem="message" />
        <component v-if="isComments" :is="compComments" :messageItem="message" :message="message" />
        <component v-if="isSprint" :is="compSprint" :messageItem="message" :message="message" />
        <component v-if="isOrder" :is="compOrder" :messageItem="message" :message="message" />
        <component v-if="isNews" :is="compNews" :message="message" :messageItem="message" />
        <component v-if="isEvent" :is="compEvent" :message="message" :messageItem="message" />
        <component v-if="isTicket" :is="compTicket" :message="message" :messageItem="message" />
        <component v-if="isLink" :is="compLink" :message="message" :messageItem="message" />
        <component v-if="isHelpDeskTicket" :is="compHelpDesk" :messageItem="message" :message="message" />
    </div>
</template>

<script>
export default {
    props: {
        message: {
            type: Object,
            required: true
        },
        myMessage: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        isLink() {
            return this.message?.share?.shareWidget === 'link'
        },
        isConference() {
            return this.message?.share?.type === 'meetings.PlannedMeetingModel'
        },
        isWorkgroup() {
            const t = this.message?.share?.type
            return t === 'workgroups.WorkGroupModel' || t === 'workgroups.WorkgroupModel'
        },
        isTask() {
            return this.message?.share?.type === 'tasks.TaskModel'
        },
        isFile() {
            const t = this.message?.share?.type
            return t === 'files' || t === 'common.File'
        },
        isComments() {
            const t = this.message?.share?.type
            return t === 'comments.CommentModel' || t === 'comments'
        },
        isSprint() {
            return this.message?.share?.type === 'tasks.TaskSprintModel'
        },
        isOrder() {
            return this.message?.share?.type === 'crm.GoodsOrderModel'
        },
        isNews() {
            return this.message?.share?.type === 'bpms_common.NewsModel'
        },
        isEvent() {
            return this.message?.share?.type === 'event_calendar.EventCalendarModel'
        },
        isTicket() {
            return this.message?.share?.type === 'tickets.TicketModel'
        },
        isHelpDeskTicket() {
            return this.message?.share?.type === 'help_desk.HelpDeskTicketModel'
        },
        compConference() {
            if (!this.isConference) return null
            return () => import('./Conference')
        },
        compWorkgroup() {
            if (!this.isWorkgroup) return null
            return () => import('./Workgroup')
        },
        compTask() {
            if (!this.isTask) return null
            return () => import('./Task')
        },
        compFile() {
            if (!this.isFile) return null
            return () => import('./File')
        },
        compComments() {
            if (!this.isComments) return null
            return () => import('./Comments')
        },
        compSprint() {
            if (!this.isSprint) return null
            return () => import('./Sprint')
        },
        compOrder() {
            if (!this.isOrder) return null
            return () => import('./Order')
        },
        compNews() {
            if (!this.isNews) return null
            return () => import('./SharedNews')
        },
        compEvent() {
            if (!this.isEvent) return null
            return () => import('./SharedEvent')
        },
        compTicket() {
            if (!this.isTicket) return null
            return () => import('./SharedTicket')
        },
        compLink() {
            if (!this.isLink) return null
            return () => import('./LinkCommon')
        },
        compHelpDesk() {
            if (!this.isHelpDeskTicket) return null
            return () => import('./ShareHelpDesk.vue')
        }
    }
}
</script>
