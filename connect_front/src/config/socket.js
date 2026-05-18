import { io } from 'socket.io-client'
const socket = io(process.env.VUE_APP_SOCKET_HOST, {
    debug: true,
    reconnection: true,
    autoConnect: false,
    path: process.env.VUE_APP_SOCKET_PATH,
    transports: ["websocket", "polling"]
})
export default socket