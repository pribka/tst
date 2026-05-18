<template>
    <a-spin :spinning="loading">
        <div class="add-metric-wrapper">
            <a-form-model
                :model="form"
                ref="metricForm"
                class="form">
                <a-form-model-item
                    ref="name"
                    class="name error-message-off"
                    prop="name"
                    :rules="{
                        required: true,
                        trigger: ['change', 'blur'],
                    }">
                    <a-input
                        size="large"
                        :placeholder="$t('okr.metricName')"
                        v-model="form.name"
                        class="name" />
                </a-form-model-item>
                <a-form-model-item ref="description" class="description error-message-off" prop="description">
                    <a-input
                        size="large"
                        :placeholder="$t('okr.description')"
                        v-model="form.description"
                        class="description" />
                </a-form-model-item>               
            </a-form-model>
            <a-button
                class="submit-button"
                type="primary"
                @click="submit">
                {{ submitButtonText }}
            </a-button>
        </div>
    </a-spin>
</template>
<script>
import { mapActions, mapState } from 'vuex'
export default {
    name: 'AddMetric',
    props: {
        inject: {
            type: Object,
            default: () => {}
        },
        edit: {
            type: Boolean,
            default: false
        },
    },
    data() {
        return {
            form: {
                name: '',
                description: '',
            }
        }
    },
    computed: {
        ...mapState({
            loading: state => state.okr.addMetricLoading
        }),
        submitButtonText() {
            return this.edit ? this.$t('okr.save') : this.$t('okr.addButton')
        }
    },
    methods: {
        ...mapActions({
            addMetric: 'okr/addMetric',
            updateMetric: 'okr/updateMetric'
        }),
        fillForm() {
            this.form.name = this.inject.name
            this.form.description = this.inject.description
        },
        submit() {
            this.$refs.metricForm.validate(valid => {
                if (valid) {
                    if (this.edit) {
                        this.updateMetric({
                            id: this.inject.id,
                            name: this.form.name,
                            description: this.form.description
                        })
                            .then(() => {
                                this.$message.success(this.$t('okr.metricUpdated'))
                                this.close()
                            })
                    } else {
                        this.addMetric({
                            name: this.form.name,
                            description: this.form.description
                        })
                            .then(() => {
                                this.$message.success(this.$t('okr.metricAdded'))
                                this.close()
                            })
                    }
                } else {
                    this.$message.warning(this.$t('okr.checkFormFields'))
                    return
                }
            })
        },
        close() {
            this.edit ? this.$emit('close', this.inject.id) : this.$emit('close')
            this.resetForm()
        },
        resetForm() {
            this.$refs.metricForm.resetFields()
        },
    }
}
</script>
<style lang="scss" scoped>
.add-metric-wrapper {
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 20px;
    .form {
        display: flex;
        flex-direction: column;
        gap: 10px;
        .ant-input {
            border-radius: 4px;
            margin-bottom: 0;
        }
        .error-message-off.ant-form-item {
            margin-bottom: 0;
            &::v-deep {
                .ant-form-explain {
                    display: none;
                }
            }
        }
    }
    .submit-button {
        width: fit-content;
        border-radius: 4px;
    }
}
</style>