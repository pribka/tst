export function getChatSharePreviewText(share, t, toPlainAndTrim = value => String(value || '')) {
    if (!share || typeof share !== 'object' || typeof t !== 'function') {
        return ''
    }

    const shareName = String(share.name || '').trim()
    const shareCounter = String(share.counter || '').trim()

    if (share.type === 'tasks.TaskModel') {
        return `${t('chat.task2')}${shareCounter ? `: #${shareCounter}` : ''}${shareName ? ` ${shareName}` : ''}`.trim()
    }

    if (share.type === 'comments.CommentModel' || share.type === 'comments') {
        return t('chat.comment2', { text: toPlainAndTrim(share.text, 100) })
    }

    if (share.type === 'meetings.PlannedMeetingModel') {
        return t('chat.meeting2', { name: shareName })
    }

    if (share.type === 'workgroups.WorkgroupModel' || share.type === 'workgroups.WorkGroupModel') {
        return share.is_project
            ? t('chat.project2', { name: shareName })
            : t('chat.team', { name: shareName })
    }

    if (share.type === 'tasks.TaskSprintModel') {
        return t('chat.sprint2', { name: shareName })
    }

    if (share.type === 'event_calendar.EventCalendarModel' || share.type === 'event') {
        return t('chat.event2', { name: shareName })
    }

    if (share.type === 'crm.GoodsOrderModel') {
        return t('chat.order2', { counter: shareCounter })
    }

    if (share.type === 'tickets.TicketModel') {
        return t('chat.ticket2', { name: share?.config_1c?.name || shareName })
    }

    return share.model ? t(share.model) : ''
}
