import Vue from 'vue'
export default {
    SET_TICKET_LIST(state, data) {
        state.ticketList.push(...data) 
    },
    CLEAR_TICKET_LIST(state) {
        state.ticketList.splice(0)
    },
    SET_TICKETS_PAGE(state, data) {
        state.ticketsPage = data
    },
    SET_TICKET_COUNT(state, data) {
        state.ticketCount = data
    },
    SET_TICKET_NEXT(state, data) {
        state.ticketNext = data
    },
    ADD_TICKET(state, data) {
        state.ticketList.unshift(data)
    },
    UPDATE_TICKET(state, data) {
        const findedIndex = state.ticketList.findIndex(ticket => ticket.id === data.id)
        if(findedIndex !== -1) {
            state.ticketList[findedIndex] = data
            Vue.set(state.ticketList, findedIndex, data)
        }
    },
    // SET_TICKET_STATUS(state, { ticketId, data }) {
    //     const findedIndex = state.ticketList.findIndex(ticket => ticket.id === ticketId)
    //     if(findedIndex !== -1) {
    //         state.ticketList[findedIndex] = data
    //         Vue.set(state.ticketList, findedIndex, data)
    //     }
    // }
}