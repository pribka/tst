<template>
    <a-drawer
        title=""
        :visible="visible"
        class="dv_drawer"
        @close="visible = false"
        destroyOnClose
        :width="drawerWidth"
        :zIndex="1100"
        :afterVisibleChange="afterVisibleChange"
        placement="right">
        <div ref="drawerHeader" class="drawer_header flex items-center justify-between truncate">
            <div v-if="report" class="text-base font-semibold truncate label">
                {{ report.name }}
            </div>
            <a-skeleton
                v-else
                active
                :paragraph="{ rows: 1 }" />
            <div class="flex items-center pl-4">
                <template v-if="!showFooter && showActionButtons">
                    <a-button 
                        v-if="actions.approve && actions.approve.availability" 
                        type="success" 
                        ghost 
                        class="mr-2"
                        :loading="approveLoading"
                        :disabled="rejectLoading"
                        @click="approve()">
                        {{ $t('Approve') }}
                    </a-button>
                    <a-button 
                        v-if="actions.approve && actions.approve.availability" 
                        type="danger" 
                        ghost 
                        class="mr-2"
                        :loading="rejectLoading"
                        :disabled="approveLoading"
                        @click="reject()">
                        {{ $t('Send for revision') }}
                    </a-button>
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
            <a-spin :spinning="loading">
                <template v-if="report">
                    <div class="aside_info" :class="{'with-footer' : (showFooter && showActionButtons)}">
                        <div class="status-and-upload">
                            <div class="status">
                                <div class="item">
                                    <div class="label">
                                        {{ $t('Status') }}:
                                    </div>
                                    <div class="value">
                                        <a-tag :color="report.status?.color || ''">
                                            {{ report.status.name }}
                                        </a-tag>
                                    </div>
                                </div>
                            </div>
                            <div class="upload">
                                <a-button
                                    type="default"
                                    icon="cloud-upload"
                                    :loading="approveLoading || rejectLoading"
                                    :disabled="uploadDisabled"
                                    @click="upload">
                                    {{ $t('Upload') }}
                                </a-button>
                            </div>
                        </div>
                        <div v-if="report.update_is_disabled && report.update_is_available" class="error-banner">
                            <a-alert :message="$t('The reporting period is not over yet. Uploading reports is prohibited until the end of the reporting period.')" type="error" show-icon />
                        </div>
                        <div class="item">
                            <div class="label">
                                {{ $t('Organization') }}:
                            </div>
                            <div class="value">
                                <div class="flex items-center">
                                    <div :key="report.contractor.logo" class="pr-2">
                                        <a-avatar 
                                            :size="30"
                                            :src="report.contractor.logo"
                                            icon="fi-rr-users-alt" 
                                            flaticon />
                                    </div>
                                    <span class="w-full truncate">{{ report.contractor.name }}</span>
                                </div>
                            </div>
                        </div>
                        <div class="file_list">
                            <div v-for="file in report_files" :key="file.id" class="file_list_item">
                                <template v-if="file.original_file">
                                    <div class="file_item">
                                        <div class="label">
                                            {{ file.name }}:
                                        </div>
                                        <div class="value">
                                            {{ file.original_file.name }}.{{ file.original_file.extension }}
                                        </div>
                                    </div>
                                    <div class="file_item">
                                        <div class="label">
                                            {{ $t('Uploaded by') }}:
                                        </div>
                                        <div v-if="uploaded_by" class="value">
                                            <Profiler 
                                                :user="uploaded_by" 
                                                initStatus
                                                :getPopupContainer="getPopupContainer" />
                                        </div>
                                        <div v-else class="no-data">
                                            {{ $t('No data') }}
                                        </div>
                                    </div>
                                    <div class="file_item">
                                        <div class="label">
                                            {{ $t('Uploaded at') }}:
                                        </div>
                                        <div class="value" v-if="upload_date">
                                            {{ $moment(upload_date).format('DD.MM.YYYY, в HH:mm') }}
                                        </div>
                                        <div v-else class="no-data">
                                            {{ $t('No data') }}
                                        </div>
                                    </div>
                                </template>
                                <template v-else>
                                    <div class="file_item">
                                        <div class="label">
                                            {{ file.name }}:
                                        </div>
                                        <div class="no-data">
                                            {{ $t('Not uploaded') }}
                                        </div>
                                    </div>
                                </template>
                                <div class="file_item buttons">
                                    <a v-if="file?.original_file?.path && report.file_viewing_is_available"
                                       download
                                       target="_blank"
                                       :href="file.original_file.path">
                                        <a-button 
                                            type="default"
                                            class="w-full"
                                            icon="download" >
                                            {{ $t('Download') }}
                                        </a-button>
                                    </a>
                                    <a-button
                                        v-else
                                        type="default"
                                        icon="download"
                                        disabled >
                                        {{ $t('Download') }}
                                    </a-button>
                                    <a-button 
                                        type="default"
                                        icon="delete"
                                        :loading="approveLoading || rejectLoading"
                                        :disabled="!file.original_file || fileDeleteDisabled"
                                        @click="fileDelete(file)">
                                        {{ $t('Delete') }}
                                    </a-button>
                                </div>
                            </div>
                            <div class="disintegration">
                                <div class="revoked-without-routing">
                                    <span class="label">{{ $t('Revoked without routing') }}:</span>
                                    <span v-if="report?.revoked_without_routing !== null" class="value">{{report.revoked_without_routing}}</span>
                                    <span v-else class="value no-data">{{ $t('Not specified') }}</span>
                                </div>
                                <div class="transferring-to-another-system">
                                    <span class="label">{{ $t('Transfer to another system') }}:</span>
                                    <span v-if="report?.transferring_to_another_system !== null" class="value">{{report.transferring_to_another_system}}</span>
                                    <span v-else class="value no-data">{{ $t('Not specified') }}</span>
                                </div>
                            </div>
                        </div>
                        <div class="mt-5">
                            <div class="mb-1 font-semibold">
                                {{ $t('Comments') }}
                            </div>
                            <vue2CommentsComponent
                                bodySelector=".doc_body"
                                :related_object="report.id"
                                model="report" />
                        </div>
                    </div>
                    <div v-if="showFooter" class="drawer_footer">
                        <div v-if="showActionButtons" class="action-buttons">
                            <a-button 
                                v-if="actions.approve && actions.approve.availability" 
                                type="success" 
                                ghost 
                                class="mr-2"
                                :loading="approveLoading"
                                :disabled="rejectLoading"
                                @click="approve()">
                                {{ $t('Approve') }}
                            </a-button>
                            <a-button 
                                v-if="actions.approve && actions.approve.availability" 
                                type="danger" 
                                ghost 
                                class="mr-2"
                                :loading="rejectLoading"
                                :disabled="approveLoading"
                                @click="reject()">
                                {{ $t('Send for revision') }}
                            </a-button>
                        </div>
                    </div>
                </template>
                <a-empty v-else class="mt-10" />
            </a-spin>
        </div>
    </a-drawer>
