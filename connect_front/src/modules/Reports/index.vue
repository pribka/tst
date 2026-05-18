<template>
    <ModuleWrapper 
        :pageTitle="pageTitle">
        <template v-if="!isMobile" v-slot:h_left>
            <div class="search_input">
                <a-input
                    v-model="searchQuery"
                    :placeholder="$t('reports_mobule.search_placeholder')"
                    @input="handleSearchInput" />
                <div class="flex items-center gap-1">
                    <i class="fi fi-rr-search" />
                    <a-button
                        v-if="searchQuery"
                        type="link"
                        size="small"
                        class="clear_btn"
                        icon="fi-rr-cross-small"
                        shape="circle"
                        flaticon
                        @click="clearSearch" />
                </div>
            </div>
        </template>
        <template v-slot:h_right>
            <div class="reports-header-actions">
                <a-button v-if="!isMobile" type="primary" ghost @click="openImportReportModal">
                    {{ $t('Upload report') }}
                </a-button>
                <HelpButton partCode="reports" type="button" />
            </div>
        </template>
        <div v-if="isMobile" class="mb-2">
            <div class="search_input">
                <a-input
                    v-model="searchQuery"
                    :placeholder="$t('reports_mobule.search_placeholder')"
                    @input="handleSearchInput" />
                <div class="flex items-center gap-1">
                    <i class="fi fi-rr-search" />
                    <a-button
                        v-if="searchQuery"
                        type="link"
                        size="small"
                        class="clear_btn"
                        icon="fi-rr-cross-small"
                        shape="circle"
                        flaticon
                        @click="clearSearch" />
                </div>
            </div>
        </div>
        <div v-if="!isMobile" class="flex items-center justify-between gap-2">
            <a-spin :spinning="categoriesLoading || categoriesCountLoading" size="small">
                <Segmented
                    v-model="displaySectionCode"
                    @change="changeDisplaySection"
                    :options="displaySectionOptions" />
            </a-spin>
            <Segmented  
                v-model="templatesSource"
                @change="changeTemplateSource"
                :options="tabOptions" />
        </div>
        <template v-if="isMobile">
            <Segmented  
                v-model="templatesSource"
                class="mb-2"
                @change="changeTemplateSource"
                :options="tabOptions" />
            <a-spin :spinning="categoriesLoading || categoriesCountLoading" size="small">
                <Segmented
                    v-model="displaySectionCode"
                    @change="changeDisplaySection"
                    :options="displaySectionOptions" />
            </a-spin>
        </template>
        <TemplateGrid
            ref="templateGrid"
            :templatesSource="templatesSource"
            :displaySectionCode="displaySectionCode"
            :searchQuery="appliedSearchQuery"
            class="mt-3" />
        <div v-if="isMobile" class="float_add">
            <a-button
                shape="circle"
                size="large"
                type="primary"
                @click="openImportReportModal">
                <i class="fi fi-rr-file-upload"></i>
            </a-button>
        </div>
        <div v-if="reportDragActive || reportDropLoading" class="report-drop-overlay">
            <div class="report-drop-overlay__content">
                <a-spin v-if="reportDropLoading" />
                <span>{{ reportDropLoading ? $t('Processing report settings') : $t('Upload report') }}</span>
            </div>
        </div>
        <a-modal
            :visible="importReportModalVisible"
            :title="$t('Upload report')"
            @cancel="closeImportReportModal">
            <div class="report-import-form">
                <label class="report-import-form__label">{{ $t('Report settings JSON file') }}</label>
                <input
                    ref="reportSettingsFileInput"
                    type="file"
                    accept="application/json,.json"
                    @change="handleReportSettingsFileChange" />
                <div v-if="selectedReportSettingsFile" class="report-import-form__file">
                    {{ selectedReportSettingsFile.name }}
                </div>
            </div>
            <template slot="footer">
                <div class="report-import-form__actions w-full">
                    <a-button
                        type="primary"
                        :block="isMobile"
                        :disabled="!selectedReportSettingsFile"
                        :loading="importReportLoading"
                        @click="importReportSettings">
                        {{ $t('Upload') }}
                    </a-button>
                    <a-button
                        type="ui_ghost"
                        :block="isMobile"
                        @click="closeImportReportModal">
                        {{ $t('Cancel') }}
                    </a-button>
                </div>
            </template>
        </a-modal>
    </ModuleWrapper>
