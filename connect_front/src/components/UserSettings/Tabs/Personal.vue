<template>
    <div v-if="form">
        <div class="my_personal" ref="personalTab">
            <a-form-model
                ref="profileForm"
                :model="form"
                :rules="rules">
                <a-row :gutter="30">
                    <a-col :md="recBlock ? 15 : 18" :xl="17">
                        <a-row :gutter="15">
                            <a-col :md="12" :xl="8">
                                <a-form-model-item ref="last_name" :label="$t('last_name')" prop="last_name">
                                    <a-input v-model="form.last_name" size="large" />
                                </a-form-model-item>
                            </a-col>
                            <a-col :md="12" :xl="8">
                                <a-form-model-item ref="first_name" :label="$t('first_name')" prop="first_name">
                                    <a-input v-model="form.first_name" size="large" />
                                </a-form-model-item>
                            </a-col>
                            <a-col :md="12" :xl="8">
                                <a-form-model-item ref="middle_name" :label="$t('middle_name')" prop="middle_name">
                                    <a-input v-model="form.middle_name" size="large" />
                                </a-form-model-item>
                            </a-col>
                            <a-col :md="12" :xl="8">
                                <a-form-model-item ref="job_title" :label="$t('job_title')" prop="job_title">
                                    <a-input v-model="form.job_title" size="large" />
                                </a-form-model-item>
                            </a-col>
                            <a-col :md="12" :xl="8">
                                <a-form-model-item ref="contact_phone" :label="$t('contact_phone')" prop="contact_phone">
                                    <a-input v-model="form.contact_phone" size="large" />
                                </a-form-model-item>
                            </a-col>
                            <a-col :md="12" :xl="8">
                                <a-form-model-item ref="birthday" :label="$t('birthday')" prop="birthday">
                                    <a-date-picker 
                                        v-model="form.birthday" 
                                        :showToday="false"
                                        :getCalendarContainer="getCalendarContainer"
                                        :placeholder="$t('select_date')"
                                        dropdownClassName="birthday_select"
                                        format="DD.MM.YYYY"
                                        size="large" 
                                        style="width: 100%;" />
                                </a-form-model-item>
                            </a-col>
                            <a-col :span="24">
                                <a-form-model-item ref="is_make_events_in_task_automatically" prop="is_make_events_in_task_automatically" class="mb-2">
                                    <a-checkbox :checked="form.is_make_events_in_task_automatically" class="event_auto_check" @change="changeEventAuto">
                                        {{$t('is_make_events_in_task_automatically')}}
                                    </a-checkbox>
                                </a-form-model-item>
                            </a-col>
                            <a-col :span="24"></a-col>
                            <a-col :span="24">
                                <a-button type="primary" :block="isMobile" :loading="loading" size="large" @click="formSubmit()">
                                    {{$t('save')}}
                                </a-button>
                            </a-col>
                            <a-col :span="24">
                                <div class="mt-5" />
                            </a-col>
                            <a-col :md="24" :xl="24">
                                <a-row :gutter="30">
                                    <a-col :md="24" :xl="12">
                                        <a-form-model-item ref="org" :label="$t('Default organization')" prop="org" class="mb-2">
                                            <a-spin size="small" :spinning="orgLoading">
                                                <OrgSelect
                                                    v-model="form.org"
                                                    inputType="defaultInput"
                                                    :placeholder="$t('Default organization')"
                                                    :selectProject="selectOrg"
                                                    :showDefaultOrganizationSwitcher="false" />
                                            </a-spin>
                                        </a-form-model-item>
                                    </a-col>
                                </a-row>
                            </a-col>
                            <a-col :md="24" :xl="24">
                                <a-row :gutter="30">
                                    <a-col :md="24" :xl="12">
                                        <a-form-model-item ref="timezone" :label="$t('timezone')" prop="timezone" class="mb-2">
                                            <div class="timezone_field">
                                                <a-select
                                                    v-model="form.timezone"
                                                    :disabled="form.timezone_auto_detect || timezoneLoading"
                                                    :loading="timezoneLoading"
                                                    show-search
                                                    size="large"
                                                    :filter-option="false"
                                                    :not-found-content="$t('no_data')"
                                                    :getPopupContainer="getSelectPopupContainer"
                                                    :placeholder="$t('select_timezone')"
                                                    @change="changeTimezone"
                                                    @search="handleTimezoneSearch"
                                                    @dropdownVisibleChange="handleTimezoneDropdownVisibleChange">
                                                    <a-select-opt-group
                                                        v-for="group in filteredTimezoneGroups"
                                                        :key="group.key">
                                                        <span slot="label">{{ group.label }}</span>
                                                        <a-select-option
                                                            v-for="option in group.options"
                                                            :key="option.value"
                                                            :value="option.value">
                                                            {{ option.label }}
                                                        </a-select-option>
                                                    </a-select-opt-group>
                                                </a-select>
                                                <a-checkbox :checked="form.timezone_auto_detect" :disabled="timezoneLoading" class="timezone_auto_detect_checkbox" @change="changeTimezoneAutoDetect">
                                                    {{ $t('timezone_auto_detect') }}
                                                </a-checkbox>
                                            </div>
                                        </a-form-model-item>
                                    </a-col>
                                </a-row>
                            </a-col>
                        </a-row>
                        <template v-if="!isMobile">
                            <div v-if="tgBotLink" class="flex mt-6">
                                <qr-code :size="100" :text="tgBotLink"></qr-code>
                                <span class="ml-2">{{$t('qr_code_info')}}
                                    <a class="blue_colors" target="_blank" :href="tgBotLink">{{$t('by_link')}}</a></span>
                            </div>
                            <div class="flex mt-6">
                                <a-button
                                    type="ui"
                                    size="large"
                                    :block="isMobile"
                                    :loading="unsubLoading"
                                    @click="unsubscribe()">
                                    {{$t('unsubscribe')}}
                                </a-button>
                            </div>
                        </template>
                    </a-col>
                    <a-col v-if="recBlock" :md="9" :xl="7" :class="isMobile && 'mt-4'">
                        <div class="recommendations_block">
                            <h4>{{$t('recommendations')}}</h4>
                            <div class="list">
                                <div v-if="!user.last_name" class="item">
                                    <i class="fi fi-rr-cross-small"></i> {{$t('fill_last_name')}}
                                </div>
                                <div v-if="!user.first_name" class="item">
                                    <i class="fi fi-rr-cross-small"></i> {{$t('fill_first_name')}}
                                </div>
                                <div v-if="!user.middle_name" class="item">
                                    <i class="fi fi-rr-cross-small"></i> {{$t('fill_middle_name')}}
                                </div>
                                <div v-if="!user.job_title" class="item">
                                    <i class="fi fi-rr-cross-small"></i> {{$t('fill_job_title')}}
                                </div>
                                <div v-if="!user.birthday" class="item">
                                    <i class="fi fi-rr-cross-small"></i> {{$t('fill_birthday')}}
                                </div>
                                <div v-if="!user.avatar" class="item">
                                    <i class="fi fi-rr-cross-small"></i> {{$t('upload_avatar')}}
                                </div>
                            </div>
                        </div>
                        <template v-if="isMobile">
                            <div v-if="tgBotLink" class="flex mt-6">
                                <qr-code :size="100" :text="tgBotLink"></qr-code>
                                <span class="ml-2">{{$t('qr_code_info')}}
                                    <a class="blue_colors" target="_blank" :href="tgBotLink">{{$t('by_link')}}</a></span>
                            </div>
                            <div class="flex mt-6">
                                <a-button
                                    type="ui"
                                    size="large"
                                    :block="isMobile"
                                    :loading="unsubLoading"
                                    @click="unsubscribe()">
                                    {{$t('unsubscribe')}}
                                </a-button>
                            </div>
                        </template>
                    </a-col>
                </a-row>
            </a-form-model>
        </div>
    </div>
