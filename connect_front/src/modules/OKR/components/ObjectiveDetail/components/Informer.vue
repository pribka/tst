<template>
    <a-spin :spinning="loading">
        <a-form-model
            ref="ruleForm"
            :model="form"
            class="mini_form okr-details-informer"
            :rules="rules">
            <ListView inline labelDark>
                <!-- <ListViewItem :title="$t('okr.progress')">
                    <div class="progress">
                        <a-progress
                            class="custom-progress"
                            :percent="percent"
                            :show-info="false"
                            :strokeWidth="12"
                            strokeColor="#4777FF" />
                        <span class="value">{{ percent }}%</span>
                    </div>
                </ListViewItem> -->
                <!-- <ListViewItem :title="$t('okr.status')">
                    <a-form-model-item v-if="edit" ref="status" label="" prop="status">
                        <DSelect
                            v-model="form.status"
                            apiUrl="/okr/objectives/objective_statuses/"
                            class="okr-status-select"
                            :class="`okr-status-select-${form.status}`"
                            size="default"
                            inputType="ghost"
                            showPlaceholder
                            :placeholder="$t('okr.objectiveStatus')"
                            :listObject="false"
                            labelKey="name"
                            valueKey="code"
                            :default-active-first-option="false"
                            :filter-option="false"
                            :not-found-content="null"
                            @change="dataChange({field: 'status'})" />
                    </a-form-model-item>
                    <span v-else>
                        <a-tag :color="objective.status.color">
                            {{ objective.status.name }}
                        </a-tag>
                    </span>
                </ListViewItem> -->
                <ListViewItem :title="$t('okr.organization')">
                    <div v-if="objective.organization">
                        <div class="organization">
                            <a-avatar 
                                :size="20"
                                :src="objective.organization.logo"
                                icon="fi-rr-users-alt" 
                                flaticon />
                            <span>{{ objective.organization.name }}</span>
                        </div>
                    </div>
                    <div v-else class='text-gray-300'>
                        {{ $t('okr.organizationNotSpecified') }}
                    </div>
                </ListViewItem>
                <ListViewItem :title="$t('okr.department')">
                    <a-form-model-item v-if="edit" ref="department" label="" prop="department">
                        <DSelect
                            v-model="form.department"
                            :apiUrl="`users/my_organizations/${currentContractor.id}/departments_select_list/`"
                            class="w-full"
                            size="default"
                            allowClear
                            infinity
                            inputType="ghost"
                            showPlaceholder
                            :placeholder="$t('okr.department')"
                            :listObject="false"
                            labelKey="name"
                            resultsKey="results"
                            :default-active-first-option="false"
                            :filter-option="false"
                            :not-found-content="null"
                            @change="dataChange({field: 'department'})" />
                    </a-form-model-item>
                    <span v-else>
                        <div v-if="objective.department" class="organization">
                            <a-avatar 
                                :size="20"
                                :src="objective.department.logo"
                                icon="fi-rr-users-alt" 
                                flaticon />
                            <span>{{ objective.department.name }}</span>
                        </div>
                        <div v-else class='text-gray-300'>
                            {{ $t('okr.notSelected') }}
                        </div>
                    </span>
                </ListViewItem>
                <!-- <ListViewItem :title="$t('okr.priority')">
                    <a-form-model-item v-if="edit" ref="value_efforts" label="" prop="value_efforts">
                        <DSelect
                            v-model="form.value_efforts"
                            :initOptionList="valueEfforts"      
                            useOptionsBadge
                            class="w-full"
                            oneSelect
                            infinity
                            allowClear
                            size="default"
                            inputType="ghost"
                            :useOptionFlex="false"
                            useSearchApi
                            showPlaceholder
                            :placeholder="$t('okr.selectPriority')"
                            searchKey="text"
                            labelKey="name"
                            valueKey="code"
                            :listObject="false"
                            :default-active-first-option="false"
                            :filter-option="false"
                            :not-found-content="null"
                            @change="dataChange({field: 'value_efforts'})">
                        </DSelect>
                    </a-form-model-item>
                    <div v-else>
                        <a-badge
                            v-if="objective.value_efforts"
                            :color="badgeColor"
                            :text="badgeName" />
                        <div v-else class='text-gray-300'>
                            {{ $t('okr.notSelected') }}
                        </div>
                    </div>
                </ListViewItem> -->
                <ListViewItem :title="$t('okr.remind')">
                    <a-form-model-item v-if="edit" ref="remind" label="" prop="remind">
                        <DSelect
                            v-model="form.notification"
                            :initOptionList="reminders"
                            class="w-full"
                            oneSelect
                            infinity
                            allowClear
                            size="default"
                            inputType="ghost"
                            :useOptionFlex="false"
                            useSearchApi
                            showPlaceholder
                            :placeholder="$t('okr.setReminder')"
                            searchKey="text"
                            labelKey="name"
                            valueKey="code"
                            :listObject="false"
                            :default-active-first-option="false"
                            :filter-option="false"
                            :not-found-content="null"
                            @change="dataChange({field: 'notification'})">
                        </DSelect>
                    </a-form-model-item>
                    <div v-else>
                        <div v-if="objective.notification" class="obj-visibility">{{ objective.notification.name }}</div>
                        <div v-else class='text-gray-300'>
                            {{ $t('okr.notSelected') }}
                        </div>
                    </div>
                </ListViewItem>
                <ListViewItem :title="$t('okr.owner')">
                    <a-form-model-item v-if="edit" ref="owner" label="" prop="owner">
                        <DSelect
                            v-model="form.owner"
                            :initOptionList="stakeholders"
                            class="w-full"
                            oneSelect
                            size="default"
                            inputType="ghost"
                            :useOptionFlex="false"
                            useSearchApi
                            showPlaceholder
                            :placeholder="$t('okr.selectAuthor')"
                            searchKey="text"
                            labelKey="full_name"
                            :listObject="false"
                            :default-active-first-option="false"
                            :filter-option="false"
                            :not-found-content="null"
                            @change="dataChange({field: 'owner'})" />
                    </a-form-model-item>
                    <span v-else>
                        <Profiler
                            v-if="objective.owner"
                            :popoverText="$t('okr.owner')"
                            :avatarSize="20"
                            class="obj-profiler"
                            nameClass="text-sm"
                            :user="objective.owner" />
                        <div v-else class='text-gray-300'>
                            {{ $t('okr.notSelected') }}
                        </div>
                    </span>
                </ListViewItem>
                <ListViewItem :title="$t('okr.operator')">
                    <a-form-model-item v-if="edit" ref="operator" label="" prop="operator">
                        <DSelect
                            v-model="form.operator"
                            :initOptionList="stakeholders"
                            class="w-full"
                            oneSelect
                            size="default"
                            inputType="ghost"
                            :useOptionFlex="false"
                            useSearchApi
                            showPlaceholder
                            :placeholder="$t('okr.selectAssignee')"
                            searchKey="text"
                            labelKey="full_name"
                            :listObject="false"
                            :default-active-first-option="false"
                            :filter-option="false"
                            :not-found-content="null"
                            @change="dataChange({field: 'operator'})" />
                    </a-form-model-item>
                    <span v-else>
                        <Profiler
                            v-if="objective.operator"
                            :popoverText="$t('okr.operator')"
                            :avatarSize="20"
                            class="obj-profiler"
                            nameClass="text-sm"
                            :user="objective.operator" />
                        <div v-else class='text-gray-300'>
                            {{ $t('okr.notSelected') }}
                        </div>
                    </span>
                </ListViewItem>
                <ListViewItem :title="$t('okr.timelines')">
                    <a-form-model-item v-if="edit" ref="period" prop="period" class="form-item">
                        <a-range-picker
                            class="w-full"
                            :allowClear="false"
                            inputType="ghost"
                            :getCalendarContainer="trigger => trigger.parentElement"
                            :locale="locale"
                            :ranges="ranges"
                            v-model="form.period"
                            :placeholder="[$t('okr.startDate'), $t('okr.endDate')]"
                            :valueFormat="dateFormat"
                            format="DD.MM.YYYY"
                            @change="dataChange({field: 'period'})">
                            <i slot="suffixIcon" class="fi fi-rr-calendar"></i>
                        </a-range-picker>
                    </a-form-model-item>
                    <template v-else>
                        {{ `${$moment(objective.date_start).format('DD.MM.YYYY')} - ${$moment(objective.date_end).format('DD.MM.YYYY')}` }}
                    </template>
                </ListViewItem>
                <ListViewItem :title="$t('okr.privacy')" :class="(edit && form.is_public === undefined) && 'error'">
                    <a-form-model-item v-if="edit" ref="is_public" label="" prop="is_public">
                        <DSelect
                            v-model="form.is_public"
                            :disabled="form.is_public === 'withVisors'"
                            :initOptionList="publicOptions"
                            class="w-full"
                            oneSelect
                            size="default"
                            inputType="ghost"
                            :useOptionFlex="false"
                            useSearchApi
                            showPlaceholder
                            :placeholder="$t('okr.selectIsPublic')"
                            searchKey="text"
                            valueKey="value"
                            labelKey="name"
                            :listObject="false"
                            :default-active-first-option="false"
                            :filter-option="false"
                            :not-found-content="null" />
                    </a-form-model-item>
                    <span v-else>
                        <div class="obj-visibility">{{ visibility[objectiveVisibility] }}</div>
                    </span>
                </ListViewItem>
                <ListViewItem v-if="showVisors" :title="$t('okr.visors')">
                    <a-form-model-item v-if="edit" ref="visors" label="" prop="visors">
                        <UserDrawer
                            :id="form.id || ''"
                            :taskId="form.id ? form.id : null"
                            class="w-full"
                            v-model="form.visors"
                            :title="$t('okr.selectWatchers')"
                            :inputPlaceholder="$t('okr.selectWatchers')"
                            multiple
                            inputType="ghost"
                            :metadata="{ key: 'visors', value: form.metadata }"
                            :changeMetadata="changeMetadata" />
                    </a-form-model-item>
                    <span v-else>
                        <div v-if="objective.visors.length" class="obj-visors">
                            <Profiler
                                :avatarSize="20"
                                class="obj-profiler"
                                nameClass="text-sm"
                                :user="objective.visors[0]" />
                            <a-popover v-if="objective.visors.length > 1" overlayClassName="more-users-list">
                                <template slot="content">
                                    <div class="users-list">
                                        <Profiler
                                            v-for="user in objective.visors.slice(1)"
                                            :key="user.id"
                                            :avatarSize="20"
                                            nameClass="text-sm"
                                            :user="user" />
                                    </div>
                                </template>
                                <div class="more">
                                    {{ `+ Еще ${objective.visors.length - 1}` }}
                                </div>
                            </a-popover>
                        </div>
                        <div v-else class='text-gray-300'>
                            {{ $t('okr.notSelected') }}
                        </div>
                    </span>
                </ListViewItem>
            </ListView>
        </a-form-model>
    </a-spin>
