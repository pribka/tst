export default {
    getTaskVisiblePoints: state => id => {
        if(Object.keys(state.taskPointVisible)?.length && state.taskPointVisible?.[id]) {
            return state.taskPointVisible[id]
        } else {
            return false
        }
    },
    getUserVisiblePoints: state => id => {
        if(Object.keys(state.userPointVisible)?.length && state.userPointVisible?.[id]) {
            return state.userPointVisible[id]
        } else {
            return false
        }
    }
}