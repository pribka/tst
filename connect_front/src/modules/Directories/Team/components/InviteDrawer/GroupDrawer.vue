<template>
    <a-drawer
        :title="driwerTitle"
        class="sgroup_drawer"
        :width="windowWidth > 380 ? 380 : windowWidth"
        :destroyOnClose="true"
        :zIndex="1200"
        @close="visible = false"
        :visible="visible">
        <div class="drawer_header">
            <a-input-search
                :loading="searchLoading"
                v-model="search"
                @input="onSearch"
                :placeholder="$t('team.team_name_placeholder')" />
        </div>
        <div class="drawer_body pr_scroll">
            <div class="drawer_scroll">
                <OldSelected 
                    ref="projectOldSelector"
                    :itemSelect="selectWork"
                    avatarField="workgroup_logo"
                    titleField="name"
                    avatarIcon="team"
                    dbId="project"
                    :getPopupContainer="getPopupContainer" />
                <ul class="bordered-items">
                    <li 
                        class="cursor-pointer item px-3 py-3 flex items-center justify-between" 
                        @click="selectWork(work)" 
                        v-for="(work, index) in workList" 
                        :key="index">
                        <div class="flex items-center justify-between w-full truncate">
                            <div class="flex items-center truncate">
                                <div>
                                    <a-avatar 
                                        :size="30" 
                                        icon="team" 
                                        :src="workgroupLogoPath(work)" />
                                </div>
                                <div class="pl-2 truncate">
                                    {{work.name}}
                                </div>
                            </div>
                            <div class="pl-2">
                                <a-radio :checked="checkSelected(work)" />
                            </div>
                        </div>
                    </li>
                </ul>
                <Loader
                    class="chat__active-chats"
                    rowClass="px-2 lg:px-4 py-3"
                    v-if="loading && page === 1"
                    titleFull
                    hideParagraph
                    :skeletonRow="7" />
                <infinite-loading 
                    ref="userInfinite" 
                    @infinite="getWorkList" 
                    :distance="10">
                    <div slot="spinner"><a-spin v-if="page !== 1" /></div>
                    <div slot="no-more"></div>
                    <div slot="no-results"></div>
                </infinite-loading>
            </div>
        </div>
    </a-drawer>
</template>

<script>
let timer = null
export default {
    components: {
        InfiniteLoading: () => import('vue-infinite-loading'),
        OldSelected: () => import('@apps/DrawerSelect/OldSelected.vue'),
        Loader: () => import('./Loader.vue')
    },
    props: {
        value: {
            type: Object
        },
        inputSize: {
            type: String,
            default: 'default'
        },
        selectProject: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            driwerTitle: this.$t('team.select_team'),
            search: '',
            visible: false,
            searchLoading: false,
            scrollStatus: true,
            page: 0,
            loading: false,
            workList: []
        }
    },
    computed: {
        size() {
            if(this.inputSize === 'large')
                return 'ant-input-lg'
            else
                return 'default'
        },
        windowWidth() {
            return this.$store.state.windowWidth
        }
    },
    methods: {
        getPopupContainer() {
            return document.querySelector('.pr_scroll')
        },
        onSearch() {
            clearTimeout(timer)
            timer = setTimeout(() => {
                this.scrollStatus = true
                this.page = 0
                this.workList = []
                if(this.search.length && this.search.length > 2) {
                    this.getWorkList(this.search)
                } else {
                    this.getWorkList()
                }
            }, 800)
        },
        clear() {
            //this.$emit('input', null)
            this.selectProject(null)
        },
        selectWork(work) {
            //this.$emit('input', work)
            this.selectProject(work)
            this.$refs.projectOldSelector.saveSelect(work)
            this.visible = false
        },
        checkSelected(work) {
            if(this.value) {
                if(work.id === this.value.id)
                    return true
                else
                    return false
            } else
                return false
        },
        open() {
            this.visible = true
        },
        async getWorkList($state = null) {
            if(!this.loading && this.scrollStatus && this.visible) {
                try {
                    this.loading = true
                    this.page = this.page+1
                    let params = {
                        page_size: 15,
                        page: this.page,
                        is_project: 0,
                        page_name: 'workgroup_drawer'
                    }
                    if(this.search) {
                        params.workgroups_name = this.search
                        this.searchLoading = true
                    }

                    const { data } = await this.$http.get('/work_groups/workgroups/', { params })
                    if(data && data.results.length)
                        this.workList = this.workList.concat(data.results)
                    if(!data.next) {
                        if($state)
                            $state.complete()
                        this.scrollStatus = false
                    } else {
                        if($state)
                            $state.loaded()
                    }
                } catch(e) {

                } finally {
                    if(this.search)
                        this.searchLoading = false
                    this.loading = false
                }
            } else {
                if($state)
                    $state.complete()
            }
        },
        workgroupLogoPath(workgroup) {
            return workgroup?.workgroup_logo?.path || ''
        }
    }
}
</script>

<style lang="scss" scoped>
.sgroup_drawer{
    &::v-deep{
        .ant-drawer-content,
        .ant-drawer-wrapper-body{
            overflow: hidden;
        }
        .ant-drawer-body{
            padding: 0px;
            height: calc(100% - 40px);
        }
        .drawer_header{
            border-bottom: 1px solid var(--borderColor);
            input{
                border-radius: 0px;
                height: 42px;
                border: 0px;
            }
        }
        .drawer_body{
            height: calc(100% - 43px);
            .drawer_scroll{
                height: 100%;
                overflow-y: auto;
                overflow-x: hidden;
                .item{
                    &:not(:last-child){
                        border-bottom: 1px solid var(--borderColor);
                    }
                    &:hover{
                        background: var(--hoverBg);
                    }
                    .name{
                        display: -webkit-box;
                        -webkit-line-clamp: 2;
                        -webkit-box-orient: vertical;
                        overflow: hidden;
                        text-overflow: ellipsis;
                    }
                }
            }
        }
    }
}
</style>