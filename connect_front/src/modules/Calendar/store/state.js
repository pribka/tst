import store from '@/store'
const initActiveState = () => {
    const localType = localStorage.getItem('cType')
    if(localType) {
        if(store.state.isMobile) {
            if(localType === 'multiMonthYear')
                return 'timeGridDay'
            if(localType === 'dayGridMonth')
                return 'timeGridDay'
        } else {
            if(localType === 'multiMonthYear')
                return 'dayGridMonth'
        }
        return localType
    }
    return 'dayGridMonth'
}

export default () => ({
    events: [],
    activeType: initActiveState(),
    eventDrawerZIndex: 1000
})