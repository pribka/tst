<template>
    <div>
        <a-modal
            :visible="visibleInfo"
            :title="$t('task.information')"
            :zIndex="4000"
            :afterClose="afterCloseInfo"
            @cancel="closeInfoModal()">
            <div 
                v-if="infoData" 
                class="info_wrapper">
                <div 
                    v-if="infoData.comment.length" 
                    class="info_comment">
                    <label class="font-semibold mb-1">
                        {{ $t('task.comment') }}
                    </label>
                    <div 
                        v-html="infoData.comment" 
                        class="break-words" />
                </div>
                <div 
                    v-if="infoData.attachments.length" 
                    class="file_list">
                    <div 
                        v-for="file in infoData.attachments" 
                        :key="file.id"
                        class="item_file">
                        <img 
                            :src="file.path" 
                            :alt="file.name" />
                    </div>
                </div>
            </div>
            <template slot="footer">
                <a-button @click="closeInfoModal()">
                    {{ $t('task.close') }}
                </a-button>
            </template>
        </a-modal>

        <a-modal
            :visible="visible"
            :title="$t('task.incomplete_shipment')"
            :zIndex="4000"
            :afterClose="afterClose"
            @cancel="closeFormModal()">
            <a-form-model
                ref="incompleteForm"
                :model="form"
                :rules="rules">
                <a-form-model-item
                    ref="quantity_success"
                    :label="$t('task.quantity')"
                    prop="quantity_success">
                    <a-input-number
                        v-model="form.quantity_success"
                        size="large"
                        style="min-width: 200px;"
                        :min="1"
                        :max="incomplete && incomplete.quantity_valid ? incomplete.quantity_valid : 1"
                        :formatter="countFormatter" />
                </a-form-model-item>
                <a-form-model-item
                    ref="comment"
                    :label="$t('task.comment')"
                    prop="comment">
                    <a-textarea
                        v-model="form.comment"
                        :auto-size="{ minRows: 2, maxRows: 6 }"/>
                </a-form-model-item>
                <a-form-model-item
                    ref="attachments"
                    :label="$t('task.photo')"
                    prop="attachments">
                    <Upload
                        :key="visible"
                        v-model="form.attachments"
                        :defaultList="fileList"
                        :limit="10"
                        multiple />
                </a-form-model-item>
            </a-form-model>
            <div slot="footer" class="flex">
                <a-button 
                    :block="isMobile" 
                    @click="closeFormModal()">
                    {{ $t('task.close') }}
                </a-button>
                <a-button
                    class="ml-2"
                    :block="isMobile"
                    :loading="loading"
                    type="primary"
                    @click="incompleteShipment()">
                    {{ $t('task.send') }}
                </a-button>
            </div>
        </a-modal>
    </div>
</template>

<script>
import Upload from '@apps/Upload'
export default {
    components: {
        Upload
    },
    props: {
        visibleInfo: {
            type: Boolean,
            default: false
        },
        afterCloseInfo: {
            type: Function,
            default: () => {}
        },
        afterClose: {
            type: Function,
            default: () => {}
        },
        infoData: {
            type: Object,
            default: () => null
        },
        closeInfoModal: {
            type: Function,
            default: () => {}
        },
        visible: {
            type: Boolean,
            default: false
        },
        incomplete: {
            type: Object,
            default: () => null
        },
        closeFormModal: {
            type: Function,
            default: () => {}
        },
        updateProductList: {
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
        return{
            loading: false,
            fileList: [],
            form: {
                quantity_success: null,
                comment: '',
                attachments: []
            },
            rules: {
                quantity_success: [
                    { required: true, message: this.$t('field_required'), trigger: 'blur' }
                ],
                comment: [
                    { required: true, message: this.$t('field_required'), trigger: 'blur' }
                ]
            }
        }
    },
    methods: {
        countFormatter(value) {
            if(value > this.incomplete?.quantity_valid)
                return this.incomplete.quantity_valid
            else
                return value
        },
        incompleteShipment() {
            this.$refs.incompleteForm.validate(async valid => {
                if (valid) {
                    try {
                        this.loading = true
                        const {data} = await this.$http.patch(`/tasks/delivery/${this.incomplete.id}/`, this.form)
                        this.updateProductList(data)
                        this.$message.success(this.$t('task.product_shipped'))
                        this.closeFormModal()
                    } catch(e) {
                        console.log(e)
                        this.$message.error(this.$t('task.error'))
                    } finally {
                        this.loading = false
                    }
                } else {
                    console.log('error submit!!')
                    return false;
                }
            })
        }
    }
}
</script>

<style lang="scss" scoped>
.info_wrapper{
    .info_comment{
        border-bottom: 1px solid var(--borderColor);
        margin-bottom: 8px;
        padding-bottom: 8px;
    }
}
</style>