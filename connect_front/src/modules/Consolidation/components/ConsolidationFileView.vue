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
            <div v-if="consolidation" class="text-base font-semibold truncate label">
                {{ consolidation.name }}
            </div>
            <a-skeleton
                v-else
                active
                :paragraph="{ rows: 1 }" />
            <div class="flex items-center pl-4">
                <template v-if="showActionButtons">
                    <a-dropdown 
                        :getPopupContainer="getPopupContainer" 
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
                                v-if="consolidation.consolidation_file && consolidation.consolidation_file.path" 
                                key="download"
                                class="flex items-center"
                                @click="documentDownload()">
                                <i class="fi fi-rr-file-upload mr-2"></i>
                                {{ $t('Download file') }}
                            </a-menu-item>
                            <template v-if="actions.delete && actions.delete.availability">
                                <a-menu-divider />
                                <a-menu-item 
                                    key="delete" 
                                    class="text-red-500 flex items-center" 
                                    @click="deleteHandler()">
                                    <i class="fi fi-rr-trash mr-2"></i>
                                    {{ $t('Delete file') }}
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
        <div v-if="isMobile" class="drawer_body">
        </div>
        <div v-else class="drawer_body doc_body">
            <div 
                class="grid" 
                :class="showAside ? 'md:grid-cols-[1fr,300px] lg:grid-cols-[1fr,400px]' : 'grid-cols-[1fr]'"
                style="min-height: 100%;">
                <div class="document_html" style="min-height: 100%;">

                    <div class="d_f_actions" :class="!showAside && 'hide_aside'">
                        <div class="d_f_actions__sticky">
                            <a-button 
                                :icon="showAside ? 'fi-rr-arrow-alt-to-right' : 'fi-rr-arrow-alt-to-left'" 
                                flaticon 
                                shape="circle"
                                @click="showAside = !showAside" />
                            <a-button 
                                v-if="consolidation && consolidation.consolidation_file && consolidation.consolidation_file.path" 
                                icon="fi-rr-file-upload" 
                                v-tippy="{ inertia : true}"
                                :content="$t('Download report')"
                                flaticon 
                                shape="circle"
                                :loading="loading"
                                @click="documentDownload()" />
                        </div>
                    </div>

                    <template v-if="consolidation">
                        <div v-if="consolidation_files.length">
                            <div v-if="consolidation_files.length === 1">
                                <iframe v-if="pdfsrc[activeTabKey]" :src="pdfsrc[activeTabKey]" class="w-full h-[90vh]" />
                                <div v-else class="h-[100vh] body_text">
                                    <a-spin v-if="getPDFLoading" spinning :tip="$t('Loading...')" class="spinner" />
                                    <a-empty v-else class="empty">
                                        <span slot="description" class="no-data">{{$t('Preview unavailable')}}</span>
                                    </a-empty>
                                </div>
                            </div>
                            <div v-else>
                                <a-tabs @change="tabIsChange" :default-active-key="activeTabKey">
                                    <a-tab-pane
                                        v-for="(file, index) in consolidation.consolidation_files"
                                        :key="file.id"
                                        :tab="file.original_file.name ? file.original_file.name : `${$t('File')} ${index + 1}`">
                                        <iframe v-if="pdfsrc[file.id]" :src="pdfsrc[file.id]" class="w-full h-[90vh]" :id="file.id" />
                                        <div v-else class="h-[100vh] body_text">
                                            <a-spin v-if="getPDFLoading" spinning :tip="$t('Loading...')" class="spinner" />
                                            <a-empty v-else class="empty">
                                                <span slot="description" class="no-data">{{$t('Preview unavailable')}}</span>
                                            </a-empty>
                                        </div>
                                    </a-tab-pane>
                                </a-tabs>
                            </div>
                        </div>
                        <div v-else class="body_text">
                            <a-empty />
                        </div>
                    </template>
                    <div v-else class="body_text">
                        <a-skeleton
                            active
                            :paragraph="{ rows: 5 }" />
                    </div>
                </div>

                <div v-if="showAside" class="aside_info">
                    <template v-if="consolidation">
                        <div>
                            <div class="item">
                                <div class="label">
                                    {{$t('Consolidation status')}}:
                                </div>
                                <div class="value">
                                    <a-tag :color="consolidation.status?.color || ''">
                                        {{ consolidation.status.name }}
                                    </a-tag>
                                </div>
                            </div>

                            <div class="item">
                                <div class="label">
                                    {{$t('Final report')}}:
                                </div>
                                <div v-for="file in consolidation.consolidation_files" :key="file.id" class="consolidation_files_list">
                                    <a-popover>
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
                                    <div class="truncate pl-4">{{ file.original_file.name }}.{{file.original_file.extension}}</div>
                                </div>
                            </div>

                            <div class="item">
                                <div class="label">
                                    {{$t('Generated at')}}:
                                </div>
                                <div class="value">
                                    {{$moment(consolidation.consolidated_at).format('DD.MM.YYYY')}} {{$t('at')}} {{$moment(consolidation.consolidated_at).format('HH:mm')}}
                                </div>
                            </div>

                            <div class="item">
                                <div class="label">
                                    {{$t('Created for organization')}}:
                                </div>
                                <div class="value">
                                    <div class="flex items-center">
                                        <div :key="consolidation.org_administrator.logo" class="pr-2">
                                            <a-avatar 
                                                :size="30"
                                                :src="consolidation.org_administrator.logo"
                                                icon="fi-rr-users-alt" 
                                                flaticon />
                                        </div>
                                        <span class="w-full pr-11">{{ consolidation.org_administrator.name }}</span>
                                    </div>
                                </div>
                            </div>

                            <div class="item">
                                <div class="label">
                                    {{$t('Report form')}}:
                                </div>
                                <div class="value">
                                    {{ consolidation.report_form.name }}
                                </div>
                            </div>

                            <div class="item">
                                <div class="label">
                                    {{$t('Period')}}:
                                </div>
                                <div class="value">
                                    {{ $moment(consolidation.start).format('DD.MM.YYYY') }} - {{ $moment(consolidation.end).format('DD.MM.YYYY') }}
                                </div>
                            </div>

                            <div class="item">
                                <div class="label">
                                    {{$t('Participating organizations')}}:
                                </div>
                                <div v-if="consolidation.members && consolidation.members.length" class="item">
                                    <div 
                                        v-for="org in consolidation.members" 
                                        :key="org.id"
                                        class="item__mem">
                                        <div class="flex items-center">
                                            <div :key="org.logo" class="pr-2">
                                                <a-avatar 
                                                    :size="30"
                                                    :src="org.logo"
                                                    icon="fi-rr-users-alt" 
                                                    flaticon />
                                            </div>
                                            <span class="w-full pr-11">{{ org.name }}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="mt-5">
                            <div class="mb-1 font-semibold">
                                {{$t('Comments')}}
                            </div>
                            <vue2CommentsComponent
                                bodySelector=".doc_body"
                                :related_object="consolidation.id"
                                model="consolidation.ConsolidationModel" />
                        </div>
                    </template>
                    <a-skeleton
                        v-else
                        active
                        :paragraph="{ rows: 2 }" />
                </div>
            </div>
        </div>
    </a-drawer>