</template>

<script>
const REPORT_SETTINGS_EXPORT_KIND = 'ReportSetting'
const DEFAULT_TEMPLATES_SOURCE = 'templates'
const DEFAULT_DISPLAY_SECTION_CODE = ''
const SEARCH_DEBOUNCE_MS = 600
const DRAG_LISTENER_OPTIONS = { capture: true }

export default {
    components: {
        ModuleWrapper: () => import('@/components/ModuleWrapper/index.vue'),
        HelpButton: () => import('@apps/Support/components/HelpButton.vue'),
        Segmented: () => import('@apps/UIModules/Segmented'),
        TemplateGrid: () => import('./components/Templates/TemplateGrid.vue')
    },
    computed: {
        isMobile() { 
            return this.$store.state.isMobile
        },
        pageTitle() {
            return this.$route?.meta?.title || ''
        },
        tabOptions() {
            return [
                { key: 'templates', title: this.$t('reports_mobule.report_catalog') },
                { key: 'my_templates', title: this.$t('reports_mobule.save_versions') },
            ]
        },
        reportCategories() {
            return this.$store.state.reports.reportCategories || []
        },
        displaySectionOptions() {
            const options = [
                { 
                    key: '', 
                    title: this.$t('reports_mobule.all_reports'),
                    count: this.reportCategoryCounts.total || 0
                },
            ]

            this.reportCategories.forEach(item => {
                if (item?.code && item?.string_view) {
                    options.push({
                        key: item.code,
                        title: item.string_view,
                        count: this.reportCategoryCounts[item.code] || 0
                    })
                }
            })

            return options
        }
    },
    data() {
        return {
            templatesSource: DEFAULT_TEMPLATES_SOURCE,
            displaySectionCode: DEFAULT_DISPLAY_SECTION_CODE,
            searchQuery: '',
            appliedSearchQuery: '',
            categoriesLoading: false,
            categoriesCountLoading: false,
            reportCategoryCounts: {},
            importReportModalVisible: false,
            selectedReportSettingsFile: null,
            importReportLoading: false,
            reportDragActive: false,
            reportDropLoading: false,
            reportDragCounter: 0,
            searchTimer: null
        }
    },
    created() {
        this.applyRouteQueryState()
    },
    mounted() {
        this.initReportCategories()
        this.getReportCategoryCounts()
        window.addEventListener('dragenter', this.handleWindowDragEnter, DRAG_LISTENER_OPTIONS)
        window.addEventListener('dragover', this.handleWindowDragOver, DRAG_LISTENER_OPTIONS)
        window.addEventListener('dragleave', this.handleWindowDragLeave, DRAG_LISTENER_OPTIONS)
        window.addEventListener('drop', this.handleWindowDrop, DRAG_LISTENER_OPTIONS)
    },
    methods: {
        async initReportCategories() {
            this.categoriesLoading = true
            const categories = await this.$store.dispatch('reports/getReportCategories')
            this.categoriesLoading = false

            if (!Array.isArray(categories)) {
                return
            }

            const categoriesCodes = categories.map(item => item.code)
            if (this.displaySectionCode && !categoriesCodes.includes(this.displaySectionCode)) {
                this.displaySectionCode = DEFAULT_DISPLAY_SECTION_CODE
                this.syncQueryState()
                this.$refs.templateGrid.reload()
            }
        },
        async getReportCategoryCounts() {
            const isMyTemplates = this.templatesSource === 'my_templates'
            const url = isMyTemplates
                ? '/reports/user_report_settings/count_by_category/'
                : '/reports/report_settings/count_by_category/'
            const requestedSource = this.templatesSource
            const requestedSearch = this.appliedSearchQuery
            const params = {}

            if (requestedSearch) {
                params.search = requestedSearch
            }

            this.categoriesCountLoading = true
            try {
                const { data } = await this.$http.get(url, { params })
                if (requestedSource !== this.templatesSource || requestedSearch !== this.appliedSearchQuery) {
                    return
                }
                this.reportCategoryCounts = data || {}
            } catch (error) {
                console.error(error)
                if (requestedSource === this.templatesSource && requestedSearch === this.appliedSearchQuery) {
                    this.reportCategoryCounts = {}
                }
            } finally {
                if (requestedSource === this.templatesSource && requestedSearch === this.appliedSearchQuery) {
                    this.categoriesCountLoading = false
                }
            }
        },
        handleSearchInput() {
            clearTimeout(this.searchTimer)
            this.searchTimer = setTimeout(() => {
                this.applySearch()
            }, SEARCH_DEBOUNCE_MS)
        },
        applySearch(force = false) {
            const normalizedSearch = this.searchQuery.trim()
            if (!force && normalizedSearch === this.appliedSearchQuery) {
                return
            }

            this.appliedSearchQuery = normalizedSearch
            this.getReportCategoryCounts()
            this.$refs.templateGrid.reload()
        },
        clearSearch() {
            clearTimeout(this.searchTimer)
            this.searchQuery = ''
            this.applySearch(true)
        },
        applyRouteQueryState() {
            const templatesSource = this.$route?.query?.templates_source
            const displaySectionCode = this.$route?.query?.display_section_code

            if (this.tabOptions.some(option => option.key === templatesSource)) {
                this.templatesSource = templatesSource
            }

            if (typeof displaySectionCode === 'string') {
                this.displaySectionCode = displaySectionCode
            }
        },
        syncQueryState() {
            const query = { ...this.$route.query }

            if (this.templatesSource === DEFAULT_TEMPLATES_SOURCE) {
                delete query.templates_source
            } else {
                query.templates_source = this.templatesSource
            }

            if (this.displaySectionCode === DEFAULT_DISPLAY_SECTION_CODE) {
                delete query.display_section_code
            } else {
                query.display_section_code = this.displaySectionCode
            }

            const currentQuery = { ...this.$route.query }
            if (JSON.stringify(currentQuery) === JSON.stringify(query)) {
                return
            }

            this.$router.replace({ query })
        },
        changeTemplateSource() {
            this.syncQueryState()
            this.getReportCategoryCounts()
            this.$refs.templateGrid.reload()
        },
        changeDisplaySection() {
            this.syncQueryState()
            this.$refs.templateGrid.reload()
        },
        openImportReportModal() {
            this.selectedReportSettingsFile = null
            this.importReportModalVisible = true
            this.$nextTick(() => {
                if (this.$refs.reportSettingsFileInput) {
                    this.$refs.reportSettingsFileInput.value = ''
                }
            })
        },
        closeImportReportModal() {
            if (this.importReportLoading) {
                return
            }
            this.importReportModalVisible = false
            this.selectedReportSettingsFile = null
        },
        handleReportSettingsFileChange(event) {
            const [file] = event.target.files || []
            this.selectedReportSettingsFile = file || null
        },
        isFileDrag(event) {
            return Array.from(event.dataTransfer?.types || []).includes('Files')
        },
        isReportSettingsJsonFile(file) {
            const fileName = file?.name || ''
            return /^ReportSetting-.+\.json$/i.test(fileName)
        },
        handleWindowDragEnter(event) {
            if (!this.isFileDrag(event)) {
                return
            }
            event.preventDefault()
            this.reportDragCounter += 1
            this.reportDragActive = true
        },
        handleWindowDragOver(event) {
            if (!this.isFileDrag(event)) {
                return
            }
            event.preventDefault()
            event.dataTransfer.dropEffect = 'copy'
            this.reportDragActive = true
        },
        handleWindowDragLeave(event) {
            if (!this.isFileDrag(event)) {
                return
            }
            this.reportDragCounter = Math.max(0, this.reportDragCounter - 1)
            if (!this.reportDragCounter) {
                this.reportDragActive = false
            }
        },
        handleWindowDrop(event) {
            if (!this.isFileDrag(event)) {
                return
            }
            event.preventDefault()
            this.reportDragCounter = 0
            this.reportDragActive = false

            const [file] = event.dataTransfer?.files || []
            if (!this.isReportSettingsJsonFile(file)) {
                return
            }

            this.importReportSettingsFile(file, { fromDrop: true })
        },
        readReportSettingsFile(file) {
            return new Promise((resolve, reject) => {
                const reader = new FileReader()
                reader.onload = () => resolve(reader.result)
                reader.onerror = () => reject(reader.error)
                reader.readAsText(file)
            })
        },
        normalizeImportedReportSettings(parsedSettings) {
            const template = parsedSettings?.kind === REPORT_SETTINGS_EXPORT_KIND
                ? parsedSettings.template
                : parsedSettings

            if (!template?.metadata?.modelName) {
                throw new Error('invalid_report_settings_file')
            }

            return {
                ...template,
                id: null,
                editable: false,
                imported: true,
                is_base: false,
                name: template.name || parsedSettings?.reportName || this.$t('Untitled'),
                description: template.description || '',
                appSectionCode: template.appSectionCode || '',
                base_report: template.base_report || null,
                template: template.template || null,
                complexFilterMode: template.complexFilterMode ?? template.complexFilter ?? template.metadata?.complexFilter ?? false,
                metadata: template.metadata
            }
        },
        async importReportSettingsFile(file, { fromDrop = false } = {}) {
            if (!file) {
                return
            }

            this.importReportLoading = true
            if (fromDrop) {
                this.reportDropLoading = true
            }
            try {
                const fileContent = await this.readReportSettingsFile(file)
                const parsedSettings = JSON.parse(fileContent)
                const templateData = this.normalizeImportedReportSettings(parsedSettings)
                await this.$store.dispatch('reports/openReportModal', templateData)
                this.importReportModalVisible = false
                this.selectedReportSettingsFile = null
            } catch (error) {
                console.error(error)
                this.$message.error(this.$t('Failed to upload report settings'))
            } finally {
                this.importReportLoading = false
                if (fromDrop) {
                    this.reportDropLoading = false
                }
            }
        },
        async importReportSettings() {
            await this.importReportSettingsFile(this.selectedReportSettingsFile)
        }
    },
    beforeDestroy() {
        clearTimeout(this.searchTimer)
        window.removeEventListener('dragenter', this.handleWindowDragEnter, DRAG_LISTENER_OPTIONS)
        window.removeEventListener('dragover', this.handleWindowDragOver, DRAG_LISTENER_OPTIONS)
        window.removeEventListener('dragleave', this.handleWindowDragLeave, DRAG_LISTENER_OPTIONS)
        window.removeEventListener('drop', this.handleWindowDrop, DRAG_LISTENER_OPTIONS)
    }
}
</script>

