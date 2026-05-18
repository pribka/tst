<template>
    <div>
        <div
            class="table-header mb-5">
            <div class="theader"></div>
            <div class="theader">{{$t('File')}}</div>
            <div class="theader">{{$t('Uploaded')}}</div>
            <div class="theader">{{$t('Responsible')}}</div>
            <div class="theader"></div>
            <div class="theader"></div>
        </div>
        <template v-if="report_files.length">
            <div
                v-for="file, index in report_files"
                :key="`${report.id}_${file.id}`"
                class="files_info items-center">
                <div class="file_name pr-5">
                    <template v-if="file.name">
                        {{ file.name }}:
                    </template>
                    <template v-else>
                        {{$t('File')}} {{ `${index + 1}` }}:
                    </template>
                </div>
                <div v-if="file?.original_file?.path" class="file truncate pr-5">
                    <div v-if="report.file_viewing_is_available">
                        <div @click="openReport(report, file)" class="cursor-pointer blue_color">
                            <a-popover>
                                <template slot="content">
                                    {{ file.original_file.name }}.{{ file.original_file.extension }}
                                </template>
                                <div class="truncate">
                                    {{ file.original_file.name }}.{{ file.original_file.extension }}
                                </div>
                            </a-popover>
                        </div>
                    </div>
                    <div v-else class="truncate">
                        {{ file.original_file.name }}.{{ file.original_file.extension }}
                    </div>
                </div>
                <div v-else>
                    <div class="text-gray-300">
                        {{$t('Not uploaded')}}
                    </div>
                </div>
                <div class="upload_date">
                    <div v-if="file.upload_date">
                        {{ $moment(file.upload_date).format('DD.MM.YYYY в HH.mm') }}
                    </div>
                    <div v-else class="text-gray-300">
                        {{$t('Not uploaded')}}
                    </div>
                </div>
                <div class="uploaded_by">
                    <div v-if="file.uploaded_by">
                        <Profiler :user="file.uploaded_by" />
                    </div>
                    <div v-else class="text-gray-300">
                        {{$t('No data')}}
                    </div>
                </div>
                <div class="download">
                    <template v-if="file?.original_file?.path && report.file_viewing_is_available">
                        <a-popover>
                            <template slot="content">
                                <p>{{$t('Download file')}}</p>
                            </template>
                            <a download
                               target="_blank"
                               :href="file.original_file.path">
                                <a-button
                                    type="link"
                                    icon="download" />
                            </a>
                        </a-popover>
                    </template>
                    <template v-else>
                        <a-button
                            type="link"
                            icon="download"
                            disabled />
                    </template>
                </div>
                <div class="delete">
                    <template v-if="file?.original_file?.path && report.update_is_available">
                        <a-popover>
                            <template slot="content">
                                <p>{{$t('Delete file')}}</p>
                            </template>
                            <a-icon flaticon type="fi-rr-trash" />
                            <a-button
                                type="link"
                                ghost
                                flaticon
                                icon="fi-rr-trash"
                                :disabled="fileChangeIsDisabled(report)"
                                @click="deleteReportFile(report, file)" />
                        </a-popover>
                    </template>
                    <template v-else>
                        <a-button
                            type="link"
                            ghost
                            flaticon
                            icon="fi-rr-trash"
                            disabled />
                    </template>
                </div>
            </div>
        </template>
        <div class="disintegration files_info">
            <div class="revoked-without-routing">
                <span class="label file_name">{{$t('Revoked without routing')}}:</span>
                <span v-if="report?.revoked_without_routing !== null" class="value">{{report.revoked_without_routing}}</span>
                <span v-else class="value no-data">{{$t('Not specified')}}</span>
            </div>
            <div class="transferring-to-another-system">
                <span class="label">{{$t('Transferring to another system')}}:</span>
                <span v-if="report?.transferring_to_another_system !== null" class="value">{{report.transferring_to_another_system}}</span>
                <span v-else class="value no-data">{{$t('Not specified')}}</span>
            </div>
        </div>
        <div v-if="showPersonalReception" class="personal_reception">
            <a-empty v-if="personalReceptionNoData" class="data-not-loaded">
                <span slot="description">
                    <div class="no-data">{{$t('No data on personal reception of citizens')}}</div>
                </span>
            </a-empty>
            <div v-else-if="noPersonalReception" class="no-personal-reception">
                {{$t('No personal reception during the reporting period')}}
            </div>
            <template v-else-if="report?.personal_reception_issues.length">
                <div class="personal-reception-quantity">
                    <div class="label">{{$t('Number of personal receptions held')}}:</div>  
                    <div class="value">{{ report?.personal_reception_quantity }}</div>
                </div>
                <div class="issues-table">
                    <div class="table-header">
                        <div class="column">{{$t('Issue number')}}</div>
                        <div class="column">{{$t('Issue date')}}</div>
                        <div class="column">{{$t('Status')}}</div>
                        <div class="column">{{$t('Number of days in queue')}}</div>
                    </div>
                    <div class="table-body">

                        <div v-for="(org, index) in orgList" :key="index">
                            <template v-if="org?.issues.length">
                                <div v-if="org.org_id !== report.contractor.id" class="row" :class="{'border-top': index !== 0}">
                                    <div class="org-label">{{ org.org_name }}</div>
                                    <div class="pr-quantity">Проведено приемов: {{ org.personal_reception_quantity }}</div>
                                </div>

                                <div v-for="issue in org.issues" :key="issue.id" class="row">
                                    <div class="cell">{{ issue.number }}</div>
                                    <div class="cell">{{ $moment(issue.issue_date).format('DD.MM.YYYY') }}</div>
                                    <div class="cell">{{ issue.personal_reception.status_name }}</div>
                                    <div class="cell">{{ issue.personal_reception.days_in_queue }}</div>
                                </div>
                            </template>

                        </div>
                    </div>
                    <div class="table-footer">
                        <div class="cell">{{$t('Total')}}: {{ issuesTotalCount || '' }}</div>
                    </div>
                </div>
            </template>
        </div>
    </div>