</template>

<script>
import axios from 'axios'
import eventBus from '@/utils/eventBus'

export default {
    name: 'ConsolidationFileView',
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
            if(this.consolidation &&
               this.actions &&
               this.consolidation?.status?.code !== 'consolidated')
                return true
            else
                return false
        },
        consolidation_files() {
            return this.consolidation.consolidation_files
        }
    },
    data() {
        return {
            visible: false,
            consolidation: null,
            activeTabKey: null,
            pdfsrc: {},
            loading: false,
            actionLoading: false,
            actions: null,
            showAside: true,
            getPDFLoading: false,
            cancelTokenSource: {}
        }
    },
    watch: {
        '$route.query'(val) {
            if(val.consolidated_report) {
                if(val?.active_tab) {
                    this.activeTabKey=val.active_tab
                }
                this.visible = true
            }
        },
    },
    created() {
        eventBus.$on('open_report', () => {
            this.visible = true
        })

        if(this.$route.query.consolidated_report)
            this.visible = true
    },
    methods: {
        tabIsChange(key) {
            const index = this.consolidation_files.findIndex(file => file['id'] === key)
            if(index === -1)
                return
            if(!(this.consolidation_files[index].id in this.pdfsrc))
                this.getPDF(this.consolidation_files[index].id)
        },
        getPDF(tabKey) {
            const index = this.consolidation_files.findIndex(rf => rf.id === tabKey)
            if(index === -1)
                return
            if(!this.consolidation_files[index]?.original_file?.id)
                return
            this.$set(this.pdfsrc, tabKey, null)
            this.getPDFLoading = true
            this.cancelTokenSource[tabKey] = axios.CancelToken.source()
            this.$http.get(`/consolidation/${this.consolidation_files[index].original_file.id}/get_pdf/`, {
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
                    link.setAttribute('download', `${this.consolidation.consolidation_file?.name}.${this.consolidation.consolidation_file?.extension}`)
                    document.body.appendChild(link)
                    link.click()
                    link.remove()
                }
            } catch(e) {
                console.log(e)
                this.$message.error('Ошибка')
            } finally {
                this.loading = false
            }
        },
        deleteHandler() {
            this.$confirm({
                title: 'Вы действительно хотите удалить файл отчета?',
                content: '',
                okText: 'Удалить',
                okType: 'danger',
                zIndex: 2000,
                closable: true,
                maskClosable: true,
                cancelText: 'Закрыть',
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post(`/consolidation/${this.consolidation.id}/file_remove/`)
                            .then((data) => {
                                this.$message.success('Отчет удален')
                                eventBus.$emit('update_consolidation_in_list', data.data )
                                eventBus.$emit('update_open_consolidation', data.data )
                                this.visible = false
                                resolve()
                            })
                            .catch(e => {
                                console.log(e)
                                this.$message.error({ content: e[0] ? e[0] : 'Ошибка удаления', key: loadingKey })
                                reject(e)
                            })
                    })
                }
            })
        },
        getPopupContainer() {
            return this.$refs.drawerHeader
        },
        async afterVisibleChange(vis) {
            if(vis) {
                await this.getConsolidation()
            } else {
                const query = Object.assign({}, this.$route.query)
                this.cancelRequests()
                this.cancelTokenSource = {}
                if(query.consolidated_report) {
                    delete query.consolidated_report
                }
                if(query.active_tab) {
                    delete query.active_tab
                }
                this.$router.push({query})
                this.consolidation = null
                this.actions = null
                this.pdfsrc = {}
                this.activeTabKey = null
            }
        },
        async getConsolidation() {
            try {
                this.loading = true
                const query = Object.assign({}, this.$route.query)
                const { data } = await this.$http.get(`/consolidation/${query.consolidated_report}/file_view/`)
                if(data) {
                    this.consolidation = data
                    this.getActions()
                    if(!this.activeTabKey)
                        this.activeTabKey = this.consolidation_files[0].id
                    if(!(this.activeTabKey in this.pdfsrc))
                        this.getPDF(this.activeTabKey)
                }
            } catch(error) {
                if(error && error.detail) {
                    if(error.detail === 'Не найдено.' || error.detail === 'Страница не найдена.' || error.detail === 'У вас недостаточно прав для выполнения данного действия.') {
                        this.$message.warning('Просмотр невозможен')
                    } else {
                        this.$message.error('Ошибка')
                    }
                } else {
                    this.$message.error('Ошибка')
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
                const { data } = await this.$http.get(`/consolidation/${query.consolidated_report}/action_info/`)
                if(data?.actions) {
                    this.actions = data.actions
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.actionLoading = false
            }
        }
    },
    beforeDestroy() {
        eventBus.$off('open_report')
    }
}
</script>

<style lang="scss" scoped>
.consolidation_files_list {
    display: grid;
    grid-template-columns: 32px 1fr;
    align-items: center;
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
        &::v-deep{
            .ant-col{
                min-height: 100%;
            }
            .ant-row{
                min-height: 100%;
            }
        }
        .aside_info{
            padding: 20px;
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
        }
        .document_html{
            background: #e3e8ec;
            padding: 20px 30px;
            min-height: 100%;
            position: relative;
            &::v-deep{
                .ant-tabs-tab {
                    width: 150px;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }
            }
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
        .no-data{
            color: rgb(209 213 219);
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