</template>

<script>
import axios from 'axios'
import eventBus from '@/utils/eventBus'
export default {
    name: 'ReportView',
    components: {
        vue2CommentsComponent: () => import('@apps/vue2CommentsComponent')
    },
    computed: {
        windowWidth() {
            return this.$store.state.windowWidth
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        drawerWidth() {
            if(this.windowWidth > 1600)
                return 1600
            else {
                return '100%'
            }
        },
        showActionButtons() {
            if(this.report &&
               this.actions &&
               this.report?.status?.code !== 'consolidated')
                return true
            else
                return false
        },
        showFooter() {
            return this.isMobile
        },
        isMultipleFiles() {
            if(this.report) {
                return this.report_files.length > 1
            } else {
                return false
            }
        },
        uploadDisabled() {
            return this.report.update_is_disabled || !this.report.update_is_available
        },
        fileDeleteDisabled() {
            return !this.report.update_is_available
        },
        report_files() {
            const allowedCodes = ['f2go', 'risk_matrix'];
            return this.report.report_files.filter(item => allowedCodes.includes(item.code))
        }
        
    },
    data() {
        return {
            actionLoading: false,
            actions: null,
            activeTabKey: null,
            loading: false,
            pdfsrc: {},
            report: null,
            showAside: true,
            approveLoading: false,
            rejectLoading: false,
            upload_date: null,
            uploaded_by: null,
            visible: false,
            getPDFLoading: false,
            cancelTokenSource: {}
        }
    },
    watch: {
        '$route.query'(val) {
            if(val.report) {
                if(val?.active_tab) {
                    this.activeTabKey=val.active_tab
                }
                this.visible = true
            }
        },
    },
    created() {
        eventBus.$on('reload_report', () => {
            if(this.report)
                this.getReport()
        })
        eventBus.$on('open_report', () => {
            this.visible = true
        })

        if(this.$route.query.report)
            this.visible = true
    },
    methods: {
        getPDF(tabKey) {
            const index = this.report_files.findIndex(rf => rf.id === tabKey)
            if(index === -1)
                return
            if(!this.report_files[index]?.original_file?.id)
                return
            this.$set(this.pdfsrc, tabKey, null)
            this.getPDFLoading = true
            this.cancelTokenSource[tabKey] = axios.CancelToken.source()
            this.$http.get(`/consolidation/${this.report_files[index].original_file.id}/get_pdf/`, {
                responseType: "blob",
                cancelToken: this.cancelTokenSource[tabKey].token
            }).then(response => {
                this.$set(this.pdfsrc, tabKey, URL.createObjectURL(response.data))
                delete this.cancelTokenSource[tabKey]
            }).catch(error => {
                if (axios.isCancel(error)) {
                    console.log('Request canceled', error.message);
                } else {
                    console.log(error);
                }
            }).finally(() => {
                this.getPDFLoading = false
            })
        },
        cancelRequests() {
            for(let each in this.cancelTokenSource) {
                this.cancelTokenSource[each].cancel('Operation canceled.')
            }
        },
        tabIsChange(key) {
            const index = this.report_files.findIndex(file => file['id'] === key)
            if(index === -1)
                return
            if(!(this.report_files[index].id in this.pdfsrc))
                this.getPDF(this.report_files[index].id)
            this.uploaded_by = this.report_files[index].uploaded_by ? this.report_files[index].uploaded_by : null
            this.upload_date = this.report_files[index].upload_date ? this.report_files[index].upload_date : null
        },
        async approve() {
            try {
                this.approveLoading = true
                const { data } = await this.$http.post(`/consolidation/report/${this.report.id}/approve/`)
                if (data) {
                    this.$message.success(this.$t('Report approved'))
                    this.$set(this.report, 'status', data.report.status)
                    if (this.isMobile)
                        this.getReport()
                    eventBus.$emit('update_report_in_list', data.report)
                    eventBus.$emit('update_consolidation_in_list', data.consolidation)
                    eventBus.$emit('update_open_consolidation', data.consolidation)
                }
            } catch (e) {
                console.log(e)
                this.$message.error(
                    (typeof e === "object" && e[0])
                        ? e[0]
                        : this.$t('Error approving report')
                )
            } finally {
                this.approveLoading = false
            }
        },

        async reject() {
            try {
                this.rejectLoading = true
                const { data } = await this.$http.post(`/consolidation/report/${this.report.id}/reject/`)
                if (data) {
                    this.$message.info(this.$t('Report sent for revision'))
                    this.$set(this.report, 'status', data.report.status)
                    if (this.isMobile)
                        this.getReport()
                    eventBus.$emit('update_report_in_list', data.report)
                    eventBus.$emit('update_consolidation_in_list', data.consolidation)
                    eventBus.$emit('update_open_consolidation', data.consolidation)
                }
            } catch (e) {
                console.log(e)
                this.$message.error(
                    (typeof e === "object" && e[0])
                        ? e[0]
                        : this.$t('Error sending for revision')
                )
            } finally {
                this.rejectLoading = false
            }
        },

        editHandler() {
            this.visible = false
            eventBus.$emit('edit_report', this.report, true)
        },
        getPopupContainer() {
            return this.$refs.drawerHeader
        },
        async afterVisibleChange(vis) {
            if(vis) {
                await this.getReport()
            } else {
                const query = Object.assign({}, this.$route.query)
                this.cancelRequests()
                if(query.report) {
                    delete query.report
                }
                if(query.active_tab) {
                    delete query.active_tab
                }
                this.$router.push({query})
                this.actions = null
                this.pdfsrc = {}
                this.report = null
                this.uploaded_by = null
                this.upload_date = null
                this.activeTabKey = null
            }
        },
        async getReport() {
            try {
                this.loading = true
                const query = Object.assign({}, this.$route.query)
                const { data } = await this.$http.get(`/consolidation/report/${query.report}/file_view/`)
                if (data) {
                    this.report = data
                    if (this.report_files.length) {
                        this.uploaded_by = this.report_files[0].uploaded_by ? this.report_files[0].uploaded_by : null
                        this.upload_date = this.report_files[0].upload_date ? this.report_files[0].upload_date : null
                    }
                    this.getActions()
                    if (this.isMobile) return
                    if (!(this.activeTabKey in this.pdfsrc))
                        this.getPDF(this.activeTabKey)
                }
            } catch (error) {
                if (error && error.detail) {
                    if (
                        error.detail === this.$t('Not found') ||
                error.detail === this.$t('Page not found') ||
                error.detail === this.$t('You do not have permission to perform this action')
                    ) {
                        this.$message.warning(this.$t('Viewing not possible'))
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
            }
        },
        async getActions() {
            try {
                this.actionLoading = true
                const query = Object.assign({}, this.$route.query)
                const { data } = await this.$http.get(`/consolidation/report/${query.report}/action_info/`)
                if (data?.actions) {
                    this.actions = data.actions
                }
            } catch (e) {
                console.log(e)
            } finally {
                this.actionLoading = false
            }
        },
        fileDelete(file) {
            this.$confirm({
                title: this.$t('Are you sure you want to delete the report file?'),
                content: '',
                okText: this.$t('Delete'),
                okType: 'danger',
                zIndex: 2000,
                closable: true,
                maskClosable: true,
                cancelText: this.$t('Close'),
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post(`/consolidation/report/${this.report.id}/file_remove/`, {
                            file: file.id
                        })
                            .then((data) => {
                                this.$message.success(this.$t('File deleted'))
                                eventBus.$emit('update_open_consolidation0', data.data.consolidation)
                                eventBus.$emit('table_row_consolidations_table', {
                                    action: 'update',
                                    row: data.data.consolidation
                                })
                                this.getReport()
                                resolve()
                            })
                            .catch(e => {
                                console.log(e)
                                this.$message.error({
                                    content: e[0] ? e[0] : this.$t('Error deleting'),
                                    key: 'fileDelete'
                                })
                                reject(e)
                            })
                    })
                }
            })
        },
        upload() {
            eventBus.$emit('upload_report', this.report.consolidation, this.report)
        },

    },
    beforeDestroy() {
        eventBus.$off('reload_report')
        eventBus.$off('open_report')
    }
}
</script>

