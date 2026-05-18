<template>
    <div>
        <a-modal
            :visible="visible"
            :width="modalWidth"
            destroyOnClose
            :dialog-style="modalDialogStyle"
            :wrapClassName="modalWrapClass"
            @cancel="visible = false"
            @afterVisibleChange="afterVisibleChange">
            <template #title>
                <div class="fire_employee_modal__title">
                    <div class="fire_employee_modal__heading">{{ $t('team.fire_employee_title') }}</div>
                    <div
                        v-if="employee"
                        class="fire_employee_modal__employee">
                        <Profiler
                            :user="employee"
                            hideSupportTag
                            :avatarSize="28" />
                    </div>
                </div>
            </template>

            <a-spin :spinning="loading">
                <div
                    v-if="missingBlockingLabels.length"
                    class="fire_employee_modal__warning">
                    <div class="fire_employee_modal__warning_title">
                        {{ $t('team.fire_employee_warning_title') }}
                    </div>
                    <ul class="fire_employee_modal__warning_list">
                        <li
                            v-for="item in missingBlockingLabels"
                            :key="item">
                            {{ item }}
                        </li>
                    </ul>
                    <a-button
                        type="flat_danger"
                        class="fire_employee_modal__warning_btn"
                        :block="isMobile"
                        @click="openGlobalBulkTransferModal">
                        {{ $t('team.fire_employee_bulk_replace') }}
                    </a-button>
                </div>

                <a-tabs
                    v-model="activeTab"
                    :showBar="hasNonBlockingRelations">
                    <a-tab-pane :key="'blocking'" :tab="`${$t('team.fire_employee_blocking_relations')} (${blockingCount})`">
                        <template v-if="blockingSections.length">
                            <div
                                v-for="section in blockingSections"
                                :key="section.key"
                                class="fire_employee_modal__section">
                                <div class="fire_employee_modal__section_header">
                                    <div class="fire_employee_modal__section_heading_row">
                                        <div class="fire_employee_modal__section_title">
                                            {{ section.title }} ({{ section.items.length }})
                                        </div>
                                        <a-button
                                            v-if="canSelectSectionItems(section)"
                                            type="link"
                                            class="fire_employee_modal__section_action_btn fire_employee_modal__section_action_btn--select"
                                            @click="toggleSectionSelection(section)">
                                            {{ isSectionFullySelected(section) ? $t('deselect_all') : $t('select_all') }}
                                        </a-button>
                                        <transition name="fire_employee_modal__bulk_transfer">
                                            <a-button
                                                v-if="!isMobile && canSelectSectionItems(section) && selectedItemsCount(section.key) >= 2"
                                                type="primary"
                                                class="fire_employee_modal__section_bulk_btn"
                                                @click="openBulkTransferModal(section)">
                                                {{ $t('team.fire_employee_transfer') }}
                                            </a-button>
                                        </transition>
                                    </div>
                                    <div class="fire_employee_modal__section_actions">
                                        <transition name="fire_employee_modal__bulk_transfer">
                                            <a-button
                                                v-if="isMobile && canSelectSectionItems(section) && selectedItemsCount(section.key) >= 2"
                                                type="primary"
                                                class="fire_employee_modal__section_bulk_btn"
                                                :block="isMobile"
                                                @click="openBulkTransferModal(section)">
                                                {{ $t('team.fire_employee_transfer') }}
                                            </a-button>
                                        </transition>
                                    </div>
                                </div>

                                <div
                                    v-for="item in section.items"
                                    :key="item.assignmentKey"
                                    class="fire_employee_modal__item">
                                    <div class="fire_employee_modal__item_content">
                                        <div class="fire_employee_modal__item_name">
                                            <button
                                                v-if="canOpenRelation(item)"
                                                type="button"
                                                class="fire_employee_modal__item_link fire_employee_modal__item_link--with-avatar"
                                                @click="openRelation(item)">
                                                <a-avatar
                                                    v-if="showRelationAvatar(item)"
                                                    :size="28"
                                                    class="fire_employee_modal__item_avatar"
                                                    icon="fi-rr-users-alt"
                                                    flaticon
                                                    :src="getRelationAvatar(item)" />
                                                <span>{{ item.title }}</span>
                                            </button>
                                            <template v-else>
                                                {{ item.title }}
                                            </template>
                                        </div>
                                        <div
                                            v-if="getAssignment(section.key, item)"
                                            class="fire_employee_modal__item_assignee">
                                            {{ $t('team.fire_employee_assigned_to') }}: {{ getAssignment(section.key, item).full_name }}
                                        </div>
                                    </div>
                                    <div
                                        v-if="canSelectSectionItems(section)"
                                        class="fire_employee_modal__item_actions">
                                        <a-button
                                            :type="getAssignment(section.key, item) ? 'green' : 'flat_primary'"
                                            @click="openTransferModal(section, item)">
                                            {{ getAssignment(section.key, item) ? $t('team.change') : $t('team.fire_employee_transfer') }}
                                        </a-button>
                                        <a-checkbox
                                            :checked="isItemSelected(section.key, item.assignmentKey)"
                                            @change="toggleItemSelection(section.key, item.assignmentKey, $event.target.checked)" />
                                    </div>
                                    <a-button
                                        v-else
                                        :type="getAssignment(section.key, item) ? 'green' : 'flat_primary'"
                                        @click="openTransferModal(section, item)">
                                        {{ getAssignment(section.key, item) ? $t('team.change') : $t('team.fire_employee_transfer') }}
                                    </a-button>
                                </div>
                            </div>
                        </template>
                        <a-empty
                            v-else
                            :description="$t('team.fire_employee_no_blocking_relations')" />
                    </a-tab-pane>

                    <a-tab-pane :key="'non_blocking'" :tab="`${$t('team.fire_employee_non_blocking_relations')} (${nonBlockingCount})`">
                        <template v-if="nonBlockingSections.length">
                            <a-alert
                                class="fire_employee_modal__info_alert"
                                :description="$t('team.fire_employee_non_blocking_alert')"
                                :message="$t('team.fire_employee_non_blocking_alert_title')"
                                type="info"
                                show-icon />
                            <div
                                v-for="section in nonBlockingSections"
                                :key="section.key"
                                class="fire_employee_modal__section">
                                <div class="fire_employee_modal__section_header">
                                    <div class="fire_employee_modal__section_title">
                                        {{ section.title }} ({{ section.items.length }})
                                    </div>
                                </div>
                                <div
                                    v-for="item in section.items"
                                    :key="item.id"
                                    class="fire_employee_modal__item fire_employee_modal__item--info">
                                    <div class="fire_employee_modal__item_name">
                                        <button
                                            v-if="canOpenRelation(item)"
                                            type="button"
                                            class="fire_employee_modal__item_link fire_employee_modal__item_link--with-avatar"
                                            @click="openRelation(item)">
                                            <a-avatar
                                                v-if="showRelationAvatar(item)"
                                                :size="28"
                                                class="fire_employee_modal__item_avatar"
                                                icon="fi-rr-users-alt"
                                                flaticon
                                                :src="getRelationAvatar(item)" />
                                            <span>{{ item.title }}</span>
                                        </button>
                                        <template v-else>
                                            {{ item.title }}
                                        </template>
                                    </div>
                                </div>
                            </div>
                        </template>
                        <a-empty
                            v-else
                            :description="$t('team.fire_employee_no_non_blocking_relations')" />
                    </a-tab-pane>
                </a-tabs>
            </a-spin>

            <template #footer>
                <div class="flex items-center gap-2 w-full justify-end">
                    <a-button
                        type="ui"
                        ghost
                        :block="isMobile"
                        size="large"
                        @click="visible = false">
                        {{ $t('team.cancel') }}
                    </a-button>
                    <a-button
                        type="flat_danger"
                        size="large"
                        :block="isMobile"
                        :disabled="isSubmitDisabled"
                        :loading="submitLoading"
                        @click="openConfirmModal">
                        <span class="px-6">{{ $t('team.fire_employee_fire_action') }}</span>
                    </a-button>
                </div>
            </template>
        </a-modal>

        <a-modal
            :visible="confirmVisible"
            :width="isMobile ? 'calc(100% - 32px)' : 480"
            :footer="null"
            centered
            destroyOnClose
            wrapClassName="fire_employee_confirm_modal"
            @cancel="closeConfirmModal">
            <div class="fire_employee_confirm_modal__body">
                <video
                    v-if="confirmAnimationWebmSrc || confirmAnimationMovSrc"
                    class="fire_employee_confirm_modal__anim"
                    autoplay
                    loop
                    muted
                    playsinline>
                    <source
                        v-if="confirmAnimationWebmSrc"
                        :src="confirmAnimationWebmSrc"
                        type="video/webm" />
                    <source
                        v-if="confirmAnimationMovSrc"
                        :src="confirmAnimationMovSrc"
                        type="video/quicktime" />
                </video>
                <div class="fire_employee_confirm_modal__title">
                    {{ $t('team.fire_employee_confirm_title') }}
                </div>
                <div class="fire_employee_confirm_modal__text">
                    {{ $t('team.fire_employee_confirm_description') }}
                </div>

                <div class="fire_employee_confirm_modal__actions">
                    <a-button
                        type="flat_danger"
                        size="large"
                        block
                        :loading="submitLoading"
                        @click="submit">
                        {{ $t('team.fire_employee_confirm_action') }}
                    </a-button>
                    <a-button
                        type="ui"
                        ghost
                        size="large"
                        block
                        :disabled="submitLoading"
                        @click="closeConfirmModal">
                        {{ $t('team.cancel') }}
                    </a-button>
                </div>
            </div>
        </a-modal>

        <FireEmployeeTransferModal
            ref="transferModal"
            @submit="saveTransfer" />
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
import eventBus from '@/utils/eventBus'

