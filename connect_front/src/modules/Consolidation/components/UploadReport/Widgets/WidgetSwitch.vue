<template>
    <div class="file">
        <div v-if="file.name || file.description" class="title">
            <div v-if="file.name" class="file-title">
                {{ file.name }}
            </div>
            <div v-if="file.description" class="file-description">
                {{ file.description }}
            </div>
        </div>
        <div class="form">
            <component 
                ref="uploadWidgetSwitch"
                :is="widget"
                :form="form"
                :consolidation="consolidation"
                :report="report"
                :noInquiries="noInquiries"
                :clearFile="clearFile"
                :deleteIcon="deleteIcon"
                :file="file"
                :fileChangeIsDisabled="fileChangeIsDisabled"
                :fileIcon="fileIcon"
                :fileLoading="fileLoading"
                :formSubmit="formSubmit"
                :handleFileChange="handleFileChange"
                :showFormError="showFormError"
                :edit="edit"
                :period="period"
                :isPersonalReceptionRequired="isPersonalReceptionRequired"
                :reportID="reportID" />                                    
        </div>
    </div>
</template>

<script>
export default {
    name: 'WidgetSwitch',
    props: {
        clearFile: {
            type: Function,
            default: () => {}
        },
        deleteIcon: {
            type: String,
            default: ''
        },
        file: {
            type: Object,
            required: true
        },
        consolidation: {
            type: Object,
            required: true
        },
        report: {
            type: Object,
            required: true
        },
        form: {
            type: Object,
            required: true
        },
        fileChangeIsDisabled: {
            type: Boolean,
            default: false
        },
        fileIcon: {
            type: String,
            default: ''
        },
        fileLoading: {
            type: Boolean,
            default: false
        },
        formSubmit: {
            type: Boolean,
            default: false
        },
        handleFileChange: {
            type: Function,
            default: () => {}
        },
        reportID: {
            type: String,
            default: ''
        },
        noInquiries: {
            type: Boolean,
            default: false
        },
        showFormError: {
            type: Boolean,
            required: false
        },
        edit: {
            type: Boolean,
            default: false
        },
        isPersonalReceptionRequired: {
            type: Boolean,
            default: true
        },
        period: {
            type: String,
            default: ''
        }
    },
    computed: {
        widget() {
            return () => import(`./${this.file.widget}.vue`)
                .then(module => {
                    return module
                })
                .catch(e => {
                    console.log('error')
                    return import(`./NotWidget.vue`)
                })
        }
    }
}
</script>