<style lang="scss" scoped>
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
        .drawer_footer{
            display: flex;
            align-items: center;
            height: 40px;
            border-top: 1px solid #e8e8e8;
            padding-left: 20px;
            padding-right: 20px;
            .action-buttons{
                width: 100%;
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 5px;
            }
        }
        &::v-deep{
            .ant-col{
                min-height: 100%;
            }
            .ant-row{
                min-height: 100%;
            }
        }
        .with-footer{
            height: calc(100vh - 80px);
            overflow-y: auto;
        }
        .no-data{
            color: rgb(209 213 219);
        }
        .aside_info{
            padding: 20px;
            .error-banner{
                margin-top: 15px;
            }
            .status-and-upload{
                display: grid;
                grid-template-columns: repeat(2, auto);
                align-content: center;
                .status{}
                .upload{
                    align-self: flex-end;
                    justify-self: end;
                }
            }
            .item{
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
            }
            .file_list{
                
                .file_list_item{
                    border-bottom: 1px solid var(--borderColor);
                    .file_item{
                        &:last-child{
                            padding-bottom: 15px;
                        }
                        .label{
                            margin-top: 0.25rem;
                            margin-bottom: 0.25rem;
                            font-size: 0.875rem;
                            line-height: 1.25rem;
                            font-weight: 600;
                            }
                    }
                    .buttons{
                        display: grid;
                        grid-template-columns: repeat(2, 1fr);
                        justify-items: stretch;
                        margin-top: 1rem;
                        gap: 5px;
                        .ant-btn{
                            padding: 0 9px;
                        }
                    }
                }
                .disintegration{
                    margin-top: 10px;
                    .revoked-without-routing, .transferring-to-another-system{
                        padding-top: 15px;
                    }
                    .label{
                        margin-right: 20px;
                    }
                    .no-data{
                        color: rgba(209, 213, 219);
                    }
                }
            }
        }
        .document_html{
            background: #e3e8ec;
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
            .spinner, .empty{
                width: 100%;
                margin-top: 10rem;
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