<template>
    <div class="form">
        <label
            :for="`file_${file.code}`"
            class="add-file-input ant-input ant-input-lg flex items-center truncate cursor-pointer"
            :class="fileChangeIsDisabled && 'text-gray-300 cursor-not-allowed'">
            <a-spin :spinning="fileLoading || formSubmit" size="small">
                <div class="add-file-label">
                    <i class="fi fi-rr-cloud-upload-alt" :class="fileChangeIsDisabled && 'text-gray-300 cursor-not-allowed'"></i>
                    <span class="ml-2" :class="fileChangeIsDisabled && 'text-gray-300 cursor-not-allowed'">
                        {{ $t('Select file') }}
                    </span>
                </div>
            </a-spin>
        </label>

        <input
            type="file"
            :id="`file_${file.code}`"
            style="display:none;"
            :ref="`file_${file.code}`"
            :disabled="fileChangeIsDisabled"
            @change="handleFileChange($event, file)"/>

        <div v-if="file.original_file" class="uploaded-file">
            <div class="label">
                {{ $t('Attached files') }}
            </div>
            <div class="card">
                <div class="icon">
                    <img :data-src="fileIcon" alt="" class="file-icon lazyload">
                </div>
                <div class="file-name truncate">
                    {{ file.original_file.name }}.{{ file.original_file.extension }}
                </div>
                <div class="delete">
                    <div v-if="fileChangeIsDisabled">
                        <img :data-src="deleteIcon" class="disabled-file-icon lazyload">
                    </div>
                    <div v-else>
                        <img
                            :data-src="deleteIcon"
                            class="file-icon lazyload"
                            :class="isDisabled && 'disabled-file-icon'"
                            @click="clearFile($event, file)">
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>
<script>
import eventBus from '@/utils/eventBus'

export default {
    name: 'F2GOFile',
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
        formSubmit: {
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
        }

    },
    computed: {
        isDisabled() {
            return !this.file.original_file || this.fileLoading || this.formSubmit 
        }
    },
    created() {
        eventBus.$on('clear_file_input', () => {
            if(this.$refs[`file_${this.file.code}`].value) {
                this.$refs[`file_${this.file.code}`].value = ''
            }
        })
    },
    beforeDestroy() {
        eventBus.$off('clear_file_input')
    }
}
</script>