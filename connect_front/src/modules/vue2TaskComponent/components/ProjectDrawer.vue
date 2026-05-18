<template>
    <div 
        class="workg_draw_input ant-input flex items-center relative" 
        :class="size">
        <a-tooltip 
            v-if="value" 
            destroyTooltipOnHide
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
                            :src="workgroupLogoPath(value)" />
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

        <DrawerTemplate
            :title="driwerTitle"
            :width="windowWidth > 480 ? 450 : windowWidth"
            :destroyOnClose="true"
            @close="visible = false"
            v-model="visible">
            <template>
                <a-input-search
                    class="mb-4"
                    :loading="searchLoading"
                    v-model="search"
                    @input="onSearch"
                    :placeholder="$t('task.project_name')" />
                <OldSelected
                    class="mb-4"
                    ref="projectOldSelector"
                    :itemSelect="selectWork"
                    avatarField="workgroup_logo"
                    titleField="name"
                    avatarIcon="team"
                    dbId="project"
                    :getPopupContainer="getPopupContainer" />
                <ul class="bordered-items">
                    <li 
                        v-for="(work, index) in workList" 
                        :key="index"
                        v-tippy="{ inertia : true, duration : '[600,300]'}"
                        :content="work.name"
                        class="cursor-pointer item px-3 py-3 flex items-center justify-between" 
                        @click="selectWork(work)" >
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
                                    <!-- {{ work.date_start_plan }} -->
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
                <infinite-loading ref="userInfinite" @infinite="getWorkList" v-bind:distance="10">
                    <div slot="spinner"><a-spin v-if="page !== 1" /></div>
                    <div slot="no-more"></div>
                    <div slot="no-results"></div>
                </infinite-loading>
            </template>
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
let timer = null
export default {
    components: {
        InfiniteLoading,
        OldSelected: () => import('@apps/DrawerSelect/OldSelected.vue'),
        Loader: () => import('./Loader.vue'),
        DrawerTemplate: () => import("@/components/DrawerTemplate.vue")
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
                this.workList.splice(0)
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
                    let params = {
                        page_size: 15,
                        page: this.page,
                        is_project: 1,
                        page_name: 'project_drawer',
                        filters: {"is_finished": false}
                    }
                    if(this.search) {
                        params.workgroups_name = this.search
                        this.searchLoading = true
                    }

                    const { data } = await this.$http.get('/work_groups/workgroups/', { params })
                    if(data?.results?.length)
                        this.workList.push(...data.results)
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
    }
}
</script>

<style lang="scss" scoped>
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

::v-deep  {
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
</style>
