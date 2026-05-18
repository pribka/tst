<template>
    <div 
        class="workg_draw_input ant-input flex items-center relative flex-wrap" 
        :class="size">
        <template v-if="value && value.length">
            <a-tooltip 
                v-for="item in value"
                :key="item.id"
                destroyTooltipOnHide
                :title="item.name" 
                class="mr-1">
                <a-tag 
                    color="blue" 
                    class="tag_block truncate" 
                    @click="open()">
                    <div class="flex items-center truncate">
                        <div class="mr-1">
                            <a-avatar 
                                :size="15" 
                                icon="team" 
                                :key="item.id"
                                :src="workgroupLogoPath(item)" />
                        </div>
                        {{item.name}}
                    </div>
                </a-tag>
            </a-tooltip>
        </template>
        <a-button
            @click="open()"
            type="link"
            size="small"
            :icon="(!value && !value.length) && 'plus'"
            class="px-0 change_btn">
            {{value ? $t('task.change') : $t('task.select')}}
        </a-button>
        <a-button
            v-if="value && value.length"
            @click="clear()"
            type="link"
            flaticon
            icon="fi-rr-cross-small"
            class="px-0 text-current remove_brn" />

        <DrawerTemplate
            :title="driwerTitle"
            :width="windowWidth > 480 ? 480 : windowWidth"
            destroyOnClose
            @close="visible = false"
            v-model="visible">
            <div class="drawer_search mb-2">
                <a-input-search
                    :loading="searchLoading"
                    v-model="search"
                    @input="onSearch"
                    :placeholder="$t('task.project_name')" />
            </div>
            <div class="drawer_body pr_scroll">
                <div class="drawer_scroll">
                    <!--<OldSelected 
                        ref="projectOldSelector"
                        :itemSelect="selectWork"
                        avatarField="workgroup_logo"
                        titleField="name"
                        avatarIcon="team"
                        dbId="project"
                        :getPopupContainer="getPopupContainer" />-->
                    <ul class="bordered-items select-none">
                        <li 
                            class="cursor-pointer item py-3 flex items-center justify-between" 
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
                        rowClass="lg:px-4 py-3"
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
import { errorHandler } from '@/utils/index.js'
let timer = null
export default {
    components: {
        InfiniteLoading: () => import('vue-infinite-loading'),
        Loader: () => import('../Loader.vue'),
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue')
    },
    props: {
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
        selectProject: {
            type: Function,
            default: () => {}
        },
        params: {
            type: [Object, String],
            default: () => null
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
            this.$emit('input', [])
            this.selectProject([])
        },
        selectWork(work) {
            const selectedList = [...this.value]
            const index = selectedList.findIndex(f => f.id === work.id)
            if(index !== -1)
                selectedList.splice(index, 1)
            else
                selectedList.push(work)
            this.$emit('input', selectedList)
            this.selectProject(selectedList)
            //this.$refs.projectOldSelector.saveSelect(work)
            //this.visible = false
        },
        checkSelected(work) {
            const find = this.value.find(f => f.id === work.id)
            return find ? true : false
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
                        is_project: 1,
                        page_name: 'project_drawer',
                        my: 1,
                        moderator: 1,
                    }
                    if(this.params)
                        params = {...params, ...this.params}
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
                } catch(error) {
                    errorHandler({error})
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
    }
}
</script>

<style lang="scss" scoped>
.change_btn{
    height: 22px;
}
</style>

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
        margin-bottom: 3px;
    }
    &.ant-input-lg{
        height: initial;
        min-height: 40px;
    }
}
</style>

