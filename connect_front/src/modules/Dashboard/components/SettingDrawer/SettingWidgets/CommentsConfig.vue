<template>
    <div>
        <a-form-model-item
            :label="$t('dashboard.task')"
            prop="parent"
            class="mt-2">
            <div class="popover_input ant-input flex items-center relative ant-input-lg truncate">
                <a-tooltip
                    v-if="relObject"
                    :title="relObject.name"
                    class="mr-2 truncate">
                    <a-tag
                        color="blue"
                        class="tag_block truncate"
                        @click="taskDrawer = true">
                        {{ relObject.name }}
                    </a-tag>
                </a-tooltip>
                <a-button
                    @click="taskDrawer = true"
                    type="link"
                    :icon="!relObject && 'plus'"
                    class="px-0">
                    {{ relObject ? $t('dashboard.change') : $t('dashboard.select') }}
                </a-button>
                <a-button
                    v-if="relObject"
                    @click="clearSelect()"
                    type="link"
                    icon="close-circle"
                    class="px-0 text-current remove_parent" />
            </div>
        </a-form-model-item>
        <a-form-model-item
            :label="$t('dashboard.request')"
            prop="request"
            class="mt-2">
            <div class="popover_input ant-input flex items-center relative ant-input-lg truncate">
                <a-tooltip
                    v-if="relTicket"
                    :title="ticketTitle"
                    class="mr-2 truncate">
                    <a-tag
                        color="blue"
                        class="tag_block truncate"
                        @click="requestDrawer = true">
                        {{ ticketTitle }}
                    </a-tag>
                </a-tooltip>
                <a-button
                    @click="requestDrawer = true"
                    type="link"
                    :icon="!relTicket && 'plus'"
                    class="px-0">
                    {{ relTicket ? $t('dashboard.change') : $t('dashboard.select') }}
                </a-button>
                <a-button
                    v-if="relTicket"
                    @click="clearTicketSelect()"
                    type="link"
                    icon="close-circle"
                    class="px-0 text-current remove_parent" />
            </div>
        </a-form-model-item>
        <a-form-model-item
            :label="$t('dashboard.event')"
            prop="event"
            class="mt-2">
            <div class="popover_input ant-input flex items-center relative ant-input-lg truncate">
                <a-tooltip
                    v-if="relEvent"
                    :title="relEventTitle"
                    class="mr-2 truncate">
                    <a-tag
                        color="blue"
                        class="tag_block truncate"
                        @click="eventDrawer = true">
                        {{ relEventTitle }}
                    </a-tag>
                </a-tooltip>
                <a-button
                    @click="eventDrawer = true"
                    type="link"
                    :icon="!relEvent && 'plus'"
                    class="px-0">
                    {{ relEvent ? $t('dashboard.change') : $t('dashboard.select') }}
                </a-button>
                <a-button
                    v-if="relEvent"
                    @click="clearEventSelect()"
                    type="link"
                    icon="close-circle"
                    class="px-0 text-current remove_parent" />
            </div>
        </a-form-model-item>
        <TaskSelectDrawer
            v-model="relObject"
            :taskDrawer="taskDrawer"
            :selectParentTask="selectParentTask"
            :closeHandler="closeHandler" />
        <RequestSelectDrawer
            v-model="relTicket"
            :visible="requestDrawer"
            :closeHandler="closeRequestHandler" />
        <EventSelectDrawer
            v-model="relEvent"
            :visible="eventDrawer"
            :closeHandler="closeEventHandler" />
    </div>
</template>

<script>
export default {
    props: {
        widget: {
            type: Object,
            required: true
        },
        closeSettingDrawer: {
            type: Function,
            default: () => {}
        }
    },
    components: {
        TaskSelectDrawer: () => import('@apps/vue2TaskComponent/components/EditDrawer/TaskSelectDrawer.vue'),
        RequestSelectDrawer: () => import('./components/RequestSelectDrawer.vue'),
        EventSelectDrawer: () => import('./components/EventSelectDrawer.vue')
    },
    computed: {
        related_object() {
            return this.widget.random_settings?.related_object || null
        },
        related_model() {
            return this.widget.random_settings?.related_model || null
        },
        ticketTitle() {
            if(!this.relTicket)
                return ''
            const number = this.relTicket.number ? `#${this.relTicket.number}` : ''
            return `${number} ${this.relTicket.name || ''}`.trim()
        },
        relEventTitle() {
            if(!this.relEvent)
                return ''
            return this.relEvent.name || ''
        }
    },
    data() {
        return {
            relObject: null,
            relTicket: null,
            relEvent: null,
            taskDrawer: false,
            requestDrawer: false,
            eventDrawer: false
        }
    },
    created() {
        if(this.related_object) {
            if(this.related_model === 'help_desk_tickets')
                this.relTicket = this.related_object
            else if(this.related_model === 'events')
                this.relEvent = this.related_object
            else
                this.relObject = this.related_object
        }
    },
    watch: {
        relTicket(val) {
            if(val)
                this.relEvent = null
            if(val)
                this.relObject = null
        },
        relEvent(val) {
            if(val) {
                this.relObject = null
                this.relTicket = null
            }
        },
        relObject(val) {
            if(val) {
                this.relTicket = null
                this.relEvent = null
            }
        }
    },
    methods: {
        clearSelect() {
            this.relObject = null
        },
        clearTicketSelect() {
            this.relTicket = null
        },
        clearEventSelect() {
            this.relEvent = null
        },
        selectParentTask() {
            this.relTicket = null
            this.relEvent = null
        },
        closeHandler() {
            this.taskDrawer = false
        },
        closeRequestHandler() {
            this.requestDrawer = false
        },
        closeEventHandler() {
            this.eventDrawer = false
        },
        getSavedConfig() {
            if(this.relTicket) {
                return {
                    related_object: this.relTicket,
                    related_model: 'help_desk_tickets'
                }
            }
            if(this.relEvent) {
                return {
                    related_object: this.relEvent,
                    related_model: 'events'
                }
            }
            if(this.relObject) {
                return {
                    related_object: this.relObject,
                    related_model: 'tasks.TaskModel'
                }
            }
            return {
                related_object: null,
                related_model: null
            }
        },
        async saveConfig() {
            try {
                const randomSettings = this.getSavedConfig()
                await this.$http.patch(`/widgets/user_widgets_on_desktop/${this.widget.id}/`, {
                    random_settings: randomSettings
                })
                this.$store.commit('dashboard/UPDATE_ACTIVE_WIDGET', {
                    widgetId: this.widget.id, 
                    key: 'random_settings', 
                    value: randomSettings
                })
                this.closeSettingDrawer()
            } catch(e) {
                console.log(e)
                this.$message.error('Ошибка')
            }
        },
        async resetConfig() {
            try {
                await this.$http.patch(`/widgets/user_widgets_on_desktop/${this.widget.id}/`, {
                    random_settings: {
                        related_object: null,
                        related_model: null
                    }
                })
                this.$store.commit('dashboard/UPDATE_ACTIVE_WIDGET', {
                    widgetId: this.widget.id, 
                    key: 'random_settings', 
                    value: {
                        related_object: null,
                        related_model: null
                    }
                })
                this.closeSettingDrawer()
            } catch(e) {
                console.log(e)
                this.$message.error('Ошибка')
            }
        }
    }
}
</script>
