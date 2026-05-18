<template>
    <div class="outside-users-wrap">
        <template v-if="multiple">
            <UserItem 
                v-for="user in list"
                checkedClass="outside-users-checked-class"
                class="user-item"
                :key="user.id"
                :multiple="multiple"
                :checkSelected="checkSelected"
                :itemSelect="itemSelect"
                :item="user" />
        </template>
        <template v-else>
            <a-radio-group v-model="selectedUserID" class="w-full">
                <UserItem 
                    v-for="user in list"
                    checkedClass="outside-users-checked-class"
                    class="user-item"
                    :key="user.id"
                    :multiple="multiple"
                    :checkSelected="checkSelected"
                    :itemSelect="itemSelect"
                    :item="user" />
            </a-radio-group>
        </template>
        <div v-if="page === 1 && loading" class="flex justify-center">
            <a-spin size="small" />
        </div>
        <infinite-loading ref="userInfinite" @infinite="getList" :distance="10">
            <div slot="spinner"><a-spin v-if="page !== 1" size="small" /></div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
    </div>
</template>

<script>
export default {
    name: 'OutsideUsers',
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
        pageName: {
            type: String,
            default: 'user_select',
        },
        checkSelected: {
            type: Function,
            default: () => {}
        },
        itemSelect: {
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
        }
    },
    data() {
        return {
            search: '',
            page: 0,
            loading: false,
            list: [],
            pageSize: 15
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
        reload() {
            this.page = 0
            this.list = []
            this.getList()
        },
        async getList($state = null) {
            if(!this.loading) {
                try {
                    this.loading = true
                    this.page = this.page + 1
                    let params = {
                        page_size: this.pageSize,
                        page: this.page,
                        only_my: false
                    }
                    const { data } = await this.$http.get('user/list/', { params })
                    if(data && data.results && data.results.length) this.list.push(...data.results)
                    if(data.next) {
                        if($state) 
                            $state.loaded()
                    } else {
                        if($state) 
                            $state.complete()
                    }
                } finally {
                    this.loading = false
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
.outside-users-wrap{
    width: 100%;
    height: 100%;
    overflow: auto;
    .user-item{
        &:hover{
            background: rgba(240, 241, 247, 1);
        }
    }
}
</style>
<style lang="scss">
.outside-users-checked-class {
    background-color: rgba(240, 241, 247, 1);
}
</style>