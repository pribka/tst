import { mapState } from 'vuex'
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'

const CHAT_WINDOW_CACHE_KEY = 'chat-window-cache'
const EMPTY_CHAT_WINDOW_ID = '00000000-0000-0000-0000-000000000000'

export default {
    props: {
        item: {
            type: Object,
            required: true
        },
        disableNavigation: {
            type: Boolean,
            default: false
        },
        skipHoverMeta: {
            type: Boolean,
            default: false
        },
        isHovered: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            loading: false,
            asyncLoadComp: null
        }
    },
    computed: {
        ...mapState({
            primaryColor: state => state.config.primaryColor,
            routeActions: state => state.navigation.routeActions
        }),
        isAdd() {
            if(this.routeActions?.[this.item.name]?.pageActions?.add && this.item.name !== 'dashboard' && this.item.name !== 'pulse')
                return true
            return false
        },
        getCounter() {
            return this.$store.getters['navigation/getMenuCounter'](this.item.name)
        },
        isChatMenuItem() {
            return this.item.name === 'chat'
        }
    },
    methods: {
        handleLinkClick(e) {
            if (this.disableNavigation || e.target.closest('.menu_add_btn') || e.target.closest('.menu_window_btn'))
                e.preventDefault()
        },
        persistChatWindowCache() {
            if (typeof window === 'undefined') return

            try {
                const chatState = this.$store.state.chat || {}
                const payload = {
                    chatList: Array.isArray(chatState.chatList) ? chatState.chatList : [],
                    chatListNext: !!chatState.chatListNext,
                    chatListPage: Number(chatState.chatListPage || 0),
                    contactList: Array.isArray(chatState.contactList) ? chatState.contactList : [],
                    contactListNext: !!chatState.contactListNext,
                    contactListPage: Number(chatState.contactListPage || 0),
                    helpDeskList: Array.isArray(chatState.helpDeskList) ? chatState.helpDeskList : [],
                    helpDeskNext: !!chatState.helpDeskNext,
                    helpDeskPage: Number(chatState.helpDeskPage || 0),
                    chatDrafts: chatState.chatDrafts || {},
                    sidebarActiveTab: Number(chatState.sidebarActiveTab || 1),
                    savedAt: Date.now()
                }

                window.localStorage.setItem(CHAT_WINDOW_CACHE_KEY, JSON.stringify(payload))
            } catch (e) {
                // noop
            }
        },
        openEmptyChatWindow() {
            if (typeof window === 'undefined') return

            this.persistChatWindowCache()

            const routeData = this.$router.resolve({
                name: 'chat-window',
                params: { id: EMPTY_CHAT_WINDOW_ID },
                query: { open_sidebar: '1' }
            })

            const features = [
                'popup=yes',
                'width=480',
                'height=820',
                'left=120',
                'top=80',
                'menubar=no',
                'toolbar=no',
                'location=no',
                'status=no',
                'resizable=yes',
                'scrollbars=no'
            ].join(',')

            const openedWindow = window.open(routeData.href, 'chat-window-standalone', features)
            if (openedWindow) {
                openedWindow.focus()
            }
        },
        async handleAddClick() {
            if(this.item.name === 'positions') {
                try {
                    const comp = await import('@apps/HelpDesk/components/PositionFormModal.vue')
                    this.asyncLoadComp = comp.default || comp
                    await this.$nextTick()
                    if(this.$refs.loadCompRef)
                        this.$refs.loadCompRef.openModal()
                } catch(error) {
                    errorHandler({ error, show: false })
                }
            }
            if(this.item.name === 'categories') {
                try {
                    const comp = await import('@apps/HelpDesk/components/ModalCategoryCreate.vue')
                    this.asyncLoadComp = comp.default || comp
                    await this.$nextTick()
                    if(this.$refs.loadCompRef)
                        this.$refs.loadCompRef.openModal()
                } catch(error) {
                    errorHandler({ error, show: false })
                }
            }
            if(this.item.name === 'request') {
                eventBus.$emit('helpdesc_add_request_tickets')
            }
            if(this.item.name === 'tickets') {
                eventBus.$emit('helpdesc_add_tickets')
            }
            if(this.item.name === 'clients') {
                eventBus.$emit('helpdesc_add_client')
            }
            if(this.item.name === 'tasks') {
                this.$store.commit('task/SET_PAGE_NAME', {
                    pageName: 'page_list_task_task.TaskModel'
                })
                eventBus.$emit('add_task_modal', {
                    task_type: 'task'
                })
            }
            if(this.item.name === 'request-approvals') {
                eventBus.$emit('add_request_approvals')
            }
            if(this.item.name === 'sprints') {
                eventBus.$emit('add_sprint')
            }
            if(this.item.name === 'projects') {
                eventBus.$emit('add_proejct_modal')
                /*const query = {...this.$route.query}
                query.create_project = true
                this.$router.push({query})*/
            }
            if(this.item.name === 'groups') {
                eventBus.$emit('add_workgroup_modal')
            }
            if(this.item.name === 'sports-facilities') {
                eventBus.$emit('add_sports_facilities')
            }
            if(this.item.name === 'calendar') {
                eventBus.$emit('open_event_form', 
                    null, 
                    null, 
                    null, 
                    null, 
                    'default')
            }
            if(this.item.name === 'meetings') {
                this.$store.commit('meeting/SET_EDIT_MODAL', { show: true, model: 'main' })
            }
            if(this.item.name === 'okr') {
                eventBus.$emit('add_objective')
            }
        },
        async itemHover() {
            if (this.skipHoverMeta)
                return
            if (this.loading)
                return
            try {
                this.loading = true
                await this.$store.dispatch('navigation/getRouteActions', {
                    name: this.item.name
                })
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                this.loading = false
            }
        }
    }
}
