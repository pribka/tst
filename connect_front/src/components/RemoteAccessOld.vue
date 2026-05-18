<template>
    <a-modal :visible="modalVisible" :footer="false" :title="$t('remote.request_for_remote_access')" @cancel="closeModal">
        <template v-if="state === 'waiting'">
            <span class="text-xl">
                {{ $t('remote.waiting_for_user_response') }}
            </span>
        </template>
        <template v-else-if="state === 'server_choice'">
            <p class="text-xl mb-8">{{ $t('remote.request_for_remote_access_from_user') }} {{ requestUser }}</p>
            <div class="flex">
                <a-button block class="mr-4" size="large" type="primary" @click="allowRemoteAccess">
                    {{ $t('remote.allow') }}
                </a-button>
                <a-button block size="large" type="danger" ghost @click="denyButtonHandler">
                    {{ $t('remote.deny') }}
                </a-button>
            </div>
        </template>
    </a-modal>
</template>

<script>
import { mapMutations } from 'vuex'
import eventBus from '@/utils/eventBus'
import {
    CONNECTION_REQUEST_TIMEOUT,
    REMOTE_ACCESS_AGENT_STATUSES,
    REMOTE_ACCESS_RECONNECT_TIMEOUT,
    REMOTE_ACCESS_SOCKET_URL,
    VNC_CLIENT_PORT,
    VNC_SERVER_PORT,
    WEB_SOCKET_CONNECTION_TIMEOUT
} from '@/utils/remoteAccess'

