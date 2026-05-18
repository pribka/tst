<template>
    <DrawerTemplate
        v-model="visible"
        :title="$t('meeting.reassign_to_project')"
        :wrapClassName="drawerWrapClass"
        destroyOnClose
        width="500px"
        @close="close">
        <div class="drawer_content">
            <a-input-search
                class="mb-3 search_input"
                :loading="searchLoading"
                v-model="search"
                ref="searchInput"
                @input="onSearch"
                :placeholder="$t('task.project_name')" />

            <div v-if="recentList.length" class="mb-3">
                <div class="block_title">{{ $t('old_selected') }}</div>
                <div class="flex items-center gap-1 flex-wrap">
                    <div
                        v-for="item in recentList"
                        :key="item.id"
                        :title="item.name"
                        class="cursor-pointer old_card"
                        @click="selectWork(item)">
                        <div v-if="selectedProject && selectedProject.id === item.id" class="old_active">
                            <i class="fi fi-rr-check" />
                        </div>
                        <a-avatar
                            :size="32"
                            icon="team"
                            :src="workgroupLogoPath(item)" />
                    </div>
                </div>
            </div>

            <div
                v-for="work in workList"
                :key="work.id"
                :title="work.name"
                class="cursor-pointer project_item flex items-center truncate"
                :class="selectedProject && selectedProject.id === work.id && 'project_item--active'"
                @click="selectWork(work)">
                <a-avatar
                    :size="32"
                    icon="team"
                    :src="workgroupLogoPath(work)" />
                <div class="ml-2 truncate project_item__name">{{ work.name }}</div>
                <i v-if="selectedProject && selectedProject.id === work.id" class="fi fi-rr-check ml-auto check_icon" />
            </div>

            <div v-if="page === 1 && loading" class="flex justify-center mt-3">
                <a-spin size="small" />
            </div>

            <div v-if="!loading && !workList.length && search" class="empty_text">
                {{ $t('meeting.noData') }}
            </div>

            <infinite-loading
                ref="infiniteLoader"
                :identifier="infiniteId"
                :force-use-infinite-wrapper="infiniteWrapperSelector"
                @infinite="getWorkList"
                v-bind:distance="10">
                <div slot="spinner"><a-spin v-if="page !== 1" size="small" /></div>
                <div slot="no-more"></div>
                <div slot="no-results"></div>
            </infinite-loading>
        </div>

        <template #footer>
            <div class="flex items-center gap-2 w-full">
                <a-button
                    type="primary"
                    size="large"
                    block
                    :loading="reassignLoading"
                    :disabled="!selectedProject"
                    @click="reassign">
                    {{ $t('meeting.reassign_to_project') }}
                </a-button>
                <a-button
                    type="ui_ghost"
                    size="large"
                    block
                    :disabled="reassignLoading"
                    @click="close">
                    {{ $t('calendar.close') }}
                </a-button>
            </div>
        </template>
    </DrawerTemplate>
</template>

<script>
import axios from 'axios'
import { errorHandler } from '@/utils/index.js'

let searchTimer = null

