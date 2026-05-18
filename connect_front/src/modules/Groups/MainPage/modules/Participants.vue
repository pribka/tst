<template>
    <div class="participants-wrapper">
        <a-spin :spinning="loading" class="h-full">
            <div class="participants">
                <template v-if="view === 'employees'">

                    <component 
                        :getRoles="getRoles"
                        :is="componentWidget"
                        class="h-full flex flex-col min-h-0"
                        :actions="actions"
                        :updatePartisipants="updatePartisipants"
                        :isFounder="isFounder"
                        :id="id" />
                        
                </template>
                <div v-if="view === 'organizations'">
                    <template v-if="!organizations.length">
                        <a-empty class="mt-10">
                            <span slot="description">Нет организаций участников</span>
                        </a-empty>
                    </template>
                    <template v-else>
                        <transition-group name="org" tag="div" class="organizations">
                            <MemberOrgCard
                                v-for="organization in organizations"
                                :key="organization.id"
                                :member="organization"
                                :editMemberOrg="editMemberOrg" />
                        </transition-group>
                    </template>
                </div>
            </div>
        </a-spin>
        <AddOrgDrawer
            ref="addOrgDrawer"
            :visible="addOrgDrawerVisible"
            :onAddOrgDrawerClose="onAddOrgDrawerClose"
            :isEdit="isEdit"
            @addToOrganizations="addToOrganizations"
            @removeFromOrganizations="removeFromOrganizations"
            @updateOrganization="updateOrganization" />
    </div>
    
</template>

<script>
import Vue from 'vue'
import { mapState } from 'vuex'
export default{
    name: 'Participants',
    components: {
        MemberTable: () => import('../../components/MemberTable.vue'),
        AddOrgDrawer: () => import('./module_components/AddOrgDrawer'),
        MemberOrgCard: () => import('./module_components/MemberOrgCard.vue')
    },
    props: {
        getRoles: {
            type: Function,
            required: true
        },
        isFounder: {
            type: Boolean,
            required: true
        },
        isStudent: {
            type: Boolean,
            required: true
        },
        id: {
            type: [String, Number],
            default: null
        },
        updatePartisipants: {
            type: Function,
            default: () => {}
        },
        actions: {
            type: Object,
            default: () => null
        }
    },
    mounted() {
        this.getData()
    },
    computed: {
        ...mapState({
            project: state => state.projects.workgroupData
        }),
        isMobile() {
            return this.$store.state.isMobile
        },
        componentWidget() {
            if (this.isMobile) {
                return () => import('../../components/MemberList.vue')
            }
            return () => import('../../components/MemberTable.vue')
        }

    },
    data() {
        // const defaultView = 'organizations'
        const defaultView = 'employees'
        
        return {
            view: defaultView,
            addOrgDrawerVisible: false,
            loading: false,
            organizations: [],
            employees: [],
            isEdit: false

        }
    },
    methods: {
        openAddDrawer(isEdit) {
            this.isEdit = isEdit
            this.setAddOrgDrawerVisible(true)
        },
        async editMemberOrg(memberOrg) {
            await this.$refs.addOrgDrawer.selectOrganization(memberOrg, false, true)
            this.openAddDrawer(true)
        },
        onAddOrgDrawerClose() {
            this.isEdit = false
            this.setAddOrgDrawerVisible(false)
        },
        setView(view) {
            this.view = view
            this.getData()
        },
        setAddOrgDrawerVisible(value) {
            this.addOrgDrawerVisible = value
        },
        getData() {
            if (this.view === 'organizations' && !this.organizations.length) {
                this.fetchOrganizations()
            } else if (this.view === 'employees' && !this.employees.length) {
                this.fetchEmployees()
            }
        },
        async fetchOrganizations() {
            this.loading = true
            try {
                const { data } = await this.$http.get(`/work_groups/workgroups/${this.project.id}/member_organizations/`)
                this.organizations = data || []
            } catch(e) {
                console.log(e)
                this.$message.error('Не удалось получить организации-участников')
            } finally {
                this.loading = false
            }
        },
        addToOrganizations(newOrgMember) {
            this.organizations.unshift(newOrgMember)
        },
        removeFromOrganizations(orgMember) {
            const index = this.organizations.findIndex(item => item.organization.id === orgMember.id)
            if (index !== -1) {
                this.organizations.splice(index, 1)
            }
        },
        updateOrganization(orgMember) {
            const index = this.organizations.findIndex(item => item.id === orgMember.id)
            if (index !== -1) {
                Vue.set(this.organizations, index, orgMember)
            }
        },
        async fetchEmployees() {}
    }
}
</script>
<style lang="scss" scoped>
.participants-wrapper {
    height: 100%;
    display: flex;
    flex-direction: column;
    gap: 20px;
    .bottoms {
        display: flex;
        justify-content: space-between;
        .selector {
            display: flex;
            gap: 16px;
        }
    }
    .participants {
        height: 100%;
        .organizations {
            display: flex;
            flex-direction: column;
            gap: 15px;
            min-height: 0;
            .org-enter-active, .org-leave-active {
                transition: all 0.3s;
            }
            .org-enter, .org-leave-to {
                opacity: 0;
                transform: translateY(30px);
            }
        }
    }
}
</style>