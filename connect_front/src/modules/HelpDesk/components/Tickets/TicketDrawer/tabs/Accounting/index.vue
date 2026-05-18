<template>
    <div class="flex flex-col h-full" ref="wrapRef">
        <div class="flex items-center justify-between mb-2">
            <a-button
                v-if="actions?.create_cost?.availability"
                type="ui"
                flaticon
                icon="fi-rr-plus-small"
                @click="addAccounting()">
                {{ $t('helpdesk.add') }}
            </a-button>
            <div v-else />
            <SettingsButton
                v-if="!isMobile"
                :pageName="page_name"
                size="default"
                class="ml-2" />
        </div>

        <!-- ✅ MOBILE -->
        <MobileInfiniteList
            v-if="isMobile"
            :identifier="page_name"
            :reloadKey="`${ticket.id}_${mobileReloadKey}`"
            :emptyDescription="$t('calendar.no_data')"
            :url="() => `/help_desk/tickets/${ticket.id}/work_log/list/`">

            <template #item="{ item }">
                <TimeCard
                    :ticket="ticket"
                    :item="item"
                    :pageModel="model"
                    :pageName="page_name"
                    :colParams="colParams" />
            </template>
        </MobileInfiniteList>

        <!-- ✅ DESKTOP -->
        <UniversalTable
            v-else
            :model="model"
            :pageName="page_name"
            tableType="tickets_accounting"
            autoHeight
            :colParams="{
                ...ticket,
                getTimer: getTimer,
                getPopupContainer
            }"
            :endpoint="`/help_desk/tickets/${ticket.id}/work_log/list/`"
            :main="false"
            extendDrawer
            :hash="false" />

        <a-modal
            :visible="visible"
            :title="edit ? $t('helpdesk.edit_record') : $t('helpdesk.add_record')"
            :footer="false"
            @cancel="visible = false"
            @afterVisibleChange="afterVisibleChange">

            <a-form-model
                ref="ruleForm"
                :model="form"
                :rules="rules">

                <a-form-model-item class="mb-2">
                    <div class="time_block">
                        <div class="time_block__label">{{ $t('helpdesk.time_spent') }}</div>
                        <div class="grid grid-cols-3 gap-2">
                            <div class="item_block">
                                <div class="item_block__label">{{ $t('helpdesk.hours') }}</div>
                                <a-input-number
                                    v-model="form.duration_h"
                                    size="large"
                                    class="w-full"
                                    :min="0"
                                    :precision="0"
                                    :placeholder="$t('helpdesk.hours_placeholder')" />
                            </div>
                            <div class="item_block">
                                <div class="item_block__label">{{ $t('helpdesk.minutes') }}</div>
                                <a-input-number
                                    v-model="form.duration_m"
                                    size="large"
                                    class="w-full"
                                    :min="0"
                                    :max="59"
                                    :precision="0"
                                    :placeholder="$t('helpdesk.minutes_placeholder')" />
                            </div>
                            <div class="item_block">
                                <div class="item_block__label">{{ $t('helpdesk.seconds') }}</div>
                                <a-input-number
                                    v-model="form.duration_s"
                                    size="large"
                                    class="w-full"
                                    :min="0"
                                    :max="59"
                                    :precision="0"
                                    :placeholder="$t('helpdesk.seconds_placeholder')" />
                            </div>
                        </div>
                    </div>
                </a-form-model-item>

                <a-form-model-item
                    class="mb-2"
                    ref="description"
                    :label="$t('helpdesk.description')"
                    prop="description">
                    <a-textarea
                        v-model="form.description"
                        inputType="bg"
                        :placeholder="$t('helpdesk.description')"
                        :auto-size="{ minRows: 3, maxRows: 5 }" />
                </a-form-model-item>

                <a-form-model-item ref="date" :label="$t('helpdesk.date')" prop="date">
                    <a-date-picker
                        v-model="form.date"
                        :getCalendarContainer="trigger => trigger.parentNode"
                        format="DD.MM.YYYY"
                        class="w-full"
                        size="large" />
                </a-form-model-item>

                <a-form-model-item
                    v-if="canEditUser && customerCardId"
                    :label="$t('helpdesk.user')"
                    class="mb-2"
                    prop="user">
                    <UserMiniSelect
                        v-model="form.user"
                        :showSearch="false"
                        :showIcon="false"
                        :showRecent="false"
                        size="large"
                        inputType="bordered_input"
                        :apiUrl="userSelectApi"
                        :storeName="`${customerCardId}_user_select`"
                        :placeholder="$t('helpdesk.user')" />
                </a-form-model-item>
                <a-form-model-item class="mb-3">
                    <a-checkbox v-model="form.is_result">
                        {{ $t('helpdesk.is_results') }}
                    </a-checkbox>
                </a-form-model-item>

                <a-button
                    type="primary"
                    :loading="loading"
                    size="large"
                    block
                    class="mb-3"
                    @click="onSubmit()">
                    {{ edit ? $t('helpdesk.save') : $t('helpdesk.add') }}
                </a-button>
            </a-form-model>
        </a-modal>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils'
