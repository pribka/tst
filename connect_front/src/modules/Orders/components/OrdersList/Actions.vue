<template>
    <div class="flex items-center">
        <a-tooltip v-if="!isMobile">
            <template slot="title">
                Подробнее о заказе
            </template>
            <a-button
                class="mr-1 ant-btn-icon-only"
                type="link"
                :loading="openLoading"
                @click="openCheckActions(record.id)">
                <i class="fi fi-rr-eye"></i>
            </a-button>
        </a-tooltip>
        <component 
            :is="menuWidget"
            ref="order_menu"
            :record="record"
            :loading="loading"
            @start="start"
            @end="end"
            @share="share"
            @addTask="createTask" />
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { priceFormatter } from '@/utils'
export default {
    props: {
        record: {
            type: Object,
            required: true
        },
        openOrder: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            loading: false,
            openLoading: false
        }
    },
    computed: {
        // isAuthor() {
        //     if(this.user?.id === this.item.owner.id)
        //         return true
        //     else
        //         return false
        // },
        isMobile() {
            return this.$store.state.isMobile
        },
        menuWidget() {
            if(this.isMobile)
                return () => import('./ActionsMenu/MobileMenu')
            return () => import('./ActionsMenu/DropdownMenu')
        }
    },
    methods: {
        async openCheckActions(id) {
            try {
                this.openLoading = true
                const data = await this.$store.dispatch('orders/getOrderActions', {
                    id
                })
                if(data?.actions?.edit && data?.actions?.open_edit) {
                    eventBus.$emit('orderEdit', this.record)
                } else {
                    this.openOrder(id)
                }
            } catch(e) {
                console.log(e)
                this.openOrder(id)
            } finally {
                this.openLoading = false
            }
        },
        share() {
            this.$store.commit('share/SET_SHARE_PARAMS', {
                model: 'crm.GoodsOrderModel',
                shareId: this.record.id,
                object: this.record,
                shareUrl: `${window.location.href}/?order=${this.record.id}`,
                shareTitle: `Заказ - ${this.record.counter}`
            })
        },
        async deleteSprint() {
            try {
                await this.$http.post(`table_actions/update_is_active/`, [
                    {id: this.record.id, is_active: false}
                ]
                )
                this.$emit('delete', this.record.id)
            } catch (e) {
                this.$message.error(this.$t('error') + e)
            } finally {
                this.loading = false
            }
        },

        async start() {
            try {
                await this.$http.put(`tasks/sprint/${this.record.id}/update_status/`, {status: 'in_process'})
                this.$emit('updateStatus', {status: 'in_process', id: this.record.id})
                this.$message.success("Спринт начат")
            } catch (e) {
                console.log(e)
                this.$message.error(this.$t('error'))
            } finally {
                this.loading = false
            }
        },
        async end() {
            try {
                await this.$http.put(`tasks/sprint/${this.record.id}/update_status/`, {status: 'completed'})
                this.$emit('updateStatus', {status: 'completed', id: this.record.id})
                this.$message.success("Спринт завершен")
            } catch (e) {
                this.$message.error(this.$t('error'))
            } finally {
                this.loading = false
            }
        },
        async edit() {
            this.$emit('edit', this.record)
        },
        async createTask() {
            let query = Object.assign({}, this.$route.query)

            if(query && query.task) {
                this.$store.commit('task/CHANGE_TASK_SHOW', false)
                delete query.task
                await this.$router.push({query})
            }

            let form = {
                // attachments: [this.file],
                reason_name: this.record.counter,
                reason_model: 'order',
                reason_id: this.record.id,
                delivery_point: this.record.delivery_point,
                name: `${this.record.counter} от ${this.$moment(this.record.created_at).format('DD.MM.YYYY')} на сумму ${priceFormatter(this.record.amount)}`,
                task_type: 'logistic'
            }

            if(this.record.operator) {
                form.operator = this.record.operator
            }
            if(this.record.logistic_manager) {
                form.owner = this.record.logistic_manager
            }

            eventBus.$emit('ADD_WATCH', {type: 'add_task', data: form})
        },

    }
}
</script>
