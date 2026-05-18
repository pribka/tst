<template>
    <div>
        <div
            class="files_info mb-5">
            <div class="theader"></div>
            <div class="theader">{{$t('File')}}</div>
            <div class="theader">{{$t('Uploaded')}}</div>
            <div class="theader">{{$t('Responsible')}}</div>
            <div class="theader"></div>
            <div class="theader"></div>
        </div>
        <template v-if="report.report_files.length">
            <div
                v-for="file, index in report.report_files"
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
                    <div v-if="report.file_viewing_is_available && file?.pdf_file?.path">
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
    }
}
</script>
<style lang="scss" scoped>
.files_info {
    display: grid;
    grid-template-columns: 130px 1fr 150px 250px 40px 40px;
    grid-template-rows: auto;
    min-height: 2.75rem;
    margin-top: 0.5rem;
}
.theader {
    font-weight: 600;
}
.file_name {
    margin-left: 10px;
}
</style>