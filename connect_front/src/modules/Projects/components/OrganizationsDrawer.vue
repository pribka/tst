<template>
    <div 
        class="workg_draw_input ant-input flex items-center relative" 
        :class="size">
        <a-tooltip 
            v-if="value" 
            :title="value.name" 
            class="mr-2">
            <a-tag 
                color="blue"  
                class="tag_block truncate" 
                @click="open()">
                <div class="flex items-center truncate">
                    <div class="mr-1">
                        <a-avatar 
                            :size="15" 
                            icon="team" 
                            :key="value.id"
                            :src="value.logo" />
                    </div>
                    {{value.name}}
                </div>
            </a-tag>
        </a-tooltip>
        <a-button
            @click="open()"
            type="link"
            :icon="!value && 'plus'"
            class="px-0">
            {{value ? $t('task.change') : $t('task.select')}}
        </a-button>
        <a-button
            v-if="value"
            @click="clear()"
            type="link"
            icon="close-circle"
            class="px-0 text-current remove_brn" />

        <a-drawer
            :title="driwerTitle"
            class="workg_select_driwer"
            :width="windowWidth > 480 ? 380 : windowWidth"
            :destroyOnClose="true"
            :zIndex="1200"
            @close="visible = false"
            :visible="visible">
            <div class="drawer_header overflow-hidden">
                <PageFilter
                    :model="model"
                    :key="pageName"
                    onlySearch
                    size="large"
                    :page_name="pageName"/>
            </div>
            <div class="drawer_body pr_scroll">
                <div class="drawer_scroll">
                    <OldSelected 
                        ref="projectOldSelector"
                        :itemSelect="selectWork"
                        avatarField="logo"
                        avatarFieldAsRootField
                        titleField="name"
                        avatarIcon="team"
                        dbId="organization"
                        :getPopupContainer="getPopupContainer" />
                    <ul class="bordered-items">
                        <li 
                            class="cursor-pointer item px-3 py-3 flex items-center justify-between" 
                            @click="selectWork(organization)" 
                            v-for="(organization, index) in organizationList" 
                            :key="index">
                            <div class="flex items-center justify-between w-full truncate">
                                <div class="flex items-center truncate">
                                    <div>
                                        <a-avatar 
                                            :size="30" 
                                            icon="team" 
                                            :src="organization.logo" />
                                    </div>
                                    <div class="pl-2 truncate">
                                        {{organization.name}}
                                    </div>
                                </div>
                                <div class="pl-2">
                                    <a-radio :checked="checkSelected(organization)" />
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
                    <infinite-loading ref="userInfinite" @infinite="getWorkList" v-bind:distance="10">
                        <div slot="spinner"><a-spin v-if="page !== 1" /></div>
                        <div slot="no-more"></div>
                        <div slot="no-results"></div>
                    </infinite-loading>
                </div>
            </div>
            <div class="drawer_footer flex items-center">
                <a-button
                    block
                    type="ui"
                    ghost
                    class="px-8"
                    @click="visible = false">
                    {{$t('task.close')}}
                </a-button>
            </div>
        </a-drawer>
    </div>
</template>

<script>
import InfiniteLoading from 'vue-infinite-loading'
import eventBus from '@/utils/eventBus'

let timer = null
export default {
    components: {
        InfiniteLoading,
        OldSelected: () => import('@apps/DrawerSelect/OldSelected.vue'),
        PageFilter: () => import('@/components/PageFilter'),
        Loader: () => import('./Loader.vue')
    },
    props: {
        value: {
            type: Object
        },
        title: {
            type: String,
            default: ''
        },
        inputSize: {
            type: String,
            default: 'default'
        },
        selectProject: {
            type: Function,
            default: () => {}
        },
        pageName: {
            type: String,
            default: 'select_organization_drawer'
        },

    },
    data() {
        return {
            driwerTitle: this.title ? this.title : this.$t('task.select_project'),
            search: '',
            visible: false,
            searchLoading: false,
            scrollStatus: true,
            page: 0,
            loading: false,
            organizationList: [],
            model: 'catalogs.ContractorModel'
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
    mounted() {
        eventBus.$on(`update_filter_${this.model}`, () => {
            this.reload()
        })

    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.model}`)
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
                this.organizationList = []
                if(this.search.length && this.search.length > 2) {
                    this.getWorkList(this.search)
                } else {
                    this.getWorkList()
                }
            }, 800)
        },
        clear() {
            this.$emit('input', null)
            this.selectProject(null)
        },
        selectWork(work) {
            this.$emit('input', work)
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
                    const params = {
                        page: this.page,
                        page_size: this.pageSize,
                        page_name: this.pageName,
                        display: 'descendants_director',

                    }
                    if(this.search) {
                        params.workgroups_name = this.search
                        this.searchLoading = true
                    }

                    const { data } = await this.$http.get(`/users/my_organizations/`, { params })
                    if(data && data.results.length)
                        this.organizationList = this.organizationList.concat(data.results)
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
        },
        reload() {
            this.scrollStatus = true
            this.page = 0
            this.organizationList = []
            this.getWorkList()
        }
    }
}
</script>

<style lang="scss">
.workg_draw_input{
    .remove_brn{
        right: 0;
        top: 50%;
        position: absolute;
        margin-top: -16px;
    }
    .tag_block{
        max-width: 300px;
    }
}
.workg_select_driwer{
    .ant-drawer-content,
    .ant-drawer-wrapper-body{
        overflow: hidden;
    }
    .ant-drawer-body{
        padding: 0px;
        height: calc(100% - 40px);
    }
    .drawer_footer{
        border-top: 1px solid var(--borderColor);
        height: 40px;
        padding-left: 15px;
        padding-right: 15px;
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
        height: calc(100% - 83px);
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
</style>
