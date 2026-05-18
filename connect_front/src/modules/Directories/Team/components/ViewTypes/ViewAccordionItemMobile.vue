<template>
    <div 
        class="border custom_border_color overflow-hidden"
        :class="[parentId ? 'mobile_border' : 'rounded-lg']">
        <div class="bg-white flex justify-between items-center w-full custom_hover cursor-pointer">
            <div
                class="pl-4 py-2 flex-grow flex items-center truncate"
                @click="selectKey(organization.id, organization.is_endpoint)">
                <div class="mr-2">
                    <template v-if="isDepartment">
                        <a-avatar 
                            flaticon
                            icon="fi-rr-users-alt" 
                            :size="24" />
                    </template>
                    <template v-else>
                        <a-avatar 
                            icon="team" 
                            :size="24" 
                            :src="organization.logo" />
                    </template>
                    
                </div>
                <span class="truncate" ref="organizationName">
                    {{ organization.full_name || organization.name }}
                </span>
                <a-button 
                    v-if="isOverflowing"
                    v-tippy="{ touch: true }" 
                    :content="organization.full_name || organization.name"
                    @click.stop=""
                    type="ui" 
                    shape="circle"
                    ghost
                    flaticon
                    icon="fi-rr-info">
                </a-button>
            </div>
            <div class="flex items-center">
                <template v-if="showEdit">
                    <a-button 
                        v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }" 
                        :content="editTooltipTitle"
                        type="ui" 
                        shape="circle"
                        @click="editOrganization"
                        ghost
                        class="flex items-center justify-center">
                        <i class="fi fi-rr-edit"></i>
                    </a-button>
                </template>
                <div 
                    class="px-4 py-2"
                    @click="selectKey(organization.id, organization.is_endpoint)">
                    <div :class="isExpand && 'rotate-90'">
                        <i class="fi fi-rr-angle-small-right"></i>
                    </div>
                </div>
            </div>
        </div>
        <transition
            name="expand"
            @enter="enter"
            @after-enter="afterEnter"
            @leave="leave">
            <div v-show="isExpand">
                <div class="custom_bg p-4 border-t custom_border_color">
                    <AccordionItemHeader 
                        class="mb-4"
                        :organization="organization"
                        :relationId="relationId"
                        :parentId="parentId"
                        :isDepartment="isDepartment"/>
                        
                    <template v-if="isExpand" >
                        <OrganizationStatistics 
                            :organization="organization"
                            :parentId="parentId"
                            :parentMemberCount="parentMemberCount"
                            :isDepartment="isDepartment"/>
                    </template>

                    <template v-if="showDepartments">
                        <ul class="mt-4">
                            <div class="-mt-2 mb-3 flex flex-wrap justify-between items-center">
                                <p class="mt-2 mr-2 font-semibold ">{{ $t('team.internal_subdivisions') }}</p>
                                <template v-if="departmentCount > pageSize">
                                    <a-pagination 
                                        size="small" 
                                        class="mt-2 ml-auto"
                                        :value="departmentsPage"
                                        @change="changeDepartmentPage"
                                        :total="departmentCount"
                                        :pageSize="5" />
                                </template>
                            </div>
                            <div class="-mx-4">
                                <template v-if="receivedDepartmentCount">
                                    <ViewAccordionItem
                                        v-for="department in childrenDepartmentsList" 
                                        :key="department.id"
            
                                        isDepartment
                                        :parentPermittedActions="permittedActions"
                                        :parentMemberCount="organization.members_count"
                                        :evenNumbered="!evenNumbered"
                                        :activeEl="activeEl"
                                        :organization="department"
                                        :parentId="organization.id"
                                        :isParentAdmin="isAdmin"
                                        :relationId="getRelationId(department)"
                                        :expandedKeys="expandedKeys"
                                        :selectedKeys="selectedKeys"
                                        :parentKeys="parentKeys.concat(department.id)" />
                                </template>
                                <template v-else>
                                    <div 
                                        class="h-[40px] rounded-lg bg-gray-200"
                                        v-for="department in dislplayedDepartmentCount"
                                        :key="department">
                                    </div>
                                </template>
                            </div>
                        </ul>
                    </template>
                    <!-- <template v-if="departmentsLoading">
                        <div class="mt-4 flex justify-center">
                            <a-spin />
                        </div>
                    </template> -->
                    <template v-if="showChildren">
                        <ul class="mt-4">
                            <div class="-mt-2 mb-3 flex flex-wrap justify-between items-center">
                                <p class="mt-2 font-semibold ">{{ $t('team.structural_subdivisions') }}</p>
                                <template v-if="structureCount > pageSize">
                                    <a-pagination 
                                        size="small" 
                                        :value="page"
                                        class="mt-2 ml-auto"
                                        @change="changeStructuresPage"
                                        :total="structureCount"
                                        :pageSize="5" />
                                </template>
                            </div>
                            <div class="-mx-4">
                                <template v-if="receivedStructureCount">
                                    <ViewAccordionItem
                                        v-for="organization in childrenList" 
                                        :key="organization.id"
         
                                        :evenNumbered="!evenNumbered"
                                        :activeEl="activeEl"
                                        :parentPermittedActions="permittedActions"
        
                                        :organization="organization.contractor"
                                        :parentId="getParentId(organization)"
                                        :isParentAdmin="isAdmin"
                                        :relationId="getRelationId(organization)"
                                        :expandedKeys="expandedKeys"
                                        :selectedKeys="selectedKeys"
                                        :parentKeys="parentKeys.concat(organization.id)" />
                                </template>
                                <template v-else>
                                    <div 
                                        class="h-[40px] rounded-lg bg-gray-100"
                                        v-for="structure in dislplayedStructureCount"
                                        :key="structure">
                                    </div>
                                </template>
                            </div>
                        </ul>
                    </template>
                    <!-- <template v-if="childrenLoading">
                        <div class="mt-4 flex justify-center">
                            <a-spin />
                        </div>
                    </template> -->
                </div>
            </div>
        </transition>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'

