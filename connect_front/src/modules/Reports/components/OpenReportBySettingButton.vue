<template>
    <a-button
        :type="type"
        :size="size"
        flaticon
        icon="fi-rr-square-poll-vertical"
        :loading="openReportLoading"
        v-tippy
        :class="btnClass"
        :content="$t(tooltip)"
        @click.stop="openReport">
        <template v-if="showText">
            {{ $t(buttonText) }}
        </template>
    </a-button>
</template>

<script>
import { errorHandler } from '@/utils/index.js'

export default {
    props: {
        reportSetting: {
            type: Object,
            required: true
        },
        payloadTransformer: {
            type: Function,
            default: payload => payload
        },
        btnClass: {
            type: String,
            default: ''
        },
        showText: {
            type: Boolean,
            default: true
        },
        buttonText: {
            type: String,
            default: 'Reporting'
        },
        tooltip: {
            type: String,
            default: 'Reporting'
        },
        type: {
            type: String,
            default: 'flat_primary'
        },
        size: {
            type: String,
            default: 'large'
        }
    },
    data() {
        return {
            openReportLoading: false
        }
    },
    methods: {
        openReport() {
            if(!this.reportSetting?.id)
                return
            this.openReportLoading = true
            this.$http.get(`/reports/report_settings/${this.reportSetting.id}/`)
                .then(({ data }) => {
                    const payload = this.payloadTransformer({
                        ...data,
                        appSectionCode: data.app_section_code,
                    })
                    return this.$store.dispatch('reports/openReportModal', payload)
                })
                .catch(error => {
                    errorHandler({error, show: false})
                })
                .finally(() => {
                    this.openReportLoading = false
                })
        }
    }
}
</script>
