<template>
    <div class="project-users-wrap">
        <template v-if="multiple">
            <div class="multiple">
                <div class="buttons">
                    <a-button
                        type="ui"
                        class="select-all"
                        ghost
                        :disabled="isListEmpty || loading"
                        @click="selectAll" >
                        {{ $t('select_all') }}
                    </a-button>
                    <a-button
                        type="ui"
                        ghost
                        class="clear-all"
                        :disabled="isListEmpty || loading"
                        @click="clearAll">
                        {{ $t('deselect_all') }}
                    </a-button>
                </div>
                <div class="list">
                    <UserItem 
                        v-for="user in list"
                        checkedClass="project-checked-class"
                        :key="user.id"
                        :multiple="multiple"
                        :checkSelected="checkSelected"
                        :itemSelect="itemSelect"
                        :item="user" />
                    <infinite-loading ref="userInfinite" @infinite="getList" :distance="10">
                        <div slot="spinner"><a-spin v-if="page !== 1" size="small" /></div>
                        <div slot="no-more"></div>
                        <div slot="no-results"></div>
                    </infinite-loading>
                    <div v-if="page === 1 && loading" class="flex justify-center">
                        <a-spin size="small" />
                    </div>
                </div>
                <div v-if="isListEmpty" class="empty">
                    <a-empty :description="false" />
                </div>
            </div>
        </template>
        <template v-else>
            <div class="list w-full">
                <a-radio-group v-model="selectedUserID" class="w-full">
                    <UserItem 
                        v-for="user in list"
                        checkedClass="project-checked-class"
                        :key="user.id"
                        :multiple="multiple"
                        :checkSelected="checkSelected"
                        :itemSelect="itemSelect"
                        :item="user" />
                    <infinite-loading ref="userInfinite" @infinite="getList" :distance="10">
                        <div slot="spinner"><a-spin v-if="page !== 1" size="small" /></div>
                        <div slot="no-more"></div>
                        <div slot="no-results"></div>
                    </infinite-loading>
                    <div v-if="page === 1 && loading" class="flex justify-center">
                        <a-spin size="small" />
                    </div>
                </a-radio-group>
                <div v-if="isListEmpty" class="empty">
                    <a-empty :description="false" />
                </div>
            </div>
        </template>
    </div>
</template>

<script>
export default {
    name: 'ProjectsUsers',
    components: {
        InfiniteLoading: () => import('vue-infinite-loading'),
        UserItem: () => import('../../UserItem.vue')
    },
    props: {
        multiple: {
            type: Boolean,
            default: false
        },
        model: {
            type: String,
            default: "users.ProfileModel",
        },
        checkSelected: {
            type: Function,
            default: () => {}
        },
        itemSelect: {
            type: Function,
            default: () => {}
        },
        deselectUser: {
            type: Function,
            default: () => {}
        },
        selectedList: {
            type: Array,
            default: () => []
        },
        singleSelected: {
            type: [String, null],
            default: null
        },
        selectedProjectID: {
            type: [String, null],
            default: null
        }
    },
    data() {
        return {
            search: '',
            page: 0,
            next: null,
            loading: false,
            list: [],
            pageSize: null,
            operation: '',
            isListEmpty: false
        }
    },
    computed: {
        selectedUserID: {
            get() {
                return this.singleSelected
            },
            set(val) {
                const selectedUser = this.list.find(user => user.id === val)
                if (selectedUser) {
                    this.itemSelect(selectedUser)
                }
            }
        }
    },
    methods: {
        selectAll() {
            if (!this.selectedProjectID || !this.list.length) return
            if (this.next) {
                this.pageSize = 'all'
                this.operation = 'selectAll'
                this.page = 0
                this.next = null
                this.list = []
                if (this.$refs.userInfinite) {
                    this.$refs.userInfinite.stateChanger.reset()
                }
            } else {
                this.selectUnselectedUsers()
            }
        },
        selectUnselectedUsers() {
            this.list.forEach(user => {
                if(!this.checkSelected(user))
                    this.itemSelect(user)
            })
            this.operation = ''
        },
        deselectAllUsers() {
            this.list.forEach(user => this.deselectUser(user))
            this.operation = ''
        },
        clearAll() {
            if (!this.selectedProjectID || !this.list.length) return
            if (this.next) {
                this.pageSize = 'all'
                this.operation = 'clearAll'
                this.page = 0
                this.next = null
                this.list = []
                if (this.$refs.userInfinite) {
                    this.$refs.userInfinite.stateChanger.reset()
                }
            } else {
                this.deselectAllUsers()
            }
        },
        async reload() {
            this.page = 0
            this.list = []
            this.operation = ''
            if (this.$refs.userInfinite) {
                this.$refs.userInfinite.stateChanger.reset()
            }
        },
        async getList($state = null) {
            if (!this.selectedProjectID) return
            if (!this.loading) {
                try {
                    this.loading = true
                    this.page = this.page + 1
                    let params = {
                        page_size: this.pageSize ? this.pageSize : 10,
                        page: this.page,
                        display: 'descendants'
                    }
                    const { data } = await this.$http.get(`work_groups/workgroups/${this.selectedProjectID}/get_workgroups_members_short/`, { params })
                    this.next = data.next
                    if(data && data.results && data.results.length)
                        this.list.push(...data.results)
                    if(this.pageSize === 'all') {
                        this.pageSize = null
                        switch (this.operation) {
                        case 'selectAll':
                            this.selectUnselectedUsers()
                            break
                        case 'clearAll':
                            this.deselectAllUsers()
                            break
                        }
                        this.operation = ''
                    }
                    if(data.next) {
                        if($state) {
                            $state.loaded()
                        }
                    } else {
                        if($state) {
                            $state.complete()
                        }
                    }
                } finally {
                    this.loading = false
                    this.isListEmpty = this.list.length === 0
                }
            } else {
                if($state) 
                    $state.complete()
            }
        }
    }
}
</script>
<style lang="scss" scoped>
.project-users-wrap {
    background-color: rgba(240, 241, 247, 1);
    border-radius: 16px;
    width: 100%;
    height: 100%;
    padding: 12px;
    .multiple {
        display: flex;
        flex-direction: column;
        gap: 12px;
        min-height: 0;
        height: 100%;
        .buttons {
            display: flex;
            justify-content: space-between;
            border-radius: 8px;
            background-color: rgba(255, 255, 255, 1);
            .select-all.ant-btn-background-ghost, .clear-all.ant-btn-background-ghost {
                &:hover {
                    background-color: rgba(71, 119, 255, 1) !important;
                    color: rgba(255, 255, 255, 1) !important;
                }
            }
            @media (max-width: 650px) {
                flex-direction: column;
                justify-content: start;
                gap: 8px;
            }
        }
        .list {
            flex: 1;
        }
    }
    .list {
        overflow: auto;
        height: 100%;
    }
    .empty {
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
    }
}
</style>
<style lang="scss">
.project-checked-class {
    background-color: #fff;
}
</style>
