<template>
    <a-spin :spinning="loading">
        <a-form-model
            ref="ruleForm"
            :model="form"
            :rules="rules">
            <div class="top-informer-wrapper">
                <div class="label">{{ $t('okr.progress') }}</div>
                <div class="progress-bar">
                    <a-progress
                        class="custom-progress"
                        :percent="percent"
                        :show-info="false"
                        :strokeWidth="12"
                        strokeColor="#4777FF" />
                    <span class="value">{{ percent }}%</span>
                </div>
                <div class="label">{{ $t('okr.priority') }}</div>
                <div class="value_efforts">
                    <a-form-model-item v-if="edit" class="mb-0" ref="value_efforts" label="" prop="value_efforts">
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
                </div>
                <div class="label">{{ $t('okr.status') }}</div>
                <div class="status">
                    <a-form-model-item v-if="edit" class="mb-0" ref="status" label="" prop="status">
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
                </div>
            </div>
        </a-form-model>
    </a-spin>
</template>
<script>
import { mapState, mapMutations, mapActions, mapGetters } from 'vuex'
import DSelect from '@apps/DrawerSelect/Select.vue'

export default {
    name: 'Informer',
    components: {
        DSelect
    },
    data() {
        return {
            loading: false,
            rules: {},
            form: {
                status: undefined,
                value_efforts: undefined
            }
        }
    },
    created() {
        if(this.edit) {
            this.fillForm()
        }
    },
    computed: {
        ...mapState({
            objective: state => state.okr.objectiveDetail,
            valueEfforts: state => state.okr.valueEfforts
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
        percent() {
            return parseInt(this.objective.progress*100)
        }
    },
    methods: {
        ...mapMutations({
            SET_OBJECTIVE_DETAIL: 'okr/SET_OBJECTIVE_DETAIL',
            UPDATE_OBJECTIVE_ON_LIST: 'okr/UPDATE_OBJECTIVE_ON_LIST'
        }),
        fillForm() {
            if (this.objective?.status?.code) {
                this.form.status = this.objective.status.code
            }
            this.form.value_efforts = this.objective?.value_efforts?.code || null
        },
        dataChange({field, useTimer = false, valueKey = false, multiple = false}) {
            let payload = {}
            let patch = false
            switch (field) {
            case 'status':
                payload.status = this.form.status
                patch = true
                break
            case 'value_efforts':
                payload.value_efforts = this.form.value_efforts ? this.form.value_efforts : null
                patch = true
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
.top-informer-wrapper {
    display: grid;
    grid-template-columns: 1fr 290px 190px;
    grid-template-rows: auto auto;
    grid-auto-flow: column;
    align-items: center;
    column-gap: 30px;
    row-gap: 8px;
    .label {
        color: #888888;
    }
    .progress-bar {
        display: flex;
        gap: 8px;
        align-items: center;
        max-width: 700px;
        .custom-progress {
            flex: 1;
        }
    }
}
</style>
<style lang="scss">
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