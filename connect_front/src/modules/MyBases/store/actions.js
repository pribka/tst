import axios from '@/config/axios'
export default {
    
    getTicketList({ commit, state }, params) {
        return new Promise((resolve, reject) => {
            axios('tickets/list/', { params })
                .then(({ data }) => {
                    commit('SET_TICKET_LIST', data.results)
                    commit('SET_TICKET_COUNT', data.count)
                    commit('SET_TICKET_NEXT', data.next)
                    
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    getTicketsPage({ commit, state }, params) {
        return new Promise((resolve, reject) => {
            axios('tickets/list/', { params })
                .then(({ data }) => {
                    commit('SET_TICKETS_PAGE', data.results)
                    commit('SET_TICKET_COUNT', data.count)
                    commit('SET_TICKET_NEXT', data.next)
                    
                    resolve(data)
                })
                .catch((error) => { reject(error) })
        })
    },
    addTicket({ commit }, form) {
        return new Promise((resolve, reject) => {
            axios.post('tickets/new_ticket/', form)
                .then(data => {
                    commit('ADD_TICKET', data.data)
                    resolve(data.data)
                })
                .catch(error => reject(error))
        })
    },
    updateTicket({ commit }, { ticketId, form }) {
        return new Promise((resolve, reject) => {
            axios.put(`tickets/ticket/${ticketId}/update/`, form)
                .then(({ data }) => {
                    commit('UPDATE_TICKET', data)
                    resolve(data)
                })
                .catch(error => reject(error))
        })
    },
    setTicketStatus({ commit }, { ticketId, isApproved }) {
        return new Promise((resolve, reject) => {
            axios.post(`tickets/ticket/${ticketId}/set_status/`, {
                approved: isApproved
            })
                .then(({ data }) => {
                    commit('UPDATE_TICKET', data)
                    resolve(data)
                })
                .catch(error => {
                    console.error(error)
                    reject(error)
                })
        })
    }

}