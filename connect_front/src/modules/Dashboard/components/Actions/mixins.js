import eventBus from '@/utils/eventBus'
const updateKey = 'widgets_update'
import { errorHandler } from '@/utils/index.js'
export default {
    props: {
        widget: {
            type: Object,
            required: true
        },
        editNameHandler: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        widgets() {
            return this.$store.state.dashboard.widgets
        },
    },
    data() {
        return {
            loading: false,
            actions: null,
            actionLoading: false,
            visible: false
        }
    },
    methods: {
        deleteWidget() {
            this.$confirm({
                title: this.$t('dashboard.widget_delete_message'),
                cancelText: this.$t('cancel'),
                okText: this.$t('remove'),
                onOk: async () => {
                    try {
                        this.$message.loading({ content: this.$t('dashboard.updating'), key: updateKey })
                        await this.$store.dispatch('dashboard/deleteActiveWidget', { id: this.widget.id })
                        this.$message.success({ content: this.$t('dashboard.updated'), key: updateKey, duration: 2 })
                    } catch(error) {
                        errorHandler({error, key: updateKey})
                    }
                }
            })
        },
        async deleteWidgetMobile() {
            this.$confirm({
                title: this.$t('dashboard.widget_delete_message'),
                cancelText: this.$t('cancel'),
                okText: this.$t('remove'),
                onOk: async () => {
                    try {
                        this.$message.loading({ content: this.$t('dashboard.updating'), key: updateKey })
                        await this.$store.dispatch('dashboard/deleteMobileActiveWidget', { id: this.widget.id })
                        this.$message.success({ content: this.$t('dashboard.updated'), key: updateKey, duration: 2 })
                    } catch(error) {
                        errorHandler({error, key: updateKey})
                    }
                }
            })
        },
        async showMobileVersion(value) {
            try {
                this.actionLoading = true
                this.$store.commit('dashboard/UPDATE_ACTIVE_WIDGET', {
                    widgetId: this.widget.id,
                    key: 'is_mobile',
                    value
                })
                await this.$http.patch(`/widgets/user_widgets_on_desktop/${this.widget.id}/`, {
                    is_mobile: value
                })
            } catch(error) {
                errorHandler({error})
            } finally {
                this.actionLoading = false
            }
        },
        async showDesctopVersion(value) {
            try {
                this.actionLoading = true
                this.$store.commit('dashboard/UPDATE_ACTIVE_WIDGET', {
                    widgetId: this.widget.id,
                    key: 'is_desktop',
                    value
                })
                await this.$http.patch(`/widgets/user_widgets_on_desktop/${this.widget.id}/`, {
                    is_desktop: value
                })
            } catch(error) {
                errorHandler({error})
            } finally {
                this.actionLoading = false
            }
        },
        async pinWidget() {
            try {
                this.actionLoading = true
                //this.$message.loading({ content: 'Обновление', key: updateKey })
                await this.$store.dispatch('dashboard/pinActiveWidget', { id: this.widget.id })
                //this.$message.success({ content: 'Обновлено', key: updateKey, duration: 2 })
            } catch(error) {
                errorHandler({error})
            } finally {
                this.actionLoading = false
            }
        },
        openWidgetSetting() {
            eventBus.$emit('openSetting', this.widget)
        },
        visibleChange(vis) {
            if(vis) {
                this.getWidgetAction()
            } else {
                this.clearActions()
            }
        },
        clearActions() {
            this.actions = null
        },
        async getWidgetAction() {
            try {
                this.loading = true
                const { data } = await this.$http.get(`/widgets/user_widgets_on_desktop/${this.widget.id}/actions/`)
                if(data?.actions) {
                    this.actions = data.actions
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        },
    }
}