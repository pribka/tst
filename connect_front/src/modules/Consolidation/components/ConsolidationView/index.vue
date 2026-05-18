<template>
    <div>
        <a-drawer
            title=""
            destroyOnClose
            placement="right"
            :visible="visible"
            :width="drawerWidth"
            class="dv_drawer"
            wrapClassName="consolidation_wrap"
            :after-visible-change="afterVisibleChange"
            @close="onClose">
            <div v-if="consolidation" ref="drawerHeader" class="drawer_header flex items-center justify-between truncate">
                <div v-if="consolidation?.name" class="text-base font-semibold truncate label">
                    {{ consolidation?.name }}
                </div>
                <div class="flex items-center pl-4">
                    <template>
                        <a-dropdown
                            v-if="showActionButton"
                            :getPopupContainer="getPopupContainer"
                            :disabled="disabledActionButton"
                            :trigger="['click']">
                            <a-button
                                type="ui"
                                ghost
                                shape="circle"
                                :loading="actionLoading"
                                icon="fi-rr-menu-dots-vertical"
                                flaticon />
                            <a-menu slot="overlay">
                                <a-menu-item
                                    v-if="actions?.edit && actions?.edit?.availability"
                                    key="edit"
                                    class="flex items-center"
                                    @click="editHandler()">
                                    <i class="fi fi-rr-edit mr-2"></i>
                                    {{$t('Edit')}}
                                </a-menu-item>
                                <a-menu-item
                                    v-if="actions?.download && actions?.download?.availability"
                                    key="download"
                                    class="flex items-center"
                                    @click="documentDownload()">
                                    <i class="fi fi-rr-file-upload mr-2"></i>
                                    {{$t('Download report')}}
                                </a-menu-item>
                                <template v-if="actions?.delete && actions?.delete?.availability">
                                    <a-menu-divider />
                                    <a-menu-item
                                        key="delete"
                                        class="text-red-500 flex items-center"
                                        @click="deleteHandler()">
                                        <i class="fi fi-rr-trash mr-2"></i>
                                        {{$t('Delete')}}
                                    </a-menu-item>
                                </template>
                            </a-menu>
                        </a-dropdown>
                    </template>
                    <a-button
                        type="ui"
                        ghost
                        shape="circle"
                        class="ml-2 text-current"
                        icon="close"
                        @click="visible = false" />
                </div>
            </div>
            <div v-if="isMobile" class="drawer_body doc_body">
                <a-tabs default-active-key="1">
                    <a-tab-pane key="1" :tab="$t('Information')">
                        <a-spin tip="Загрузка..." :spinning="loading" class="w-full">
                            <div v-if="consolidation" class="aside_info">
                                <div class="item">
                                    <a-button
                                        type="primary"
                                        ghost flaticon icon="fi-rr-sitemap"
                                        :loading="consolidateLoading"
                                        class="w-full"
                                        size="large"
                                        :disabled="!consolidateIsAvailable"
                                        @click="consolidateHandler()">
                                        {{$t('Consolidation')}}
                                    </a-button>
                                </div>
                                <div class="item">
                                    <div class="label">
                                        {{$t('Status')}}:
                                    </div>
                                    <div>
                                        <a-tag :color="consolidation.status.color || ''">
                                            {{ consolidation.status.name }}
                                        </a-tag>
                                        <div v-if="showRetractButton" class="mt-3">
                                            <a-button
                                                type="danger"
                                                @click="rollback">
                                                {{$t('Retract consolidation of reports')}}
                                            </a-button>
                                        </div>
                                    </div>
                                </div>
                                <div class="item">
                                    <div class="label">
                                        {{$t('Auto approval of reports')}}:
                                    </div>
                                    <template v-if="auto_approve">
                                        <span class="auto_approve">{{$t('Active')}}</span>
                                    </template>
                                    <template v-else>
                                        <span class="text-gray-300">{{$t('Absent')}}</span>
                                    </template>
                                </div>
                                <div class="item">
                                    <div class="label">
                                        {{$t('Description')}}:
                                    </div>
                                    <div v-if="consolidation.description" >
                                        <TextViewer
                                            :body="consolidation.description"/>
                                    </div>
                                    <div v-else class="text-gray-300" >
                                        {{$t('Absent')}}
                                    </div>
                                </div>
                                <div v-if="consolidation.attachments.length" class="item">
                                    <div class="label">{{$t('Attached files')}}:</div>
                                    <div ref="lght_wrap" class="attachment_files">
                                        <CommentFile
                                            v-for="file in consolidation.attachments"
                                            :key="file.id"
                                            :file="file"
                                            :id="consolidation.id" />
                                    </div>
                                </div>
                                <div class="item">
                                    <div class="label">
                                        {{$t('Final report')}}:
                                    </div>
                                    <div v-if="isMobile">
                                        <template v-if="consolidation?.consolidation_files.length">
                                            <div v-for="file in consolidation.consolidation_files" :key="file.id" class="consolidation_files_list">
                                                <a v-if="consolidation.update_is_available"
                                                   download
                                                   target="_blank"
                                                   :href="file.original_file.path"
                                                   class="download_consolidation_file">
                                                    <a-button
                                                        type="link"
                                                        icon="download" />
                                                </a>
                                                <div class="truncate">
                                                    {{ file.name }}.{{file.extension}}
                                                </div>
                                            </div>
                                            <div class="truncate mt-2">
                                                {{$t('Formed')}}: {{this.$moment(consolidated_at).format('DD.MM.YYYY в HH:mm')}}
                                            </div>
                                            <div v-if="consolidation.consolidator">
                                                <div class="font-semibold mt-2">
                                                    {{$t('Responsible for consolidation')}}:
                                                </div>
                                                <div>
                                                    <Profiler :user="consolidation.consolidator" />
                                                </div>
                                            </div>
                                            <div class="send-to-report">
                                                <div class="font-semibold mt-2">
                                                    {{$t('Send to summary report')}}:
                                                </div>
                                                <div class="select">
                                                    <a-select
                                                        v-model="recipients"
                                                        mode="multiple"
                                                        :maxTagCount="1"
                                                        size="large"
                                                        :getPopupContainer="trigger => trigger.parentElement"
                                                        :loading="recipientListLoading"
                                                        :placeholder="recipientsPlaceholder"
                                                        option-label-prop>
                                                        <a-select-option
                                                            v-for="item in recipientList"
                                                            :key="item.id"
                                                            :value="item.id"
                                                            :label="item.name">
                                                            <div>{{ item.label }}</div>
                                                        </a-select-option>
                                                    </a-select>
                                                </div>
                                                <div class="send-button">
                                                    <a-button
                                                        type="primary"
                                                        ghost
                                                        :loading="recipientListLoading"
                                                        :disabled="!recipients.length"
                                                        @click="sendDocuments">
                                                        {{$t('Send_cons_btn')}}
                                                    </a-button>
                                                </div>
                                            </div>
                                        </template>
                                        <div v-else class="text-gray-300">
                                            {{$t('Not formed')}}
                                        </div>
                                    </div>
                                    <div v-else>
                                        <template v-if="consolidation?.consolidation_files.length">
                                            <div v-for="file in consolidation.consolidation_files" :key="file.id" class="consolidation_files_list">
                                                <a v-if="consolidation.update_is_available"
                                                   download
                                                   target="_blank"
                                                   :href="file.original_file.path"
                                                   class="download_consolidation_file">
                                                    <a-button
                                                        type="link"
                                                        icon="download" />
                                                </a>
                                                <div v-if="consolidation.update_is_available" class="cursor-pointer blue_color truncate pl-4" @click="showFile(file)">
                                                    {{ file.name }}.{{file.extension}}
                                                </div>
                                                <div v-else class="truncate">
                                                    {{ file.name }}.{{file.extension}}
                                                </div>
                                            </div>
                                            <div class="truncate mt-2">
                                                {{$t('Formed')}}: {{this.$moment(consolidated_at).format('DD.MM.YYYY в HH:mm')}}
                                            </div>
                                            <div v-if="consolidation.consolidator">
                                                <div class="font-semibold mt-2">
                                                    {{$t('Responsible for consolidation')}}:
                                                </div>
                                                <div>
                                                    <Profiler :user="consolidation.consolidator" />
                                                </div>
                                            </div>
                                        </template>
                                        <div v-else class="text-gray-300">
                                            {{$t('Not formed')}}
                                        </div>
                                    </div>
                                </div>
                                <div class="item">
                                    <div class="label">
                                        {{$t('Author')}}:
                                    </div>
                                    <div>
                                        <Profiler :user="consolidation.author" />
                                    </div>
                                </div>
                                <div class="item">
                                    <div class="label">
                                        {{$t('Administrator organization')}}:
                                    </div>
                                    <div class="value">
                                        <div class="flex items-center w-full">
                                            <div :key="consolidation?.org_administrator?.logo" class="pr-2">
                                                <a-avatar
                                                    :size="30"
                                                    :src="consolidation?.org_administrator?.logo"
                                                    icon="fi-rr-users-alt"
                                                    flaticon />
                                            </div>
                                            <span class="break-all">{{ consolidation?.org_administrator?.name }}</span>
                                        </div>
                                    </div>
                                </div>
                                <div class="item">
                                    <div class="label">
                                        {{$t('Report deadline')}}:
                                    </div>
                                    <div v-if="consolidation?.dead_line">
                                        <DeadLine
                                            :status="consolidation?.status"
                                            :date="consolidation?.dead_line" />
                                    </div>
                                    <div v-else class="text-gray-300">
                                        {{$t('Not specified')}}
                                    </div>
                                </div>
                                <div class="item">
                                    <div class="label">
                                        {{$t('Created')}}:
                                    </div>
                                    <div>
                                        {{$moment(consolidation.created_at).format('DD.MM.YYYY')}}
                                    </div>
                                </div>
                                <div class="item">
                                    <div class="label">
                                        {{$t('Report form')}}:
                                    </div>
                                    <div>
                                        {{consolidation?.report_form?.name}}
                                    </div>
                                    <div v-if="consolidation?.report_form?.code === 'ipf_proposal' && consolidation?.ipf_proposal_subtype?.name">
                                        {{$t('Application type')}} - "{{ consolidation.ipf_proposal_subtype.name }}"
                                    </div>
                                </div>
                                <div class="item">
                                    <div class="label">
                                        {{$t('Period')}}:
                                    </div>
                                    <div>
                                        {{$moment(consolidation?.start).format('DD.MM.YYYY')}} - {{$moment(consolidation?.end).format('DD.MM.YYYY')}}
                                    </div>
                                </div>
                                <div class="mt-5">
                                    <div class="mb-1 font-semibold">
                                        {{$t('Comments')}}
                                    </div>
                                    <vue2CommentsComponent
                                        bodySelector=".aside_info"
                                        :related_object="consolidation.id"
                                        model="consolidation" />
                                </div>
                            </div>
                        </a-spin>
                    </a-tab-pane>
                    <a-tab-pane key="2" :tab="$t('Reports')">
                        <div v-if="consolidation?.summary" class="summary-mobile">
                            <div class="total">{{$t('Total organizations')}}: {{ consolidation.summary.total }}</div>
                            <div class="approved">{{$t('Approved')}}: {{ consolidation.summary.approved }}</div>
                            <div class="not_loaded">{{$t('Not uploaded')}}: {{ consolidation.summary.not_loaded }}</div>
                            <div class="rejected">{{$t('On revision')}}: {{ consolidation.summary.rejected }}</div>
                            <div class="on_review">{{$t('Under review')}}: {{ consolidation.summary.on_review }}</div>
                        </div>
                        <ReportsListItem
                            v-for="report in reports"
                            :report="report"
                            :key="report.id"
                            class="mx-3"
                            :fileChangeIsDisabled="fileChangeIsDisabled"
                            :openReport="openReport"
                            :deleteReportFile="deleteReportFile"
                            :uploadReport="uploadReport" />
                    </a-tab-pane>
                    <a-tab-pane key="3" :tab="$t('History')">
                        <div v-if="consolidation" class="history_list">
                            <History 
                                :related_object="consolidation.id" 
                                injectContainer
                                filterPrefix="consolidation"
                                modelLabel="consolidation.ConsolidationModel" />
                        </div>
                    </a-tab-pane>
                </a-tabs>
            </div>
            <div v-else class="drawer_body doc_body">
                <a-tabs class="custom_tabs">
                    <a-tab-pane key="info" :tab="$t('Information')">
                        <div
                            class="grid"
                            :class="showAside ? 'md:grid-cols-[1fr,300px] lg:grid-cols-[1fr,400px]' : 'grid-cols-[1fr]'"
                            style="min-height: 100%;">
                            <a-skeleton :loading="loading" active :paragraph="{ rows: 5 }" class="document_html" >
                                <div class="summary_wrap">
                                    <div v-if="consolidation" class='summary'>
                                        <div class="total">{{$t('Total organizations')}}: {{ consolidation.summary.total }}</div>
                                        <div class="approved">{{$t('Approved')}}: {{ consolidation.summary.approved }}</div>
                                        <div class="not_loaded">{{$t('Not uploaded')}}: {{ consolidation.summary.not_loaded }}</div>
                                        <div class="rejected">{{$t('On revision')}}: {{ consolidation.summary.rejected }}</div>
                                        <div class="on_review">{{$t('Under review')}}: {{ consolidation.summary.on_review }}</div>
                                    </div>
                                </div>
                                <div style="min-height: 100%;">
                                    <template v-if="consolidation">
                                        <div v-if="consolidation?.reports">
                                            <Report
                                                v-for="report in consolidation.reports"
                                                class="mb-5 border custom_border_color overflow-hidden rounded-lg"
                                                :key="report.id"
                                                :report="report"
                                                :openReport="openReport"
                                                :deleteReportFile="deleteReportFile"
                                                :fileChangeIsDisabled="fileChangeIsDisabled"
                                                :uploadReport="uploadReport" />
                                        </div>
                                        <div v-else class="body_text">
                                            <a-empty />
                                        </div>
                                    </template>
                                </div>
                            </a-skeleton>
                            <a-skeleton :loading="loading" active :paragraph="{ rows: 5 }">
                                <div v-if="showAside" class="aside_info">
                                    <template v-if="consolidation">
                                        <div>
                                            <div class="item">
                                                <a-button
                                                    type="primary"
                                                    ghost flaticon icon="fi-rr-sitemap"
                                                    :loading="consolidateLoading"
                                                    class="w-full"
                                                    size="large"
                                                    :disabled="!consolidateIsAvailable"
                                                    @click="consolidateHandler()">
                                                    {{$t('Consolidation')}}
                                                </a-button>
                                            </div>
                                            <div class="item">
                                                <div class="label">
                                                    {{$t('Status')}}:
                                                </div>
                                                <div class="status-and-rollback-button">
                                                    <a-tag :color="consolidation.status.color || ''">
                                                        {{ consolidation.status.name }}
                                                    </a-tag>
                                                    <div v-if="showRetractButton" class="rollback-button">
                                                        <a-button
                                                            type="danger"
                                                            @click="rollback">
                                                            {{$t('Retract consolidation of reports')}}
                                                        </a-button>
                                                    </div>
                                                </div>
                                            </div>
                                            <div class="item">
                                                <div class="label">
                                                    {{$t('Auto approval of reports')}}:
                                                </div>
                                                <template v-if="auto_approve">
                                                    <span class="auto_approve">{{$t('Active')}}</span>
                                                </template>
                                                <template v-else>
                                                    <span class="text-gray-300">{{$t('Absent')}}</span>
                                                </template>
                                            </div>
                                            <div class="item">
                                                <div class="label">
                                                    {{$t('Description')}}:
                                                </div>
                                                <div v-if="consolidation.description" >
                                                    <TextViewer
                                                        :body="consolidation.description"/>
                                                </div>
                                                <div v-else class="text-gray-300" >
                                                    {{$t('Absent')}}
                                                </div>
                                            </div>
                                            <div v-if="consolidation.attachments.length" class="item">
                                                <div class="label">{{$t('Attached files')}}:</div>
                                                <div ref="lght_wrap" class="attachment_files">
                                                    <CommentFile
                                                        v-for="file in consolidation.attachments"
                                                        :key="file.id"
                                                        :file="file"
                                                        :id="consolidation.id" />
                                                </div>
                                            </div>
                                            <div class="item">
                                                <div class="label">
                                                    {{$t('Final report')}}:
                                                </div>
                                                <div>
                                                    <div v-if="consolidation?.consolidation_files.length">
                                                        <div v-for="file in consolidation.consolidation_files" :key="file.id">
                                                            <div v-if="consolidation.update_is_available"  class="consolidation_files_list">
                                                                <a-popover v-if="consolidation.update_is_available">
                                                                    <template slot="content">
                                                                        <p>{{$t('Download file')}}</p>
                                                                    </template>
                                                                    <a download
                                                                       target="_blank"
                                                                       :href="file.original_file.path"
                                                                       class="download_consolidation_file">
                                                                        <a-button
                                                                            type="link"
                                                                            icon="download" />
                                                                    </a>
                                                                </a-popover>
                                                                <div v-if="consolidation.update_is_available" @click="showFile(file)" class="cursor-pointer blue_color truncate pl-4">
                                                                    {{ file.original_file.name }}.{{file.original_file.extension}}
                                                                </div>
                                                            </div>
                                                            <div v-else class="truncate">
                                                                {{ file.original_file.name }}.{{file.original_file.extension}}
                                                            </div>
                                                        </div>
                                                        <div class="truncate mt-2">
                                                            {{$t('Formed')}}: {{this.$moment(consolidated_at).format('DD.MM.YYYY в HH:mm')}}
                                                        </div>
                                                        <div v-if="consolidation.consolidator">
                                                            <div class="font-semibold mt-2">
                                                                {{$t('Responsible for consolidation')}}:
                                                            </div>
                                                            <div class="mt-1">
                                                                <Profiler :user="consolidation.consolidator" />
                                                            </div>
                                                        </div>
                                                        <div class="send-to-report">
                                                            <div class="font-semibold mt-2">
                                                                {{$t('Send to summary report')}}:
                                                            </div>
                                                            <div class="select">
                                                                <a-select
                                                                    v-model="recipients"
                                                                    mode="multiple"
                                                                    :maxTagCount="1"
                                                                    size="large"
                                                                    :getPopupContainer="trigger => trigger.parentElement"
                                                                    :loading="recipientListLoading"
                                                                    :placeholder="recipientsPlaceholder"
                                                                    option-label-prop>
                                                                    <a-select-option
                                                                        v-for="item in recipientList"
                                                                        :key="item.id"
                                                                        :value="item.id"
                                                                        :label="item.name">
                                                                        <div>{{ item.label }}</div>
                                                                    </a-select-option>
                                                                </a-select>
                                                            </div>
                                                            <div class="send-button">
                                                                <a-button
                                                                    type="primary"
                                                                    ghost
                                                                    :loading="recipientListLoading"
                                                                    :disabled="!recipients.length"
                                                                    @click="sendDocuments">
                                                                    {{$t('Send_cons_btn')}}
                                                                </a-button>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div v-else class="text-gray-300">
                                                        {{$t('Not formed')}}
                                                    </div>
                                                </div>
                                            </div>
                                            <div class="item">
                                                <div class="label">
                                                    {{$t('Author')}}:
                                                </div>
                                                <div>
                                                    <Profiler :user="consolidation.author" />
                                                </div>
                                            </div>
                                            <div class="item">
                                                <div class="label">
                                                    {{$t('Administrator organization')}}:
                                                </div>
                                                <div class="value">
                                                    <div class="flex items-center">
                                                        <div :key="consolidation?.org_administrator?.logo" class="pr-2">
                                                            <a-avatar
                                                                :size="30"
                                                                :src="consolidation?.org_administrator?.logo"
                                                                icon="fi-rr-users-alt"
                                                                flaticon />
                                                        </div>
                                                        <span class="w-full pr-11">{{ consolidation?.org_administrator?.name }}</span>
                                                    </div>
                                                </div>
                                            </div>
                                            <div class="item">
                                                <div class="label">
                                                    {{$t('Report deadline')}}:
                                                </div>
                                                <div v-if="consolidation?.dead_line">
                                                    <DeadLine
                                                        :status="consolidation?.status"
                                                        :date="consolidation?.dead_line" />
                                                </div>
                                                <div v-else class="text-gray-300">
                                                    {{$t('Not specified')}}
                                                </div>
                                            </div>
                                            <div class="item">
                                                <div class="label">
                                                    {{$t('Created')}}:
                                                </div>
                                                <div>
                                                    {{$moment(consolidation.created_at).format('DD.MM.YYYY')}}
                                                </div>
                                            </div>
                                            <div class="item">
                                                <div class="label">
                                                    {{$t('Report form')}}:
                                                </div>
                                                <div>
                                                    {{consolidation?.report_form?.name}}
                                                </div>
                                                <div v-if="consolidation?.report_form?.code === 'ipf_proposal' && consolidation?.ipf_proposal_extra?.subtype?.name">
                                                    {{$t('Application type')}} - "{{ consolidation.ipf_proposal_extra.subtype.name }}"
                                                </div>
                                            </div>
                                            <div class="item">
                                                <div class="label">
                                                    {{$t('Period')}}:
                                                </div>
                                                <div>
                                                    {{$moment(consolidation?.start).format('DD.MM.YYYY')}} - {{$moment(consolidation?.end).format('DD.MM.YYYY')}}
                                                </div>
                                            </div>
                                            <div class="mt-5">
                                                <div class="mb-1 font-semibold">
                                                    {{$t('Comments')}}
                                                </div>
                                                <vue2CommentsComponent
                                                    bodySelector=".aside_info"
                                                    :related_object="consolidation.id"
                                                    model="consolidation" />
                                            </div>
                                        </div>
                                    </template>
                                </div>
                            </a-skeleton>
                        </div>
                    </a-tab-pane>
                    <a-tab-pane key="history" :tab="$t('Change history')">
                        <div v-if="consolidation" class="history_list">
                            <History 
                                :related_object="consolidation.id" 
                                injectContainer
                                filterPrefix="consolidation"
                                modelLabel="consolidation.ConsolidationModel" />
                        </div>
                    </a-tab-pane>
                </a-tabs>
            </div>
        </a-drawer>
        <UploadReport
            :consolidation="consolidation" />
    </div>
