<template>
    <a-modal 
        :visible="visible" 
        wrapClassName="modal"
        :footer="null" 
        :getContainer="getContainer"
        @cancel="hideModal">
        <template slot="title">
            <a-form-model
                ref="titleForm"
                :model="form"
                :rules="rules"
                layout="vertical"
                class="mb-0">
                <a-form-model-item
                    prop="title"
                    class="mb-0">
                    <a-input
                        v-model="form.title"
                        inputType="ghost"
                        :placeholder="$t('Aggregate field title')"/>
                </a-form-model-item>
            </a-form-model>
        </template>
        <a-form-model class="mb-auto" ref="form" :model="form" :rules="rules">
            <a-form-model-item 
                class="mb-2"
                prop="field">
                <TreeSelectField
                    :key="appSectionCode"
                    v-model="form.field"
                    :modelName="modelName"
                    @change="onTreeSelect" />
            </a-form-model-item>
            <a-form-model-item prop="aggregationType">
                <div ref="aggregationTypeWrap" class="flex">
                    <a-select
                        v-model="form.aggregationType"
                        size="large"
                        allowClear
                        :disabled="!form.field"
                        :placeholder="$t('Aggregation type')"
                        :getPopupContainer="triggerNode => triggerNode.parentNode"
                        style="width: 100%">
                        <a-select-option
                            v-for="option in aggregationOptions"
                            :key="option.value"
                            :value="option.value">
                            {{ option.label }}
                        </a-select-option>
                    </a-select>
                </div>
            </a-form-model-item>
        </a-form-model>

        <div class="mt-6 flex items-center pb-4">
            <a-button type="primary" class="mr-1" @click="submit">{{ $t('Create field') }}</a-button>
            <a-button type="ui" ghost @click="hideModal">{{ $t('Cancel') }}</a-button>
        </div>
    </a-modal>
</template>

<script>
import Vue from 'vue';

export default {
    components: {
        TreeSelectField: () => import('./TreeSelectField.vue')
    },
    props: {
        getContainer: {
            type: Function,
            default: () => document.body
        },
        templatesSource: {
            type: String,
            default: 'templates'
        }
    },
    computed: {
        getURL() {
            return `reports/${this.activeMetadata.modelName}/`
        },  
        visible() {
            return this.$store.state.reports.createAggregateFieldVisible
        },
        activeTemplate() {
            return this.$store.state.reports.activeTemplate
        },
        activeMetadata() {
            return this.activeTemplate.metadata
        },
        editMode() {
            return this.activeTemplate.editMode
        },    
        modelName() {
            return this.activeMetadata.modelName;
        },
        selectedFieldType() {
            return this.form.field?.type
        },
        aggregationOptions() {
            const options = [
                { value: 'min', label: this.$t('Min') },
                { value: 'max', label: this.$t('Max') },
                { value: 'count', label: this.$t('Count') },
                { value: 'distinct_count', label: this.$t('Unique values') },
                { value: 'concatenate', label: this.$t('Concatenate values') },
            ]
            if (this.selectedFieldType?.includes('Decimal') || 
                this.selectedFieldType?.includes('Integer') || 
                this.selectedFieldType?.includes('Duration')) {
                return options.concat([
                    { value: 'sum', label: this.$t('Sum') },
                    { value: 'avg', label: this.$t('Average') },
                ])
                
            }
            return options
        },
        appSectionCode() {
            return this.activeTemplate.appSectionCode
        }
    },
    data() {
        return {
            form: {
                title: '',
                field: null,
                aggregationType: ''
            },
            rules: {
                title: [
                    {
                        required: true,
                        message: this.$t("project.field_require"),
                        trigger: "blur",
                    },
                ],
                aggregationType: [
                    {
                        required: true,
                        message: this.$t("project.field_require"),
                        trigger: "blur",
                    },
                ],
                field: [
                    {
                        required: true,
                        message: this.$t("project.field_require"),
                        trigger: "blur",
                    },
                ],
            },
            treeSelectLoading: false,
            treeSelectValue: null,
        };
    },
    methods: {
        submit() {
            Promise.all([
                this.$refs.titleForm.validate(),
                this.$refs.form.validate()
            ])
                .then(() => {
                    this.createNewField()
                })
                .catch(error => {
                    console.error(error)
                    this.$message.error(this.$t('Fill required fields'))
                })
        },
        createNewField() {
            const availableFields = this.$store.state.reports.activeTemplate.availableFields
            const currentAggregateFields = availableFields.find(field => field.name === 'aggregate_fields').children
            const exists = currentAggregateFields.findIndex(field => field.title === this.form.title) !== -1
            if (exists) {
                this.$message.error(this.$t('A field with this title already exists'))
                return
            }
            const newField = {
                [this.form.aggregationType]: this.form.field.name,
                aggregate: true,
                name: this.form.field.name,
                active: true,
                type: this.form.field.type,
                verbose_name: this.form.title, 
                title: this.form.title, 
                defaultTitle: this.form.title, 
            }
            const aggregateFieldsIndex = availableFields.findIndex(field => field.name === 'aggregate_fields')
            availableFields[aggregateFieldsIndex].children.unshift(newField)
            if (!this.$store.state.reports.activeTemplate.metadata.availableAggregateFields) {
                Vue.set(this.$store.state.reports.activeTemplate.metadata, 'availableAggregateFields', [])
            }
            this.$store.state.reports.activeTemplate.metadata.availableAggregateFields.unshift(newField)
            this.hideModal()
        },
        clearForm() {
            this.form = {
                name: '',
                description: ''
            }
        },
        hideModal() {
            this.$store.commit('reports/CLOSE_CREATE_AGGREGATE_FIELD_MODAL')
            this.clearForm()
        },
        onTreeSelect(val) {
            this.form.description = val;
        },
    },
}
</script>

<style lang="scss" scoped>
.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
:deep {
    .ant-tabs-bar {
        margin-bottom: 0;
    }
    .ant-tabs-tab {
        padding-top: 0;
        padding-bottom: 14px;
    }
}
</style>