<template>
    <a-modal
        :title="$t('approvals.reject_modal_title')"
        :visible="rejectVisible"
        :maskClosable="false"
        @cancel="closeRejectModal()">
        <a-form-model ref="form" :model="rejectForm">
            <p class="mb-2">{{ $t('approvals.rejection_reason') }}</p>
            <a-form-model-item 
                label="" 
                :rules="{
                    required: true,
                    message: $t('field_required'),
                }"
                prop="rejection_reason" 
                class="mb-0">
                <div class="textarea_wrapper">
                    <a-textarea
                        v-model="rejectForm.rejection_reason"
                        class="textarea_input"
                        ref="descriptionTextArea"
                        :maxLength="descriptionMaxCount"
                        :placeholder="$t('approvals.rejection_reason_placeholder')"
                        @input="adjustHeight" />
                    <div class="description_length">
                        {{rejectForm.rejection_reason.length}}/{{ descriptionMaxCount }}
                    </div>
                </div>
            </a-form-model-item>
        </a-form-model>
        <template #footer>
            <div class="flex w-full items-center justify-end gap-2">
                <a-button 
                    type="flat_danger" 
                    :loading="loading"
                    :block="isMobile"
                    @click="approvalsReject()">
                    {{ $t('approvals.reject') }}
                </a-button>
                <a-button 
                    type="ui_ghost" 
                    :disabled="loading"
                    :block="isMobile"
                    @click="closeRejectModal()">
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
            rejectVisible: false,
            loading: false,
            descriptionMaxCount: 1024,
            rejectForm: {
                rejection_reason: ""
            }
        }
    },
    methods: {
        async approvalsReject() {
            this.$refs.form.validate(async (v) => {
                if (v) {
                    try {
                        this.loading = true
                        const { data } = await this.$http.post(`/processes/workflow_requests/${this.approvals.id}/reject/`, {
                            rejection_reason: this.rejectForm.rejection_reason
                        })
                        if(data) {
                            eventBus.$emit(`update_filter_${this.model}_${this.pageName}`);
                            await this.getDetail(true)
                            this.closeRejectModal()
                        }
                    } catch(error) {
                        errorHandler({error})
                    } finally {
                        this.loading = false
                    }
                }
            })
        },
        openRejectModal() {
            this.rejectVisible = true
        },
        closeRejectModal() {
            this.rejectForm.rejection_reason = ""
            this.rejectVisible = false
        },
        adjustHeight(event) {
            const textarea = event.target;
            textarea.style.height = 'auto'
            const maxHeight = window.innerHeight - 100
            textarea.style.height = `${Math.min(textarea.scrollHeight, maxHeight)}px`
        },
    }
}
</script>

<style lang="scss" scoped>
.textarea_wrapper{
    position: relative;
    .description_length{
        position: absolute;
        bottom: 10px;
        right: 10px;
        z-index: 5;
        color: #888;
        font-size: 13px;
        line-height: 13px;
    }
    .textarea_input{
        margin-bottom: 0px!important;
        padding-bottom: 25px;
    }
}
</style>