</template>

<script>
import CommentFile from '@apps/vue2CommentsComponent/CommentFIle.vue'
import DeadLine from '../DeadLine'
import ReportsListItem from './ReportsListItem'
import Report from './Report'
import TextViewer from '@apps/CKEditor/TextViewer.vue'
import UploadReport from '../UploadReport'
import eventBus from '@/utils/eventBus'
import vue2CommentsComponent from '@apps/vue2CommentsComponent'
import History from '@apps/History/index.vue'
const loadingKey = 'report_file_deleting'
export default {
    name: 'ConsolidationView',
    components: {
        CommentFile,
        DeadLine,
        ReportsListItem,
        Report,
        TextViewer,
        UploadReport,
        vue2CommentsComponent,
        History
    },
    data() {
        return {
            actionLoading: false,
            actions: null,
            consolidateLoading: false,
            consolidation: null,
            isExpand: false,
            loading: false,
            pageName: 'consolidations_table',
            range: [],
            recipientList: [],
            recipientListLoading: false,
            recipients: [],
            report_form: null,
            reports: [],
            showAside: true,
            visible: false,
            oldStatusID: ''
        };
    },
    computed: {
        recipientsPlaceholder() {
            return this.recipientList.length ? this.$t('Participant organizations') : this.$t('No available consolidations')
        },
        showRetractButton() {
            return this.consolidateIsAvailable && this.consolidation.status.code === 'completed'
        },
        consolidated_at() {
            return this.consolidation.consolidated_at
        },
        consolidateIsAvailable() {
            return this.consolidation.update_is_available &&
                   this.consolidation.reports.every(
                       report => report.status.code === 'approved' || report.status.code === 'consolidated')
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        drawerWidth() {
            if(this.windowWidth > 1600) {
                return 1600
            } else if(this.isMobile) {
                return '100%'
            } else {
                return '95%'
            }
        },
        disabledActionButton() {
            if(this.actions?.edit?.availability === true || this.actions?.delete?.availability === true || this.actions?.download?.availability === true)
                return false
            else
                return true
        },
        showActionButton() {
            if(this.isMobile) {
                return !this.disabledActionButton
            } else {
                return true
            }
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        auto_approve() {
            return this.consolidation.auto_approve
        }
    },
    methods: {
        rollback() {
            this.$confirm({
                title: this.$t('Do you really want to retract the current consolidation of reports?'),
                content: this.$t('after_cconfirmation_message'),
                okText: this.$t('Yes'),
                okType: 'danger',
                zIndex: 2000,
                closable: true,
                maskClosable: true,
                cancelText: this.$t('Cancel'),
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post(`/consolidation/${this.consolidation.id}/rollback/`)
                            .then((data) => {
                                this.$message.success(this.$t('Consolidation retracted'))
                                this.updateConsolidation(data.data)
                                
                                resolve()
                            })
                            .catch(e => {
                                console.log(e)
                                this.$message.error({ content: e[0] ? e[0] : this.$t('Error'), key: loadingKey })
                                reject(e)
                            })
                    })
                }
            })
        },
        deleteHandler() {
            this.$confirm({
                title: this.$t('Do you really want to delete consolidation') + ` "${this.consolidation.name}"?`,
                content: '',
                okText: this.$t('Delete'),
                okType: 'danger',
                zIndex: 2000,
                closable: true,
                maskClosable: true,
                cancelText: this.$t('Close'),
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post(`/consolidation/${this.consolidation.id}/delete/`)
                            .then(() => {
                                this.$message.success(this.$t('Consolidation deleted'))
                                eventBus.$emit('consolidationTableReload')
                                eventBus.$emit(`table_row_${this.pageName}`, {
                                    action: 'delete',
                                    row: this.consolidation
                                })
                                this.visible = false
                                resolve()
                            })
                            .catch(e => {
                                console.log(e)
                                this.$message.error({ content: e[0] ? e[0] : this.$t('Error deleting'), key: loadingKey })
                                reject(e)
                            })
                    })
                }
            })
        },
        async documentDownload() {
            this.loading = true
            try {
                const { data } = await this.$http(this.consolidation.consolidation_file.path, {
                    responseType: 'blob'
                })
                if(data) {
                    const url = window.URL.createObjectURL(new Blob([data]))
                    const link = document.createElement('a')
                    link.href = url
                    link.setAttribute('download', `${this.consolidation.consolidation_file.name}.${this.consolidation.consolidation_file.extension}`)
                    document.body.appendChild(link)
                    link.click()
                    link.remove()
                }
            } catch(e) {
                console.log(e)
                this.$message.error(this.$t('Error'))
            } finally {
                this.loading = false
            }
        },
        editHandler() {
            eventBus.$emit('edit_consolidation', this.consolidation.id)
        },
        getPopupContainer() {
            return this.$refs.drawerHeader
        },
        async getActions() {
            try {
                this.actionLoading = true
                const query = Object.assign({}, this.$route.query)
                const { data } = await this.$http.get(`/consolidation/${query.consolidation}/action_info/`)
                if(data?.actions) {
                    this.actions = data.actions
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.actionLoading = false
            }
        },
        showFile(file) {
            let query = Object.assign({}, this.$route.query)
            if(!query.consolidated_report && !query.active_tab) {
                query.consolidated_report = this.consolidation.id
                query.active_tab = file.id
                this.$router.push({query})
            }
        },
        async updateConsolidation(consolidation) {
            await this.getActions()
            this.consolidation = consolidation
            this.reports = consolidation.reports
        },
        fileChangeIsDisabled(report) {
            if(this.consolidation.auto_approve) {
                return ['consolidated',].includes(report.status.code)
            } else {
                return ['approved', 'consolidated'].includes(report.status.code)
            }
        },
        deleteReportFile(report, file) {
            this.$confirm({
                title: this.$t('Do you really want to delete the report file?'),
                content: '',
                okText: this.$t('Delete'),
                okType: 'danger',
                zIndex: 2000,
                closable: true,
                maskClosable: true,
                cancelText: this.$t('Close'),
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post(`/consolidation/report/${report.id}/file_remove/`, {
                            file: file.id
                        })
                            .then((data) => {
                                this.$message.success(this.$t('File deleted'))
                                this.updateConsolidation(data.data.consolidation)
                                resolve()
                            })
                            .catch(e => {
                                console.log(e)
                                this.$message.error({ content: e[0] ? e[0] : this.$t('Error deleting'), key: loadingKey })
                                reject(e)
                            })
                    })
                }
            })
        },
        uploadReport(report) {
            eventBus.$emit('upload_report', this.consolidation, report)
        },
        openReport(report, file=null) {
            let query = Object.assign({}, this.$route.query)
            if(file) {
                if(!query.report && !query.active_tab) {
                    query.report = report.id
                    query.active_tab = file.id
                    this.$router.push({query})
                }
            } else {
                if(!query.report) {
                    query.report = report.id
                    this.$router.push({query})
                }
            }
        },
        async getRecipientList() {
            this.recipientListLoading = true
            try {
                const { data } = await this.$http.get(`/consolidation/${this.consolidation.id}/get_recipients/`)
                if(data) {
                    this.recipientList = data
                    this.recipients = this.recipientList.map(item => item.id)
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.recipientListLoading = false
            }
        },
        sendDocuments() {
            this.$confirm({
                title: this.$t('Do you really want to upload data from this report?'),
                content: this.$t('Existing files in target reports will be replaced'),
                okText: this.$t('Upload'),
                okType: 'danger',
                cancelText: this.$t('Cancel'),
                onOk: async () => {
                    return new Promise((resolve, reject) => {
                        this.recipientListLoading = true
                        this.$http.post(`/consolidation/${this.consolidation.id}/send_documents/`, {
                            recipients: this.recipients
                        })
                            .then((data) => {
                                if(data.status === 200) {
                                    this.$message.success(this.$t('Reports successfully uploaded'))
                                    if(this.isMobile) {
                                        eventBus.$emit('consolidation_list_reload')
                                    } else {
                                        eventBus.$emit('update_filter_consolidation.ConsolidationModel')
                                    }
                                } else {
                                    this.$message.error(this.$t('Failed to upload reports'))
                                }
                                resolve()
                            })
                            .catch(e => {
                                console.log(e)
                                this.$message.error({ content: e[0] ? e[0] : this.$t('Error uploading files'), key: loadingKey })
                                reject(e)
                            })
                            .finally(() => {
                                this.recipientListLoading = false
                            })
                    })
                },
            })
        },
        async getReports() {
            const params = {
                report_form: this.report_form?.id,
                start: this.$moment(this.range[0]).format('YYYY-MM-DD'),
                end: this.$moment(this.range[1]).format('YYYY-MM-DD')
            }
            this.loading = true

            try {
                const { data } = await this.$http.get(`/consolidation/reports_to_consolidation/`, {
                    params: params
                })

                if(data) {
                    this.reports = data
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        },
        consolidateHandler() {
            if(this.consolidation.consolidation_files.length) {
                this.$confirm({
                    title: this.$t('Do you really want to create a new consolidated report?'),
                    content: this.$t('The existing report will be deleted'),
                    okText: this.$t('Create'),
                    okType: 'danger',
                    cancelText: this.$t('Cancel'),
                    onOk: () => {
                        this.consolidate()
                    },
                })
            } else {
                this.consolidate()
            }
        },
        async consolidate() {
            if(this.reports.length) {

                this.consolidateLoading = true
                try {
                    const {data} = await this.$http.post(`/consolidation/${this.consolidation.id}/consolidate/`)
                    if(data.status === 200) {
                        this.consolidation = data.data
                        this.$message.success(this.$t('Consolidated report created'))
                        this.updateConsolidation(data.data)
                        this.getRecipientList()
                    }
                } catch(e) {
                    console.log(e)
                    let errorMessage
                    if(e[0]) {
                        errorMessage = e[0]
                    } else if(e?.message) {
                        errorMessage = e.message
                    } else {
                        errorMessage = 'Ошибка'
                    }
                    this.$message.error(errorMessage)
                } finally {
                    this.consolidateLoading = false
                }
            } else {
                this.$message.error(this.$t('Report list is empty!'))
            }
        },
        async reloadConsolidation() {
            await this.getConsolidation()
            await this.getActions()
        },
        onClose() {
            this.visible = false
        },
        async afterVisibleChange(vis) {
            if(vis) {
                await this.getConsolidation()
                await this.getActions()
            } else {
                if(this.consolidation.status.id !== this.oldStatusID) {
                    eventBus.$emit(`table_row_${this.pageName}`, {
                        action: 'update'
                    })
                }
                const query = Object.assign({}, this.$route.query)
                if(query.consolidation) {
                    delete query.consolidation
                }
                if(query.active_tab) {
                    delete query.active_tab
                }
                this.$router.push({query})
                this.consolidation = null
                this.range = []
                this.recipientList = []
                this.recipientListLoading = false
                this.recipients = []
                this.report_form = null
                this.reports = []
                this.oldStatusID = ''
            }
        },
        async getConsolidation() {
            try {
                this.loading = true
                const query = Object.assign({}, this.$route.query)
                const { data } = await this.$http.get(`/consolidation/${query.consolidation}/`)
                if(data && data?.reports) {
                    this.consolidation = data
                    this.reports = data.reports
                    this.oldStatusID = data.status.id
                    if(this.consolidation.consolidation_files.length)
                        this.getRecipientList()
                }
            } catch(error) {
                if(error && error.detail) {
                    if(error.detail === 'Не найдено.' || error.detail === 'Страница не найдена.' || error.detail === 'У вас недостаточно прав для выполнения данного действия.') {
                        this.$message.warning(this.$t('Consolidation not found or deleted'))
                    } else {
                        this.$message.error(this.$t('Error'))
                    }
                } else {
                    this.$message.error(this.$t('Error'))
                }
                console.log(error)
                this.visible = false
            } finally {
                this.loading = false
                if(this.consolidation.attachments?.length) {
                    this.$nextTick(() => {
                        const lightboxWrap = this.$refs.lght_wrap,
                            lightbox = lightboxWrap.querySelectorAll('.lht_l')
                        if(lightbox?.length) {
                            lightGallery(lightboxWrap, {
                                selector: ".lht_l",
                                thumbnail: true,
                                rotateLeft: true,
                                rotateRight: true,
                                flipHorizontal: false,
                                flipVertical: false,
                                fullScreen: true,
                                animateThumb: true,
                                showThumbByDefault: true,
                                download: true,
                                speed: 300
                            })
                        }
                    })
                }
            }
        },
    },
    watch: {
        '$route.query'(val) {
            if(val.consolidation) {
                this.visible = true
            }
        },
    },
    created() {
        eventBus.$on('update_open_consolidation', data => {
            this.updateConsolidation(data)
        })
        eventBus.$on('reload_open_consolidation', () => {
            this.reloadConsolidation()
        })
        if(this.$route.query?.consolidation) {
            this.visible = true
        }
    },
    beforeDestroy() {
        eventBus.$off('update_open_consolidation')
        eventBus.$off('reload_open_consolidation')
    },
}
</script>


<style lang="scss" scoped>
.custom_border_color {
    border-color: var(--bgColor6);
}
.consolidation_files_list {
    display: grid;
    grid-template-columns: 32px 1fr;
    align-items: center;
}
.item_header {

}
.item_body {
    transition: background-color 0.1s ease;
}
.dv_drawer{
    &::v-deep{
        .ant-drawer-header-no-title{
            display: none;
        }
        .ant-drawer-wrapper-body,
        .ant-drawer-content{
            overflow: hidden;
        }
        .ant-drawer-body{
            padding: 0px;
            height: 100%;
        }
    }
    .drawer_body{
        height: calc(100% - 40px);
        overflow-y: auto;
        .history_list{
            padding: 15px;
        }
        .summary-mobile{
            padding: 15px;
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            row-gap: 10px;
            column-gap: 10px;
            .total{
                grid-column: span 2;
            }
        }
        .summary_wrap{
            height: 40px;
            margin-bottom: 15px;
            .summary{
                display: grid;
                grid-template-columns: repeat(5, auto);
                grid-template-rows: 40px;
                column-gap: 30px;
                align-items: center;
            }
        }
        &::v-deep{
            .ant-tabs-bar{
                margin: 0px;
            }
            .ant-col{
                min-height: 100%;
            }
            .ant-row{
                min-height: 100%;
            }
            .ant-select-lg .ant-select-selection--multiple .ant-select-selection__rendered li {
                max-width: 65%;
            }
        }
        .aside_info{
            padding: 20px;
            .item{
                .send-to-report{
                    .select{
                        margin-top: 0.25rem;
                        min-width: 0px;
                        .ant-select{
                            width: 100%;
                        }
                        &::v-deep{
                            li.ant-select-dropdown-menu-item{
                                overflow: visible;
                                text-overflow: clip;
                                white-space: normal;
                            }
                        }
                    }
                    .send-button{
                        margin-top: 1rem;
                    }
                }
                &:not(:last-child){
                    border-bottom: 1px solid var(--borderColor);
                    padding-bottom: 15px;
                }
                &:not(:first-child){
                    padding-top: 15px;
                }
                .label{
                    margin-bottom: 0.25rem;
                    font-size: 0.875rem;
                    line-height: 1.25rem;
                    font-weight: 600;
                }
                &__mem{
                    &:not(:last-child){
                        margin-bottom: 6px;
                    }
                }
                .attachment_files{
                    display: flex;
                    flex-wrap: wrap;
                }
                .status-and-rollback-button{
                    display: grid;
                    grid-template-columns: max-content max-content;
                    grid-template-rows: auto;
                    column-gap: 30px;
                    align-items: center;

                    .rollback-button{
                        // margin-top: 15px;
                    }
                }
            }
        }
        .document_html{
            padding: 20px 30px;
            min-height: 100%;
            position: relative;
            .d_f_actions{
                position: absolute;
                top: 20px;
                right: 0;
                margin-right: -16px;
                z-index: 5;
                bottom: 0px;
                &.hide_aside{
                    margin-right: 16px;
                }
                &__sticky{
                    position: sticky;
                    top: 20px;
                    left: 0;
                    display: flex;
                    flex-direction: column;
                    &::v-deep{
                        .ant-btn{
                            margin-bottom: 10px;
                        }
                    }
                }
            }
            .body_text{
                background: #ffffff;
                padding: 20px;
                border: 1px hsl( 0,0%,82.7% ) solid;
                border-radius: var(--borderRadius);
                box-shadow: 0 0 5px hsla( 0,0%,0%,.1 );
                min-height: 100%;
                &::v-deep{
                    figure{
                        &.table{
                            margin: 0.9em auto;
                            display: table;
                        }
                    }
                }
            }
        }
        .custom_tabs::v-deep {
            .ant-tabs-nav-container {
                padding: 0 30px;
            }
        }
    }
    .drawer_header{
        border-bottom: 1px solid var(--border2);
        height: 40px;
        padding: 0 15px;
        &::v-deep{
            .ant-skeleton-paragraph{
                display: none;
            }
            .ant-skeleton-content{
                .ant-skeleton-title{
                    width: 90%!important;
                    margin: 0px;
                    height: 20px;
                }
            }
        }
    }
}
</style>