<template>
    <div 
        class="workg_draw_input ant-input flex items-center flex-wrap relative gap-2" 
        :class="size">
        <a-tag 
            v-for="org in value"
            :key="org.id"
            color="blue" 
            class="tag_block truncate"
            @click="open()">
            <div class="flex items-center truncate">
                <div class="mr-1">
                    <a-avatar 
                        :size="15" 
                        icon="team" 
                        :key="org.id"
                        :src="org.logo" />
                </div>
                {{org.name}}
            </div>
        </a-tag>
        <a-button
            @click="open()"
            type="link"
            size="small"
            class="px-0">
            {{value.length ? $t('task.change') : $t('task.select')}}
        </a-button>
        <div class="remove_brn">
            <a-button
                v-if="value.length"
                @click="clear()"
                type="ui"
                ghost
                size="small"
                flaticon
                shape="circle"
                icon="fi-rr-cross-small" />
        </div>

        <DrawerTemplate
            :title="driwerTitle"
            :width="windowWidth > 480 ? 480 : windowWidth"
            destroyOnClose
            @close="visible = false"
            v-model="visible">
            <div class="mb-2">
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
                            class="cursor-pointer item py-3 flex items-center justify-between" 
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
            <template #footer>
                <a-button
                    block
                    type="ui"
                    ghost
                    class="px-8"
                    @click="visible = false">
                    {{$t('task.close')}}
                </a-button>
            </template>
        </DrawerTemplate>
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
        Loader: () => import('./Loader.vue'),
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue')
    },
    props: {
        defaultActiveFirstOption: {
            type: Boolean,
            default: false
        },
        value: {
            type: Array
        },
        title: {
            type: String,
            default: ''
        },
        inputSize: {
            type: String,
            default: 'default'
        },
        pageName: {
            type: String,
            default: 'select_organization_drawer'
        },
        selectProject: {
            type: Function,
            default: () => {}
        }
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
        if(this.defaultActiveFirstOption) {
            const params = {
                page: 1,
                page_size: 1,
                page_name: this.pageName,
                display: 'tree',
            }
            this.$http.get(`/users/my_organizations/`, { params })
                .then(({ data }) => {
                    this.selectWork(data.results[0])
                })
                .catch(error => {
                    console.error(error)
                })
        }
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
            this.$emit('input', [])
            this.selectProject(null)
        },
        selectWork(work) {
            const index = this.value.findIndex(f => f.id === work.id)
            const selected = [...this.value]
            if(index !== -1) {
                selected.splice(index, 1)
            } else {
                selected.push(work)
            }
            this.$emit('input', selected)
            this.selectProject(work)
            if (this.$refs?.projectOldSelector)
                this.$refs.projectOldSelector.saveSelect(work)
        },
        checkSelected(work) {
            if(this.value?.length) {
                const find = this.value.find(f => f.id === work.id)
                return find ? true : false
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
                        display: 'tree',
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
    min-height: 40px;
    height: auto;
    position: relative;
    .remove_brn{
        right: 5px;
        top: 0;
        height: 100%;
        position: absolute;
        display: flex;
        margin-top: 0px;
        align-items: center;
    }
    .tag_block{
        max-width: 300px;
        margin: 0px;
    }
}
</style>