</template>

<script>
import { mapState } from 'vuex'
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'
import { buildTimezoneGroups, getBrowserTimeZone } from '@/utils/timezones'
export default {
    components: {
        QrCode: () => import('vue-qrcode-component'),
        OrgSelect: () => import('@/modules/DrawerSelect/OrgSelect.vue')
    },
    computed: {
        ...mapState({
            user: state => state.user.user,
            isMobile: state => state.isMobile
        }),
        filteredTimezoneGroups() {
            if (!this.timezoneSearch) {
                return this.timezoneGroups
            }

            const normalizedSearch = this.timezoneSearch.trim().toLowerCase()

            return this.timezoneGroups
                .map(group => ({
                    ...group,
                    options: group.options.filter(option => option.searchText.includes(normalizedSearch))
                }))
                .filter(group => group.options.length)
        },
        recBlock() {
            if(this.user) {
                return !this.user.last_name || !this.user.first_name || !this.user.middle_name || !this.user.avatar || !this.user.job_title || !this.user.birthday
            }
            return false
        },
        tgBotURL() {
            return this.$store?.state?.config?.config?.tg_bot_settings?.url
        },
        tgBotLink() {
            if (this.user) {
                return `${this.tgBotURL}?start=${this.user.telegram_connect_token}`
            }
            return null
        }
    },
    data() {
        return {
            loading: false,
            unsubLoading: false,
            orgLoading: false,
            timezoneLoading: false,
            timezoneSearch: '',
            timezoneGroups: [],
            form: null,
            rules: {
                last_name: [
                    { required: true, message: this.$t('field_required'), trigger: 'change' },
                    { max: 255, message: this.$t('required_sym', { sym: 255 }), trigger: 'change' },
                ],
                first_name: [
                    { required: true, message: this.$t('field_required'), trigger: 'change' },
                    { max: 255, message: this.$t('required_sym', { sym: 255 }), trigger: 'change' },
                ]
            }
        }
    },
    created() {
        this.getMyOrganization()
        this.timezoneGroups = buildTimezoneGroups({
            locale: this.getTimezoneLocale(),
            translate: key => this.$t(key)
        })
        this.form = {
            ...this.user,
            org: null,
            job_title: this.user.job_title || '',
            contact_phone: this.user.contact_phone || '',
            birthday: this.user.birthday ? this.$moment(this.user.birthday) : null,
            timezone: this.user.timezone || getBrowserTimeZone(),
            timezone_auto_detect: !!this.user.timezone_auto_detect
        }
    },
    methods: {
        getTimezoneLocale() {
            const localeMap = {
                ru: 'ru-RU',
                kk: 'kk-KZ',
                en: 'en-GB'
            }

            return localeMap[this.user?.language] || 'en-GB'
        },
        async selectOrg(work) {
            try {
                this.orgLoading = true
                await this.$http.post('/users/current_contractor/change/', {
                    id: work.id
                })
                if(work)
                    this.$store.commit('user/CHANGE_USER_ORG', work)
                this.$nextTick(() => {
                    eventBus.$emit('support_current_contractor_changed', {
                        contractorId: work?.id || null
                    })
                })
            } catch(error) {
                errorHandler({error})
            } finally {
                this.orgLoading = false
            }
        },
        async getMyOrganization() {
            try {
                this.orgLoading = true
                const { data } = await this.$http.get('/users/current_contractor/detail/')
                if(data) {
                    this.form.org = data
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.orgLoading = false
            }
        },
        changeEventAuto() {
            this.form.is_make_events_in_task_automatically = !this.form.is_make_events_in_task_automatically
        },
        syncUserProfile(updatedUser) {
            if (!updatedUser) {
                return
            }

            localStorage.setItem('user', JSON.stringify(updatedUser))
            this.$store.commit('user/SET_USER', updatedUser)
            this.form = {
                ...this.form,
                ...updatedUser,
                org: this.form.org
            }
            eventBus.$emit('user_profile_updated')
        },
        async updateTimezoneProfile(payload, rollback) {
            try {
                this.timezoneLoading = true
                const { data } = await this.$http.put('users/update_profile/', payload)
                if (data) {
                    this.syncUserProfile(data)
                }
            } catch (error) {
                if (rollback) {
                    rollback()
                }
                errorHandler({error})
            } finally {
                this.timezoneLoading = false
            }
        },
        async changeTimezone(timezone) {
            const previousTimezone = this.user?.timezone || this.form.timezone
            this.form.timezone = timezone
            await this.updateTimezoneProfile(
                { timezone },
                () => {
                    this.form.timezone = previousTimezone
                }
            )
        },
        async changeTimezoneAutoDetect(event) {
            const nextValue = !!event.target.checked
            const previousValue = this.form.timezone_auto_detect
            this.form.timezone_auto_detect = nextValue
            if (nextValue) {
                this.form.timezone = getBrowserTimeZone()
            }

            await this.updateTimezoneProfile(
                { timezone_auto_detect: nextValue },
                () => {
                    this.form.timezone_auto_detect = previousValue
                    if (previousValue) {
                        this.form.timezone = getBrowserTimeZone()
                    } else {
                        this.form.timezone = this.user?.timezone || this.form.timezone
                    }
                }
            )
        },
        getCalendarContainer() {
            return this.$refs['personalTab']
        },
        getSelectPopupContainer(trigger) {
            return trigger.parentNode
        },
        handleTimezoneSearch(value) {
            this.timezoneSearch = value
        },
        handleTimezoneDropdownVisibleChange(isVisible) {
            if (!isVisible) {
                this.timezoneSearch = ''
            }
        },
        async unsubscribe() {
            try {
                this.unsubLoading = true
                const {data} = await this.$http.post('notifications/tg_unsubscribe/', {})
                if(data) {
                    this.$message.info(this.$t('tg_unsubscribe_success'))
                }
            } catch(error) {
                errorHandler({error})
            } finally {
                this.unsubLoading = false
            }
        },
        async formSubmit() {
            this.$refs.profileForm.validate(async valid => {
                if (valid) {
                    try {
                        this.loading = true
                        const userForm = {...this.form}
                        if (userForm.timezone_auto_detect) {
                            userForm.timezone = getBrowserTimeZone()
                        }
                        if(userForm.birthday) {
                            userForm.birthday = this.$moment(userForm.birthday).format('YYYY-MM-DD')
                        }
                        const { data } = await this.$http.put('users/update_profile/', userForm)
                        if(data) {
                            localStorage.setItem('user', JSON.stringify(data))
                            this.$store.commit('user/SET_USER', data)
                            this.$message.success(this.$t('data_updated'))
                            eventBus.$emit('user_profile_updated')
                        }
                    } catch(error) {
                        errorHandler({error})
                    } finally {
                        this.loading = false
                    }
                } else {
                    this.$message.warning(this.$t('check_data'))
                }
            })
        }
    }
}
</script>


<style lang="scss" scoped>
.event_auto_check{
    display: flex;
    align-items: center;
    &::v-deep{
        .ant-checkbox + span{
            line-height: 22px;
        }
    }
}
.my_personal{
    .timezone_field{
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    .timezone_auto_detect_checkbox{
        display: flex;
        align-items: center;
        margin-top: 0;
        line-height: 22px;
        margin-top: 5px;
        &::v-deep{
            .ant-checkbox + span{
                line-height: 22px;
                padding-left: 8px;
            }
        }
    }
    .item{
        display: flex;
        &:not(:last-child){
            margin-bottom: 15px;
        }
        .label{
            min-width: 200px;
            font-weight: 300;
        }
    }
}
.recommendations_block{
    background-color: #eff2f5;
    border-radius: var(--borderRadius);
    padding: 15px;
    h4{
        margin-bottom: 15px;
        font-size: 18px;
        font-weight: 600;
    }
    .list{
        .item{
            display: flex;
            align-items: center;
            i{
                font-size: 18px;
                margin-right: 3px;
                color: var(--red);
            }
            &:not(:last-child){
                margin-bottom: 10px;
            }
        }
    }
}
</style>
