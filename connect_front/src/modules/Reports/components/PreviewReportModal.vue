<template>
    <a-modal
        ref="previewReportModal"
        v-model="visible"
        wrapClassName="fullscreen-modal"
        :footer="null"
        :getContainer="getContainer"
        @cancel="hideModal">
        <template slot="title">
            <div class="flex justify-between items-center">
                <div>{{ modalTitle }}</div>
                <div class="flex items-center" v-if="false">
                    <a-button type="link" @click="0">{{ $t('How it works?') }}</a-button>
                </div>
            </div>
        </template>

        <div class="flex items-center gap-1 mb-2">
            <a-button
                flaticon
                v-tippy
                type="ui"
                :loading="loading"
                :content="$t('report_data_update')"
                icon="fi-rr-refresh"
                @click="reportReload" />
            <template v-if="hasGroups">
                <a-button
                    flaticon
                    v-tippy
                    type="ui"
                    :content="$t('report_expand_all')"
                    icon="fi-rr-arrow-circle-down"
                    @click="expandAllGroups" />
                <a-button
                    flaticon
                    v-tippy
                    type="ui"
                    :content="$t('report_collapse_all')"
                    icon="fi-rr-arrow-circle-up"
                    @click="collapseAllGroups" />
                <a-button
                    v-for="level in outlineLevels"
                    :key="`outline_${level}`"
                    flaticon
                    v-tippy
                    type="ui"
                    :content="$t('report_level', { level: String(level) })"
                    :class="currentOutlineLevel === level && 'active_outline_btn'"
                    @click="setOutlineLevel(level)">
                    {{ level }}
                </a-button>
            </template>
        </div>

        <div class="html-content mb-6 flex-grow overflow-y-auto">
            <div
                ref="HTMLTable"
                v-html="HTMLTable" />
        </div>

        <div class="flex items-center">
            <a-button
                @click="downloadExcel"
                :loading="downloadLoading"
                type="primary"
                class="mr-1">
                {{ $t('Download Excel') }}
            </a-button>
            <a-button
                type="primary"
                ghost
                class="mr-1"
                @click="hideModal">
                {{ $t('Edit report') }}
            </a-button>
        </div>
    </a-modal>
</template>

<script>
import { errorHandler } from '@/utils/index.js'

