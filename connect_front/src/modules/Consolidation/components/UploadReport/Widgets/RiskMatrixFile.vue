<template>
    <div>
        <div class="switch">
            <span class="label">
                {{$t('No inquiries for selected period')}}
            </span>
            <span class="switcher">
                <a-switch
                    v-model="noInquiriesSwitchValue"
                    :loading="generating"
                    @change="noInquiriesIsChange" />
            </span>
        </div>
        <div v-show="!noInquiriesSwitchValue">
            <div class="switch">
                <span class="label">
                    {{$t('Use data from Inquiries module')}}
                </span>
                <span class="switcher">
                    <a-switch
                        v-model="useInquiriesSwitchValue"
                        :loading="generating"
                        @change="generateReportFilesIsChange" />
                </span>
            </div>
            <div class="form">
                <div v-if="showWarning" class="warning">
                    {{$t('Delete the existing file to use data from the Inquiries module')}}
                </div>
                <!-- <label :for="`file_${file.code}`" class="add-file-input ant-input ant-input-lg flex items-center truncate cursor-pointer" :class="fileChangeIsDisabled && 'text-gray-300 cursor-not-allowed'">
                    <a-spin :spinning="fileLoading || generating" size="small">
                        <div class="add-file-label">
                            <i class="fi fi-rr-cloud-upload-alt" :class="fileChangeIsDisabled && 'text-gray-300 cursor-not-allowed'"></i>
                            <span class="ml-2" :class="fileChangeIsDisabled && 'text-gray-300 cursor-not-allowed'">Выбрать файл</span>
                        </div>
                    </a-spin>
                </label>
                <input
                    type="file"
                    :id="`file_${file.code}`"
                    style="display:none;"
                    :ref="`file_${file.code}`"
                    :disabled="fileChangeIsDisabled"
                    v-on:change="handleFileChange($event, file)" /> -->
                <div v-if="file.original_file" class="uploaded-file">
                    <div class="label">
                        Прикрепленные файлы
                    </div>
                    <div class="two-columns">
                        <div class="card" :class="{'red-card':showWarning}">
                            <div class="icon">
                                <img 
                                    :data-src="fileIcon" 
                                    alt=""
                                    class="file-icon lazyload" >
                            </div>
                            <div class="file-name truncate">
                                {{ file.original_file.name }}.{{ file.original_file.extension }}
                            </div>
                            <div class="delete">
                                <div v-if="fileChangeIsDisabled">
                                    <img
                                        :data-src="deleteIcon" 
                                        alt=""
                                        class="disabled-file-icon lazyload" >
                                </div>
                                <div v-else>
                                    <img
                                        :data-src="deleteIcon" 
                                        alt=""
                                        class="file-icon lazyload"
                                        @click="clear($event, file)">
                                </div>
                            </div>
                        </div>
                        <div v-if="useInquiriesSwitchValue" class="regenerate">
                            <a-tooltip placement="topRight" :title="$t('Update risk map data')">
                                <a-button
                                    shape="circle"
                                    icon="redo"
                                    :loading="generating"
                                    @click="regenerate" />
                            </a-tooltip>
                        </div>
                    </div>
                    <div v-if="showSuccessInfo" class="success_info">
                        <div>{{$t('Report generated')}}</div>
                        <div v-if="riskAssessmentsCount">{{$t('Processed inquiries')}}: {{ riskAssessmentsCount }}. </div>
                        <div v-if="filePath" >
                            <a 
                                download
                                target="_blank"
                                :href="filePath">
                                {{$t('Download file for review')}}
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>
<script>
import eventBus from '@/utils/eventBus'