const createBlockingRelations = () => ({
    director: false,
    admin: false,
    projects: [],
    workgroups: [],
    chats: [],
    tasks: [],
    tickets: []
})

const createAssignments = () => ({
    director: null,
    admin: null,
    projects: {},
    workgroups: {},
    chats: {},
    tasks: {},
    tickets: {}
})

export default {
    components: {
        FireEmployeeTransferModal: () => import('./FireEmployeeTransferModal.vue')
    },
    props: {
        org: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            visible: false,
            confirmVisible: false,
            loading: false,
            submitLoading: false,
            employee: null,
            activeTab: 'blocking',
            confirmAnimationWebmSrc: '',
            confirmAnimationMovSrc: '',
            blockingRelations: createBlockingRelations(),
            nonBlockingRelations: {
                projects: [],
                workgroups: [],
                tasks: [],
                tickets: []
            },
            assignments: createAssignments(),
            selectedBlockingItems: {}
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        modalWidth() {
            return this.isMobile ? '100%' : 860
        },
        modalDialogStyle() {
            return this.isMobile
                ? { top: '0', paddingBottom: '0', margin: '0 auto', maxWidth: '100vw' }
                : { top: '20px' }
        },
        modalWrapClass() {
            return this.isMobile ? 'fire_employee_modal fire_employee_modal--mobile' : 'fire_employee_modal'
        },
        blockingSections() {
            if (!this.employee?.id) return []

            const sections = []

            if (this.blockingRelations.director) {
                sections.push({
                    key: 'director',
                    title: this.$t('team.fire_employee_organization_director'),
                    statusText: this.$t('team.fire_employee_transfer_required'),
                    hasUnresolved: !this.assignments.director,
                    items: [{
                        entityType: null,
                        rawItem: null,
                        assignmentKey: 'director',
                        payloadKey: 'director',
                        title: this.$t('team.fire_employee_organization_director')
                    }]
                })
            }

            if (this.blockingRelations.admin) {
                sections.push({
                    key: 'admin',
                    title: this.$t('team.fire_employee_organization_admin'),
                    statusText: this.$t('team.fire_employee_transfer_required'),
                    hasUnresolved: !this.assignments.admin,
                    items: [{
                        entityType: null,
                        rawItem: null,
                        assignmentKey: 'admin',
                        payloadKey: 'admin',
                        title: this.$t('team.fire_employee_organization_admin')
                    }]
                })
            }

            const projectSections = [
                { key: 'projects', title: this.$t('team.projects'), payloadKey: 'founder' },
                { key: 'workgroups', title: this.$t('team.fire_employee_workgroups'), payloadKey: 'founder' },
                { key: 'chats', title: this.$t('team.fire_employee_chats'), payloadKey: 'user' },
                { key: 'tickets', title: this.$t('team.fire_employee_tickets'), payloadKey: 'specialist' }
            ]

            projectSections.forEach(section => {
                const items = (this.blockingRelations[section.key] || []).map(item => ({
                    id: item.id,
                    entityType: section.key === 'projects'
                        ? 'project'
                        : section.key === 'workgroups'
                            ? 'workgroup'
                            : section.key === 'tickets'
                                ? 'ticket'
                                : null,
                    rawItem: item,
                    assignmentKey: item.id,
                    payloadKey: section.payloadKey,
                    title: this.getRelationItemTitle(section.key, item)
                }))

                if (items.length) {
                    sections.push({
                        key: section.key,
                        title: section.title,
                        statusText: this.$t('team.fire_employee_transfer_required'),
                        hasUnresolved: items.some(item => !this.getAssignment(section.key, item)),
                        items
                    })
                }
            })

            const taskItems = []
            ;(this.blockingRelations.tasks || []).forEach(task => {
                if (task.owner?.id === this.employee.id) {
                    taskItems.push({
                        id: task.id,
                        entityType: 'task',
                        rawItem: task,
                        assignmentKey: `${task.id}:owner`,
                        payloadKey: 'owner',
                        title: `${this.getRelationItemTitle('tasks', task)} · ${this.$t('team.fire_employee_task_owner')}`
                    })
                }

                if (task.operator?.id === this.employee.id) {
                    taskItems.push({
                        id: task.id,
                        entityType: 'task',
                        rawItem: task,
                        assignmentKey: `${task.id}:operator`,
                        payloadKey: 'operator',
                        title: `${this.getRelationItemTitle('tasks', task)} · ${this.$t('team.fire_employee_task_operator')}`
                    })
                }
            })

            if (taskItems.length) {
                sections.push({
                    key: 'tasks',
                    title: this.$t('team.fire_employee_tasks'),
                    statusText: this.$t('team.fire_employee_transfer_required'),
                    hasUnresolved: taskItems.some(item => !this.getAssignment('tasks', item)),
                    items: taskItems
                })
            }

            return sections
        },
        nonBlockingSections() {
            const config = [
                { key: 'projects', title: this.$t('team.projects') },
                { key: 'workgroups', title: this.$t('team.fire_employee_workgroups') },
                { key: 'tasks', title: this.$t('team.fire_employee_tasks') },
                { key: 'tickets', title: this.$t('team.fire_employee_tickets') }
            ]

            return config
                .map(section => ({
                    ...section,
                    items: (this.nonBlockingRelations[section.key] || []).map(item => ({
                        id: item.id,
                        entityType: section.key === 'projects'
                            ? 'project'
                            : section.key === 'workgroups'
                                ? 'workgroup'
                                : section.key === 'tasks'
                                    ? 'task'
                                    : 'ticket',
                        rawItem: item,
                        title: this.getRelationItemTitle(section.key, item)
                    }))
                }))
                .filter(section => section.items.length)
        },
        blockingCount() {
            return this.blockingSections.reduce((total, section) => total + section.items.length, 0)
        },
        nonBlockingCount() {
            return this.nonBlockingSections.reduce((total, section) => total + section.items.length, 0)
        },
        hasNonBlockingRelations() {
            return this.nonBlockingCount > 0
        },
        hasBlockingRelations() {
            return this.blockingCount > 0
        },
        missingBlockingLabels() {
            return this.blockingSections
                .filter(section => section.hasUnresolved)
                .map(section => section.title.toLowerCase())
        },
        isSubmitDisabled() {
            return this.loading || this.submitLoading || this.blockingSections.some(section => section.hasUnresolved)
        }
    },
    mounted() {
        this.loadConfirmAnimation()
    },
    methods: {
        async loadConfirmAnimation() {
            try {
                const animationModule = await import('@/assets/animate/connection_error.webm')
                this.confirmAnimationWebmSrc = animationModule?.default || animationModule || ''
            } catch (error) {
                this.confirmAnimationWebmSrc = ''
            }

            this.confirmAnimationMovSrc = `${process.env.BASE_URL}animate/connection_error.mov`
        },
        open(employee) {
            this.loading = true
            this.employee = employee
            this.visible = true
        },
        resetState() {
            this.loading = false
            this.submitLoading = false
            this.confirmVisible = false
            this.employee = null
            this.activeTab = 'blocking'
            this.blockingRelations = createBlockingRelations()
            this.nonBlockingRelations = {
                projects: [],
                workgroups: [],
                tasks: [],
                tickets: []
            }
            this.assignments = createAssignments()
            this.selectedBlockingItems = {}
        },
        getRelationItemTitle(type, item) {
            if (type === 'tasks') {
                const number = item.counter ? `#${item.counter}` : ''
                return [number, item.name].filter(Boolean).join(' ')
            }

            if (type === 'tickets') {
                const number = item.number ? `#${item.number}` : ''
                return [number, item.name].filter(Boolean).join(' ') || `${this.$t('team.fire_employee_ticket_fallback')} ${number}`
            }

            return item.name || item.title || item.id
        },
        getAssignment(sectionKey, item) {
            if (sectionKey === 'director' || sectionKey === 'admin') {
                return this.assignments[sectionKey]
            }

            return this.assignments[sectionKey]?.[item.assignmentKey] || null
        },
        canOpenRelation(item) {
            return ['project', 'workgroup', 'task', 'ticket'].includes(item?.entityType)
        },
        showRelationAvatar(item) {
            return ['project', 'workgroup'].includes(item?.entityType)
        },
        getRelationAvatar(item) {
            const logo = item?.rawItem?.workgroup_logo
            if (!logo) return null
            return typeof logo === 'string' ? logo : logo.path || null
        },
        async openRelation(item) {
            if (!this.canOpenRelation(item)) return

            const query = { ...this.$route.query }

            if (item.entityType === 'project') {
                await this.$router.push({
                    query: {
                        ...query,
                        viewProject: item.rawItem.id
                    }
                })
                return
            }

            if (item.entityType === 'workgroup') {
                await this.$router.push({
                    query: {
                        ...query,
                        viewGroup: item.rawItem.id
                    }
                })
                return
            }

            if (item.entityType === 'task') {
                delete query.task

                if (this.$route.query.task) {
                    await this.$router.push({ query })
                }

                await this.$router.push({
                    query: {
                        ...query,
                        task: item.rawItem.id
                    }
                })
                return
            }

            if (query.ticketView) {
                eventBus.$emit('ticket_drawer_close')
                delete query.ticketView
                await this.$router.push({ query })
                await new Promise(resolve => setTimeout(resolve, 500))
            }

            await this.$router.push({
                query: {
                    ...query,
                    ticketView: item.rawItem.id
                }
            })
        },
        openTransferModal(section, item) {
            this.$refs.transferModal.open({
                sectionKey: section.key,
                assignmentKey: item.assignmentKey,
                payloadKey: item.payloadKey,
                title: item.title,
                entityLabel: this.getTransferEntityLabel(section.key, item),
                selectedUser: this.getAssignment(section.key, item),
                organizationId: this.org.id,
                excludedUserIds: [this.employee.id]
            })
        },
        openBulkTransferModal(section) {
            const selectedItems = section.items.filter(item => this.isItemSelected(section.key, item.assignmentKey))
            if (!selectedItems.length) return

            this.$refs.transferModal.open({
                isBulk: true,
                sectionKey: section.key,
                items: selectedItems.map(item => ({
                    sectionKey: section.key,
                    assignmentKey: item.assignmentKey,
                    payloadKey: item.payloadKey
                })),
                title: section.title,
                entityLabel: this.getTransferEntityLabel(section.key, selectedItems[0]),
                organizationId: this.org.id,
                excludedUserIds: [this.employee.id]
            })
        },
        openGlobalBulkTransferModal() {
            const items = this.blockingSections.reduce((result, section) => {
                section.items.forEach(item => {
                    result.push({
                        sectionKey: section.key,
                        assignmentKey: item.assignmentKey,
                        payloadKey: item.payloadKey
                    })
                })

                return result
            }, [])

            if (!items.length) return

            this.$refs.transferModal.open({
                isBulk: true,
                sectionKey: 'all',
                items,
                title: this.$t('team.fire_employee_bulk_replace'),
                organizationId: this.org.id,
                excludedUserIds: [this.employee.id]
            })
        },
        canSelectSectionItems(section) {
            return this.activeTab === 'blocking' && section.items.length > 1
        },
        selectedItemsCount(sectionKey) {
            return Object.keys(this.selectedBlockingItems[sectionKey] || {}).filter(key => this.selectedBlockingItems[sectionKey][key]).length
        },
        isItemSelected(sectionKey, assignmentKey) {
            return Boolean(this.selectedBlockingItems[sectionKey]?.[assignmentKey])
        },
        isSectionFullySelected(section) {
            return section.items.length > 0 && section.items.every(item => this.isItemSelected(section.key, item.assignmentKey))
        },
        toggleSectionSelection(section) {
            const shouldSelectAll = !this.isSectionFullySelected(section)
            const sectionSelection = {}

            section.items.forEach(item => {
                sectionSelection[item.assignmentKey] = shouldSelectAll
            })

            this.selectedBlockingItems = {
                ...this.selectedBlockingItems,
                [section.key]: sectionSelection
            }
        },
        toggleItemSelection(sectionKey, assignmentKey, checked) {
            this.selectedBlockingItems = {
                ...this.selectedBlockingItems,
                [sectionKey]: {
                    ...(this.selectedBlockingItems[sectionKey] || {}),
                    [assignmentKey]: checked
                }
            }
        },
        getTransferEntityLabel(sectionKey, item) {
            if (sectionKey === 'projects') return this.$t('team.project_1').toLowerCase()
            if (sectionKey === 'workgroups') return this.$t('team.team').toLowerCase()
            if (sectionKey === 'tasks') return this.$t('team.fire_employee_task_item').toLowerCase()
            if (sectionKey === 'tickets') return this.$t('team.fire_employee_ticket_item').toLowerCase()
            if (sectionKey === 'chats') return this.$t('team.fire_employee_chat_item').toLowerCase()
            if (sectionKey === 'director') return this.$t('team.fire_employee_organization_director').toLowerCase()
            if (sectionKey === 'admin') return this.$t('team.fire_employee_organization_admin').toLowerCase()

            return item?.title || ''
        },
        saveTransfer({ sectionKey, assignmentKey, selectedUser, items }) {
            if (Array.isArray(items) && items.length) {
                const nextAssignments = { ...this.assignments }

                items.forEach(item => {
                    if (item.sectionKey === 'director' || item.sectionKey === 'admin') {
                        nextAssignments[item.sectionKey] = selectedUser
                        return
                    }

                    nextAssignments[item.sectionKey] = {
                        ...(nextAssignments[item.sectionKey] || {}),
                        [item.assignmentKey]: selectedUser
                    }
                })

                this.assignments = nextAssignments

                if (sectionKey === 'all') {
                    this.selectedBlockingItems = {}
                }

                return
            }

            if (Array.isArray(assignmentKey)) {
                const nextAssignments = { ...(this.assignments[sectionKey] || {}) }

                assignmentKey.forEach(key => {
                    nextAssignments[key] = selectedUser
                })

                this.assignments = {
                    ...this.assignments,
                    [sectionKey]: nextAssignments
                }
                return
            }

            if (sectionKey === 'director' || sectionKey === 'admin') {
                this.assignments = {
                    ...this.assignments,
                    [sectionKey]: selectedUser
                }
                return
            }

            this.assignments = {
                ...this.assignments,
                [sectionKey]: {
                    ...this.assignments[sectionKey],
                    [assignmentKey]: selectedUser
                }
            }
        },
        buildPayload() {
            const payload = {
                organization: this.org.id,
                user: this.employee.id
            }

            if (this.blockingRelations.director && this.assignments.director?.id) {
                payload.director = this.assignments.director.id
            }

            if (this.blockingRelations.admin && this.assignments.admin?.id) {
                payload.admin = this.assignments.admin.id
            }

            const mapCollection = (sectionKey, payloadIdKey, userKey) => {
                const relations = this.blockingRelations[sectionKey] || []
                if (!relations.length) return

                payload[sectionKey] = relations
                    .map(item => {
                        const assignedUser = this.assignments[sectionKey]?.[item.id]
                        if (!assignedUser?.id) return null

                        return {
                            [payloadIdKey]: item.id,
                            [userKey]: assignedUser.id
                        }
                    })
                    .filter(Boolean)
            }

            mapCollection('projects', 'project', 'founder')
            mapCollection('workgroups', 'workgroup', 'founder')
            mapCollection('chats', 'chat', 'user')
            mapCollection('tickets', 'ticket', 'specialist')

            if (this.blockingRelations.tasks?.length) {
                payload.tasks = []

                this.blockingRelations.tasks.forEach(task => {
                    const taskPayload = { task: task.id }
                    const owner = this.assignments.tasks?.[`${task.id}:owner`]
                    const operator = this.assignments.tasks?.[`${task.id}:operator`]

                    if (owner?.id) {
                        taskPayload.owner = owner.id
                    }

                    if (operator?.id) {
                        taskPayload.operator = operator.id
                    }

                    if (taskPayload.owner || taskPayload.operator) {
                        payload.tasks.push(taskPayload)
                    }
                })
            }

            return payload
        },
        async loadRelations() {
            if (!this.employee?.id || !this.org?.id) return

            try {
                this.loading = true
                const [blockingResponse, nonBlockingResponse] = await Promise.all([
                    this.$http.get('/users/my_organizations/fire/blocking_relations/', {
                        params: {
                            organization: this.org.id,
                            user: this.employee.id
                        }
                    }),
                    this.$http.get('/users/my_organizations/fire/non_blocking_relations/', {
                        params: {
                            organization: this.org.id,
                            user: this.employee.id
                        }
                    })
                ])

                this.blockingRelations = {
                    ...createBlockingRelations(),
                    ...(blockingResponse?.data?.blocking_relations || {})
                }
                this.nonBlockingRelations = {
                    projects: [],
                    workgroups: [],
                    tasks: [],
                    tickets: [],
                    ...(nonBlockingResponse?.data?.non_blocking_relations || {})
                }
            } catch (error) {
                errorHandler({ error })
                this.visible = false
            } finally {
                this.loading = false
            }
        },
        openConfirmModal() {
            if (this.isSubmitDisabled) return
            this.confirmVisible = true
        },
        closeConfirmModal() {
            if (this.submitLoading) return
            this.confirmVisible = false
        },
        async submit() {
            if (this.isSubmitDisabled) return

            try {
                this.submitLoading = true
                await this.$http.post('/users/my_organizations/fire/', this.buildPayload())
                eventBus.$emit('update_filter_catalogs.ContractorModel')
                eventBus.$emit('update_filter_catalogs.ContractorModel_catalogs.ContractorModel_list')
                this.$message.success(this.$t('team.fire_employee_success'))
                this.$emit('success', this.employee)
                this.confirmVisible = false
                this.visible = false
            } catch (error) {
                errorHandler({ error })
            } finally {
                this.submitLoading = false
            }
        },
        afterVisibleChange(vis) {
            if (vis) {
                this.loadRelations()
            } else {
                this.resetState()
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.fire_employee_modal {
    &__title {
        display: flex;
        flex-direction: column;
    }

    &__heading {
        font-size: 18px;
        font-weight: 600;
        line-height: 1;
        margin-bottom: 5px;
    }

    &__employee {
        margin-top: 4px;
    }

    &__warning {
        background: #fff4f4;
        border-radius: var(--borderRadius);
        margin-bottom: 16px;
        padding: 16px 20px;
    }

    &__warning_title {
        color: #d43838;
        font-weight: 600;
        margin-bottom: 8px;
    }

    &__warning_list {
        color: #d43838;
        list-style: disc;
        margin: 0;
        padding-left: 18px;

        li {
            display: list-item;
            list-style: disc;
        }
    }

    &__warning_btn {
        margin-top: 16px;
    }

    &__section {
        margin-bottom: 20px;
    }

    &__info_alert {
        margin-bottom: 16px;
    }

    &__section_header {
        align-items: center;
        display: flex;
        gap: 12px;
        justify-content: space-between;
        margin-bottom: 10px;
    }

    &__section_heading_row {
        align-items: center;
        display: flex;
        flex: 1 1 auto;
        gap: 12px;
        justify-content: space-between;
        min-width: 0;
    }

    &__section_title {
        flex: 1 1 auto;
        font-size: 15px;
        font-weight: 600;
        min-width: 0;
    }

    &__section_actions {
        align-items: center;
        display: flex;
        flex: 0 0 auto;
        flex-wrap: wrap;
        gap: 10px;
        justify-content: flex-end;
        margin-left: auto;
    }

    &__section_action_btn {
        height: auto;
        padding: 0;
    }

    &__section_action_btn--select {
        flex-shrink: 0;
    }

    &__section_bulk_btn {
        margin-left: 0;
    }

    &__item {
        align-items: center;
        background: #f7f8fb;
        border: 1px solid var(--border1);
        border-radius: var(--borderRadius);
        display: flex;
        justify-content: space-between;
        padding: 14px 16px;

        &:not(:last-child) {
            margin-bottom: 10px;
        }
    }

    &__item--info {
        justify-content: flex-start;
    }

    &__item_content {
        flex: 1 1 auto;
        min-width: 0;
        padding-right: 16px;
    }

    &__item_actions {
        align-items: center;
        display: flex;
        flex-shrink: 0;
        gap: 12px;
    }

    &__item_name {
        color: var(--text);
        font-weight: 600;
        word-break: break-word;
    }

    &__item_link {
        background: transparent;
        border: 0;
        color: var(--blue);
        cursor: pointer;
        display: inline-block;
        font: inherit;
        max-width: 100%;
        overflow-wrap: anywhere;
        padding: 0;
        text-align: left;
        word-break: break-word;

        &:hover {
            text-decoration: underline;
        }
    }

    &__item_link--with-avatar {
        align-items: center;
        display: inline-flex;
        gap: 10px;
        max-width: 100%;
    }

    &__item_avatar {
        flex-shrink: 0;
    }

    &__item ::v-deep .ant-btn {
        flex-shrink: 0;
    }

    &__item ::v-deep .ant-checkbox-wrapper,
    &__item ::v-deep .ant-checkbox {
        flex-shrink: 0;
    }

    &__item_assignee {
        color: var(--gray);
        font-size: 12px;
        margin-top: 4px;
    }

    &__bulk_transfer-enter-active,
    &__bulk_transfer-leave-active {
        transition: opacity .2s ease, transform .2s ease;
    }

    &__bulk_transfer-enter,
    &__bulk_transfer-leave-to {
        opacity: 0;
        transform: translateX(16px);
    }
}
</style>

<style lang="scss">
.fire_employee_confirm_modal {
    &__body {
        padding: 24px 24px 20px;
        text-align: center;
    }

    &__anim {
        display: block;
        height: 88px;
        margin: 0 auto 14px;
        object-fit: contain;
        width: 88px;
    }

    &__title {
        color: #0f172a;
        font-size: 24px;
        font-weight: 700;
        line-height: 1.2;
        margin-bottom: 10px;
    }

    &__text {
        color: #667085;
        font-size: 15px;
        font-weight: 500;
        line-height: 1.45;
        margin: 0 auto;
        max-width: 360px;
        white-space: pre-line;
    }

    &__actions {
        margin: 20px -24px -20px;
        padding: 16px 24px 20px;
    }

    .ant-btn + .ant-btn {
        margin-top: 12px;
    }
}

@media (max-width: 768px) {
    .fire_employee_confirm_modal {
        .ant-modal {
            margin: 16px auto;
            max-width: calc(100vw - 32px);
        }

        &__body {
            padding: 20px 16px 16px;
        }

        &__anim {
            height: 72px;
            margin-bottom: 12px;
            width: 72px;
        }

        &__title {
            font-size: 20px;
            margin-bottom: 8px;
        }

        &__text {
            font-size: 14px;
            max-width: 100%;
        }

        &__actions {
            margin: 16px -16px -16px;
            padding: 14px 16px 16px;
        }
    }
}

</style>

<style lang="scss">
.fire_employee_modal--mobile {
    .ant-modal {
        height: 100vh;
        margin: 0;
        max-width: 100vw;
        padding-bottom: 0;
        top: 0;
    }

    .ant-modal-content {
        border-radius: 0;
        display: flex;
        flex-direction: column;
        height: 100vh;
    }

    .ant-modal-body {
        flex: 1 1 auto;
        overflow-y: auto;
    }

    .fire_employee_modal__section_header {
        align-items: stretch;
        flex-direction: column;
        gap: 8px;
    }

    .fire_employee_modal__section_actions {
        justify-content: flex-start;
        width: 100%;
    }

    .fire_employee_modal__section_title {
        padding-right: 8px;
    }

    .fire_employee_modal__section_bulk_btn {
        margin-left: 0;
        width: 100%;
    }
}
</style>