export default {
    props: {
        getContainer: {
            type: Function,
            default: () => document.body
        }
    },
    computed: {
        activeTemplate() {
            return this.$store.state.reports.activeTemplate
        },
        modelName() {
            return this.activeTemplate.metadata.modelName
        }
    },
    data() {
        return {
            visible: false,
            HTMLTable: '',
            downloadLoading: false,
            modalTitle: '',
            loading: false,
            openedGroups: new Set(),
            hasGroups: false,
            linkClickHandler: null,
            outlineLevels: [],
            currentOutlineLevel: 1
        }
    },
    methods: {
        getIndentFromRow(row) {
            const className = row && row.className ? String(row.className) : ''
            const match = className.match(/indent-(\d+)/)
            if (!match) return null
            const n = Number(match[1])
            return Number.isFinite(n) ? n : null
        },
        getMaxIndentInTable() {
            const root = this.$refs.HTMLTable
            if (!root) return 0

            const hasToggle = !!root.querySelector('.group-toggle')
            const hasChild = !!root.querySelector('.group-child')
            if (!hasToggle || !hasChild) return 0

            const rows = root.querySelectorAll('tr')
            let maxIndent = 0

            rows.forEach(row => {
                const indent = this.getIndentFromRow(row)
                if (indent === null) return
                if (indent > maxIndent) maxIndent = indent
            })

            return maxIndent
        },
        updateOutlineLevels() {
            const maxIndent = this.getMaxIndentInTable()

            if (!maxIndent) {
                this.outlineLevels = []
                this.currentOutlineLevel = 1
                return
            }

            this.outlineLevels = Array.from({ length: maxIndent + 1 }, (_, i) => i + 1)

            if (!this.outlineLevels.includes(this.currentOutlineLevel)) {
                this.currentOutlineLevel = 1
            }
        },
        syncIconsAndOpenedGroups() {
            const root = this.$refs.HTMLTable
            if (!root) return

            this.openedGroups.clear()

            const toggles = root.querySelectorAll('.group-toggle')

            toggles.forEach(toggle => {
                const groupId = this.getGroupIdFromToggleRow(toggle)
                if (!groupId) return

                const children = root.querySelectorAll(`.group-child-of-${groupId}`)
                const icon = root.querySelector(`#icon-${groupId}`)

                const isOpen = children.length && getComputedStyle(children[0]).display !== 'none'
                if (isOpen) this.openedGroups.add(groupId)

                if (icon) icon.textContent = isOpen ? '−' : '+'
            })
        },
        setOutlineLevel(level) {
            const root = this.$refs.HTMLTable
            if (!root) return

            this.currentOutlineLevel = level

            const maxAllowedIndent = level - 1
            const rows = root.querySelectorAll('tr')

            rows.forEach(row => {
                const indent = this.getIndentFromRow(row)
                if (indent === null) return
                row.style.display = indent <= maxAllowedIndent ? 'table-row' : 'none'
            })

            this.syncIconsAndOpenedGroups()
        },
        getGroupIdFromToggleRow(row) {
            const className = row && row.className ? String(row.className) : ''
            const match = className.match(/group-id-(data_g\d+_\d+)/)
            return match ? match[1] : null
        },
        getAllGroupIds() {
            const root = this.$refs.HTMLTable
            if (!root) return []
            const toggles = root.querySelectorAll('.group-toggle')
            const ids = []
            toggles.forEach(t => {
                const id = this.getGroupIdFromToggleRow(t)
                if (id) ids.push(id)
            })
            return ids
        },
        updateHasGroups() {
            const root = this.$refs.HTMLTable
            if (!root) {
                this.hasGroups = false
                return
            }
            const hasToggle = !!root.querySelector('.group-toggle')
            const hasChild = !!root.querySelector('.group-child')
            this.hasGroups = Boolean(hasToggle && hasChild)
        },
        openGroupSilently(groupId) {
            const root = this.$refs.HTMLTable
            if (!root) return

            const rows = root.querySelectorAll(`.group-child-of-${groupId}`)
            const icon = root.querySelector(`#icon-${groupId}`)

            rows.forEach(row => {
                row.style.display = 'table-row'
            })

            if (icon) icon.textContent = '−'
        },
        restoreOpenedGroups() {
            if (!this.openedGroups.size) return
            this.openedGroups.forEach(groupId => {
                this.openGroupSilently(groupId)
            })
        },
        captureOpenedGroups() {
            const root = this.$refs.HTMLTable
            if (!root) return

            this.openedGroups.clear()

            const toggles = root.querySelectorAll('.group-toggle')

            toggles.forEach(toggle => {
                const groupId = this.getGroupIdFromToggleRow(toggle)
                if (!groupId) return

                const children = root.querySelectorAll(`.group-child-of-${groupId}`)
                if (children.length && getComputedStyle(children[0]).display !== 'none') {
                    this.openedGroups.add(groupId)
                }
            })
        },
        expandAllGroups() {
            const root = this.$refs.HTMLTable
            if (!root) return

            const allChildren = root.querySelectorAll('.group-child')
            allChildren.forEach(row => {
                row.style.display = 'table-row'
            })

            const ids = this.getAllGroupIds()
            ids.forEach(groupId => {
                const icon = root.querySelector(`#icon-${groupId}`)
                if (icon) icon.textContent = '−'
                this.openedGroups.add(groupId)
            })

            if (this.outlineLevels.length) this.currentOutlineLevel = this.outlineLevels[this.outlineLevels.length - 1]
        },
        collapseAllGroups() {
            const root = this.$refs.HTMLTable
            if (!root) return

            const allChildren = root.querySelectorAll('.group-child')
            allChildren.forEach(row => {
                row.style.display = 'none'
            })

            const ids = this.getAllGroupIds()
            ids.forEach(groupId => {
                const icon = root.querySelector(`#icon-${groupId}`)
                if (icon) icon.textContent = '+'
            })

            this.openedGroups.clear()

            if (this.outlineLevels.length) this.currentOutlineLevel = 1
        },
        reportReload() {
            this.captureOpenedGroups()
            const url = `reports/${this.modelName}/list_post/`

            const payload = this.$store.getters['reports/reportParams']()
            this.loading = true

            this.$http.post(url, payload)
                .then(({ data }) => {
                    const root = this.$refs.HTMLTable
                    if (root && this.linkClickHandler) {
                        root.removeEventListener('click', this.linkClickHandler)
                        this.linkClickHandler = null
                    }
                    this.showModalWithHTML(data)
                })
                .catch(error => {
                    errorHandler({ error })
                })
                .finally(() => {
                    this.loading = false
                })
        },
        showModalWithHTML(HTMLTable) {
            this.visible = true
            this.HTMLTable = HTMLTable

            this.$nextTick(() => {
                this.initTitle()
                this.initTableScripts()
                this.initLinkRouting()
                this.updateHasGroups()
                this.updateOutlineLevels()
                if (this.outlineLevels.length) this.setOutlineLevel(this.currentOutlineLevel)
                this.restoreOpenedGroups()
            })
        },
        initLinkRouting() {
            const root = this.$refs.HTMLTable
            if (!root) return

            if (this.linkClickHandler) {
                root.removeEventListener('click', this.linkClickHandler)
            }

            this.linkClickHandler = (e) => {
                const a = e.target.closest('a')
                if (!a || !root.contains(a)) return

                const href = a.getAttribute('href')
                if (!href) return

                let taskUid = null
                let ticketViewUid = null
                let viewProjectUid = null
                let sprintUid = null

                try {
                    const url = new URL(href, window.location.origin)
                    taskUid = url.searchParams.get('task')
                    ticketViewUid = url.searchParams.get('ticketView')
                    viewProjectUid = url.searchParams.get('viewProject')
                    sprintUid = url.searchParams.get('sprint')
                } catch (_) {

                }

                if (!taskUid && !ticketViewUid && !viewProjectUid && !sprintUid) return

                e.preventDefault()
                e.stopPropagation()

                const query = {
                    ...this.$route.query
                }

                if (taskUid) {
                    query.task = taskUid
                }

                if (ticketViewUid) {
                    query.ticketView = ticketViewUid
                }

                if (viewProjectUid) {
                    query.viewProject = viewProjectUid
                }

                if (sprintUid) {
                    query.sprint = sprintUid
                }

                this.$router.push({ query })
            }

            root.addEventListener('click', this.linkClickHandler)
        },
        initTitle() {
            const reportTitle = this.$refs.HTMLTable?.querySelector('h1')
            this.modalTitle = reportTitle?.textContent || ''
        },
        initTableScripts() {
            const root = this.$refs.HTMLTable
            if (!root) return

            const toggleNodes = root.querySelectorAll('[onclick]')

            toggleNodes.forEach(toggle => {
                const onclickValue = toggle.getAttribute('onclick')
                const match = onclickValue && onclickValue.match(/toggleGroup\('(.+?)'\)/)
                if (!match) return

                const groupId = match[1]

                toggle.removeAttribute('onclick')
                toggle.onclick = null

                toggle.addEventListener('click', (e) => {
                    e.preventDefault()
                    e.stopPropagation()
                    this.toggleGroup(groupId)
                })
            })
        },
        toggleGroup(groupId) {
            const root = this.$refs.HTMLTable
            if (!root) return

            const rows = root.querySelectorAll(`.group-child-of-${groupId}`)
            const icon = root.querySelector(`#icon-${groupId}`)
            const isHidden = rows.length && getComputedStyle(rows[0]).display === 'none'

            if (isHidden) {
                rows.forEach(row => {
                    row.style.display = 'table-row'
                })
                if (icon) icon.textContent = '−'
                this.openedGroups.add(groupId)
            } else {
                this.hideDescendants(groupId)
                if (icon) icon.textContent = '+'
                this.openedGroups.delete(groupId)
            }

            if (this.outlineLevels.length) {
                this.currentOutlineLevel = this.detectCurrentOutlineLevel()
            }
        },
        detectCurrentOutlineLevel() {
            const root = this.$refs.HTMLTable
            if (!root) return 1

            const rows = root.querySelectorAll('tr')
            let maxVisibleIndent = 0
            let found = false

            rows.forEach(row => {
                const indent = this.getIndentFromRow(row)
                if (indent === null) return
                if (getComputedStyle(row).display === 'none') return
                found = true
                if (indent > maxVisibleIndent) maxVisibleIndent = indent
            })

            if (!found) return 1
            return maxVisibleIndent + 1
        },
        hideDescendants(groupId) {
            const root = this.$refs.HTMLTable
            if (!root) return

            const descendants = root.querySelectorAll(`.group-child-of-${groupId}`)
            descendants.forEach(row => {
                row.style.display = 'none'

                const match = String(row.className || '').match(/group-id-(data_g\d+_\d+)/)
                if (match) {
                    const childGroupId = match[1]
                    this.openedGroups.delete(childGroupId)
                    this.hideDescendants(childGroupId)
                    const icon = root.querySelector(`#icon-${childGroupId}`)
                    if (icon) icon.textContent = '+'
                }
            })
        },
        hideModal() {
            const root = this.$refs.HTMLTable
            if (root && this.linkClickHandler) {
                root.removeEventListener('click', this.linkClickHandler)
                this.linkClickHandler = null
            }
            this.openedGroups.clear()
            this.hasGroups = false
            this.outlineLevels = []
            this.currentOutlineLevel = 1
            this.visible = false
            this.HTMLTable = ''
        },
        downloadExcel() {
            const url = `reports/${this.modelName}/list_post/`

            this.downloadLoading = true

            const payload = this.$store.getters['reports/reportParams'](false)
            this.$http.post(url, payload, { responseType: 'blob' })
                .then(response => {
                    this.downloadFile(response)
                })
                .catch(error => {
                    errorHandler({ error })
                })
                .finally(() => {
                    this.downloadLoading = false
                })
        },
        downloadFile(response) {
            const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })

            const link = document.createElement('a')
            link.href = window.URL.createObjectURL(blob)
            link.download = `${this.$t('Report - ')}${this.modalTitle}.xlsx`
            link.click()

            window.URL.revokeObjectURL(link.href)
        }
    }
}
</script>