</template>
<script>
import { mapState, mapMutations, mapActions, mapGetters } from 'vuex'
import DSelect from '@apps/DrawerSelect/Select.vue'
import UserDrawer from '@apps/DrawerSelect/index.vue'
import locale from 'ant-design-vue/es/date-picker/locale/ru_RU'
import ranges from '@apps/OKR/mixins/ranges'

export default {
    name: 'Informer',
    components: {
        DSelect,
        UserDrawer
    },
    data() {
        return {
            dateFormat: 'YYYY-MM-DD',
            loading: false,
            locale,
            form: {
                status: undefined,
                period: [],
                parent: undefined,
                owner: undefined,
                operator: undefined,
                department: undefined,
                is_public: undefined,
                value_efforts: undefined,
                notification: 'never',
                visors: [],
                metadata: {
                    visors: []
                },
            },
            rules: {},
            publicOptions: [
                {
                    name: this.$t('okr.visibleToAll'),
                    value: 'isPublic',
                },
                {
                    name: this.$t('okr.visibleToMe'),
                    value: 'onlyOwner',
                },
                {
                    name: this.$t('okr.addWatchers'),
                    value: 'withVisors',
                },
            ],
            visibility: {
                isPublic: this.$t('okr.visibleToAll'),
                onlyOwner: this.$t('okr.visibleToMe'),
                withVisors: this.$t('okr.addWatchers'),
            }
        }
    },
    mixins: [
        ranges
    ],
    created() {
        if(this.edit) {
            this.fillForm()
        }
    },
    watch: {
        'form.visors.length': {
            handler(newValue, oldValue) {
                if (newValue > 0) {
                    this.form.is_public = 'withVisors'
                }
                if (newValue === 0 && oldValue > newValue) {
                    this.form.is_public = undefined
                }
                this.dataChange({field: 'visors'})
            }
        },
        'form.is_public': {
            handler(newValue, oldValue) {
                if (newValue !== 'withVisors') {
                    this.form.visors = []
                    this.changeMetadata({
                        key: 'visors',
                        value: [] 
                    })
                    this.dataChange({field: 'is_public'})
                }
            }
        }
    },
    computed: {
        ...mapState({
            currentContractor: state => state.user.user.current_contractor || null,
            objective: state => state.okr.objectiveDetail,
            reminders: state => state.okr.reminders,
            stakeholders: state => state.okr.stakeholders,
            valueEfforts: state => state.okr.valueEfforts,
        }),
        ...mapGetters({
            objectiveVisibility: 'okr/objectiveVisibility'
        }),
        badgeColor() {
            return this.objective?.value_efforts?.hex_color ? this.objective.value_efforts.hex_color : undefined
        },
        badgeName() {
            return this.objective?.value_efforts?.name ? this.objective.value_efforts.name : ''
        },
        edit() {
            return !!this.objective?.actions?.edit
        },
        period() {
            return `${this.$moment(this.objective.date_start).format(this.dateFormat)} - ${this.$moment(this.objective.date_end).format(this.dateFormat)}`
        },
        percent() {
            return parseInt(this.objective.progress*100)
        },
        organization() {
            return this.objective.organization ? this.objective.organization.name : this.$t('okr.notSpecified')
        },
        department() {
            return this.objective.department ? this.objective.department.name : this.objective.organization ? this.objective.organization.name : this.$t('okr.notSpecified')
        },
        parent() {
            return this.objective.parent ? this.objective.parent.objective : '-'
        },
        showVisors() {
            if (this.edit) {
                return this.form.is_public === 'withVisors'
            } else {
                return !!this.objective.visors.length
            }
        }
    },
    methods: {
        ...mapMutations({
            SET_OBJECTIVE_DETAIL: 'okr/SET_OBJECTIVE_DETAIL',
            UPDATE_OBJECTIVE_ON_LIST: 'okr/UPDATE_OBJECTIVE_ON_LIST'
        }),
        ...mapActions({
            fetchKeyResults: 'okr/fetchKeyResults'
        }),
        changeMetadata({ key, value }) {
            this.$set(this.form.metadata, key, value)
        },
        fillForm() {
            this.form.period = [
                this.objective.date_start,
                this.objective.date_end
            ]
            this.form.parent = this.objective?.parent?.id || null
            if (this.objective?.parent?.id) {
                this.form.parent = this.objective.parent.id
            }
            if (this.objective?.status?.code) {
                this.form.status = this.objective.status.code
            }
            if (this.objective?.department?.id) {
                this.form.department = this.objective.department.id
            }
            if (this.objective?.operator?.id) {
                this.form.operator = this.objective.operator.id
            }
            if (this.objective?.owner?.id) {
                this.form.owner = this.objective.owner.id
            }
            this.form.value_efforts = this.objective?.value_efforts?.code || null
            this.form.notification = this.objective?.notification?.code || null
            this.form.visors = this.objective.visors
            this.form.is_public = String(this.objective.is_public)
            if (this.objective.is_public) {
                this.form.is_public = 'isPublic'
            } else if (this.form.visors.length) {
                this.form.is_public = 'withVisors'
            } else {
                this.form.is_public = 'onlyOwner'
            }
        },
        dataChange({field, useTimer = false, valueKey = false, multiple = false}) {
            let payload = {}
            let patch = false
            switch (field) {
            case 'status':
                payload.status = this.form.status
                patch = true
                break
            case 'period':
                payload = {
                    date_start: this.$moment(this.form.period[0]).format('YYYY-MM-DD'),
                    date_end: this.$moment(this.form.period[1]).format('YYYY-MM-DD')
                }
                patch = true
                break
            case 'owner':
                payload.owner = this.form.owner
                patch = true
                break
            case 'operator':
                payload.operator = this.form.operator
                patch = true
                break
            case 'value_efforts':
                payload.value_efforts = this.form.value_efforts ? this.form.value_efforts : null
                patch = true
                break
            case 'notification':
                payload.notification = this.form.notification ? this.form.notification : null
                patch = true
                break
            case 'department':
                if (this.form.department) {
                    payload = {
                        department: this.form.department
                    }
                } else {
                    this.form.parent = undefined
                    payload = {
                        department: null,
                        parent: null
                    }
                }
                patch = true
                break
            case 'is_public':
                if (this.form.is_public === 'isPublic' || this.form.is_public === 'onlyOwner') {
                    payload = {
                        is_public: this.form.is_public === 'isPublic',
                        visors: []
                    }
                    patch = true
                }
                break
            case 'visors':
                if (this.form.visors.length !== 0) {
                    payload = {
                        is_public: false,
                        visors: this.form.visors.map(visor => visor.id)
                    }
                    patch = true
                }
                break
            }  
            if (patch)
                this.patchObjective(payload, field)
        },
        async patchObjective(payload, field) {
            this.loading = true
            try {
                const { data } = await this.$http.patch(`okr/objectives/${this.objective.id}/`, payload)
                if (data) {
                    this.UPDATE_OBJECTIVE_ON_LIST({
                        objectiveID: this.objective.id,
                        data: data
                    })
                    if (this.objective) {
                        this.SET_OBJECTIVE_DETAIL(data)
                    }
                    if (field === 'period') {
                        this.fetchKeyResults({
                            objectiveID: this.objective.id
                        })
                    }
                }
            } catch(e) {
                this.$message.error(this.$t('okr.saveDataFailed'))
                this.fillForm()
            } finally {
                this.loading = false
            }

        }
    }
}
</script>
<style lang="scss" scoped>
.okr-details-informer {
    .progress {
        display: flex;
        gap: 8px;
        align-items: center;
        .custom-progress {
            flex: 1;
        }
    }
    .organization {
        display: flex;
        gap: 8px;
        align-items: center;
    }
    .obj-visibility {
            border-radius: 8px;
            width: fit-content;
            padding: 4px 8px;
            background: #FFF;
            color: #4777FF;
    }
    .obj-visors {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
    }
    .obj-profiler {
        width: fit-content;
        display: flex;
        align-items: center;
        padding-left: 8px;
        padding-right: 8px;
        height: 28px;
        border-radius: 8px;
        background-color: #E8EDFA;
    }
    .more {
        background: #E8EDFA;
        border-radius: 8px;
        height: 28px;
        line-height: 28px;
        padding-left: 10px;
        padding-right: 10px;
    }
    
}
</style>
<style lang="scss">
.more-users-list {
    .users-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
        max-height: 170px;
        overflow-y: auto;
        overflow-x: hidden;
        padding-right: 4px;
    }
}
.error {
    .item_label {
        color: red !important;
    }
    .ant-select {
        background-color: rgba(255, 0, 0, 0.05);
        border-radius: 8px;
        padding-left: 8px;
    }
}
.okr-status-select {
    &.okr-status-select-as_planned {
        .ant-select-selection{
            background-color: #e6efe3;
            color: #368225;
            padding-left: 8px;
        }
    }
    &.okr-status-select-at_risk {
        .ant-select-selection{
            background-color: #feffe6;
            color: #fadb14;
            padding-left: 8px;
        }
    }
    &.okr-status-select-lags_behind {
        .ant-select-selection{
            background-color: #fdd5d5;
            color: #FF5C5C;
            padding-left: 8px;
        }
    }
    &.okr-status-select-achieved {
        .ant-select-selection{
            background-color: #e6fffb;
            color: #13c2c2;
            padding-left: 8px;
        }
    }
    &.okr-status-select-partly_achieved {
        .ant-select-selection{
            background-color: #e8ecfa;
            color: #4777FF;
            padding-left: 8px;
        }
    }
    &.okr-status-select-not_achieved {
        .ant-select-selection{
            background-color: #f9f0ff;
            color: #722ed1;
            padding-left: 8px;
        }
    }
    &.okr-status-select-abandoned {
        .ant-select-selection{
            background-color: #fffbe6;
            color: #faad14;
            padding-left: 8px;
        }
    }
}
</style>