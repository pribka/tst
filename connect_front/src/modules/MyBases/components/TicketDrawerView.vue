<template>
    <a-drawer
        class="connect_drawer"
        :width="drawerWidth"
        :visible="drawerVisible"
        :closable="false"
        @close="closeDrawer" >
        <div class="head_wrapper flex items-center justify-between">
            <div
                class="text-base font-semibold truncate label">
                {{ drawerTitle }}
            </div>
            <a-button
                type="link"
                class="ml-2 text-current"
                icon="close"
                @click="closeDrawer()" />
        </div>
        <div class="body_wrapper text-base">
            <template v-if="ticket">
                <div class="mb-4">
                    <span class="font-semibold mr-1">База:</span>
                    <span>{{ ticket.connection_option.name }}</span>
                </div>
                <template v-if="ticket.config_1c">
                    <div class="mb-4">
                        <span class="font-semibold mr-1">Конфигурация:</span>
                        <span>{{ ticket.config_1c.name }}</span>
                    </div>
                </template>
                <div class="mb-4">
                    <span class="font-semibold mr-1">Кол-во пользователей:</span>
                    <span>{{ ticket.user_count }}</span>
                </div>
                <div class="mb-4">
                    <span class="font-semibold mr-1">Контактный телефон:</span>
                    <a :href="`tel:${ticket.phone}`">{{ ticket.phone }}</a>
                </div>
                <template v-if="ticket.email">
                    <div class="mb-4">
                        <span class="font-semibold mr-1">Электронная почта:</span>
                        <a :href="`mailto:${ticket.email}`">{{ ticket.email }}</a>
                    </div>
                </template>
                <template v-if="ticket.company">
                    <div class="mb-4">
                        <span class="font-semibold mr-1">Организация:</span>
                        <span>{{ ticket.company }}</span>
                    </div>
                </template>
                <div class="mb-4">
                    <span class="font-semibold mr-1">Вид деятельности:</span>
                    <span>{{ ticket.activity_type }}</span>
                </div>
                <div class="mb-4">
                    <div class="font-semibold mb-2">Автор:</div>
                    <Profiler
                        :avatarSize="22"
                        nameClass="text-sm"
                        :user="ticket.author" />
                </div>
                <template v-if="ticket.processed_by">
                    <div class="mb-4">
                        <div class="font-semibold mb-2">Менеджер:</div>
                        <Profiler
                            :avatarSize="22"
                            nameClass="text-sm"
                            :user="ticket.processed_by" />
                    </div>
                </template>
                <template v-if="ticket.description">
                    <div>
                        <span class="font-semibold mr-1">Дополнительная информация:</span>
                        <span>{{ ticket.description }}</span>
                    </div>
                </template>
                <!-- <span @click="share">share</span> -->
            </template>
            <template v-else>
                <a-skeleton />
            </template>
        </div>
        <div class="footer_wrapper flex items-center">
            <template v-if="permissions?.actions?.set_status?.availability">
                <a-button
                    class="flex items-center mr-1"
                    :loading="setStatusLoading"
                    @click="setStatus(true)"
                    type="primary" >
                    Одобрить
                </a-button>
                <a-button
                    class="flex items-center mr-1"
                    :loading="setStatusLoading"
                    @click="setStatus(false)"
                    type="danger" >
                    Отклонить
                </a-button>
            </template>
            <a-button
                v-if="permissions?.actions?.edit?.availability"
                class="flex items-center"
                :type="isMobile ? 'default' : 'ui'"
                :ghost="!isMobile"
                @click="openEditDrawer">
                <template v-if="!isMobile">
                    <div class="blue_color">
                        Редактировать
                    </div>
                </template>
                <template v-else>
                    <div class="edit_icon_wrap blue_color">
                        <i class="fi fi-rr-edit"></i>
                    </div>
                </template>
            </a-button>
        </div>
    </a-drawer>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { mapActions, mapState } from 'vuex'
