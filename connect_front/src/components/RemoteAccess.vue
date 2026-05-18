<template>
    <a-modal
        :visible="modalVisible"
        :footer="false"
        :title="$t('remote.request_for_remote_access')"
        :afterClose="afterClose"
        @cancel="closeModal">
        <template v-if="state === 'waiting'">
            <span class="text-xl">
                {{ $t('remote.waiting_for_user_response') }}
            </span>
        </template>
        <template v-else-if="state === 'no_app_request'">
            <p class="text-base mb-2">
                {{ $t('remote.web_remote_access_support_request', { requestUser }) }}
                {{ $t('remote.web_remote_access_requires_desktop_app') }}
            </p>
            <a-button block size="large" class="mb-2" @click="downloadDesktopApp">
                {{ $t('download_app') }}
            </a-button>
            <a-button block size="large" type="primary" @click="closeModal">
                {{ $t('close') }}
            </a-button>
        </template>
        <template v-else-if="state === 'no_app_response'">
            <p class="text-base mb-2">
                {{ $t('remote.web_remote_access_client_not_in_app') }}
            </p>
            <a-button block size="large" type="primary" @click="closeModal">
                {{ $t('close') }}
            </a-button>
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
            keepAlive: true,
            noAppRequestPayload: null,
        }
    },
    sockets: {
        // Принимаем запрос на подключение, если приложение не запущено
        'remote:access:request'(data) {
            if (this.$store.state.isApp) {
                return
            }

            this.requestUser = data.username || ''
            this.noAppRequestPayload = {
                chat_uid: data.chat_uid,
                initiator: data.initiator,
                state: 'no_app',
                status: false,
            }
            this.state = 'no_app_request'
            this.openModal()
        },
        // Принимаем ответ на запрос на подключение
        'remote:access:response'(data) {
            if (this.state !== 'waiting') {
                return
            }

            clearTimeout(this.requsetTimer)
            this.requsetTimer = null

            if (data.state === 'no_app') {
                this.state = 'no_app_response'
                this.openModal()
                return
            }

            if (!data.status) {
                this.$message.info(this.$t('remote.user_refused_connection'))
                this.closeModal()
                return
            }

            this.closeModal()

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
        downloadDesktopApp() {
            window.open('https://connect.gos24.kz/media/desktop/connect_gos24_desktop.exe', '_blank')
        },
        setAppMode(value) {
            this.$store.commit('SET_IS_APP', value)
        },
        startAgentConnection() {
            this.initWebSocket()
                .catch(() => null)
        },
        // Запуск VNC Client
        initWebSocket() {
            if (this.webSocket?.readyState === WebSocket.OPEN) {
                this.SET_AGENT_STATUS(REMOTE_ACCESS_AGENT_STATUSES.CONNECTED)
                this.setAppMode(true)
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
                    this.setAppMode(true)
                    resolve(socket)
                }

                socket.onclose = () => {
                    clearTimeout(this.webSocketConnectTimer)
                    if (this.webSocket === socket) {
                        this.webSocket = null
                    }
                    if (this.keepAlive) {
                        this.SET_AGENT_STATUS(REMOTE_ACCESS_AGENT_STATUSES.DISCONNECTED)
                        this.setAppMode(false)
                        this.scheduleReconnect()
                    }
                    rejectConnection(new Error('Remote access websocket closed'))
                }

                socket.onerror = () => {
                    this.SET_AGENT_STATUS(REMOTE_ACCESS_AGENT_STATUSES.DISCONNECTED)
                    this.setAppMode(false)
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
                this.setAppMode(false)
                this.$message.error(this.$t('remote.vnc_agent_is_off'))
                throw error
            }
        },

        sendVNCRequest() {
            const currentUser = this.$store.state.user.user || {}
            const payload = {
                chat_uid: this.$store.state.chat.activeChat.chat_uid,
                username: this.getMyUsername(),
                initiator: currentUser.uid || currentUser.id || null
            }
            this.state = 'waiting'
            this.openModal()
            this.$socket.client.emit('remote:access:request', payload)

            this.requsetTimer = setTimeout(() => {
                this.closeModal()
                this.$message.info(this.$t('remote.waiting_time_expired'))
            }, CONNECTION_REQUEST_TIMEOUT)
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
        },
        afterClose() {
            if (this.state === 'no_app_request' && this.noAppRequestPayload)
                this.$socket.client.emit('remote:access:response', this.noAppRequestPayload)

            if (this.state === 'no_app_request' || this.state === 'no_app_response')
                this.state = null

            this.requestUser = ''
            this.noAppRequestPayload = null
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
