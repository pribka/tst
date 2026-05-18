import moment from 'moment'
import Vue from 'vue'

export default {
    CLEAR_EVENTS(state) {
        state.events = []
    },
    ADD_EVENT(state, value) {
        const startTime = moment(value.start_at).format('HH:mm:ss'),
            endTime = moment(value.end_at).format('HH:mm:ss')

        const allDay = (startTime === '00:00:00' && endTime === '23:59:59') ? true : false

        state.events.push({
            ...value,
            allDay,
            title: value.name,
            start: value.start_at,
            end: value.end_at
        })
    },
    SET_EVENTS(state, value) {
        state.events = value.map(item => {
            const startTime = moment(item.start_at).format('HH:mm:ss'),
                endTime = moment(item.end_at).format('HH:mm:ss')

            const allDay = (startTime === '00:00:00' && endTime === '23:59:59') ? true : false

            return {
                ...item,
                allDay,
                title: item.name,
                start: item.start_at,
                end: item.end_at
            }
        })
    },
    EPDATE_EVENTS_DATE(state, value) {
        const index = state.events.findIndex(f => f.id === value.id)
        if(index !== -1) {
            Vue.set(state.events[index], 'start', value.start)
            Vue.set(state.events[index], 'end', value.end)
        }
    },
    SET_ACTIVE_TYPE(state, value) {
        state.activeType = value
        localStorage.setItem('cType', value)
    },
    SET_DRAWER_INDEX(state, value) {
        state.eventDrawerZIndex = value
    },
    SET_START_ACTIVE_TYPE(state, value) {
        state.activeType = value
    }
}