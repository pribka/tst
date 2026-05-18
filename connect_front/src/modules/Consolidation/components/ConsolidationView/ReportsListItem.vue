<template>
    <div>
        <a-card
            style="border-radius: var(--borderRadius);"
            size="small"
            :bordered="false"
            :ref="`task_card_${report.id}`"
            :class="report.update_is_available ? 'bg_white' : 'bg_grey'"
            class="report-list-item-card mobile-card mmb"
            @click="report.view_is_available && openReport(report)">
            <a-tag v-if="report.status && report.status.name"
                   :color="report.status.color || ''"
                   class="mb-2">
                {{ report.status.name }}
            </a-tag>
            <div class="w-full flex items-center">
                <div :key="report.contractor.logo" class="pr-2">
                    <a-avatar 
                        :size="30"
                        :src="report.contractor.logo"
                        icon="fi-rr-users-alt" 
                        flaticon />
                </div>
                <span class="break-all">{{ report.contractor.name }}</span>
            </div>
            <div class="file-list-wrap">
                <div v-for="file in report_files" :key="file.id" class="file-list-item">
                    <div v-if="file.original_file" class="uploaded-file">
                        <span class="label">{{ file.name }}</span>: 
                        <span class="file-name">
                            {{$t('Uploaded')}}
                        </span>
                    </div>
                    <div v-else class="file-not-uploaded">
                        <span class="label">{{ file.name }}</span>: {{$t('Not uploaded')}}
                    </div>
                </div>
            </div>
        </a-card>
    </div>
</template>

<script>
export default {
    components: {
    },
    props: {
        report: [Object],
        showStatus: {
            type: Boolean,
            default: false
        },
        fileChangeIsDisabled: {
            type: Function,
            default: () => {}
        },
        openReport: {
            type: Function,
            default: () => {}
        },
        deleteReportFile: {
            type: Function,
            default: () => {}
        },
        uploadReport: {
            type: Function,
            default: () => {}
        },
    },
    computed: {
        report_files() {
            const allowedCodes = ['f2go', 'risk_matrix'];
            const report_files = this.report.report_files.filter(item => allowedCodes.includes(item.code))
            return report_files
        }
    },
    methods: {
    }
}
</script>

<style lang="scss" scoped>
.report-list-item-card{
    &.mobile-card{
        transition: all 0.5s cubic-bezier(0.645, 0.045, 0.355, 1);
        &.touch{
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
            transform: scale(0.97);
        }
    }
    &.mmb{
        margin-bottom: 10px;
    }
    &.bg_white{
        margin-bottom: 10px;
        background-color: white;
    }
    &.bg_grey{
        margin-bottom: 10px;
        background-color: rgb(241 245 249);
    }
    .consolidation_name {
        min-height: 45px;
    }
    .file-list-wrap {
        margin-top: 8px;
        .file-list-item{
            margin-top: 2px;
            margin-bottom: 2px;
            .uploaded-file{
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            .file-not-uploaded{
                color: #d1d5db;
            }
            .label{
                font-weight: 600;
            }
            .file-name{
            }
        }
    }
}
</style>