<template>
    <div class="all-users-wrap">
        <div v-if="showCandidates && candidates && candidates.length" class="candidates_block">
            <div class="block_label">{{ $t('candidates') }}</div>
            <template v-if="multiple">
                <UserItem 
                    v-for="user in candidates"
                    checkedClass="all-users-checked-class"
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
                        v-for="user in candidates"
                        checkedClass="all-users-checked-class"
                        class="user-item"
                        :key="user.id"
                        :multiple="multiple"
                        :checkSelected="checkSelected"
                        :itemSelect="itemSelect"
                        :item="user" />
                </a-radio-group>
            </template>
        </div>
        <div v-if="showCandidates && candidates && candidates.length" class="block_label">
            {{ $t('all_user') }}
        </div>
        <template v-if="multiple">
            <UserItem 
                v-for="user in list"
                checkedClass="all-users-checked-class"
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
                    checkedClass="all-users-checked-class"
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
    name: 'AllUsers',
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
        },
        showCandidates: {
            type: Boolean,
            default: false
        },
        candidates: {
            type: Array,
            default: () => []
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
                        page: this.page
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
.block_label{
    margin-bottom: 10px;
    color: #888888;
}
.candidates_block{
    border-bottom: 1px solid var(--borderColor);
    padding-bottom: 15px;
    margin-bottom: 15px;
}
.all-users-wrap{
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
.all-users-checked-class {
    background-color: rgba(240, 241, 247, 1);
}
</style>