export default {
    data() {
        return {
            modalVisible: false,
            state: null,
            requestUser: '',
            webSocket: null,
            webSocketConnectTimer: null,
            reconnectTimer: null,
            connectPromise: null,
            requsetTimer: null,
            chatId: null,
            keepAlive: true,
        }
    },
    sockets: {
        // Принимаем запрос на подключение
        'remote:access:request'(data) {
            this.chatId = data.chat_uid
            this.requestUser = data.username
            this.openModal()
            this.state = 'server_choice'
        },
        // Принимаем ответ на запрос на подключение
        'remote:access:response'(data) {
            if (!data.status) {
                this.$message.info(this.$t('remote.user_refused_connection'))
                this.closeModal()
                return
            }
            if (this.state === 'waiting') {
                this.state = 'connected'
                this.connectViaVNC(data)
                const url = `chat/${data.chat_uid}/connect_vnc/`
                this.$http.post(url)
                    .catch(() => null)

                this.closeModal()
            }

        },
    },
    mounted() {
        this.startAgentConnection()
        eventBus.$on('send_remote_access_request', this.requestRemoteAccess)
        window.addEventListener('focus', this.startAgentConnection)
        window.addEventListener('online', this.startAgentConnection)
    },
    beforeDestroy() {
        this.keepAlive = false
        eventBus.$off('send_remote_access_request', this.requestRemoteAccess)
        window.removeEventListener('focus', this.startAgentConnection)
        window.removeEventListener('online', this.startAgentConnection)
        clearTimeout(this.reconnectTimer)
        clearTimeout(this.webSocketConnectTimer)
        clearTimeout(this.requsetTimer)
        if (this.webSocket) {
            this.webSocket.close()
            this.webSocket = null
        }
    },
    methods: {
        ...mapMutations('remoteAccess', ['SET_AGENT_STATUS']),
        startAgentConnection() {
            this.initWebSocket()
                .catch(() => null)
        },
        // Запуск VNC Server
        runVNCServer() {
            const remoteSessionId = Math.floor(100000000 + Math.random() * 900000000)
            const VNCpayload = {
                remote_id: remoteSessionId,
                type: 1, // Сервер
                port: VNC_SERVER_PORT,
            }
            this.webSocket.send(JSON.stringify(VNCpayload));

            const payload = {
                chat_uid: this.chatId,
                status: true,
                remote_id: remoteSessionId
            }
            // Отправляем клиенту уведомление, что сервер согласен на подключение
            this.$socket.client.emit('remote:access:response', payload)
            this.state = 'connected'
            this.closeModal()
        },

        // Запуск VNC Client
        connectViaVNC(data) {
            const remoteSessionId = data.remote_id;
            const payload = {
                type: 0,
                id: remoteSessionId,
                port: VNC_CLIENT_PORT
            }

            this.webSocket.send(JSON.stringify(payload));

        },

        initWebSocket() {
            if (this.webSocket?.readyState === WebSocket.OPEN) {
                this.SET_AGENT_STATUS(REMOTE_ACCESS_AGENT_STATUSES.CONNECTED)
                return Promise.resolve(this.webSocket)
            }
            if (this.connectPromise) {
                return this.connectPromise
            }

            clearTimeout(this.reconnectTimer)
            this.SET_AGENT_STATUS(REMOTE_ACCESS_AGENT_STATUSES.CONNECTING)

            this.connectPromise = new Promise((resolve, reject) => {
                const socket = new WebSocket(REMOTE_ACCESS_SOCKET_URL)
                this.webSocket = socket

                const rejectConnection = error => {
                    if (this.connectPromise) {
                        this.connectPromise = null
                    }
                    reject(error)
                }

                this.webSocketConnectTimer = setTimeout(() => {
                    socket.close()
                    rejectConnection(new Error('Remote access websocket connection timeout'))
                }, WEB_SOCKET_CONNECTION_TIMEOUT)

                socket.onopen = () => {
                    clearTimeout(this.webSocketConnectTimer)
                    this.connectPromise = null
                    this.SET_AGENT_STATUS(REMOTE_ACCESS_AGENT_STATUSES.CONNECTED)
                    resolve(socket)
                }

                socket.onclose = () => {
                    clearTimeout(this.webSocketConnectTimer)
                    if (this.webSocket === socket) {
                        this.webSocket = null
                    }
                    if (this.keepAlive) {
                        this.SET_AGENT_STATUS(REMOTE_ACCESS_AGENT_STATUSES.DISCONNECTED)
                        this.scheduleReconnect()
                    }
                    rejectConnection(new Error('Remote access websocket closed'))
                }

                socket.onerror = () => {
                    this.SET_AGENT_STATUS(REMOTE_ACCESS_AGENT_STATUSES.DISCONNECTED)
                }
            })

            return this.connectPromise
        },

        scheduleReconnect() {
            if (!this.keepAlive || this.reconnectTimer || this.connectPromise || this.webSocket?.readyState === WebSocket.OPEN) {
                return
            }

            this.reconnectTimer = setTimeout(() => {
                this.reconnectTimer = null
                this.initWebSocket()
                    .catch(() => null)
            }, REMOTE_ACCESS_RECONNECT_TIMEOUT)
        },

        async ensureWebSocketConnection() {
            try {
                return await this.initWebSocket()
            } catch (error) {
                this.SET_AGENT_STATUS(REMOTE_ACCESS_AGENT_STATUSES.DISCONNECTED)
                this.$message.error(this.$t('remote.vnc_agent_is_off'))
                throw error
            }
        },

        sendVNCRequest() {
            const payload = {
                chat_uid: this.$store.state.chat.activeChat.chat_uid,
                username: this.getMyUsername()
            }
            this.$socket.client.emit('remote:access:request', payload)
            this.state = 'waiting'
            this.openModal()

            this.requsetTimer = setTimeout(() => {
                this.closeModal()
                this.$message.info(this.$t('remote.waiting_time_expired'))
            }, CONNECTION_REQUEST_TIMEOUT)
        },

        allowRemoteAccess() {
            this.ensureWebSocketConnection()
                .then(() => {
                    this.runVNCServer()
                })
                .catch(() => null)
        },
        denyButtonHandler() {
            this.closeModal()
        },

        denyRemoteAccess() {
            const payload = {
                chat_uid: this.chatId,
                status: false,
                remote_id: false
            }
            this.$socket.client.emit('remote:access:response', payload)
            this.$message.info(this.$t('remote.you_refused_remote_connection'))
        },



        requestRemoteAccess() {
            this.ensureWebSocketConnection()
                .then(() => {
                    this.sendVNCRequest()
                })
                .catch(() => null)
        },

        closeModal() {
            this.modalVisible = false

            clearTimeout(this.requsetTimer)

            // Если закрыли модалку когда ждали ответ на приглашение к подключению
            if (this.state === 'waiting') {
                this.state = null
            }
            // Если закрыли модалку когда пришел запрос на подключение
            if (this.state === 'server_choice') {
                this.denyRemoteAccess()
                this.state = null
            }
        },
        openModal() {
            this.modalVisible = true
        },
        getMyUsername() {
            const user = this.$store.state.user.user
            if (user) {
                if (user.full_name) {
                    return user.full_name
                }
                return `${user.last_name} ${user.first_name} ${user.middle_name}`
            }
            return ''
        },

    }
}
</script>
