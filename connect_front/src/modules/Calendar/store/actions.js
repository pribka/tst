import moment from 'moment'
import axios from '@/config/axios'
import eventBus from '@/utils/eventBus'

export default {
    getEvents({ commit }, {start, end, activeType}) {
        return new Promise((resolve, reject) => {
            const startDate = moment(start).add(-1, 'days').toISOString(),
                endDate = moment(end).toISOString()

            axios.get('/calendars/events/', {
                params: {
                    start: startDate,
                    end: endDate
                }
            })
                .then(({ data }) => {
                    if(data) {
                        commit('SET_EVENTS', data)
                    }
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    changeEventDate({ commit, state }, cEvent) {
        return new Promise((resolve, reject) => {
            const { event } = cEvent
            const start_at = moment(event.start).toISOString()
            let end_at = moment(event.end).toISOString()
            if(state.activeType === 'timeGridDay') {
                if(!end_at) {
                    end_at = moment(start_at).add(30, 'minutes').toISOString()
                }
            }
            if(state.activeType === 'timeGridWeek') {
                if(!end_at) {
                    end_at = moment(start_at).add(1, 'hours').toISOString()
                }
            }
            if(state.activeType === 'dayGridMonth') {
                if(!end_at && moment(event.start).format('HH:mm') === '00:00') {
                    end_at = moment(event.start).set('hour', 23).set('minute', 59).set('second', 59).toISOString()
                }
            }

            axios.patch(`/calendars/events/${event.id}/`, {
                start_at,
                end_at,
                all_day: event.allDay
            })
                .then(({ data }) => {
                    const newData = {...data}
                    if(event?.extendedProps?.meeting)
                        newData.meeting = event.extendedProps.meeting
                    eventBus.$emit('edit_event', newData)
                    resolve(newData)
                })
                .catch((error) => { reject(error) })
        })
    }
}