export default {
    name: 'RiskMatrixFile',
    data() {
        return {
            filePath: null,
            generating: false,
            noInquiriesSwitchValue: false,
            riskAssessmentsCount: null,
            showSuccessInfo: false,
            showWarning: false,
            useInquiriesSwitchValue: false
        }
    },
    props: {
        file: {
            type: Object,
            required: true
        },
        handleFileChange: {
            type: Function,
            default: () => {}
        },
        clearFile: {
            type: Function,
            default: () => {}
        },
        fileChangeIsDisabled: {
            type: Boolean,
            default: false
        },
        fileLoading: {
            type: Boolean,
            default: false
        },
        fileIcon: {
            type: String,
            default: ''
        },
        deleteIcon: {
            type: String,
            default: ''
        },
        reportID: {
            type: String,
            default: ''
        },
        noInquiries: {
            type: Boolean,
            default: false
        }
    },
    mounted(){
        if(this.noInquiries) {
            this.noInquiriesSwitchValue = true
        } else if(this.file.is_generated) {
            this.useInquiriesSwitchValue = true
        }
    },
    methods: {
        regenerate() {
            const payload = {
                file_code: "risk_matrix"
            }
            this.showSuccessInfo = false
            this.riskAssessmentsCount = null,
            this.filePath = null
            this.getGeneratedFile(payload, '', false)
            eventBus.$emit('no-inquiries', false)
        },
        async getGeneratedFile(payload, errorMessage = '', switchToggleOff = true) {
            try {
                this.generating = true
                const { data } = await this.$http.post(`/consolidation/report/${this.reportID}/generate/`, payload)

                if (data) {
                    if (data.id) {
                        this.file.original_file = data
                        this.file.is_generated = true

                        if (data?.extra_info?.risk_assessments_count) {
                            this.riskAssessmentsCount = data?.extra_info?.risk_assessments_count
                        }
                        if (data?.path) {
                            this.filePath = data.path
                        }
                        this.showSuccessInfo = true
                    } else {
                        this.$message.error(errorMessage ? errorMessage : this.$t('File generation failed'))
                        this.file.is_generated = false
                        if (switchToggleOff) {
                            this.useInquiriesSwitchValue = false
                        }
                    }
                }
            } catch (e) {
                console.log(e)
                this.$message.error(
                    (typeof e === "object" && e[0])
                        ? e[0]
                        : this.$t('File upload error')
                )
                if (this.noInquiriesSwitchValue) {
                    this.noInquiriesSwitchValue = false
                }
                if (this.useInquiriesSwitchValue && switchToggleOff) {
                    this.useInquiriesSwitchValue = false
                }
            } finally {
                this.generating = false
            }
        },

        noInquiriesIsChange(val) {
            if (val) {
                const payload = {
                    file_code: "risk_matrix",
                    no_inquiries: true
                }
                this.getGeneratedFile(payload)
                eventBus.$emit('no-inquiries', true)
            } else {
                this.useInquiriesSwitchValue = false
                this.clearFile(null, this.file)
            }
        },

        clear(event, file) {
            this.clearFile(event, file)
            this.showWarning = false
            this.showSuccessInfo = false
            this.riskAssessmentsCount = null
            this.filePath = null
            this.useInquiriesSwitchValue = false
        },

        async generateReportFilesIsChange(val) {
            if (val) {
                if (this.file.original_file) {
                    this.showWarning = true
                    this.useInquiriesSwitchValue = false
                } else {
                    const payload = {
                        file_code: "risk_matrix"
                    }
                    const errorMessage = this.$t('No inquiries for period')
                    this.getGeneratedFile(payload, errorMessage)
                    eventBus.$emit('no-inquiries', false)
                }
            }
        }
    }
}
</script>
<style lang="scss" scoped>
.warning{
    width: 100%;
    background-color: rgb(233, 185, 185);
    margin-bottom: 15px;
    border-radius: 4px;
    padding: 15px;
    line-height: 1.5;
}
.success_info{
    width: 100%;
    background-color: rgb(240, 252, 240);
    margin-top: 15px;
    border-radius: 4px;
    padding: 15px;
    line-height: 1.5;
}
.red-card{
    color: rgb(233, 185, 185);
    border: 1px solid var(--Neutral-5, rgb(233, 185, 185))!important;
}
.switch {
    display: grid;
    grid-template-columns: 1fr auto;
    grid-template-rows: auto;
    column-gap: 30px;
    width: 100%;
    margin-bottom: 20px;
    align-items: center;
    .label{
        line-height: normal;
    }
    .switcher{
    }
}
.two-columns{
    display: grid;
    grid-template-columns: repeat(2, auto);
    grid-template-rows: max-content;
    column-gap: 30px;
    align-items: center;
}
</style>