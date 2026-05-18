<template>
    <a-modal 
        v-model="visible" 
        wrapClassName="create-template-modal"
        :footer="null"
        :getContainer="getContainer"
        @cancel="hideModal">
        <template slot="title">
            <div class="flex justify-between items-center ">
                <div class="">{{ $t('Save template') }}</div>
            </div>
        </template>
        <a-form-model class="pt-2 mb-auto" ref="form" :model="form" :rules="rules">
            <a-form-model-item prop="name" class="mb-2">
                <a-input
                    v-model="form.name"
                    size="large"
                    :placeholder="$t('Name')"/>
            </a-form-model-item>
            <a-form-model-item prop="description">
                <a-input
                    v-model="form.description"
                    size="large"
                    :placeholder="$t('Description')"/>
            </a-form-model-item>
        </a-form-model>

        <div class="mt-6 flex justify-between items-center pb-4">
            <div class="footer-left" :class="isMobile && 'w-full'">
                <a-button type="primary" :block="isMobile" class="mr-1" @click="submit">{{ $t('Save template') }}</a-button>
            </div>
            <div class="footer-right" :class="isMobile && 'w-full'">
                <a-button type="ui" ghost :block="isMobile" @click="hideModal">{{ $t('Cancel') }}</a-button>
            </div>
        </div>
    </a-modal>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
import { mapState } from 'vuex'
export default {
    props: {
        getContainer: {
            type: Function,
            default: () => document.body
        }
    },
    computed: {
        ...mapState({
            isMobile: state => state.isMobile
        }),
        activeTemplate() {
            return this.$store.state.reports.activeTemplate
        },
        activeMetadata() {
            return this.activeTemplate.metadata
        },
        editMode() {
            return this.activeTemplate.editMode
        },
        baseReport() {
            if (this.activeTemplate.is_base) {
                return this.activeTemplate.id
            }
            if (this.activeTemplate.base_report) {
                return this.activeTemplate.base_report
            }
            return null
        }
    },
    data() {
        return {
            visible: false,
            form: {
                name: '',
                description: '',
            },
            rules: {
                name: [
                    {
                        required: true,
                        message: this.$t("project.field_require"),
                        trigger: "blur",
                    },
                ],
            }
        };
    },
    methods: {
        submit() {
            this.$refs.form.validate()
                .then(async () => {
                    if (this.editMode) {
                        await this.editTemplate()
                    } else {
                        await this.createTemplate()
                    }
                })
                .catch(error => {
                    console.error(error)
                    this.$message.error(this.$t('Fill required fields'))
                })
        },
        createTemplate() {
            const url = '/reports/user_report_settings/'
            const payload = {
                ...this.form,
                app_section_code: this.activeTemplate.appSectionCode,
                metadata: {
                    ...this.activeMetadata,
                    complexFilter: this.activeTemplate.complexFilterMode || false
                },
                base_report: this.baseReport
            }
            if(this.activeTemplate.complexFilterMode)
                this.$set(payload.metadata, 'complexFilter', this.activeTemplate.complexFilterMode)
            if(this.activeTemplate.template)
                this.$set(payload, 'template', this.activeTemplate.template)

            this.$http.post(url, payload)
                .then(() => {

                    this.$store.commit('reports/RESET_TEMPLATES', { listKey: 'my_templates' })
                    this.$store.commit('reports/RESET_CHANGES')

                    this.hideModal()
                    this.clearForm()
                })
                .catch(error => {
                    errorHandler({error})
                })
        },
        editTemplate() {
            const url = `/reports/user_report_settings/${this.activeTemplate.id}/`
            const payload = {
                ...this.form,
                //app_section_code: 'tasks',
                metadata: {
                    ...this.activeMetadata,
                    complexFilter: this.activeTemplate.complexFilterMode || false
                }
            }
            if(this.activeTemplate.complexFilterMode)
                this.$set(payload.metadata, 'complexFilter', this.activeTemplate.complexFilterMode)
            this.$http.put(url, payload)
                .then(({ data }) => {
                    this.$store.commit('reports/RESET_TEMPLATES', { listKey: 'my_templates' })
                    this.$store.state.reports.activeTemplate.name = data.name
                    this.$store.state.reports.activeTemplate.description = data.description
                    this.$store.commit('reports/RESET_CHANGES')
                    this.hideModal()
                })
                .catch(error => {
                    errorHandler({error})
                })
        },
        clearForm() {
            this.form = {
                name: '',
                description: ''
            }
        },
        showModal() {
            this.visible = true;
            if (this.editMode) {
                this.form.name = String(this.activeTemplate.name)
                this.form.description = String(this.activeTemplate.description)
            }
        },
        hideModal() {
            this.visible = false;
            this.clearForm()
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
    .create-template-modal .ant-modal {
        max-width: 500px;
    }
}

@media (max-width: 768px) {
    :deep(.create-template-modal .ant-modal) {
        width: calc(100vw - 32px) !important;
        max-width: 500px;
        margin: 16px auto;
        top: 0;
        padding-bottom: 0;
    }

    :deep(.create-template-modal .ant-modal-content) {
        border-radius: 12px;
    }

    .mt-6.flex.justify-between.items-center.pb-4 {
        flex-direction: column;
        align-items: stretch;
        gap: 8px;
    }
}
</style>
