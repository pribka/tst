<template>
    <div class="ticket-members">
        <div class="ticket-members__header">
            <div class="ticket-members__title-row">
                <div class="ticket-members__title">
                    {{ $t('helpdesk.ticket_members_title') }}
                </div>
                <div class="ticket-members__description">
                    {{ $t('helpdesk.ticket_members_description') }}
                </div>
            </div>

            <a-button
                v-if="canEdit"
                type="link"
                size="small"
                class="ticket-members__add-btn"
                style="padding-left: 0px;padding-right: 0px;"
                icon="fi-rr-plus"
                flaticon
                :loading="loading"
                @click="openSelector">
                {{ $t('helpdesk.ticket_members_add') }}
            </a-button>
        </div>

        <a-spin :spinning="loading" class="w-full" size="small">
            <div
                v-if="normalizedMembers.length"
                class="ticket-members__list">
                <div
                    v-for="member in normalizedMembers"
                    :key="member.id"
                    class="ticket-members__item">
                    <div class="ticket-members__row">
                        <div class="ticket-members__member">
                            <a-avatar
                                :size="32"
                                icon="user"
                                :src="memberAvatar(member)"
                                class="ticket-members__avatar" />
                            <div class="ticket-members__meta">
                                <div class="ticket-members__name">
                                    {{ member.full_name || member.name }}
                                </div>
                                <div
                                    v-if="getMemberSubtitle(member)"
                                    class="ticket-members__subtitle">
                                    {{ getMemberSubtitle(member) }}
                                </div>
                            </div>
                        </div>
                        <a-button
                            v-if="canEdit"
                            type="ui"
                            ghost
                            shape="circle"
                            flaticon
                            icon="fi-rr-trash"
                            class="ticket-members__remove"
                            v-tippy
                            :content="$t('helpdesk.ticket_members_remove')"
                            :loading="memberRemovingId === member.id && loading"
                            @click="$emit('remove', member.id)" />
                    </div>
                </div>
            </div>
            <div v-else class="ticket-members__empty">
                {{ $t('helpdesk.ticket_members_empty') }}
            </div>
        </a-spin>

        <DrawerTemplate
            v-model="selectorVisible"
            destroyOnClose
            :width="selectorWidth"
            :wrapClassName="drawerWrapClass"
            :title="$t('helpdesk.ticket_members_add')"
            @afterVisibleChange="afterVisibleChange"
            @close="selectorVisible = false">
            <a-input-search
                ref="searchInput"
                v-model="search"
                class="mb-4"
                size="large"
                :loading="searchLoading"
                :placeholder="$t('employee_full_name')"
                @input="onSearch" />

            <div class="ticket-members-selector__results">
                <div
                    v-for="user in usersList"
                    :key="user.id"
                    class="ticket-members-selector__item"
                    :class="checkSelected(user) && 'active'">
                    <UserItem
                        :item="user"
                        multiple
                        :checkSelected="checkSelected"
                        :itemSelect="toggleUser" />
                </div>

                <div v-if="page === 1 && listLoading" class="flex justify-center mt-2">
                    <a-spin size="small" />
                </div>

                <a-empty
                    v-if="hasLoadedOnce && !listLoading && !usersList.length"
                    :description="$t('helpdesk.no_data')" />

                <infinite-loading
                    ref="membersInfinite"
                    :identifier="infiniteId"
                    :force-use-infinite-wrapper="infiniteWrapperSelector"
                    :distance="10"
                    @infinite="getUsers">
                    <div slot="spinner">
                        <a-spin v-if="page !== 1" size="small" />
                    </div>
                    <div slot="no-more"></div>
                    <div slot="no-results"></div>
                </infinite-loading>
            </div>

            <template #footer>
                <div class="ticket-members-selector__footer">
                    <a-button
                        type="primary"
                        size="large"
                        :block="isMobile"
                        :disabled="!orgAdminId"
                        :loading="loading"
                        @click="applySelection">
                        {{ selectButtonText }}
                    </a-button>
                    <a-button
                        type="ui_ghost"
                        size="large"
                        :block="isMobile"
                        @click="selectorVisible = false">
                        {{ $t('helpdesk.close') }}
                    </a-button>
                </div>
            </template>
        </DrawerTemplate>
    </div>
</template>

<script>
import axios from 'axios'

let searchTimer = null

