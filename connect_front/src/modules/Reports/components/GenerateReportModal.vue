<template>
    <a-modal 
        :visible="visible" 
        @cancel="hideModal"
        wrapClassName="modal reports-generate-modal"
        :closable="!isMobile"
        :width="isMobile ? '100vw' : undefined"
        :bodyStyle="modalBodyStyle"
        :style="modalStyle"
        :footer="null"
        @afterVisibleChange="afterVisibleChange">
        <template slot="title">
            <div class="flex justify-between items-start ">
                <div class="w-full max-w-[600px]">
                    <a-form-model 
                        v-if="activeTemplate.editable && editMode"
                        ref="headerForm" 
                        v-on-click-outside="disableEditMode"
                        :model="form" 
                        :rules="rules" 
                        class="">
                        <a-form-model-item prop="name" class="mb-0">
                            <a-input
                                v-model="formName"
                                ref="nameField"
                                class="form__title"
                                @blur="handleHeaderFieldBlur"
                                @keyup.enter="disableEditMode"
                                :placeholder="$t('Report name')" />
                        </a-form-model-item>
                        <a-form-model-item class="mb-0">
                            <a-input
                                v-model="formDescription"
                                class="form__description"
                                @blur="handleHeaderFieldBlur"
                                @keyup.enter="disableEditMode"
                                :placeholder="$t('Report description')" />
                        </a-form-model-item>
                    </a-form-model>
                    <template v-else>
                        <div class="template-title-row">
                            <a-button
                                v-if="activeTemplate.editable"
                                flaticon
                                type="link"
                                v-tippy
                                :content="$t('report_fields_edit')"
                                shape="circle"
                                icon="fi-rr-edit"
                                @click="triggerTemplateEdit" />
                            <div
                                @click="triggerTemplateEdit"
                                :class="activeTemplate.editable && 'cursor-pointer'">
                                {{ activeTemplate?.name || $t('Untitled') }}
                            </div>
                        </div>
                        <div
                            @click="triggerTemplateEdit"
                            class="template-description"
                            :class="activeTemplate.editable && 'cursor-pointer'">
                            {{ templateDescription }}
                        </div>
                    </template>
                </div>
                <div class="flex items-center">
                    <a-button
                        v-if="isMobile"
                        type="ui"
                        shape="circle"
                        ghost
                        flaticon
                        icon="fi-rr-cross-small"
                        @click="hideModal" />
                    <template v-if="activeTemplate.is_base">
                        <OpenReportModalButton 
                            v-if="!isMobile"
                            class="mr-1"
                            :showMore="false"
                            :sectionCode="activeTemplate.appSectionCode" 
                            :baseTemplateId="activeTemplate.id">
                            <template #button="{ templateLoading }">
                                <a-button 
                                    :loading="templateLoading"
                                    type="link">
                                    {{ $t('reports_mobule.save_versions') }}
                                </a-button>
                            </template>
                        </OpenReportModalButton>
                    </template>
                    <a-button
                        v-if="!isMobile && canShareReportSettings"
                        type="ui_ghost"
                        class="mr-1"
                        flaticon
                        icon="fi-rr-share"
                        @click="openShareModal">
                        {{ $t('Share') }}
                    </a-button>
                    <HelpButton partCode="reports" />
                </div>
            </div>
        </template>

        <div ref="modalBody" class="report-modal-body" :class="isMobile && 'report-modal-body_mobile'">
            <div v-if="isMobile" class="report-modal-mobile-actions report-modal-mobile-actions_top">
                <a-button
                    type="primary"
                    block
                    class="report-modal-mobile-generate-button"
                    @click="generateReportV2"
                    :loading="generateReportV2Loading">
                    {{ $t('Generate report') }}
                </a-button>
                <a-button
                    v-if="activeTemplate.editable && hasChanges"
                    type="primary"
                    block
                    flaticon
                    icon="fi-rr-disk"
                    @click="updateTemplate">
                    {{ $t('Save changes') }}
                </a-button>
                <a-button class="report-modal-mobile-version-button" type="primary" ghost block @click="createTemplate">
                    {{ $t('Save as new version') }}
                </a-button>
                <a-button
                    v-if="canShareReportSettings"
                    type="default"
                    block
                    flaticon
                    icon="fi-rr-share"
                    @click="openShareModal">
                    {{ $t('Share') }}
                </a-button>
                <OpenReportModalButton
                    v-if="activeTemplate.is_base"
                    :showMore="false"
                    :sectionCode="activeTemplate.appSectionCode"
                    :baseTemplateId="activeTemplate.id">
                    <template #button="{ templateLoading }">
                        <a-button
                            :loading="templateLoading"
                            type="default"
                            block
                            class="report-modal-mobile-link-button">
                            {{ $t('reports_mobule.save_versions') }}
                        </a-button>
                    </template>
                </OpenReportModalButton>
            </div>

            <div class="report-modal-content-grid" :class="isMobile && 'report-modal-content-grid_mobile'">
            <div v-if="!isMobile" class="min-h-0 flex flex-col px-5 py-6 bg-[#F8F9FD] rounded-xl">
                <div class="pb-3 border-b border-[#DADADA]">{{ $t('Available fields') }}</div>
                <div class="pt-3 overflow-y-auto">
                    <FieldTree 
                        :fields="availableFields"
                        :checkedFields="checkedFields"
                        :loadData="loadTreeData"
                        :model="modelName"
                        @add="onAddField" />
                </div>
            </div>
            <div class="min-h-0 flex flex-col px-5 py-6 col-span-2 bg-[#F8F9FD] rounded-xl">
                <a-button
                    v-if="isMobile"
                    type="flat_primary"
                    block
                    flaticon
                    icon="fi-rr-plus"
                    class="mb-3"
                    @click="fieldsDrawerVisible = true">
                    {{ $t('Add fields') }}
                </a-button>
                <a-tabs v-model="activeTab" class="report-modal-tabs">
                    <a-tab-pane 
                        v-for="tab in tabs" 
                        :key="tab.key">
                        <template slot="tab">
                            <i class="mr-2 fi" :class="tab.icon"></i>
                            {{ $t(tab.title) }}
                        </template>
                    </a-tab-pane>
                </a-tabs>
                <div class="pt-3 overflow-y-auto">
                    <component 
                        :is="bodyComponent" />
                </div>
            </div>
            </div>

        </div>

        <div v-if="!isMobile" class="mt-6 flex justify-between items-center pb-4">
            <div class="footer-left">
                <a-button type="primary" ghost class="mr-1" @click="createTemplate">{{ $t('Save as new version') }}</a-button>
                <template v-if="activeTemplate.editable">
                    <a-button 
                        v-if="hasChanges" 
                        type="primary" 
                        ghost 
                        class="mr-1" 
                        @click="updateTemplate">
                        {{ $t('Save changes') }}
                    </a-button>
                    <!-- <a-button type="default" ghost class="mr-1" @click="discardChanges" :disabled="!hasChanges">{{ $t('Discard changes') }}</a-button> -->
                </template>
            </div>
            <div class="footer-right flex items-center">
                <template>
                    <a-button
                        v-tippy
                        :content="$t('Generate report old version')"
                        class="mr-1"
                        icon="fi-rr-poll-h"
                        flaticon
                        type="primary"
                        @click="generateReport"
                        :loading="generateReportLoading" />
                    <a-button class="mr-1" type="primary" @click="generateReportV2" :loading="generateReportV2Loading">
                        {{ $t('Generate report') }}
                    </a-button>
                </template>
                <a-button type="ui" ghost @click="hideModal">{{ $t('Close') }}</a-button>
            </div>
        </div>
        <template v-if="visible">
            <PreviewReportModal
                :getContainer="nestedModalContainer"
                ref="previewReportModal" />
            <CreateTemplateModal
                :getContainer="nestedModalContainer"
                ref="createTemplateModal" />
            <CreateAggregateFieldModal :getContainer="nestedModalContainer" />
            <a-modal
                :visible="shareModalVisible"
                :title="$t('Share report settings')"
                :width="420"
                wrapClassName="report-share-modal-wrap"
                :getContainer="nestedModalContainer"
                @cancel="closeShareModal">
                <div class="report-share-modal">
                    <div class="report-share-modal__title">{{ activeTemplate?.name || $t('Untitled') }}</div>
                    <div class="report-share-modal__description">
                        {{ $t('Download report settings as JSON file') }}
                    </div>
                </div>
                <template slot="footer">
                    <div class="report-share-modal__actions">
                        <a-button
                            block
                            type="primary"
                            flaticon
                            icon="fi-rr-download"
                            @click="downloadReportSettings">
                            {{ $t('Download JSON') }}
                        </a-button>
                        <a-button
                            block
                            flaticon
                            icon="fi-rr-comment"
                            :loading="shareReportSettingsLoading"
                            @click="shareReportSettingsToChat">
                            {{ $t('Share to chat') }}
                        </a-button>
                    </div>
                </template>
            </a-modal>
            <DrawerTemplate
                v-if="isMobile"
                :value="fieldsDrawerVisible"
                wrapClassName="report-fields-drawer"
                title=""
                height="100%"
                disabledBodyPadding
                destroyOnClose
                @close="fieldsDrawerVisible = false">
                <template #title>
                    <div>{{ $t('Available fields') }}</div>
                </template>
                <div class="report-fields-drawer-body">
                    <FieldTree 
                        :fields="availableFields"
                        :checkedFields="checkedFields"
                        :loadData="loadTreeData"
                        :model="modelName"
                        @add="onAddField" />
                </div>
                <template #footer>
                    <a-button
                        type="ui_ghost"
                        size="large"
                        block
                        @click="fieldsDrawerVisible = false">
                        {{ $t('Close') }}
                    </a-button>
                </template>
            </DrawerTemplate>
            <a-modal
                v-if="isMobile"
                :visible="mobileTemplateEditVisible"
                wrapClassName="report-template-mobile-edit-modal"
                :footer="null"
                :getContainer="nestedModalContainer"
                @cancel="closeMobileTemplateEditModal">
                <template slot="title">
                    {{ $t('report_fields_edit') }}
                </template>
                <a-form-model
                    ref="mobileTemplateEditForm"
                    :model="mobileTemplateEditForm"
                    :rules="rules">
                    <a-form-model-item prop="name" class="mb-2">
                        <a-input
                            v-model="mobileTemplateEditForm.name"
                            size="large"
                            :placeholder="$t('Report name')" />
                    </a-form-model-item>
                    <a-form-model-item class="mb-0">
                        <a-input
                            v-model="mobileTemplateEditForm.description"
                            size="large"
                            :placeholder="$t('Report description')" />
                    </a-form-model-item>
                </a-form-model>
                <div class="mt-4">
                    <a-button
                        type="primary"
                        block
                        :loading="mobileTemplateEditLoading"
                        @click="saveMobileTemplateMeta">
                        {{ $t('Save changes') }}
                    </a-button>
                </div>
            </a-modal>
        </template>
    </a-modal>