<style lang="scss" scoped>
.search_input{
    background: #fff;
    width: 100%;
    max-width: 1200px;
    min-width: 300px;
    display: flex;
    align-items: center;
    gap: 2px;
    padding-right: 15px;
    border-radius: var(--borderRadius);
    overflow: hidden;
    .fi-rr-search{
        opacity: 0.6;
    }
    .clear_btn{
        color: #000;
    }
    &::v-deep{
        .ant-input{
            border: 0px;
            width: 100%;
            box-shadow: initial;
            outline: none;
            padding-left: 15px;
            height: 38px;
            font-size: 16px;
            color: #000;
            &::placeholder{
                color: #000;
            }
        }
    }
}

.reports-header-actions {
    display: flex;
    align-items: center;
    gap: 8px;
}

.float_add {
    .ant-btn {
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .fi {
        line-height: 1;
    }
}

.report-import-form {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.report-import-form__label {
    color: #1f1f1f;
    font-weight: 500;
}

.report-import-form__file {
    color: #777777;
    font-size: 13px;
}

.report-import-form__actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
}

@media (max-width: 767px) {
    .report-import-form__actions {
        flex-direction: column;
    }
}

.report-drop-overlay {
    position: fixed;
    inset: 0;
    z-index: 1100;
    display: flex;
    align-items: center;
    justify-content: center;
    pointer-events: none;
    background: rgba(245, 247, 252, 0.72);
    border: 2px dashed var(--blue);
}

.report-drop-overlay__content {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 14px 22px;
    border-radius: 8px;
    background: #ffffff;
    color: var(--blue);
    font-weight: 600;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.12);
}
</style>