export default {
    components: {
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue'),
        InfiniteLoading: () => import('vue-infinite-loading'),
        UserItem: () => import('@/modules/DrawerSelect/UserItem.vue')
    },
    props: {
        members: {
            type: Array,
            default: () => []
        },
        canEdit: {
            type: Boolean,
            default: false
        },
        loading: {
            type: Boolean,
            default: false
        },
        memberRemovingId: {
            type: [String, Number, null],
            default: null
        },
        orgAdminId: {
            type: [String, null],
            default: null
        }
    },
    data() {
        return {
            selectorVisible: false,
            search: '',
            searchLoading: false,
            listLoading: false,
            hasLoadedOnce: false,
            page: 0,
            infiniteId: 0,
            next: true,
            usersList: [],
            draftSelectedIds: [],
            draftMembersMap: {},
            cancelSource: null
        }
    },
    computed: {
        normalizedMembers() {
            return this.normalizeUsersList(this.members)
        },
        draftMembers() {
            return this.draftSelectedIds
                .map(id => this.draftMembersMap[id])
                .filter(member => member?.id)
        },
        selectButtonText() {
            const count = this.draftSelectedIds.length
            if (!count) return this.$t('helpdesk.select')
            return `${this.$t('helpdesk.select')} (${count})`
        },
        selectorWidth() {
            return this.$store.state.isMobile ? this.$store.state.windowWidth : 560
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        drawerWrapClass() {
            return `ticket_members_select_drawer_${this._uid}`
        },
        infiniteWrapperSelector() {
            return `.${this.drawerWrapClass} .drawer_body`
        },
        endpoint() {
            if (!this.orgAdminId) return ''
            return `/users/my_organizations/${this.orgAdminId}/users_short/`
        }
    },
    watch: {
        members: {
            immediate: true,
            handler() {
                if (!this.selectorVisible) {
                    this.syncDraftWithMembers()
                }
            }
        },
        orgAdminId() {
            if (!this.selectorVisible) return
            this.resetList()
        }
    },
    beforeDestroy() {
        if (this.cancelSource) {
            this.cancelSource.cancel()
        }
    },
    methods: {
        openSelector() {
            this.syncDraftWithMembers()
            this.resetList()
            this.selectorVisible = true
        },
        afterVisibleChange(visible) {
            if (!visible) {
                this.search = ''
                this.resetList()
                return
            }

            this.focusSearch()
        },
        focusSearch() {
            this.$nextTick(() => {
                requestAnimationFrame(() => {
                    const el = this.$refs.searchInput?.$refs?.input
                    if (el) el.focus()
                })
            })
        },
        onSearch() {
            clearTimeout(searchTimer)
            searchTimer = setTimeout(() => {
                this.resetList()
            }, 500)
        },
        resetList() {
            if (this.cancelSource) {
                this.cancelSource.cancel()
                this.cancelSource = null
            }

            this.page = 0
            this.next = true
            this.usersList = []
            this.listLoading = false
            this.searchLoading = false
            this.hasLoadedOnce = false
            this.infiniteId += 1
        },
        mergeUsers(current = [], incoming = []) {
            const map = new Map()

            current.forEach(user => {
                if (user?.id) {
                    map.set(user.id, user)
                }
            })

            incoming.forEach(user => {
                if (user?.id && !map.has(user.id)) {
                    map.set(user.id, user)
                }
            })

            return Array.from(map.values())
        },
        normalizeUser(item) {
            const user = item?.user || item?.profile || item || null
            if (!user?.id) return null
            if (!(user?.full_name || user?.name)) return null
            return {
                ...user,
                job_title: user?.job_title || user?.position?.name || user?.position || user?.post?.name || user?.role?.name || ''
            }
        },
        normalizeUsersList(list = []) {
            return list
                .map(item => this.normalizeUser(item))
                .filter(item => item?.id)
                .reduce((acc, item) => {
                    if (!acc.find(user => user.id === item.id)) {
                        acc.push(item)
                    }
                    return acc
                }, [])
        },
        syncDraftWithMembers() {
            const members = this.normalizeUsersList(this.members)
            this.draftSelectedIds = members.map(member => member.id)
            this.draftMembersMap = members.reduce((acc, member) => {
                acc[member.id] = member
                return acc
            }, {})
        },
        checkSelected(user) {
            return this.draftSelectedIds.includes(user.id)
        },
        toggleUser(user) {
            const normalizedUser = this.normalizeUser(user)
            if (!normalizedUser?.id) return

            const index = this.draftSelectedIds.findIndex(id => id === normalizedUser.id)
            if (index !== -1) {
                this.draftSelectedIds.splice(index, 1)
                return
            }

            this.draftSelectedIds.push(normalizedUser.id)
            this.$set(this.draftMembersMap, normalizedUser.id, normalizedUser)
        },
        getMemberSubtitle(member) {
            return member?.position?.name || member?.position || member?.post?.name || member?.role?.name || member?.job_title || ''
        },
        memberAvatar(member) {
            return member?.avatar?.path || member?.image?.path || member?.logo || null
        },
        async getUsers($state = null) {
            if (!this.selectorVisible || !this.endpoint || !this.next || this.listLoading) {
                if ($state && (!this.next || !this.endpoint)) {
                    $state.complete()
                }
                return
            }

            try {
                const source = axios.CancelToken.source()
                this.cancelSource = source
                this.listLoading = true
                this.page += 1

                const params = {
                    page: this.page,
                    page_size: 20,
                    page_name: 'helpdesk_ticket_members_select',
                    display: 'tree'
                }

                if (this.search) {
                    params.search = this.search
                    this.searchLoading = true
                }

                const { data } = await this.$http.get(this.endpoint, {
                    params,
                    cancelToken: source.token
                })

                const nextUsers = this.normalizeUsersList(data?.results || [])
                nextUsers.forEach(user => {
                    if (!this.draftMembersMap[user.id]) {
                        this.$set(this.draftMembersMap, user.id, user)
                    }
                })

                this.usersList = this.mergeUsers(this.usersList, nextUsers)
                this.next = Boolean(data?.next)
                this.hasLoadedOnce = true

                if ($state) {
                    if (this.next) $state.loaded()
                    else $state.complete()
                }
            } catch (error) {
                if (!axios.isCancel(error) && error?.__CANCEL__ !== true) {
                    this.$message.error(this.$t('helpdesk.no_data'))
                }
                if ($state) {
                    $state.complete()
                }
            } finally {
                this.cancelSource = null
                this.searchLoading = false
                this.listLoading = false
            }
        },
        applySelection() {
            const memberIds = this.draftSelectedIds.slice()
            this.$emit('save', memberIds)
            this.selectorVisible = false
        }
    }
}
</script>

<style lang="scss" scoped>
.ticket-members {
    display: flex;
    flex-direction: column;
    gap: 16px;
}
.ticket-members__header {
    display: flex;
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
}
.ticket-members__title-row {
    display: flex;
    flex-direction: column;
    gap: 4px;
    width: 100%;
}
.ticket-members__add-btn {
    align-self: flex-start;
}
.ticket-members__title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 16px;
    font-weight: 500;
    line-height: 1.2;
}
.ticket-members__description {
    color: #888888;
    font-size: 13px;
    line-height: 1.4;
}
.ticket-members__list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}
.ticket-members__item {
    display: flex;
    flex-direction: column;
    gap: 4px;
}
.ticket-members__row {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
}
.ticket-members__member {
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 0;
    flex: 1 1 auto;
}
.ticket-members__avatar {
    flex: 0 0 auto;
}
.ticket-members__meta {
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
}
.ticket-members__remove {
    flex: 0 0 auto;
    opacity: 1;
    transition: opacity 0.2s ease;
    margin-top: 2px;
}
.ticket-members__subtitle {
    color: #888888;
    font-size: 13px;
    line-height: 1.3;
}
.ticket-members__empty {
    color: #888888;
    font-size: 13px;
    line-height: 1.4;
}
.ticket-members-selector__results {
    display: flex;
    flex-direction: column;
    gap: 4px;
}
.ticket-members-selector__item {
    border-radius: 8px;
    transition: background 0.2s ease;
    cursor: pointer;
    &:hover,
    &.active {
        background: #f7f9fc;
    }
}
.ticket-members-selector__footer {
    display: flex;
    justify-content: flex-start;
    gap: 8px;
    width: 100%;
}
@media (max-width: 768px) {
    .ticket-members {
        margin-bottom: 16px;
    }
    .ticket-members__title {
        font-size: 16px;
    }
    .ticket-members-selector__footer {
        width: 100%;
    }
    .ticket-members-selector__footer ::v-deep .ant-btn {
        flex: 1 1 50%;
        max-width: calc(50% - 4px);
    }
}
@media (min-width: 769px) {
    .ticket-members__remove {
        opacity: 0;
        pointer-events: none;
    }
    .ticket-members__item:hover .ticket-members__remove {
        opacity: 1;
        pointer-events: auto;
    }
}
</style>