export default {
    components: {
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue'),
        InfiniteLoading: () => import('vue-infinite-loading')
    },
    props: {
        meeting: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            visible: false,
            search: '',
            searchLoading: false,
            loading: false,
            page: 0,
            infiniteId: 0,
            scrollStatus: true,
            workList: [],
            recentList: [],
            selectedProject: null,
            reassignLoading: false,
            cancelSource: null
        }
    },
    computed: {
        drawerWrapClass() {
            return `reassign_project_drawer_${this._uid}`
        },
        infiniteWrapperSelector() {
            return `.${this.drawerWrapClass} .drawer_body`
        },
        userId() {
            return this.$store.state.user?.user?.id || 'guest'
        },
        recordKey() {
            return `reassign_recent_${this.userId}`
        }
    },
    methods: {
        open() {
            this.selectedProject = null
            this.search = ''
            this.page = 0
            this.workList = []
            this.scrollStatus = true
            this.infiniteId += 1
            this.visible = true
            this.loadRecent()
            this.$nextTick(() => {
                if (this.$refs.searchInput)
                    this.$refs.searchInput.focus()
            })
        },
        close() {
            this.visible = false
        },
        onSearch() {
            clearTimeout(searchTimer)
            searchTimer = setTimeout(() => {
                this.scrollStatus = true
                this.loading = false
                this.page = 0
                this.workList.splice(0)
                if (this.cancelSource) this.cancelSource.cancel()
                setTimeout(() => { this.infiniteId += 1 }, 100)
            }, 700)
        },
        async getWorkList($state = null) {
            if (!this.loading && this.scrollStatus && this.visible) {
                try {
                    const axiosSource = axios.CancelToken.source()
                    this.cancelSource = { cancel: axiosSource.cancel }
                    this.loading = true
                    this.page += 1
                    const params = {
                        page_size: 20,
                        page: this.page,
                        is_project: 1,
                        page_name: 'project_drawer',
                        filters: { is_finished: false }
                    }
                    if (this.search) {
                        params.workgroups_name = this.search
                        this.searchLoading = true
                    }
                    const { data } = await this.$http.get('/work_groups/workgroups/', { params, cancelToken: axiosSource.token })
                    if (data?.results?.length) this.workList.push(...data.results)
                    if (!data.next) {
                        if ($state) $state.complete()
                        this.scrollStatus = false
                    } else {
                        if ($state) $state.loaded()
                    }
                } catch (error) {
                    errorHandler({ error, show: false })
                    if ($state) $state.complete()
                } finally {
                    this.cancelSource = null
                    this.searchLoading = false
                    this.loading = false
                }
            } else {
                if ($state) $state.complete()
            }
        },
        selectWork(work) {
            if (this.selectedProject && this.selectedProject.id === work.id)
                this.selectedProject = null
            else
                this.selectedProject = work
        },
        async reassign() {
            if (!this.selectedProject) return
            try {
                this.reassignLoading = true
                await this.$http.post(`/meetings/sections/${this.meeting.id}/reassign_execution_times/`, {
                    project: this.selectedProject.id
                })
                await this.pushToRecent(this.selectedProject)
                this.$message.success(this.$t('meeting.reassign_to_project_success'))
                this.$emit('reassigned', this.selectedProject)
                this.close()
            } catch (error) {
                errorHandler({ error })
            } finally {
                this.reassignLoading = false
            }
        },
        workgroupLogoPath(workgroup) {
            return workgroup?.workgroup_logo?.path || ''
        },
        async loadRecent() {
            const arr = await this.idbGet(this.recordKey)
            this.recentList = Array.isArray(arr) ? arr : []
        },
        async pushToRecent(work) {
            const base = this.recentList.filter(i => i && i.id !== work.id)
            base.unshift(work)
            const sliced = base.slice(0, 8)
            this.recentList = sliced
            await this.idbSet(this.recordKey, sliced)
        },
        async idbEnsureStore() {
            return await new Promise((resolve, reject) => {
                const req = window.indexedDB.open('old_select')
                req.onsuccess = e => {
                    const db = e.target.result
                    const storeName = 'reassign_projects'
                    const has = Array.from(db.objectStoreNames).includes(storeName)
                    if (has) resolve(db)
                    else {
                        const version = db.version + 1
                        db.close()
                        const req2 = window.indexedDB.open('old_select', version)
                        req2.onupgradeneeded = ev => {
                            const db2 = ev.target.result
                            if (!db2.objectStoreNames.contains(storeName))
                                db2.createObjectStore(storeName, { keyPath: 'id' })
                        }
                        req2.onsuccess = ev => resolve(ev.target.result)
                        req2.onerror = err => reject(err)
                    }
                }
                req.onerror = err => reject(err)
            })
        },
        async idbGet(id) {
            try {
                const db = await this.idbEnsureStore()
                return await new Promise((resolve, reject) => {
                    const tx = db.transaction(['reassign_projects'], 'readonly')
                    const store = tx.objectStore('reassign_projects')
                    const r = store.get(id)
                    r.onsuccess = () => resolve(r.result ? r.result.value : null)
                    r.onerror = e => reject(e)
                })
            } catch (e) {
                return null
            }
        },
        async idbSet(id, value) {
            try {
                const db = await this.idbEnsureStore()
                await new Promise((resolve, reject) => {
                    const tx = db.transaction(['reassign_projects'], 'readwrite')
                    const store = tx.objectStore('reassign_projects')
                    const r = store.put({ id, value })
                    r.onsuccess = () => resolve()
                    r.onerror = e => reject(e)
                })
            } catch (e) {}
        }
    }
}
</script>

<style lang="scss" scoped>
.drawer_content {
    width: 100%;
}
.block_title {
    color: #888888;
    font-size: 12px;
    line-height: 12px;
    margin-bottom: 8px;
}
.old_card {
    position: relative;
    overflow: hidden;
    border-radius: 50%;
    cursor: pointer;
    user-select: none;
    .old_active {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        z-index: 10;
        color: #fff;
        background: rgba(0, 0, 0, 0.5);
    }
}
.project_item {
    padding: 8px 10px;
    border-radius: 8px;
    margin-bottom: 2px;
    transition: background 0.2s;
    &:hover {
        background: #f7f9fc;
    }
    &--active {
        background: #f0f5ff;
        .project_item__name {
            color: var(--blue);
            font-weight: 500;
        }
    }
    .check_icon {
        color: var(--blue);
        font-size: 14px;
        flex-shrink: 0;
    }
}
.empty_text {
    text-align: center;
    color: #888888;
    padding: 20px 0;
}
.search_input {
    &::v-deep {
        .ant-input {
            background: #f7f9fc;
            border-color: #f7f9fc;
            box-shadow: none !important;
            &::placeholder {
                color: #888888;
            }
        }
    }
}
</style>
