<template>
    <div 
        class="workg_draw_input ant-input flex items-center relative" 
        :class="size">
        <a-tooltip 
            v-if="value" 
            :title="value.name" 
            destroyTooltipOnHide
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
                            src="" />
                    </div>
                    {{ value.name }}
                </div>
            </a-tag>
        </a-tooltip>
        <a-button
            @click="open()"
            type="link"
            class="px-0">
            {{ $t('task.contractordrawer.choose') }}
        </a-button>
        <a-button
            v-if="value"
            @click="clear()"
            type="link"
            icon="close-circle"
            class="px-0 text-current remove_brn" />
        <a-drawer
            :title="$t('task.contractordrawer.drawerTitle')"
            class="workg_select_driwer"
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
                    :placeholder="$t('task.contractordrawer.searchPlaceholder')" />
            </div>
            <div class="drawer_body pr_scroll">
                <div class="drawer_scroll">
                    <OldSelected 
                        ref="contractorOldSelector"
                        :itemSelect="makeСhoice"
                        avatarField="workgroup_logo"
                        titleField="name"
                        avatarIcon="team"
                        dbId="contractors"
                        :getPopupContainer="getPopupContainer" />
                    <ul class="bordered-items">
                        <li 
                            class="cursor-pointer item px-3 py-3 flex items-center justify-between" 
                            @click="makeСhoice(contractor)" 
                            v-for="(contractor, index) in contractors" 
                            :key="index">
                            <div class="flex items-center justify-between w-full truncate">
                                <div class="flex items-center truncate">
                                    <div>
                                        <a-avatar 
                                            :size="30" 
                                            icon="team"/>
                                    </div>
                                    <div class="pl-2 truncate">
                                        {{ contractor.name }}
                                    </div>
                                </div>
                                <div class="pl-2">
                                    <a-radio :checked="checkSelected(contractor)" />
                                </div>
                            </div>
                        </li>
                    </ul>
                    <Loader
                        class="chat__active-chats"
                        rowClass="px-2 lg:px-4 py-3"
                        v-if="loading && page === 1"
                        :titleFull="true"
                        :hideParagraph="true"
                        :skeletonRow="7" />
                    <infinite-loading ref="userInfinite" @infinite="getContractors" :distance="10">
                        <div slot="spinner"><a-spin v-if="page !== 1" /></div>
                        <div slot="no-more"></div>
                        <div slot="no-results"></div>
                    </infinite-loading>
                </div>
            </div>
        </a-drawer>
    </div>
</template>

<script>
import InfiniteLoading from 'vue-infinite-loading'
let timer = null
export default {
    components: {
        InfiniteLoading,
        OldSelected: () => import('@apps/DrawerSelect/OldSelected.vue'),
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
        selectContractor: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            driwerTitle: this.title ? this.title : this.$t('task.contractordrawer.drawerTitle'),
            search: '',
            visible: false,
            searchLoading: false,
            scrollStatus: true,
            page: 0,
            loading: false,
            contractors: []
        }
    },
    computed: {
        size() {
            if (this.inputSize === 'large') {
                return 'ant-input-lg'
            } else {
                return 'default'
            }
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
                this.contractors = []
                if (this.search.length && this.search.length > 2) {
                    this.getContractors(this.search)
                } else {
                    this.getContractors()
                }
            }, 800)
        },
        clear() {
            this.$emit('input', null)
            this.selectContractor(null)
        },
        makeСhoice(work) {
            this.$emit('input', work)
            this.selectContractor(work)
            this.$refs.contractorOldSelector.saveSelect(work)
            this.visible = false
        },
        checkSelected(contractor) {
            if (this.value) {
                if (contractor.id === this.value.id) {
                    return true
                } else {
                    return false
                }
            } else {
                return false
            }
        },
        open() {
            this.visible = true
        },
        async getContractors($state = null) {
            if (!this.loading && this.scrollStatus && this.visible) {
                try {
                    this.loading = true
                    this.page = this.page + 1
                    let params = {
                        page_size: 15,
                        page: this.page,
                        search: this.search,
                        page_name: 'contractors_drawer'
                    }
                    if (this.search) {
                        this.searchLoading = true
                    }

                    const { data } = await this.$http.get('/contractor/list/', { params })
                    if (data && data.results.length) {
                        this.contractors = this.contractors.concat(data.results)
                    }
                    if (!data.next) {
                        if ($state) {
                            $state.complete()
                        }
                        this.scrollStatus = false
                    } else {
                        if ($state) {
                            $state.loaded()
                        }
                    }
                } catch (e) {

                } finally {
                    if (this.search) {
                        this.searchLoading = false
                    }
                    this.loading = false
                }
            } else {
                if ($state) {
                    $state.complete()
                }
            }
        }
    }
}
</script>

<style lang="scss" scoped>
::v-deep {

    .workg_draw_input{
        .remove_brn{
            right: 0;
            top: 50%;
            position: absolute;
            margin-top: -16px;
        }
    }
    .workg_select_driwer{
        .ant-drawer-content,
        .ant-drawer-wrapper-body{
            overflow: hidden;
        }
        .ant-drawer-body{
            padding: 0px;
            height: calc(100% - 55px);
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
            height: calc(100% - 42px);
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
