import moment from 'moment'

export const SLOT_MINUTES = 30
export const PIXELS_PER_MINUTE = 1.05
export const DEFAULT_DAY_START = 0
export const DEFAULT_DAY_END = 24 * 60

export const TYPE_META = {
    task: {
        key: 'task',
        color: '#0f766e',
        surface: '#d7fffa',
        border: '#7de2d4'
    },
    request: {
        key: 'request',
        color: '#9a3412',
        surface: '#ffe7da',
        border: '#ffc09f'
    },
    event: {
        key: 'event',
        color: '#1d4ed8',
        surface: '#dbeafe',
        border: '#93c5fd'
    }
}

export function safeMoment(value) {
    if (!value)
        return null

    const instance = moment(value)
    return instance.isValid() ? instance : null
}

export function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value))
}

export function formatClockLabel(totalMinutes) {
    const hours = String(Math.floor(totalMinutes / 60)).padStart(2, '0')
    const minutes = String(totalMinutes % 60).padStart(2, '0')
    return `${hours}:${minutes}`
}

export function roundMomentToSlot(source, slotMinutes = SLOT_MINUTES) {
    const value = moment(source)
    const roundedMinutes = Math.floor(value.minutes() / slotMinutes) * slotMinutes
    return value.clone().minutes(roundedMinutes).seconds(0).milliseconds(0)
}

export function getDefaultDurationMinutes(item) {
    if (!item)
        return 60

    if (item.startAt && item.endAt) {
        const diff = item.endAt.diff(item.startAt, 'minutes')
        return diff > 0 ? diff : 60
    }

    return 60
}

function uniqEntities(list, type) {
    const byId = new Map()

    ;(list || []).forEach(item => {
        if (!item?.id)
            return

        const key = `${type}:${item.id}`
        if (!byId.has(key))
            byId.set(key, item)
    })

    return Array.from(byId.values())
}

function getMatchedUsers(users, performerIds) {
    const source = Array.isArray(users) ? users : []
    if (!performerIds.size)
        return source

    const matched = source.filter(user => performerIds.has(String(user.id)))
    return matched.length ? matched : source
}

function toUserArray(value) {
    if (!value)
        return []

    if (Array.isArray(value))
        return value.filter(item => item && typeof item === 'object')

    return typeof value === 'object' ? [value] : []
}

function toIdArray(value) {
    if (!value)
        return []

    if (Array.isArray(value))
        return value
            .map(item => (typeof item === 'object' ? item?.id : item))
            .filter(Boolean)

    if (typeof value === 'object')
        return value.id ? [value.id] : []

    return [value]
}

function hasPerformerId(item, performerId) {
    return Array.isArray(item?.performerIds) && item.performerIds.some(id => String(id) === String(performerId))
}

function normalizeTask(task, performerIds) {
    const operatorUsers = toUserArray(task.operator)
    const operatorIds = toIdArray(task.operator)
    const sourceUsers = operatorUsers.length ? operatorUsers : task.related_users
    const relatedUsers = operatorIds.length
        ? sourceUsers.filter(user => operatorIds.some(id => String(id) === String(user?.id)))
        : getMatchedUsers(sourceUsers, performerIds)
    const normalizedPerformerIds = operatorIds.length
        ? operatorIds
        : relatedUsers.map(user => user.id)

    return {
        uid: `task:${task.id}`,
        id: task.id,
        entityType: 'task',
        name: task.name || task.counter || 'Task',
        raw: task,
        performerIds: normalizedPerformerIds,
        relatedUsers,
        primaryPerformerId: normalizedPerformerIds[0] || relatedUsers[0]?.id || null,
        startAt: safeMoment(task.date_start_plan),
        endAt: safeMoment(task.dead_line),
        allDay: false,
        meta: TYPE_META.task
    }
}

function normalizeRequest(ticket) {
    const specialistUsers = toUserArray(ticket.specialist)
    const specialistIds = specialistUsers.length
        ? specialistUsers.map(user => user.id)
        : toIdArray(ticket.specialist)
    const startAt = safeMoment(ticket.start_date || ticket.receipt_date)
    const endAt = safeMoment(ticket.end_date || ticket.dead_line)

    return {
        uid: `request:${ticket.id}`,
        id: ticket.id,
        entityType: 'request',
        name: ticket.name || ticket.number || 'Request',
        raw: ticket,
        performerIds: specialistIds,
        relatedUsers: specialistUsers,
        primaryPerformerId: specialistIds[0] || specialistUsers[0]?.id || null,
        startAt,
        endAt,
        allDay: false,
        meta: TYPE_META.request
    }
}

