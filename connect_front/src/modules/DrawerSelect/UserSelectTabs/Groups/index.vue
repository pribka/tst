<template>
    <div class="groups-wrap">
        <div class="groups-list">
            <GroupsList
                :selectedGroupID="selectedGroupID"
                @select="onSelect" />
        </div>
        <div class="user-list">
            <template v-if="selectedGroupID">
                <GroupsUsers
                    ref="groupUsersRef"
                    :multiple="multiple"
                    :selectedGroupID="selectedGroupID"
                    :checkSelected="checkSelected"
                    :itemSelect="itemSelect"
                    :deselectUser="deselectUser"
                    :selectedList="selectedList"
                    :singleSelected="singleSelected" />
            </template>
            <template v-else>
                <div class="empty">
                    {{ $t('select_team') }}
                </div>
            </template>
        </div>
    </div>
</template>

<script>
export default {
    name: 'Groups',
    components: {
        GroupsList: () => import('./GroupsList.vue'),
        GroupsUsers: () => import('./GroupsUsers.vue')
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
        }
    },
    data() {
        return {
            loading: false,
            selectedGroupID: null
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
        onSelect(groupID) {
            this.selectedGroupID = this.selectedGroupID === groupID ? null : groupID
            if (this.selectedGroupID)
                this.$nextTick(() => {
                    this.$refs.groupUsersRef.reload()
                })
        }
    }
}
</script>
<style lang="scss" scoped>
.groups-wrap {
    width: 100%;
    height: 100%;
    overflow: hidden;
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    grid-template-rows: 1fr;
    gap: 12px;
    .groups-list {
        width: 100%;
        height: 100%;
        min-width: 0;
        overflow: auto;
    }
    .user-list {
        width: 100%;
        height: 100%;
        min-width: 0;
        min-height: 0;
        overflow: hidden;
        .empty {
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            background-color: rgba(240, 241, 247, 1);
            border-radius: 16px;
        }
    }
}
</style>