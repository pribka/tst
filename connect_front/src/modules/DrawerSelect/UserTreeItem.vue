<template>
    <div>
        <div class="flex items-start" :class="!multiple && isUser && 'selectable'" @click="select">
            <div class="flex items-center mr-2">
                <span class="item_angle" :class="expanded && 'expanded'" @click="toggleExpandedState">
                    <i v-if="!isUser" class="fi fi-rr-angle-small-down"></i>
                </span>
                <template v-if="multiple">
                    <a-checkbox 
                        size="large" 
                        class="text-base mr-2 checkbox" 
                        :checked="checked"
                        :indeterminate="indeterminate"
                        @change="checkHandler({ checked: $event.target.checked, item: item, parent: parent })" />
                </template>
                <a-avatar
                    icon="user"
                    :src="avatarSrc"
                    :class="!multiple && isUser && 'cursor-pointer'" />
            </div>
            <div>
                <p 
                    class="username" 
                    :class="!isUser && 'pt-1.5'">
                    {{ item.full_name || item.name }}
                </p>
                <template v-if="isUser">
                    <p class="mt-0 opacity-50 text-xs organization_name">{{ parent.name }}</p>
                </template>
            </div>
        </div>

        <template v-if="expanded">
            <div class="pt-5">
                <!-- Organizations -->
                <template v-if="item.structural_division_count">
                    <div class="mb-5">
                        <UserTreeItem 
                            class="list_item" 
                            v-for="organization in organizations.results" 
                            :key="organization.id" 
                            :item="organization.contractor"
                            :metadata="metadata"
                            :checkHandler="checkHandler"
                            :multiple="multiple"
                            :model="model"
                            :pageName="pageName"
                            :selectSingleUser="selectSingleUser"
                            :parent="item" />
                        <infinite-loading 
                            ref="infiniteLoading"
                            @infinite="organizationsInfiniteHandler"
                            :identifier="organizationInfiniteId"
                            :distance="10">
                            <div 
                                slot="spinner"
                                class="flex items-center justify-center inf_spinner">
                                <a-spin />
                            </div>
                            <div slot="no-more"></div>
                            <div slot="no-results"></div>
                        </infinite-loading>
                    </div>
                </template>

                <!-- Users -->
                <template v-if="isAllOrganizationsLoaded">
                    <UserTreeItem 
                        class="list_item" 
                        v-for="user in users.results" 
                        :key="user.id" 
                        :item="user"
                        :metadata="metadata"
                        :checkHandler="checkHandler"
                        :multiple="multiple"
                        :model="model"
                        :pageName="pageName"
                        :selectSingleUser="selectSingleUser"
                        :parent="item" />
                    <infinite-loading 
                        ref="infiniteLoading"
                        @infinite="usersInfiniteHandler"
                        :identifier="infiniteId"
                        :distance="10">
                        <div 
                            slot="spinner"
                            class="flex items-center justify-center inf_spinner">
                            <a-spin />
                        </div>
                        <div slot="no-more"></div>
                        <div slot="no-results"></div>
                    </infinite-loading>
                </template>
            </div>
        </template>
    </div>
</template>