function normalizeEvent(event, performerIds) {
    const memberUsers = toUserArray(event.members)
    const memberIds = toIdArray(event.members)
    const sourceUsers = memberUsers.length ? memberUsers : event.related_users
    const relatedUsers = memberIds.length
        ? sourceUsers.filter(user => memberIds.some(id => String(id) === String(user?.id)))
        : getMatchedUsers(sourceUsers, performerIds)
    const normalizedPerformerIds = memberIds.length
        ? memberIds
        : relatedUsers.map(user => user.id)

    return {
        uid: `event:${event.id}`,
        id: event.id,
        entityType: 'event',
        name: event.name || 'Event',
        raw: event,
        performerIds: normalizedPerformerIds,
        relatedUsers,
        primaryPerformerId: normalizedPerformerIds[0] || relatedUsers[0]?.id || null,
        startAt: safeMoment(event.start_at),
        endAt: safeMoment(event.end_at),
        allDay: Boolean(event.all_day),
        meta: TYPE_META.event
    }
}

export function buildPlannerItems({
    tasks = [],
    tickets = [],
    events = [],
    performers = [],
    rangeStart,
    rangeEnd
}) {
    const performerIds = new Set((performers || []).map(user => String(user.id)))
    const normalized = []

    uniqEntities(tasks, 'task').forEach(task => normalized.push(normalizeTask(task, performerIds)))
    uniqEntities(tickets, 'request').forEach(ticket => normalized.push(normalizeRequest(ticket)))
    uniqEntities(events, 'event').forEach(event => normalized.push(normalizeEvent(event, performerIds)))

    return normalized.map(item => {
        const hasPerformer = Array.isArray(item.performerIds) && item.performerIds.length > 0
        const hasRange = Boolean(item.startAt && item.endAt)
        const overlapsRange = hasRange
            ? item.startAt.isBefore(rangeEnd) && item.endAt.isAfter(rangeStart)
            : false
        const isScheduled = hasPerformer && hasRange && !item.allDay && overlapsRange

        return {
            ...item,
            hasPerformer,
            hasRange,
            overlapsRange,
            isScheduled
        }
    })
}

function overlaps(a, b) {
    return a.startMinute < b.endMinute && b.startMinute < a.endMinute
}

export function buildDayLayouts(items = [], performerId, dayStart, dayEnd) {
    const layouts = []

    const dayItems = items
        .filter(item => hasPerformerId(item, performerId))
        .filter(item => item.startAt && item.endAt)
        .map(item => {
            const startMinute = clamp(item.startAt.diff(dayStart, 'minutes'), 0, DEFAULT_DAY_END - DEFAULT_DAY_START)
            const endMinute = clamp(item.endAt.diff(dayStart, 'minutes'), 0, DEFAULT_DAY_END - DEFAULT_DAY_START)
            const safeEndMinute = Math.max(endMinute, startMinute + SLOT_MINUTES)

            return {
                item,
                performerId,
                startMinute,
                endMinute: safeEndMinute
            }
        })
        .filter(layout => layout.endMinute > 0 && layout.startMinute < dayEnd.diff(dayStart, 'minutes'))
        .sort((a, b) => a.startMinute - b.startMinute)

    const lanes = []

    dayItems.forEach(layout => {
        let laneIndex = 0

        while (typeof lanes[laneIndex] === 'number' && lanes[laneIndex] > layout.startMinute)
            laneIndex += 1

        lanes[laneIndex] = layout.endMinute
        layout.lane = laneIndex
        layout.lanes = 1
        layouts.push(layout)
    })

    layouts.forEach(layout => {
        let maxLane = layout.lane

        layouts.forEach(other => {
            if (layout === other)
                return

            if (overlaps(layout, other))
                maxLane = Math.max(maxLane, other.lane)
        })

        layout.lanes = Math.max(layout.lanes, maxLane + 1)
    })

    return layouts
}

export function buildRangeDays(items = [], performerId, selectedDate, length = 14) {
    const start = moment(selectedDate).startOf('day')

    return Array.from({ length }).map((_, index) => {
        const dayStart = start.clone().add(index, 'days')
        const dayEnd = dayStart.clone().endOf('day')

        const dayItems = items
            .filter(item => hasPerformerId(item, performerId))
            .filter(item => item.startAt && item.endAt)
            .filter(item => item.startAt.isBefore(dayEnd) && item.endAt.isAfter(dayStart))
            .sort((a, b) => a.startAt.valueOf() - b.startAt.valueOf())

        return {
            key: dayStart.format('YYYY-MM-DD'),
            date: dayStart,
            items: dayItems
        }
    })
}

export function buildFortnightDays(items = [], performerId, selectedDate) {
    return buildRangeDays(items, performerId, selectedDate, 14)
}
