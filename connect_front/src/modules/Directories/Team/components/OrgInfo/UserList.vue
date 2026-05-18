<template>
    <div>
        <a-input-search
            :placeholder="$t('team.search')"
            v-model="searchText"
            allowClear
            size="large"
            class="mb-4"
            @change="search"/>
        <div 
            v-if="empty && !loading" 
            class="mt-5">
            <a-empty :description="$t('team.no_data')" />
        </div>
        <UserCard 
            v-for="item in users.results" 
            :key="item.id" 
            :deleteUser="deleteUser"
            :fireEmployee="openFireEmployeeModal"
            :leaveOrg="leaveOrg"
            :actions="actions"
            :org="org"
            :item="item" />
        <infinite-loading 
            ref="org_user_infinity"
            @infinite="getList"
            :identifier="infiniteId"
            v-bind:distance="10">
            <div 
                slot="spinner"
                class="flex items-center justify-center inf_spinner">
                <a-spin />
            </div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>

        <FireEmployeeModal
            ref="fireEmployeeModal"
            :org="org"
            @success="handleEmployeeFired" />
    </div>
</template>

<script>
import InfiniteLoading from 'vue-infinite-loading'
import UserCard from './UserCard.vue'
import debounce from '@/utils/lodash/debounce'

import eventBus from '@/utils/eventBus'
export default {
    components: {
        InfiniteLoading,
        UserCard,
        FireEmployeeModal: () => import('./FireEmployeeModal.vue')
    },
    props: {
        org: {
            type: Object,
            required: true
        },
        minusUserCount: {
            type: Function,
            default: () => {}
        },
        updateTableRowsHeight: {
            type: Function,
            default: () => {}
        },
        actions: {
            type: Object,
            default: () => null
        },
        closeDrawer: {
            type: Function,
            default: () => {}
        },
        reloadMainList: {
            type: Function,
            default: () => {}
        },
        page_name: {
            type: String,
            default:'orgInfoDrawer'
        }
    },
    data() {
        return {
            loading: false,
            page: 0,
            empty: false,
            infiniteId: 'org_users_list',
            isScrolling: false,
            model: 'catalogs.ContractorModel',
            searchText: '',

            users: {
                results: [],
                next: true,
                count: 0
            }
        }
    },
    mounted() {
        eventBus.$on(`update_filter_${this.model}` ,()=> {
            this.reloadList()
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.model}`)
    },
    methods: {

        search: debounce(async function() {
            if(this.searchText.length > 1) {
                try {
                    this.reloadList()
                    // await this.getList()
                } catch(e) {

                } finally {
                    setTimeout(() => {
                        this.loading = false
                    }, 1000)
                }
                
            } else{ 
                // await this.getList()
                this.reloadList()

            }
        },500),
        reloadList() {
            this.$nextTick(() => {
                this.page = 0
                this.empty = false
                this.users = {
                    results: [],
                    next: true,
                    count: 0
                }
                this.$refs['org_user_infinity'].stateChanger.reset()
            })
        },
        leaveOrg() {
            this.$confirm({
                title: this.$t('team.confirm_leave_organization'),
                okText: this.$t('team.leave'),
                okType: 'danger',
                closable: true,
                maskClosable: true,
                cancelText: this.$t('team.cancel'),
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post(`/users/my_organizations/${this.org.id}/leave/`)
                            .then(() => {
                                this.$message.info(this.$t('team.successfully_left_organization'))
                                this.reloadMainList()
                                this.closeDrawer()
                                resolve(true)
                            })
                            .catch((error) => { 
                                this.$message.error(this.$t('team.error'))
                                reject(error)
                            })
                    })
                }
            })
        },
        openFireEmployeeModal(record) {
            this.$refs.fireEmployeeModal.open(record)
        },
        handleEmployeeFired() {
            this.minusUserCount(this.org)
            this.reloadList()
        },
        deleteUser(record) {
            this.$confirm({
                title: this.$t('team.confirm_remove_user_from_access_group'),
                okText: this.$t('team.remove'),
                okType: 'danger',
                closable: true,
                maskClosable: true,
                cancelText: this.$t('team.cancel'),
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post(`/users/my_organizations/${this.org.id}/users/delete/`, {
                            id: record.id
                        })
                            .then(() => {
                                this.$message.info(this.$t('team.user_excluded_from_organization'))
                                this.minusUserCount(this.org)
                                this.reloadList()
                                resolve(true)
                            })
                            .catch((error) => { 
                                this.$message.error(this.$t('team.deletion_error'))
                                reject(error)
                            })
                    })
                }
            })
        },
        async getList($state) {
            if(!this.loading && this.users.next) {
                try {
                    this.loading = true
                    this.page += 1
                    const { data } = await this.$http.get(`/users/my_organizations/${this.org.id}/users/`, {
                        params: {
                            page: this.page,
                            page_size: 15,
                            page_name: this.page_name,
                            text: this.searchText

                        }
                    })

                    if(data) {
                        this.users.count = data.count
                        this.users.next = data.next
                    }

                    if(data?.results?.length)
                        this.users.results = this.users.results.concat(data.results)

                    if(this.page === 1 && !this.users.results.length) {
                        this.empty = true
                    }
                        
                    if(this.users.next)
                        $state.loaded()
                    else
                        $state.complete()
                } catch(e) {
                    console.log(e)
                } finally {
                    this.loading = false
                }
            }
        },
    }
}
</script>