import { mapGetters, mapActions, mapState } from 'vuex'
export default {
    name: 'ViewAccordionItem',
    components: {
        OrganizationStatistics: () => import('../OragnizationStatistics.vue'),
        AccordionItemHeader: () => import('./AccordionItemHeader.vue')
    },
    props: {
        organization: {
            type: Object,
            required: true,
        },
        expandedKeys: {
            type: Array,
            default: () => []
        },
        parentKeys: {
            type: Array,
            default: () => []
        },
        selectedKeys: {
            type: Array,
            default: () => []
        },
        activeEl: {
            type: Array,
            default: () => []
        },
        evenNumbered: {
            type: Boolean,
            default: false
        },
        relationId: {
            type: String,
            default: null
        },
        parentId: {
            type: String,
            default: null
        },
        isParentAdmin: {
            type: Boolean,
            default: false
        },
        isDepartment: {
            type: Boolean,
            default: false
        },
        parentMemberCount: {
            type: Number,
            default: null
        },
        parentPermittedActions: {
            type: Object,
            default: null
        },
    },
    data() {
        return {
            pageSize: 5,
            childrenLoading: false,
            departmentsLoading: false,
            permittedActions: null,
            isOverflowing: false
        }
    },
    computed: {
        ...mapGetters({
            organizationChildrenById: 'organization/organizationChildrenById'
        }),
        ...mapState({
            user: state => state.user.user,
            isMobile: state => state.isMobile,
            actionInfo: state => state.organization.actionInfo
        }),
        permissions() {
            return this.actionInfo?.[this.organization.id]
        },
        parentPermissions() {
            return this.actionInfo?.[this.parentId]
        },
        editTooltipTitle() {
            if(this.isDepartment)
                return this.$t('team.edit_internal_subdivision')
            if(!this.isDepartment && this.parentId)
                return this.$t('team.edit_structural_subdivision')
            return this.$t('team.edit_organization')
        },
        structureCount() {
            return this.organization.structural_division_count        
        },
        dislplayedStructureCount() {
            const pageSize = 5
            const remainCount = this.structureCount - pageSize * (this.page-1)
            if(remainCount >= pageSize) {
                return pageSize
            }
            return remainCount % pageSize
        },
        isAdmin() {
            return (this.organization?.director?.id === this.user.id) || this.isParentAdmin
        },
        children() {
            return this.organizationChildrenById(this.organization.id)
        },
        childrenDepartments() {
            return this.$store.state.organization.departments[this.organization.id]
        },
        childrenDepartmentsList() {
            return this.childrenDepartments?.results || []
        },
        childrenList() {
            return this.children?.results || []
        },
        hasChildren() {
            return this.organization.structural_division_count
        },
        hasDepartments() {
            return this.organization.department_count
        },
        departmentCount() {
            return this.organization.department_count
        },
        showChildren() {
            return this.structureCount
        },
        receivedStructureCount() {
            return this.children?.results?.length
        },
        receivedDepartmentCount() {
            return this.childrenDepartments?.results?.length
        },
        dislplayedDepartmentCount() {
            const pageSize = 5
            const remainCount = this.departmentCount - pageSize * (this.departmentsPage-1)
            if(remainCount >= pageSize) {
                return pageSize
            }
            return remainCount % pageSize

        },
        showDepartments() {
            return this.departmentCount
        },
        isChildrenLoaded() {
            return this.children?.length
        },
        isExpand() {
            return this.expandedKeys.includes(this.expandedKey)
        },
        expandedKey() {
            if(this.parentId)
                return `${this.organization.id}_${this.parentId}`
            return `${this.organization.id}`
        },
        isOrganizationsEmpty() {
            if(this.children)
                return !Object.keys(this.children).length
            return true
        },
        isDepartmentsEmpty() {
            if(this.childrenDepartments)
                return !Object.keys(this.childrenDepartments).length
            return true
        },
        nextOrganization() {
            if(this.isOrganizationsEmpty) 
                return true
            return this.children.next
        },
        nextDepartment() {
            if(this.isDepartmentsEmpty)
                return true
            return this.childrenDepartments.next
        },
        page() {
            const startPage = 1
            return this.children?.page || startPage
        },
        departmentsPage() {
            const startPage = 1
            return this.childrenDepartments?.page || startPage
        },
        params() {
            return {
                page: this.page,
                page_size: this.pageSize,
                page_name: this.pageName
            }
        },
        departmentsParams() {
            return {
                page: this.departmentsPage,
                page_size: this.pageSize,
                page_name: this.pageName
            }
        },
        infiniteId() {
            return `organization_${this.organization.id}_children_list`
        },
        showEdit() { 
            if(this.isDepartment)
                return this.parentPermissions?.edit?.availability
            return this.permissions?.edit?.availability
        }
    },
    mounted() {
        const firstOrganization = this.$store.state.organization.organizations.results[0]
        if(firstOrganization.id === this.organization.id) {
            eventBus.$on('open_first_organization', () => {
                this.selectKey(firstOrganization.id)
            })
        }
    },
    mounted() {
        this.checkOverflow()
    },
    updated() {
        this.checkOverflow()
    },
    methods: {
        ...mapActions({
            getOrganizationChildrenList: 'organization/getOrganizationChildrenList',
            getDepartmentList: 'organization/getDepartmentList',
            getActionInfo: 'organization/getActionInfo',
        }),
        checkOverflow() {
            const el = this.$refs.organizationName;
            if (!el) return;

            this.isOverflowing = el.scrollWidth > el.clientWidth;
        },
        isActive(key) {
            if(this.activeEl.length)
                return this.activeEl.includes(key)
            return false
        },
        async changeDepartmentPage(newPage) {
            this.$store.commit('organization/SET_DEPARTMENT_PAGE', { 
                page: newPage,
                parentId: this.organization.id
            })
            await this.getDepartments()
        },
        async selectKey(key, is_endpoint) {
            this.activeEl.splice(0)
            this.activeEl.push(key) 

            this.selectedKeys.splice(0)
            this.selectedKeys.push(key) 
        
            if(this.isExpand) {
                const foundIndex = this.expandedKeys.findIndex(key => this.expandedKey === key)
                this.expandedKeys.splice(foundIndex, 1)
            } else {
                this.expandedKeys.push(this.expandedKey)  

                if(this.hasChildren) {
                    await this.getOrganizationChildren()
                }
                if(this.hasDepartments) {
                    await this.getDepartments()
                }
            }
        },
        async getOrganizationChildren() {
            this.childrenLoading = true
            try {
                const organizations = await this.getOrganizationChildrenList({
                    params: this.params,
                    key: this.organization.id
                })
                const organizationsId = organizations.results.map(relation => relation.contractor.id)
                await this.getActionInfo({ payload: organizationsId })
            } catch(error) {
                console.error(error)
            } finally {
                this.childrenLoading = false
            }
        },
        async getDepartments() {
            this.departmentsLoading = true
            try {
                await this.getDepartmentList({
                    params: this.departmentsParams,
                    key: this.organization.id
                })
            } catch(error) {
                console.error(error)
                this.$message.error(this.$t('team.failed_to_get_data'))
            } finally {
                this.departmentsLoading = false
            }
        },
        // async getOrganizationChildren($state) {
        //     if(this.nextOrganization) {
        //         if(!this.childrenLoading) {
        //             this.childrenLoading = true
        //             try {
        //                 const params = {
        //                     ...this.params,
        //                     page_size: 'all'
        //                 }
        //                 const organizations = await this.getOrganizationChildrenList({
        //                     params: params,
        //                     key: this.organization.id
        //                 })
        //                 const organizationsId = organizations.results.map(organization => organization.id)
        //                 await this.getActionInfo({ payload: organizationsId })

        //                 if(this.nextOrganization) 
        //                     $state.loaded()
        //                 else
        //                     $state.complete()
        //             } catch(error) {
        //                 console.error(error)
        //             } finally {
        //                 this.childrenLoading = false
        //             }
        //         }
        //     } else {
        //         $state.complete()
        //     }
        // },
        
        editOrganization() {
            eventBus.$emit('edit_organization', {
                organization: this.organization,
                organizationParent: this.parentId,
                isDepartment: this.isDepartment
            })
        },
        async changeStructuresPage(newPage) {
            this.$store.commit('organization/SET_STRUCTURE_PAGE', { 
                page: newPage,
                parentId: this.organization.id
            })
            await this.getOrganizationChildren()
        },

        // Animations
        enter(el) {
            el.style.height = 'auto'
            const height = getComputedStyle(el).height
            el.style.height = 0
            setTimeout(() => {
                el.style.height = height
            })
        },
        afterEnter(el) {
            el.style.height = 'auto'
        },
        leave(el) {
            el.style.height = getComputedStyle(el).height
            setTimeout(() => {
                el.style.height = 0
            })
        },
        getRelationId(organization) {
            if(organization.relation_type) 
                return organization.id
            return null
        },
        getParentId(organization) {
            if(organization.contractor_parent) 
                return organization.contractor_parent.id
            return null
        },

    },
    beforeDestroy() {
        const firstOrganization = this.$store.state.organization?.organizations?.results?.[0]
        if(firstOrganization?.id === this.organization.id) {
            eventBus.$off('open_first_organization')
        }
    }
}
</script>

<style scoped lang="scss">
.mobile_border {
    border-left: 0;
    border-right: 0;
}
.mobile_border:not(:last-child) {
    border-bottom: 0;
}
.rotate-90 {
    transform: rotate(90deg);
}

.custom_border_color {
    border-color: var(--bgColor6);
}

.custom_bg {
    background-color: var(--bgColor2);
}
.custom_hover{
    transition: background-color 0.1s ease;
    &:hover {
        background-color: var(--bgColor2);
    }
}
.expand-enter-active, .expand-leave-active {
    transition: height 0.2s;
    overflow: hidden;
}
.custom_mb:not(:last-child) {
    margin-bottom: 1rem;
}
</style>