<script>
import InfiniteLoading from 'vue-infinite-loading';
export default {
    name: 'UserTreeItem',
    components: {
        InfiniteLoading,
    },
    props: {
        metadata: {
            type: Object,
            default: () => {}
        },
        item: {
            type: Object,
            required: true,
        },
        checkHandler: {
            default: () => {}
        },
        multiple: {
            default: false
        },
        pageName: {
            default: 'user_select'
        },
        model: {
            type: String,
            default: 'users.ProfileModel'
        },
        parent: {
            type: Object,
            default: null
        },
        selectSingleUser: {
            type: Function,
            required: true
        }
    },
    data() {
        return {
            expanded: false,

            infiniteId: new Date(),
            organizationInfiniteId: new Date(),

            users: {
                results: [],
                next: true
            },
            usersParams: {
                page: 1,
                page_size: 10,
                page_name: this.pageName,
            },

            organizations: {
                results: [],
                next: this.item.structural_division_count
            },
            organizationsParams: {
                page: 1,
                page_size: 10,
                page_name: this.pageName,
                filters: { relation_type_id: 'structural_division' }
            },
        }
    },
    computed: {

        selectedUsers() {
            return this.metadata?.value?.[this.metadata?.key] || []
        },
        isAllOrganizationsLoaded() {
            return !this.organizations.next 
        },
        avatarSrc() {
            return this.item?.avatar?.path || this.item.logo
        },
        isUser() {
            return this.item.username
        },
        checked() {
            if (this.isUser) {
                const parentOrganization = this.selectedUsers.find(item => item.parent.id === this.parent.id)
                if (parentOrganization) {
                    return parentOrganization.users.some(user => user.id === this.item.id)
                }
                return false
            }
            // if organization
            const organization = this.selectedUsers.find(item => item.parent.id === this.item.id)
            if (organization) {
                if (organization.users?.length > 0) {
                    return Boolean(organization.users.length)
                }
                return organization?.checked || false
            }
            return false
        },
        indeterminate() {
            if (this.isUser) return false
            const organization = this.selectedUsers.find(item => item.parent.id === this.item.id)
            if (organization?.users?.length) 
                return organization.users.length > 0 
                    && organization.users.length < organization.userCount
            return false
        },
    },
    methods: {
        toggleExpandedState() {
            this.expanded = !this.expanded
            if (this.expanded) { this.reset() }
        },
        reset() {
            this.infiniteId = new Date()
            this.users = { results: [] }
            this.usersParams.page = 1
            
            this.organizationInfiniteId = new Date()
            this.organizations = { results: [] }
            this.organizationsParams.page = 1
        },
        async usersInfiniteHandler($state) {
            const url = `/users/my_organizations/${this.item.id}/users_short/`
            this.$http.get(url, { params: this.usersParams })
                .then(({ data }) => {
                    data.results.unshift(...this.users.results)
                    this.users = data

                    if (data.next) {
                        this.usersParams.page++
                        $state.loaded()
                    } else {
                        $state.complete()
                    }
                })
                .catch(error => {
                    this.$message.error('Не удалось получить список пользователей')
                    console.error(error)
                    $state.complete()
                })         
        },
        organizationsInfiniteHandler($state) {
            const url = `/users/my_organizations/${this.item.id}/relations/`
            this.$http.get(url, { params: this.organizationsParams })
                .then(({ data }) => {
                    data.results.unshift(...this.organizations.results)
                    this.organizations = data
                    if (data.next) {
                        this.organizationsParams.page++
                        $state.loaded()
                    } else {
                        $state.complete()
                    }
                })
                .catch(error => {
                    this.$message.error('Не удалось получить список дочерних организаций')
                    console.error(error)
                    $state.complete()
                })         
        },
        select() {
            if (!this.multiple && this.isUser) {
                this.selectSingleUser(this.item)
            }
        }
    },
}
</script>

<style lang="scss" scoped>
:deep {
    .ant-checkbox-inner {
        width: 20px;
        height: 20px;
        border-radius: 4px;
    }
}

.list_item {
    padding-left: 35px;
    & + & {
        margin-top: 20px;
    }
}


.item_angle {
    position: relative;
    z-index: 1000;

    display: flex;
    justify-content: center;
    flex-shrink: 0;
    width: 20px;
    
    margin-right: 15px;

    color: var(--primaryColor);
    transition: transform 0.2s ease;
    cursor: pointer;
}

.item_angle.expanded {
    transform: rotate(180deg);
}

.checkbox {
    position: relative;
    z-index: 1000;
}

.username {
    transition: color 0.2s ease;
}

.selectable {
    .username,
    .organization_name {
        cursor: pointer;
    }
}
.selectable:hover {
    .username,
    .organization_name {
        color: var(--primaryColor);
    }
}

</style>