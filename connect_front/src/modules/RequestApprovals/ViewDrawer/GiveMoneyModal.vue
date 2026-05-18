<template>
    <a-modal
        :title="$t('approvals.give_money')"
        :visible="visible"
        @afterVisibleChange="afterVisibleChange"
        @cancel="closeModal()">
        <a-form-model ref="form" :model="form">
            <a-form-model-item 
                label="" 
                :rules="{
                    required: true,
                    message: $t('field_required'),
                }"
                prop="amount_paid" 
                class="mb-0">
                <a-input
                    ref="amount_paid_input"
                    size="large"
                    class="w-full"
                    :placeholder="$t('approvals.print_amount')"
                    v-model="form.amount_paid"
                    @input="onAmountPaidInput"
                    @blur="onAmountPaidBlur"/>
            </a-form-model-item>
        </a-form-model>
        <template #footer>
            <div class="flex w-full items-center justify-end gap-2">
                <a-button 
                    type="primary" 
                    :loading="loading"
                    :block="isMobile"
                    @click="approvalsReject()">
                    {{ $t('approvals.give_money_handler') }}
                </a-button>
                <a-button 
                    type="ui_ghost" 
                    :disabled="loading"
                    :block="isMobile"
                    @click="closeModal()">
                    {{ $t('cancel') }}
                </a-button>
            </div>
        </template>
    </a-modal>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
import eventBus from '@/utils/eventBus'
export default {
    props: {
        approvals: {
            type: Object,
            required: true
        },
        model: {
            type: String,
            required: true
        },
        pageName: {
            type: String,
            required: true
        },
        getDetail: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return {
            visible: false,
            loading: false,
            form: {
                amount_paid: ''
            }
        }
    },
    methods: {
        afterVisibleChange(vis) {
            if(vis) {
                if(this.approvals.amount_requested !== undefined && this.approvals.amount_requested !== null && this.approvals.amount_requested !== '') {
                    this.form.amount_paid = this.normalizeAmount(this.approvals.amount_requested)
                } else {
                    this.form.amount_paid = ''
                }

                this.$nextTick(() => {
                    if(this.$refs.amount_paid_input)
                        this.$refs.amount_paid_input.focus()
                })
            }
        },
        onAmountPaidInput(e) {
            let v = String(e.target.value || '')

            v = v.replace(',', '.')
            v = v.replace(/[^\d.]/g, '')

            const parts = v.split('.')
            const intPart = parts[0]
            const decPart = parts[1] ? parts[1].slice(0, 2) : ''

            v = `${intPart}${parts.length > 1 ? '.' + decPart : ''}`

            this.form.amount_paid = this.formatThousands(v)
        },
        onAmountPaidBlur() {
            let v = String(this.form.amount_paid || '').replace(/\s/g, '')

            if (!v) {
                this.form.amount_paid = ''
                return
            }

            let parts = v.split('.')
            let intPart = (parts[0] || '').replace(/\D/g, '') || '0'
            let decPart = (parts[1] || '').replace(/\D/g, '').slice(0, 2)

            decPart = decPart.padEnd(2, '0')

            this.form.amount_paid = this.formatThousands(`${intPart}.${decPart}`)
        },
        formatThousands(value) {
            if (!value) return ''

            const parts = String(value).split('.')
            const intPart = (parts[0] || '').replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
            const decPart = parts[1] !== undefined ? `.${parts[1]}` : ''

            return `${intPart}${decPart}`
        },
        normalizeAmount(value) {
            if (value === undefined || value === null || value === '') return ''

            const str = String(value).replace(/\s/g, '').replace(',', '.')
            if (!str) return ''

            const parts = str.split('.')
            const intPart = (parts[0] || '').replace(/\D/g, '') || '0'
            const decPart = (parts[1] || '').replace(/\D/g, '').slice(0, 2)

            const fixedDec = decPart.padEnd(2, '0')
            return this.formatThousands(`${intPart}.${fixedDec}`)
        },
        async approvalsReject() {
            this.$refs.form.validate(async (v) => {
                if (v) {
                    try {
                        this.loading = true

                        const amountPaid = this.form.amount_paid
                            ? Number(
                                String(this.form.amount_paid)
                                    .replace(/\s/g, '')
                                    .replace(',', '.')
                            )
                            : null

                        const { data } = await this.$http.post(`/processes/workflow_requests/${this.approvals.id}/give_money/`, {
                            amount_paid: amountPaid
                        })
                        if(data) {
                            eventBus.$emit(`update_filter_${this.model}_${this.pageName}`)
                            await this.getDetail(true)
                            this.closeModal()
                        }
                    } catch(error) {
                        errorHandler({error})
                    } finally {
                        this.loading = false
                    }
                }
            })
        },
        openModal() {
            this.visible = true
        },
        closeModal() {
            this.form.amount_paid = ''
            this.visible = false
        }
    }
}
</script>