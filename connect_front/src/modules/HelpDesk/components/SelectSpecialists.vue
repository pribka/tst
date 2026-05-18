<template>
    <div>
        <a-button 
            v-if="actions && actions.edit"
            type="ui"
            ghost
            shape="circle" 
            v-tippy
            :content="$t('helpdesk.add_specialists')"
            flaticon 
            icon="fi-rr-plus"
            @click="openDrawer()" />
        <DrawerTemplate 
            v-model="visible" 
            destroyOnClose
            @afterVisibleChange="afterVisibleChange"
            @close="visible = false">
            <template #title>
                <div class="drawer_title">
                    {{ $t('helpdesk.add_specialists') }}
                </div>
            </template>
            <a-input-search
                v-model="search"
                size="large"
                class="mb-4"
                @input="onSearch"
                :placeholder="$t('helpdesk.search_by_name')" />
            <div class="user_list">
                <div 
                    v-for="user in list.results" 
                    :key="user.id" 
                    class="user_list__item select-none cursor-pointer"
                    @click="userSelect(user)"> <!--:class="checkShowRadio(user) && 'cursor-pointer'"-->
                    <Profiler
                        :avatarSize="35"
                        hideSupportTag
                        trigger=""
                        :user="user" />
                    <div class="pl-2"> <!--v-if="checkShowRadio(user)"-->
                        <a-radio :checked="checkSelected(user)" />
                    </div>
                </div>
            </div>
            <a-empty v-if="empty" :description="$t('helpdesk.no_data')" />
            <infinite-loading 
                @infinite="getList"
                v-bind:distance="50"
                ref="specialists_infinity">
                <div 
                    slot="spinner"
                    class="flex items-center justify-center inf_spinner mt-3">
                    <a-spin />
                </div>
                <div slot="no-more"></div>
                <div slot="no-results"></div>
            </infinite-loading>
            <template v-if="selectedFilter.length || deleteList.length" #footer>
                <a-button 
                    type="primary" 
                    size="large" 
                    block 
                    :loading="selectLoading"
                    @click="selectedUsers()">
                    {{ $t('helpdesk.select') }}
                </a-button>
            </template>
        </DrawerTemplate>
    </div>
</template>

<script>
let timer;
export default {
    components: {
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue'),
        InfiniteLoading: () => import('vue-infinite-loading')
    },
    props: {
        actions: {
            type: Object,
            default: () => null
        },
        client: {
            type: Object,
            required: true
        },
        getSpecialistsList: {
            type: Function,
            default: () => {}
        },
        specialistsList: {
            type: Array,
            default: () => []
        }
    },
    computed: {
        selectedFilter() {
            const userIdsInList = this.specialistsList.map(s => s.user.id)
            return this.selected.filter(id => !userIdsInList.includes(id))
        }
    },
    data() {
        return {
            visible: false,
            loading: false,
            selectLoading: false,
            page: 0,
            empty: false,
            search: "",
            selected: [],
            deleteList: [],
            list: {
                next: true,
                count: 0,
                results: []
            }
        }
    },
    methods: {
        onSearch() {
            clearTimeout(timer)
            timer = setTimeout(() => {
                this.deleteList = []
                this.selected = [...this.specialistsList.map(user => user.user.id)]
                this.listReload()
            }, 800)
        },
        checkShowRadio(user) {
            const find = this.specialistsList.find(f => f.user.id === user.id)
            return find ? false : true
        },
        checkSelected(user) {
            const find = this.selected.find(f => f === user.id)
            return find ? true : false
        },
        async deleteUsers() {
            if(this.deleteList?.length) {
                try {
                    await this.$http.post(`/help_desk/customer_cards/${this.client.id}/specialists/remove/`, {
                        users: this.deleteList
                    })
                } catch(e) {
                    console.log(e)
                }
            }
        },
        async saveSelected() {
            const userIdsInList = this.specialistsList.map(s => s.user.id)
            const filteredSelected = this.selected.filter(id => !userIdsInList.includes(id))
            if(filteredSelected?.length) {
                try {
                    await this.$http.post(`/help_desk/customer_cards/${this.client.id}/specialists/add/`, {
                        users: filteredSelected.map(user => {
                            return {
                                user,
                                date_ranges: []
                            }
                        })
                    })
                } catch(e) {
                    console.log(e)
                }
            }
        },
        async selectedUsers() {
            try {
                this.selectLoading = true
                await this.saveSelected()
                await this.deleteUsers()
                this.getSpecialistsList()
                this.visible = false
            } catch(e) {
                console.log(e)
            } finally {
                this.selectLoading = false
            }
        },
        userSelect(user) {
            const index = this.selected.findIndex(f => f === user.id)
            if(index !== -1) {
                const find = this.specialistsList.find(f => f.user.id === user.id)
                if(find) {
                    this.deleteList.push(user.id)
                }
                this.selected.splice(index, 1)
            } else {
                const index2 = this.deleteList.find(f => f === user.id)
                if(index2 !== -1)
                    this.deleteList.splice(index2, 1)
                this.selected.push(user.id)
            }
        },
        openDrawer() {
            this.visible = true
        },
        afterVisibleChange(vis) {
            if(!vis) {
                this.deleteList = []
                this.search = ""
                this.selected = []
                this.page = 0
                this.empty = false
                this.list = {
                    next: true,
                    count: 0,
                    results: []
                }
            } else {
                this.selected = [...this.specialistsList.map(user => user.user.id)]
            }
        },
        async getList($state) {
            if(!this.loading && this.list.next) {
                try {
                    this.loading = true
                    this.page += 1
                    const params = {
                        page: this.page,
                        page_size: 12,
                        page_name: this.initPageName,
                        contractor: this.client.org_admin.id
                    }
                    if(this.search.length)
                        params.text = this.search
                    const { data } = await this.$http.get('/contractor_permissions/app_sections/contractors/members/', { params })
                    if(data) {
                        this.list.count = data.count
                        this.list.next = data.next
                    }
                    
                    if(data.results?.length) {
                        this.list.results = this.list.results.concat(data.results)
                    }

                    if(this.page === 1 && !this.list.results.length) {
                        this.empty = true
                    }

                    if (!data.next) {
                        $state.complete()
                    } else {
                        $state.loaded()
                    }
                } catch (error) {
                    console.log(error)
                    this.$message.error(this.$t('helpdesk.error'))
                } finally {
                    this.loading = false
                }
            } else {
                $state.complete()
            }
        },
        listReload() {
            this.page = 0
            this.empty = false
            this.list = {
                next: true,
                count: 0,
                results: []
            }
            this.$nextTick(() => {
                this.$refs['specialists_infinity'].stateChanger.reset()
            })
        }
    }
}
</script>

<style lang="scss" scoped>
.user_list{
    &__item{
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
}
</style>