</template>
<script>
export default {
    props: {
        report: {
            type: Object,
            require: true
        },
        openReport: {
            type: Function,
            default: () => {}
        },
        fileChangeIsDisabled: {
            type: Function,
            default: () => {}
        },
        deleteReportFile: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        report_files() {
            const allowedCodes = new Set(['f2go', 'risk_matrix'])
            const report_files = this.report.report_files.filter(item => allowedCodes.has(item.code))
            return report_files
        },
        showPersonalReception() {
            return this.report?.consolidation.report_form.code === 'risk_map_with_personal_reception'
        },
        personalReceptionNoData() {
            return this.report.is_personal_reception_not_loaded || false
        },
        noPersonalReception() {
            return this.report.no_personal_reception || false
        },
        orgList() {
            return this.report.personal_reception_issues.map((org) => ({
                org_id: Object.entries(org)[0][0],
                org_name: Object.entries(org)[0][1].org_name,
                personal_reception_quantity: Object.entries(org)[0][1].personal_reception_quantity,
                issues: Object.entries(org)[0][1].issues
            }))
        },
        issuesTotalCount() {
            return this.report.personal_reception_issues.reduce((result, org) => {
                return result + Object.entries(org)[0][1].issues.length
            }, 0)
        }
    }
}
</script>
<style lang="scss" scoped>
.table-header, .files_info, .disintegration{
    display: grid;
    grid-template-columns: 130px 1fr 150px 250px 40px 40px;
    grid-template-rows: auto;
    min-height: 2.75rem;
    padding: 0.7rem 0 0.7rem 0;
}
.table-header{
    .theader {
        font-weight: 600;
    }
}
.files_info {
    &:not(:last-child){
        border-bottom: 1px solid var(--borderColor);
    }
    .file_name {
        margin-left: 10px;
    }
}
.disintegration{
    .revoked-without-routing, .transferring-to-another-system{
        grid-column: span 2;
        min-height: 32px;
        display: flex;
        column-gap: 20px;
        align-items: center;
    }
    .no-data{
        color: rgba(209, 213, 219);
    }
    .value {
        padding-right: 1.25rem;
    }
}
.personal_reception {
    margin: 0 10px 0 10px;
    padding-top: 0.7rem 10px 0 10px;
    .no-data{
        color: rgba(209, 213, 219);
    }
    .data-not-loaded {
        margin-top: 15px;
    }
}
.issues-table {
    .table-header {
        line-height: normal;
        background-color: #f8f8f8;
        border: 1px solid #babfc7;
        border-radius: 8px 8px 0 0;
        display: flex;
        width: 100%;
        justify-content: space-between;
        align-items: center;
        font-weight: 700;
        color: #181d1f;
        font-size: 13px;
        padding: 0;
        .column {
            flex: 1;
            padding: 3px 1.25rem;
            position: relative;
        }
        .column:not(:last-child)::after {
            content: "|";
            position: absolute;
            right: -10px;
            top: 50%;
            transform: translateY(-50%);
            color: #babfc7;
        }
    }
    .table-body {
        max-height: 250px;
        overflow-y: auto;
        width: 100%;
        line-height: normal;
        border-left: 1px solid #babfc7;
        border-right: 1px solid #babfc7;
        .row{
            display: flex;
            width: 100%;
            justify-content: space-between;
            align-items: center;
            .cell {
                flex: 1;
                padding: 3px 1.25rem;
            }
        }
        .row:not(:last-child) {
            border-bottom: 1px solid #babfc7;
        }
        .org-label, .pr-quantity {
            justify-content: start;
            padding: 3px 1.25rem;
            align-content: center;
            background-color: #F0F9FE;
        }
        .org-label {
            width: 75%;
            min-height: 2rem;           
        }
        .pr-quantity {
            width: 25%;
            align-self: stretch;
        }
        .border-top {
            border-top: 1px solid #babfc7;
        }
    }
    .table-footer {
        line-height: normal;
        background-color: #f8f8f8;
        border: 1px solid #babfc7;
        border-radius: 0 0 8px 8px;
        width: 100%;
        padding: 10px 10px 10px 1.25rem;
        font-weight: 700;
        color: #181d1f;
        font-size: 13px;
    }
}
.personal-reception-quantity {
    grid-column: span 2;
    min-height: 32px;
    margin: 0.7rem 0 0.7rem 0;
    display: flex;
    column-gap: 20px;
    align-items: center;
}
.no-personal-reception {
    min-height: 32px;
    margin-top: 0.7rem;
    display: flex;
    align-items: center;
}
</style>