</template>

<script>
import { v1 as uuidv1 } from 'uuid'
import { vOnClickOutside } from '@vueuse/components'
import { errorHandler } from '@/utils/index.js'
import { openOnlyofficePreview } from '@/utils/onlyoffice'
import { mapState } from 'vuex'

const TABS = [
    {
        key: 'columns',
        icon: 'fi-rr-rectangle-list',
        title: 'Table columns'
    },
    {
        key: 'filters',
        icon: 'fi-rr-filter',
        title: 'Filters'
    },
    {
        key: 'grouping',
        icon: 'fi-rr-folder',
        title: 'Grouping'
    },
]

const REPORT_SETTINGS_EXPORT_KIND = 'ReportSetting'
const REPORT_SETTINGS_EXPORT_VERSION = 1

export default {
    components: {
        FieldTree: () => import('./FieldTree.vue'),
        PreviewReportModal: () => import('./PreviewReportModal.vue'),
        CreateTemplateModal: () => import('./CreateTemplateModal.vue'),
        CreateAggregateFieldModal: () => import('./CreateAggregateFieldModal.vue'),
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue'),
        HelpButton: () => import('@apps/Support/components/HelpButton.vue'),
        OpenReportModalButton: () => import('./OpenReportModalButton.vue')
    },
    directives: {
        onClickOutside: vOnClickOutside
    },
    computed: {
        ...mapState({
            isMobile: state => state.isMobile
        }),
        templateDescription() {
            if (this.activeTemplate.description) { return this.activeTemplate.description }
            if (this.activeTemplate.editable) { return this.$t('Add description') }
            return ''
        },
        formName: {
            get() { return this.activeTemplate.name },
            set(value) { this.$store.commit('reports/UPDATE_TEMPLATE_NAME', value)}
        },
        formDescription: {
            get() { return this.activeTemplate.description },
            set(value) { this.$store.commit('reports/UPDATE_TEMPLATE_DESCRIPTION', value)}
        },
        activeTemplate() {
            return this.$store.state.reports.activeTemplate
        },
        canShareReportSettings() {
            return true
        },
        activeMetadata() {
            return this.activeTemplate.metadata
        },
        modelName() {
            return this.activeMetadata.modelName
        },
        availableFields() {
            return this.activeTemplate.availableFields || []
        },
        visible() {
            return this.$store.state.reports.reportModalVisible
        },
        bodyComponent() {
            const components = {
                columns: () => import('./TabWidgets/ColumnList.vue'),
                filters: () => import('./TabWidgets/FilterTab.vue'),
                grouping: () => import('./TabWidgets/GroupingList.vue')
            }
            return components[this.activeTab] || null
        },
        checkedFields() {
            if (this.activeTemplate.complexFilterMode) {
                return []
            }
            const metadataField = this.activeTab
            const activeMetadata = this.activeMetadata[metadataField]
            return activeMetadata.map(column => column.aggregate ? column.verbose_name : column.name)
        },
        modalBodyStyle() {
            if (this.isMobile) {
                return {
                    padding: '0'
                }
            }

            return {}
        },
        modalStyle() {
            if (this.isMobile) {
                return {
                    top: 0,
                    paddingBottom: 0
                }
            }

            return {}
        },
        nestedModalContainer() {
            return this.isMobile
                ? () => document.body
                : this.getContainer
        },
        hasChanges() {
            return this.$store.getters['reports/hasChanges']
        }
    },
    data() {
        return {
            editMode: false,
            rules: {
                name: [
                    { required: true, message: this.$t('Name cannot be empty'), trigger: 'blur' }
                ]
            },
            form: {
                name: '',
                description: '',
            },
            activeTab: 'columns',
            tabs: TABS,
            fieldsDrawerVisible: false,
            mobileTemplateEditVisible: false,
            mobileTemplateEditLoading: false,
            mobileTemplateEditForm: {
                name: '',
                description: '',
            },
            shareModalVisible: false,
            shareReportSettingsLoading: false,
            generateReportLoading: false,
            generateReportV2Loading: false,
        }
    },
    beforeDestroy() {
        this.editMode = false
        this.fieldsDrawerVisible = false
        this.mobileTemplateEditVisible = false
    },
    methods: {
        getContainer() {
            return this.$refs.modalBody
        },
        afterVisibleChange(vis) {
            if(!vis) {
                this.$store.commit('reports/CLOSE_REPORT_MODAL_CHECK')
            }
        },
        disableEditMode() {
            this.editMode = false
        },
        handleHeaderFieldBlur() {
            setTimeout(() => {
                const formElement = this.$refs.headerForm?.$el
                if (formElement?.contains(document.activeElement)) {
                    return
                }
                this.disableEditMode()
            }, 0)
        },
        enableEditMode() {
            this.form = {
                name: String(this.activeTemplate.name),
                description: String(this.activeTemplate.description),
            }
            this.editMode = true
            this.$nextTick(() => {
                if(this.$refs.nameField)
                    this.$refs.nameField.focus()
            })
        },
        triggerTemplateEdit() {
            if (!this.activeTemplate.editable) {
                return
            }

            if (this.isMobile) {
                this.openMobileTemplateEditModal()
                return
            }

            this.enableEditMode()
        },
        openMobileTemplateEditModal() {
            this.mobileTemplateEditForm = {
                name: String(this.activeTemplate.name || ''),
                description: String(this.activeTemplate.description || ''),
            }
            this.mobileTemplateEditVisible = true
        },
        closeMobileTemplateEditModal() {
            this.mobileTemplateEditVisible = false
        },
        createTemplate() {
            this.$refs.createTemplateModal.showModal()
        },
        openShareModal() {
            this.shareModalVisible = true
        },
        closeShareModal() {
            this.shareModalVisible = false
        },
        getReportSettingsFileName() {
            const reportName = this.activeTemplate?.name || this.$t('Untitled')
            const safeReportName = String(reportName)
                .trim()
                .replace(/[\\/:*?"<>|]+/g, '-')
                .replace(/\s+/g, ' ')
                || this.$t('Untitled')

            return `ReportSetting-${safeReportName}.json`
        },
        getReportSettingsExportPayload() {
            const template = JSON.parse(JSON.stringify(this.activeTemplate || {}))
            delete template.availableFields

            return {
                kind: REPORT_SETTINGS_EXPORT_KIND,
                version: REPORT_SETTINGS_EXPORT_VERSION,
                exportedAt: new Date().toISOString(),
                reportName: template.name || '',
                template
            }
        },
        createReportSettingsFile() {
            const blob = new Blob(
                [JSON.stringify(this.getReportSettingsExportPayload(), null, 2)],
                { type: 'application/json;charset=utf-8' }
            )
            const fileName = this.getReportSettingsFileName()

            return new File([blob], fileName, { type: 'application/json' })
        },
        downloadReportSettings() {
            const file = this.createReportSettingsFile()
            const url = URL.createObjectURL(file)
            const link = document.createElement('a')
            link.href = url
            link.download = file.name
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
            URL.revokeObjectURL(url)
            this.closeShareModal()
        },
        async shareReportSettingsToChat() {
            this.shareReportSettingsLoading = true

            try {
                const data = await this.$uploadFile({
                    file: this.createReportSettingsFile(),
                    url: '/common/upload/',
                    fieldName: 'upload'
                })
                const uploadedFile = Array.isArray(data) ? data[0] : data

                if (!uploadedFile?.id) {
                    throw new Error('empty_uploaded_report_settings_file')
                }

                this.closeShareModal()
                this.$store.commit('share/SET_SHARE_PARAMS', {
                    model: 'files.files',
                    object: uploadedFile,
                    bodySelector: this.isMobile ? 'body' : '.reports-generate-modal',
                    shareTitle: this.activeTemplate?.name || this.$t('Untitled')
                })
            } catch (error) {
                errorHandler({ error })
                this.$message.error(this.$t('Failed to share report settings'))
            } finally {
                this.shareReportSettingsLoading = false
            }
        },
        updateTemplate() {
            this.$store.dispatch('reports/updateTemplate')
                .then(() => {
                    this.$message.success(this.$t('Saved'))
                })
        },
        saveMobileTemplateMeta() {
            this.$refs.mobileTemplateEditForm.validate(async valid => {
                if (!valid) {
                    return
                }

                this.mobileTemplateEditLoading = true
                this.$store.commit('reports/UPDATE_TEMPLATE_NAME', this.mobileTemplateEditForm.name)
                this.$store.commit('reports/UPDATE_TEMPLATE_DESCRIPTION', this.mobileTemplateEditForm.description)

                try {
                    await this.$store.dispatch('reports/updateTemplate')
                    this.$message.success(this.$t('Saved'))
                    this.closeMobileTemplateEditModal()
                } finally {
                    this.mobileTemplateEditLoading = false
                }
            })
        },
        discardChanges() {
            this.$confirm({
                title: this.$t('Discard changes?'),
                content: this.$t('All unsaved changes will be lost.'),
                okText: this.$t('Cancel'),
                cancelText: this.$t('Continue editing'),
                onOk: () => {
                    this.$store.commit('reports/DISCARD_CHANGES')
                }
            })
        },
        loadTreeData(node) {
            this.getRelatedModelMeta(node.related_model.toLowerCase())
                .then(data => {
                    const fields = data.map(field => ({
                        ...field,
                        name: `${treeNode.dataRef.name}__${field.name}`,
                        key: `${treeNode.dataRef.name}__${field.name}`,
                        defaultTitle: field.verbose_name,
                        title: field.verbose_name
                    }))

                    node.children = fields
                })
                .catch(error => {
                    console.error(error)
                    this.$message.error(this.$t('Failed to get available fields'))
                })

        },
        generateReport() {
            const url = `reports/${this.modelName}/list_post/`

            const payload = this.$store.getters['reports/reportParams']()
            this.generateReportLoading = true
            this.$http.post(url, payload)
                .then(({ data }) => {
                    this.$refs.previewReportModal.showModalWithHTML(data)
                })
                .catch(error => {
                    errorHandler({error})
                })
                .finally(() => {
                    this.generateReportLoading = false
                })
        },
        async generateReportV2() {
            const payload = this.$store.getters['reports/reportParams'](false)
            this.generateReportV2Loading = true

            try {
                const { data } = await this.$http.post('/onlyoffice/report-session/', {
                    model_name: this.modelName,
                    report_payload: payload
                })

                if (!data?.session_id) {
                    throw new Error('empty_onlyoffice_report_session')
                }

                openOnlyofficePreview(this.$store, {
                    scope: 'report_session',
                    session_id: data.session_id
                })
            } catch (error) {
                errorHandler({ error })
            } finally {
                this.generateReportV2Loading = false
            }
        },
        getRelatedModelMeta(modelName) {
            const params = {
                meta: true,
            }
            const url = `reports/${modelName}/`
            return this.$http.get(url, { params })
                .then(({ data }) => data?.meta)
                .catch(error => {
                    console.error(error)
                    this.$message.error(this.$t('Failed to get fields list'))
                })
        },
        onAddField(node) {
            if (this.activeTab === 'filters') {     
                const filterField = {
                    ...node, 
                    value: null,
                    comparison_type: '',
                    id: uuidv1()
                }
                if (this.activeTemplate.complexFilterMode) {
                    this.$store.commit('reports/ADD_ITEM', { listKey: 'complexFilters', item: filterField })
                } else {
                    this.$store.commit('reports/ADD_ITEM', { listKey: 'filters', item: filterField })
                }
            } else if (this.activeTab === 'columns') {
                const column = { ...node, is_visible: true }
                this.$store.commit('reports/ADD_ITEM', { listKey: 'columns', item: column })
                this.$store.commit('reports/REORDER_COLUMN_LIST')
            } else if (this.activeTab === 'grouping') {
                this.$store.commit('reports/ADD_ITEM', { listKey: 'grouping', item: node })

                // TODO переделать добавление из группировки если удаляется из списка колонок
                if (this.activeMetadata.columns.findIndex(column => column.name === node.name) === -1) {
                    this.$store.commit('reports/ADD_ITEM', { listKey: 'columns', item: node })
                }
            }
        },
        hideModal() {
            if (this.activeTemplate.editable && this.hasChanges) {
                this.$confirm({
                    title: this.$t('Close without saving?'),
                    content: this.$t('You have unsaved changes. All changes will be lost.'),
                    okText: this.$t('Close'),
                    cancelText: this.$t('Cancel'),
                    onOk: () => {
                        this.fieldsDrawerVisible = false
                        this.mobileTemplateEditVisible = false
                        this.$store.commit('reports/CLOSE_REPORT_MODAL')
                    }
                })
            } else {
                this.fieldsDrawerVisible = false
                this.mobileTemplateEditVisible = false
                this.$store.commit('reports/CLOSE_REPORT_MODAL')
            }
        },
        enableEditTitle() {
            this.editTitleMode = true
            this.editableTitle = this.activeTemplate?.name || ''
            this.$nextTick(() => {
                this.$refs.titleInput?.focus()
            })
        },
        saveTitle() {
            this.$refs.titleForm.validate(valid => {
                if (valid) {
                    const trimmedTitle = this.editableTitle.trim()
                    if (trimmedTitle !== this.activeTemplate?.name) {
                        this.$store.commit('reports/UPDATE_TEMPLATE_NAME', trimmedTitle)
                    }
                    this.editTitleMode = false
                } else {
                    // Если валидация не прошла, фокусируемся на поле ввода
                    this.$nextTick(() => {
                        this.$refs.titleInput?.focus()
                    })
                }
            })
        },
        cancelEditTitle() {
            this.editTitleMode = false
            this.editableTitle = this.activeTemplate?.name || ''
        }
    },
}
</script>

<style lang="scss" scoped>

:deep {
    .modal .ant-modal {
        max-width: 1240px;
        width: 100% !important;
        min-width: 500px;
        padding: 0 15px;
        top: 10px;
    }
}

:deep(.report-share-modal-wrap) {
    .ant-modal {
        width: 420px !important;
        min-width: 420px !important;
        max-width: 420px !important;
        padding: 0;
        top: 10px;
    }
}

:deep(.reports-generate-modal) {
    @media (max-width: 768px) {
        top: 0;
        padding: 0;
        overflow: hidden;

        .ant-modal {
            width: 100vw !important;
            max-width: 100vw;
            min-width: 100vw;
            margin: 0;
            top: 0 !important;
            padding: 0 !important;
            height: 100vh;
        }

        .ant-modal-content {
            display: flex;
            flex-direction: column;
            height: 100vh;
            border-radius: 0;
            overflow: hidden;
        }

        .ant-modal-header {
            padding: 16px 16px 0;
        }

        .ant-modal-body {
            flex: 1;
            min-height: 0;
            padding: 0;
        }
    }
}


.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
:deep {
    .ant-tabs-bar {
        margin-bottom: 0;
    }
    .ant-tabs-tab {
        padding-top: 0;
        padding-bottom: 14px;
    }
}

.template-description {
    color: #888888;
    font-size: 14px;
    font-weight: 400;
}

.template-title-row {
    display: inline-flex;
    align-items: center;
    gap: 8px;
}

.report-share-modal {
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.report-share-modal__title {
    font-weight: 600;
    color: #1f1f1f;
}

.report-share-modal__description {
    color: #777777;
}

.report-share-modal__actions {
    display: flex;
    flex-direction: column;
    gap: 8px;
    width: 100%;
}

.report-modal-body {
    display: grid;
    grid-template-rows: minmax(0, 1fr);
    gap: 24px;
    height: 600px;
}

.report-modal-body_mobile {
    height: 100%;
    padding: 12px 12px calc(16px + env(safe-area-inset-bottom));
    grid-template-rows: auto minmax(0, 1fr) auto;
    gap: 12px;
}

.report-modal-content-grid {
    min-height: 0;
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 24px;
}

.report-modal-content-grid_mobile {
    grid-template-columns: minmax(0, 1fr);
    gap: 12px;
}

.report-modal-content-grid_mobile > :last-child {
    grid-column: auto;
}

.report-modal-mobile-actions {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.report-modal-mobile-link-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding-left: 0;
    padding-right: 0;
    text-align: center;

    :deep(span) {
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }
}

:deep(.report-fields-drawer) {
    .drawer_body {
        padding: 0;
    }

    .node__title {
        padding-left: 0;
        padding-right: 0;
    }
}

:deep(.report-modal-tabs) {
    .ant-tabs-bar {
        min-height: 40px;
        margin-bottom: 0;
    }

    .ant-tabs-nav-container {
        min-height: 40px;
        display: flex;
        align-items: center;
    }

    .ant-tabs-tab {
        min-height: 32px;
        display: inline-flex;
        align-items: center;
        line-height: 1.2;
        padding-top: 0;
        padding-bottom: 0;
    }

    .ant-tabs-tab .fi {
        line-height: 1;
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }

    .ant-tabs-nav-scroll,
    .ant-tabs-nav-wrap,
    .ant-tabs-nav {
        min-height: 40px;
        display: flex;
        align-items: center;
    }

    @media (max-width: 768px) {
        min-height: 44px;
        display: block;

        .ant-tabs-nav-container.ant-tabs-nav-container-scrolling {
            padding-left: 24px;
            padding-right: 24px;
        }
    }
}

:deep(.report-template-mobile-edit-modal .ant-modal) {
    max-width: 520px;
}

@media (max-width: 768px) {
    :deep(.report-template-mobile-edit-modal .ant-modal) {
        width: calc(100vw - 24px) !important;
        max-width: calc(100vw - 24px);
        margin: 12px auto;
        top: 0;
        padding-bottom: 0;
    }
}
</style>
