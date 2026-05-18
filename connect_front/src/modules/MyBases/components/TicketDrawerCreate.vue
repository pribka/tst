<template>
    <a-drawer
        class="connect_drawer"
        :width="drawerWidth"
        :visible="drawerVisible"
        :afterVisibleChange="afterVisibleChange"
        :closable="false"
        @close="closeDrawer" >
        <div class="head_wrapper flex items-center justify-between">
            <div
                class="text-base font-semibold truncate label">
                {{ isEditMode ? 'Редактировать заявку' : drawerTitle }}
            </div>
            <a-button
                type="link"
                class="ml-2 text-current"
                icon="close"
                @click="closeDrawer()" />
        </div>
        <div v-if="formInfo" class="body_wrapper">
            <TicketForm
                ref="ticketFormComponent"
                :mode="mode"
                :isAttrsLoaded="isAttrsLoaded"
                :formInfo="formInfo"    
                :form="form" />
        </div>
        <div class="footer_wrapper flex items-center">
            <template v-if="isEditMode">
                <a-button
                    :loading="submitLoading"
                    @click="submit"
                    type="primary" >
                    Подтвердить
                </a-button>
            </template>
            <template v-if="isCreateMode">
                <a-button
                    :loading="submitLoading"
                    @click="submit"
                    type="primary" >
                    Подать заявку
                </a-button>
            </template>
        </div>
    </a-drawer>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { mapActions, mapState } from 'vuex'
export default {
    components: {
        TicketForm: () => import('./TicketForm.vue')
    },
    props: {
        pageName: {
            type: String,
            default: 'IncomingServiceTicketModel'
        }
    },
    data() {
        return {
            drawerVisible: false,
            form: {},
            formInfo: {},
            isAttrsLoaded: false,
            submitLoading: false,
            ticket: null,
            mode: 'create'
        }
    },
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth,
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
            return this.formInfo?.drawerTitle || 'Подать заявку'
        },
        readOnlyMode() {
            return this.mode === 'readonly'
        },
        isEditMode() {
            return this.mode === 'edit'
        },
        isCreateMode() {
            return this.mode === 'create'
        },
    },
    methods: {
        ...mapActions({
            addTicket: 'mybases/addTicket',
            updateTicket: 'mybases/updateTicket'
        }),
        openDrawer(data) {
            this.mode = data.mode || this.mode
            if(this.isCreateMode && data?.form)
                this.form = data.form
            else if(this.isEditMode && data?.ticket) {
                this.setEditMode(data.ticket)
            }
            this.drawerVisible = true
        },
        closeDrawer() {
            this.drawerVisible = false
        },
        afterVisibleChange(visible) {
            if(!visible) {
                this.mode = 'create'
                this.form = {}
            } else {
                this.getFormInfo()
            }
        },
        async setEditMode(ticket) {
            this.ticket = await this.getTicket(ticket.id)
            this.form = {
                connection_option: this.ticket.connection_option.code,
                config_1c: this.ticket.config_1c.id,
                user_count: this.ticket.user_count,
                phone: this.ticket.phone,
                email: this.ticket.email,
                company: this.ticket.company,
                activity_type: this.ticket.activity_type,
                description: this.ticket.description,
            }
        },
        async getTicket(ticketId) {
            return await this.$http(`tickets/ticket/${ticketId}/`)
                .then(({ data }) => {
                    this.ticket = data
                    return data
                })
                .catch(error => {
                    console.error(error)
                })
        },
        async getFormInfo() {
            await this.$http('tickets/form_info/')
                .then(({ data }) => {
                    this.formInfo = data
                    this.isAttrsLoaded = true
                })
                .catch(error => {
                    console.error(error)
                })
        },
        async submit() {
            const formRef = this.$refs.ticketFormComponent.$refs.ticketForm
            formRef.validate(async valid => {
                if(valid) {
                    this.submitLoading = true
                    
                    let responseTicket
                    if(this.isEditMode) {
                        responseTicket = await this.updateTicket({ticketId: this.ticket.id, form: this.form})
                    } else {
                        responseTicket = await this.addTicket(this.form)
                    }
                    
                    if(responseTicket) {
                        this.openSuccessNotification()
                        setTimeout(this.closeDrawer(), 2000)
                        eventBus.$emit('OPEN_MY_BASES_DRAWER_VIEW', responseTicket.id)
                        eventBus.$emit(`table_row_${this.pageName}`, {
                            action: this.isEditMode ? 'update' : 'create',
                            row: {
                                id: responseTicket.id || this.ticket.id,
                                ...responseTicket
                            }
                        })
                    } else
                        this.$message.error('Не удалось подать заявку')
                    
                    this.submitLoading = false
                }
            })
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
    },
    mounted() {
        eventBus.$on('OPEN_MY_BASES_DRAWER', data => this.openDrawer(data))
    },
    beforeDestroy() {
        eventBus.$off('OPEN_MY_BASES_DRAWER')
    }
}
</script>

<style lang="scss" scoped>
.connect_drawer {
    .head_wrapper {
        height: 40px;
        border-bottom: 1px solid var(--borderColor);
        padding: 10px 20px;
        background: var(--bgColor);
        
    }
    .body_wrapper {
        height: calc(100% - 80px);
        padding: 15px;
        overflow-y: scroll;
    }
    .footer_wrapper {
        height: 40px;
        padding: 10px 15px;
        background: var(--bgColor);
        border-top: 1px solid var(--borderColor);
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