import { mapState } from 'vuex'

export default {
    components: {
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable'),
        TimeCard: () => import('./TimeCard.vue'),
        MobileInfiniteList: () => import('../../../../../components/MobileInfiniteList.vue'),
        SettingsButton: () => import('@/components/TableWidgets/SettingsButton'),
        UserMiniSelect: () => import('@apps/DrawerSelect/UserMiniSelect.vue')
    },
    props: {
        ticket: { type: Object, required: true },
        actions: { type: Object, default: () => null },
        getTimer: { type: Function, default: () => {} }
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        page_name() {
            return `work_log_${this.ticket?.id || 'new'}`
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        canEditUserForCreate() {
            return !!this.actions?.create_cost?.edit_user
        },
        canEditUser() {
            if (this.edit) return this.canEditUserForEdit
            return this.canEditUserForCreate
        },
        customerCardId() {
            return this.ticket?.customer_card?.id || this.ticket?.customer_card || null
        },
        userSelectApi() {
            if (!this.customerCardId) return ''
            return `/help_desk/customer_cards/${this.customerCardId}/specialists/?display=user`
        },
        // ✅ важно для мобилки (edit/delete в карточке)
        colParams() {
            return {
                id: this.ticket?.id || null,
                getTimer: this.getTimer,
                getPopupContainer: this.getPopupContainer
            }
        }
    },
    data() {
        return {
            // ✅ добавили: ключ для перезагрузки моб. списка
            mobileReloadKey: 0,

            visible: false,
            edit: false,
            canEditUserForEdit: false,
            loading: false,
            model: 'help_desk.HelpDeskTicketWorkLogModel',
            form: {
                duration: null,
                duration_h: 0,
                duration_m: 0,
                duration_s: 0,
                description: '',
                date: null,
                user: null,
                is_result: false
            },
            rules: {
                date: [{ required: true, message: this.$t('helpdesk.required_field'), trigger: 'blur' }],
                description: [{ min: 0, max: 1024, message: this.$t('helpdesk.max_symbols', { count: 1024 }), trigger: 'blur' }]
            }
        }
    },
    methods: {
        syncWorkplanTicket() {
            if (!this.$store.hasModule('workplan') || !this.ticket?.id) return
            this.$store.dispatch('workplan/updateItem', {
                item: { id: this.ticket.id },
                list: 'ticketList'
            })
        },
        // ✅ добавили: обновление моб. списка по событию (create/update/delete уже эмитит update_filter_...)
        onMobileUpdate() {
            this.syncWorkplanTicket()
            if (this.isMobile) this.mobileReloadKey += 1
        },

        getPopupContainer() {
            return this.$refs.wrapRef
        },
        getEmptyForm() {
            return {
                duration: null,
                duration_h: 0,
                duration_m: 0,
                duration_s: 0,
                description: '',
                date: null,
                user: null,
                is_result: false
            }
        },
        getDefaultUser() {
            if (!this.user?.id) return null
            return {
                ...this.user,
                full_name: this.user.full_name || `${this.user.last_name || ''} ${this.user.first_name || ''}`.trim()
            }
        },
        extractUserId(value) {
            if (!value) return null
            if (typeof value === 'object') return value.id || null
            return value
        },
        resolveEditUserAccess(action = null) {
            if (action && Object.prototype.hasOwnProperty.call(action, 'edit_user')) {
                return !!action.edit_user
            }
            return this.canEditUserForCreate
        },
        applyDefaultUser() {
            if (!this.canEditUser || this.form.user) return
            const defaultUser = this.getDefaultUser()
            if (defaultUser) {
                this.$set(this.form, 'user', defaultUser)
            }
        },
        afterVisibleChange(vis) {
            if (!vis) {
                this.edit = false
                this.canEditUserForEdit = false
                this.form = this.getEmptyForm()
                return
            }
            if (!this.edit) {
                this.form.date = this.form.date || this.$moment()
            }
            this.applyDefaultUser()
        },
        openEdit(record, action = null) {
            if (!record) return

            this.edit = true
            this.canEditUserForEdit = this.resolveEditUserAccess(action)

            const formData = JSON.parse(JSON.stringify(record))
            const parts = this.secondsToHMS(formData.duration)

            this.form = {
                ...this.getEmptyForm(),
                duration: formData.duration,
                duration_h: parts.h,
                duration_m: parts.m,
                duration_s: parts.s,
                description: formData.description,
                date: this.$moment(formData.date),
                id: formData.id,
                user: this.canEditUserForEdit ? (formData.user || this.getDefaultUser()) : null,
                is_result: !!formData.is_result
            }
            this.visible = true
        },
        addAccounting() {
            this.edit = false
            this.canEditUserForEdit = false
            this.form.date = this.$moment()
            if (this.canEditUserForCreate) {
                this.form.user = this.getDefaultUser()
            } else {
                this.form.user = null
            }
            this.visible = true
        },
        hmsToSeconds(h, m, s) {
            const hh = Number(h || 0)
            const mm = Number(m || 0)
            const ss = Number(s || 0)
            return hh * 3600 + mm * 60 + ss
        },
        secondsToHMS(total) {
            const t = Number(total || 0)
            const h = Math.floor(t / 3600)
            const m = Math.floor((t % 3600) / 60)
            const s = t % 60
            return { h, m, s }
        },
        onSubmit() {
            this.$refs.ruleForm.validate(async valid => {
                if (!valid) return false

                const total = this.hmsToSeconds(this.form.duration_h, this.form.duration_m, this.form.duration_s)
                if (!total) {
                    this.$message.error(this.$t('helpdesk.specify_time'))
                    return false
                }

                try {
                    this.loading = true
                    const queryData = {
                        duration: total,
                        date: this.form.date.format('YYYY-MM-DD'),
                        description: this.form.description,
                        is_result: !!this.form.is_result
                    }
                    if (this.canEditUser) {
                        const userId = this.extractUserId(this.form.user)
                        if (userId) queryData.user = userId
                    }

                    if (this.edit) {
                        if (this.form?.id) queryData.id = this.form.id
                        const { data } = await this.$http.put(`/help_desk/tickets/${this.ticket.id}/work_log/update/`, queryData)
                        if (data) {
                            eventBus.$emit(`update_filter_${this.model}_${this.page_name}`)
                            this.$message.success(this.$t('helpdesk.work_effort_updated'))
                            this.visible = false
                        }
                    } else {
                        const { data } = await this.$http.post(`/help_desk/tickets/${this.ticket.id}/work_log/create/`, queryData)
                        if (data) {
                            eventBus.$emit(`update_filter_${this.model}_${this.page_name}`)
                            this.$message.success(this.$t('helpdesk.work_effort_added'))
                            this.visible = false
                        }
                    }

                    this.getTimer()
                } catch (error) {
                    errorHandler({ error })
                } finally {
                    this.loading = false
                }
            })
        }
    },
    mounted() {
        // ✅ добавили: слушаем общий update_filter, чтобы мобилка перезагружалась и после edit, и после delete
        eventBus.$on(`update_filter_${this.model}_${this.page_name}`, this.onMobileUpdate)

        eventBus.$on(`edit_accounting_${this.ticket?.id || 'new'}`, payload => {
            if (payload?.record) {
                this.openEdit(payload.record, payload.action)
                return
            }
            this.openEdit(payload)
        })
    },
    beforeDestroy() {
        // ✅ добавили off
        eventBus.$off(`update_filter_${this.model}_${this.page_name}`, this.onMobileUpdate)

        eventBus.$off(`edit_accounting_${this.ticket?.id || 'new'}`)
    }
}
</script>

<style lang="scss" scoped>
.time_block {
    background: #f7f9fc;
    border-radius: 12px;
    padding: 15px;
    &__label {
        margin-bottom: 10px;
        line-height: 16px;
    }
    .item_block {
        &__label {
            color: #888888;
            line-height: 16px;
            margin-bottom: 5px;
        }
    }
}
</style>
