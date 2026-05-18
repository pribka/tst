<template>
    <div>
        <div v-for="item in items.results" :key="item.id" class="list_item">
            <UserTreeItem
                :model="model"
                :metadata="metadata"
                :item="item"
                :checkHandler="checkHandler"
                :multiple="multiple"
                :pageName="pageName"
                :selectedUsers="selectedUsers"
                :selectSingleUser="selectSingleUser"/>
        </div>
        <template v-if="isEmpty">
            <a-empty :description="$t('no_data')" />
        </template>
        <infinite-loading
            ref="infiniteLoading"
            @infinite="infiniteHandler"
            :identifier="infiniteId"
            :distance="10">
            <div slot="spinner" class="flex items-center justify-center inf_spinner">
                <a-spin />
            </div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
    </div>
</template>

<script>
import InfiniteLoading from "vue-infinite-loading";

import eventBus from "@/utils/eventBus";
export default {
    components: {
        UserTreeItem: () => import("./UserTreeItem.vue"),
        InfiniteLoading,
    },
    props: {
        metadata: {
            type: Object,
            default: () => {}
        },
        changeMetadata: {
            type: Function,
            default: () => {}
        },
        selected: {
            type: [Object, Array, String],
            default: null,
        },
        multiple: {
            type: Boolean,
            default: false,
        },
        pageName: {
            type: String,
            default: 'user_select',
        },
        model: {
            type: String,
            default: "users.ProfileModel",
        },
        selectUsersList: {
            type: Function,
            default: () => {},
        },
        selectSingleUser: {
            type: Function,
            required: true,
        },
        id: {
            type: [String, Number],
            required: true,
        },
        
    },
    data() {
        return {
            infiniteId: new Date(),
            items: {
                results: [],
            },
            params: {
                page: 1,
                page_size: 10,
                display: "root",
                page_name: this.pageName,
            },
            /** Список отмеченных организаций с пользователями этих организаций.
             *  Элементы списка имеют вид: { id: id организации, users: список пользователей организации }
             */
            // selectedUsers: [],
            stateTree: [],
            oldSelectedState: [],
        };
    },
    computed: {
        isEmpty() {
            return this.items.count === 0;
        },
        selectedUsers: {
            get() {
                return this.metadata?.value?.[this.metadata?.key] || []
            },
            set(value) {
                this.changeMetadata({ key: this.metadata.key, value: value});
            }
        }
    },
    methods: {
        findById(id) {
            return (item) => item.id === id;
        },
        getOrganizationById(id) {
            return this.selectedUsers.find((item) => item.parent.id === id);
        },
        getOrganizationIndexById(id) {
            return this.selectedUsers.findIndex((item) => item.parent.id === id);
        },
        async getOrganizationUsers(id) {
            const url = `/users/my_organizations/${id}/users_short/`;
            const params = { page_size: "all" };
            return await this.$http
                .get(url, { params })
                .then(({ data }) => data)
                .catch((error) => {
                    this.$message.error(
                        "Не удалось получить список пользователей в организации"
                    );
                    console.error(error);
                });
        },
        async selectAllOrganization(id) {
            const organization = this.getOrganizationById(id);
            organization.users.splice(0);
            const users = await this.getOrganizationUsers(id);
            if (users) {
                const tempArray = [...this.selectedUsers]
                tempArray.push({
                    parent: { id },
                    users: [ ...users.results ],
                    userCount: users.count
                });
                this.selectedUsers = tempArray
            }
        },
        async addOrganizationUsers(organizationId) {
            const users = await this.getOrganizationUsers(organizationId);
            if (users) {
                const tempArray = [...this.selectedUsers]
                tempArray.push({
                    parent: { id: organizationId },
                    users: users.results,
                    userCount: users.count,
                });
                this.selectedUsers = tempArray

            }
        },
        resetOrganization(id) {
            const index = this.getOrganizationIndexById(id);
            if (index !== -1) {
                const tempArray = [...this.selectedUsers]
                tempArray.splice(index, 1)
                this.selectedUsers = tempArray
            }
        },
        isOrganizationExist(id) {
            return this.selectedUsers.findIndex((item) => item.parent.id === id) !== -1 
        },
        removeUserFromOrganization(organizationId, userId) {
            const organization = this.getOrganizationById(organizationId);
            const userIndex = organization.users.findIndex(
                this.findById(userId)
            )
            if (userIndex !== -1) {
                const removedUser = organization.users.splice(userIndex, 1);
                if (organization.users.length === 0) {
                    this.resetOrganization(organizationId)
                    console.log(organizationId)
                }
                return removedUser
            }
            return [];
        },
        removeUserFromAllOrganization(userId) {
            this.selectedUsers.forEach(users => {
                this.removeUserFromOrganization(users.parent.id, userId)
            })
        },
        addUserToOrganization(organization, user) {
            const parentOrganization = this.getOrganizationById(organization.id);
            if (parentOrganization) {
                parentOrganization.users.push(user);
            } else {
                const tempArray = [...this.selectedUsers]
                tempArray.push({
                    parent: { id: organization.id },
                    users: [ user ],
                    userCount: organization.members_count,
                });
                this.selectedUsers = tempArray
            }
        },
        async infiniteHandler($state) {
            const url = "/users/my_organizations/";
            this.$http
                .get(url, { params: this.params })
                .then(({ data }) => {
                    data.results.unshift(...this.items.results);
                    this.items = data;
                    

                    if (data?.next) {
                        this.params.page++;
                        $state.loaded();
                    } else {
                        $state.complete();
                    }
                })
                .catch((error) => {
                    this.$message.error("Не удалось получить список пользователей");
                    console.error(error);
                    $state.complete();
                });
        },
        /** Обработчик переключения чекбокса
         *  Важно! Функция используется родительским компонентом через ref */
        async checkHandler({ checked, item, parent = null }) {
            const isUser = item?.username
            let nextSelected = JSON.parse(JSON.stringify(this.selectedUsers))

            const getOrg = id => nextSelected.find(o => o.parent.id === id)
            const getOrgIndex = id => nextSelected.findIndex(o => o.parent.id === id)

            if (isUser) {
                if (parent) {
                    const org = getOrg(parent.id)
                    if (checked) {
                        if (org) org.users.push(item)
                        else nextSelected.push({ parent: { id: parent.id }, users: [item], userCount: parent.members_count })
                    } else {
                        if (org) {
                            const idx = org.users.findIndex(u => u.id === item.id)
                            if (idx !== -1) org.users.splice(idx, 1)
                            if (!org.users.length) nextSelected.splice(getOrgIndex(parent.id), 1)
                        }
                    }
                } else if (!checked) {
                    nextSelected = nextSelected.map(g => ({ ...g, users: g.users.filter(u => u.id !== item.id) })).filter(g => g.users.length)
                }
            } else {
                if (item.members_count === 0) this.$message.warning(this.$t('There are no users in the selected organization'))
                if (checked) {
                    if (getOrg(item.id)) {
                        const users = await this.getOrganizationUsers(item.id)
                        if (users) {
                            nextSelected = nextSelected.map(g => g.parent.id === item.id ? { ...g, users: [...users.results], userCount: users.count } : g)
                        }
                    } else {
                        const users = await this.getOrganizationUsers(item.id)
                        if (users) nextSelected.push({ parent: { id: item.id }, users: users.results, userCount: users.count })
                    }
                } else {
                    const idx = getOrgIndex(item.id)
                    if (idx !== -1) nextSelected.splice(idx, 1)
                }
            }

            this.selectedUsers = nextSelected

            const unique = this.getUniqueUsers(nextSelected)
            this.selectUsersList(unique)
        },
        syncSelectedList() {
            const uniqueUsers = this.getUniqueUsers()
            this.selectUsersList(uniqueUsers)
        },
        getUniqueUsers(source = this.selectedUsers) {
            const uniqueUsers = []
            const seenIds = new Set()
            source.forEach(organization => {
                organization.users.forEach(user => {
                    if (!seenIds.has(user.id)) {
                        uniqueUsers.push(user)
                        seenIds.add(user.id)
                    }
                })
            })
            return uniqueUsers
        },
        initStateData() {
            this.metadata
        },
        // resetStateTree() {
        //     const payload = {
        //         page_name: this.id,
        //         key: "users.ProfileModel",
        //         others: null,
        //     };
        //     this.$http.post("app_info/chosen_filters/", payload).catch((error) => {
        //         this.$message.error("Не удалось сохранить изменения");
        //         console.error(error);
        //     });
        // },
        reset() {
            this.infiniteId = new Date()
            this.items = { results: [] }
            this.params.page = 1
        },
    },
    created() {
        if (this.multiple) {
            this.initStateData()
            // this.initStateData()
            //     .then(() => {
            //         this.initUsersFromState()
            //     })
        }
    },
    mounted() {
        eventBus.$on(`update_filter_${this.model}`, () => {
            this.reset();
        });

        // eventBus.$on(`drawer_select_drop_temp_state_${this.id}`, () => {
        //     console.log(`drawer_select_drop_temp_state_${this.id}`)
        //     this.$store.commit('user_select/DROP_TEMP_STATE', { id: this.id })
        // })


    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.model}`);
        // eventBus.$off(`drawer_select_drop_temp_state_${this.id}`);
        // eventBus.$off(`drawer_select_save_state_${this.id}`);
    },
};
</script>

<style lang="scss" scoped>
.list_item {
  display: flex;
  align-items: center;

  & + & {
    margin-top: 20px;
  }
}
</style>