<style lang="scss" scoped>
:deep {
    .html-content {
        font-size: 12px;
        color: #2d2d2d;

        .creation-date {
            margin-bottom: 12px;
            color: #888888;
            font-weight: 400;

            strong {
                font-weight: 400;
            }
        }

        h1 {
            display: none;
        }

        h2 {
            margin-bottom: 8px;
            font-size: 14px;
        }

        .table-wrapper {
            overflow: auto;
            border-radius: 16px;
        }

        .table-wrapper + * {
            margin-top: 16px;
        }

        table {
            width: 100%;
        }

        thead {
            position: sticky;
            top: 0;
        }

        th {
            padding: 12px;
            background-color: #F0F1F7;
            text-align: left;
            font-weight: 400;
        }

        td, .grand-totals td {
            padding: 14px 12px;
            background-color: #F8F9FD;
            text-align: left;
            max-width: 300px;

            @media (max-width: 768px) {
                max-width: 180px;
            }
        }

        .group-toggle {
            font-weight: 400;
        }

        tr + tr {
            border-top: 1px solid #d9d9d9;
        }
    }

    .fullscreen-modal.ant-modal-wrap {
        padding-top: 15px;
    }

    .fullscreen-modal .ant-modal {
        width: calc(100% - 30px) !important;
        max-width: 100% !important;
        top: 0;
        margin: 0 auto;
        padding: 0;
        height: 100%;
    }

    .fullscreen-modal .ant-modal-content {
        display: flex;
        flex-direction: column;
        height: calc(100% - 15px);
    }

    .fullscreen-modal .ant-modal-body {
        flex-grow: 1;
        display: flex;
        flex-direction: column;
        min-height: 0;
        padding-bottom: 24px;
    }

    .active_outline_btn {
        box-shadow: inset 0 0 0 1px rgba(24, 144, 255, 0.6);
    }
}
</style>
