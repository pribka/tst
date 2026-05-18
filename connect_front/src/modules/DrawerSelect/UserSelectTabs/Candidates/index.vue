<template>
    <div class="all-users-wrap">
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
</template>

<script>
export default {
    name: 'Candidates',
    components: {
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
    }
}
</script>
<style lang="scss" scoped>
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