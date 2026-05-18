<template>
    <div class="organizations-wrap">
        <div class="org-tree">
            <OrgTree
                :selectedOrgID="selectedOrgID"
                @select="onSelect" />
        </div>
        <div class="user-list">
            <template v-if="selectedOrgID">
                <OrgUsers
                    ref="orgUsersRef"
                    :multiple="multiple"
                    :selectedOrgID="selectedOrgID"
                    :checkSelected="checkSelected"
                    :itemSelect="itemSelect"
                    :deselectUser="deselectUser"
                    :selectedList="selectedList"
                    :singleSelected="singleSelected" />
            </template>
            <template v-else>
                <div class="empty">
                    {{ $t('org_select') }}
                </div>
            </template>
        </div>
    </div>
</template>

<script>
export default {
    name: 'Organizations',
    components: {
        OrgTree: () => import('./OrgTree.vue'),
        OrgUsers: () => import('./OrgUsers.vue')
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
            selectedOrgID: null
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
        onSelect(orgID) {
            this.selectedOrgID = this.selectedOrgID === orgID ? null : orgID
            if (this.selectedOrgID)
                this.$nextTick(() => {
                    this.$refs.orgUsersRef.reload()
                })
        }
    }
}
</script>
<style lang="scss" scoped>
.organizations-wrap {
    width: 100%;
    height: 100%;
    overflow: hidden;
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    grid-template-rows: 1fr;
    gap: 12px;
    .org-tree {
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