export default {
    props: {
        pageName: {
            type: String,
            default: 'IncomingServiceTicketModel'
        }
    },
    data() {
        return {
            model: 'TicketModel',
            drawerVisible: false,
            ticket: null,
            ticketId: null,
            permissions: [],
            setStatusLoading: false,
        }
    },
    watch: {
        '$route.query'(val) {
            if(val.ticket) {
                this.openDrawer(val.ticket)
            }
        }
    },
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth,
            isMobile: state => state.isMobile
        }),
        drawerWidth() {
            const
                offset = 30,
                breakpoint1 = 900 + offset,
                breakpoint2 = 500
            if(this.windowWidth > breakpoint1)
                return 900
            else if(this.windowWidth > breakpoint2)
                return this.windowWidth - offset
            else
                return this.windowWidth
        },
        drawerTitle() {
            return 'Просмотр заявки'
        },
        canSetStatus() {
            return this.ticket ? !this.ticket.is_closed : false
        },
    },
    methods: {
        ...mapActions({
            setTicketStatus: 'mybases/setTicketStatus'
        }),
        async openDrawer(ticketId) {
            this.drawerVisible = true
            await this.getTicket(ticketId)
            await this.getPermissions()
        },
        async getTicket(ticketId) {
            await this.$http(`tickets/ticket/${ticketId}/`)
                .then(({ data }) => {
                    this.ticket = data
                })
                .catch(error => console.error(error))
        },
        closeDrawer() {
            this.drawerVisible = false
            this.ticket = null
            let query = Object.assign({}, this.$route.query)
            if(query.ticket) {
                delete query.ticket
                this.$router.push({query})
            }
        },
        openSuccessNotification() {
            this.$notification['success']({
                message: this.isEditMode ? 'Заявка успешно обновлена' : 'Заявка успешно подана',
                description:
                'С вами свяжется менеджер',
                onClick: () => {
                },
            })
        },
        async setStatus(isApproved) {
            this.setStatusLoading = true
            const responseTicket = await this.setTicketStatus({ticketId: this.ticket.id, isApproved: isApproved})
            if(responseTicket)
                this.ticket = responseTicket
            this.setStatusLoading = false

            await this.getPermissions()
            eventBus.$emit(`table_row_${this.pageName}`, {
                action: 'update',
                row: responseTicket
            })

        },
        openEditDrawer() {
            eventBus.$emit('OPEN_MY_BASES_DRAWER', { ticket: this.ticket, mode: 'edit' })
            this.closeDrawer()
        },
        share() {
            this.$store.commit('share/SET_SHARE_PARAMS', {
                model: this.model,
                shareId: this.ticket.id,
                object: this.ticket,
                shareUrl: `${window.location.origin}/my-bases?ticket=${this.ticket.id}`,
                // shareTitle: `${this.$t(`task.${this.item.task_type}`)} - ${this.ticket.name}`
                shareTitle: `${this.ticket.name}`
            })
        },
        async getPermissions() {
            await this.$http(`tickets/ticket/${this.ticket.id}/action_info/`)
                .then(({ data }) => {
                    this.permissions = data
                })
                .catch(error => console.error(error))
        }
    },
    mounted() {
        eventBus.$on('OPEN_MY_BASES_DRAWER_VIEW', ticket => this.openDrawer(ticket))
    },
    beforeDestroy() {
        eventBus.$off('OPEN_MY_BASES_DRAWER_VIEW')
    }
}
</script>

<style lang="scss" scoped>
.connect_drawer {
    .head_wrapper {
        height: 40px;
        border-bottom: 1px solid var(--borderColor);
        padding: 10px 30px;
        background: var(--bgColor);
        
    }
    .body_wrapper {
        height: calc(100% - 80px);
        padding: 30px;
        overflow-y: scroll;
    }
    .footer_wrapper {
        height: 40px;
        padding: 10px 30px;
        background: var(--bgColor);
        border-top: 1px solid var(--borderColor);
    }
    .edit_icon_wrap {
        display: flex;
        justify-content: center;
        align-items: center;
        
        line-height: 100%;
        font-size: 1rem;
    }
    &::v-deep {
        .ant-drawer-body,
        .ant-drawer-content{
            overflow: hidden;
        }
        .ant-drawer-body{
            padding: 0px;
            height: 100%;
        }
    }

}
 
</style>
