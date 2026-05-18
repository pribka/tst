export default {
    getUserStatus: state => id => {
        const find = state.onlineUsers.find(f => f === id)
        return find ? true : false
    },
    getUserOffline: state => id => {
        const find = state.offlineUser.find(f => f.id === id)
        return find || false
    },
    getUserFirstCheck: state => id => {
        const find = state.firstOnlineCheck.find(f => f === id)
        return find ? true : false
    }
}