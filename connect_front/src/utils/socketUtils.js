import socket from '@/config/socket.js'
import store from "@/store"

function checkRoomConnected(roomName) {
    const find = store.state.connectedRooms.find(f => f === roomName)
    return find
}

export const socketEmitJoin = roomName => {
    if(!checkRoomConnected(roomName)) {
        store.commit('ADD_CONNECTED_ROOMS', roomName)
        socket.emit('join_universal', roomName)
    }
}

export const socketEmitLeave = roomName => {
    if(checkRoomConnected(roomName)) {
        store.commit('DELETE_CONNECTED_ROOMS', roomName)
        socket.emit('leave_universal', roomName)
    }
}