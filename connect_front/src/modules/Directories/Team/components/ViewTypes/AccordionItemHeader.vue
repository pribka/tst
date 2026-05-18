<template>
    <div 
        class="-mt-2 flex justify-between flex-wrap items-center">
        <div class="mt-2 mr-4 flex items-center">
            <span class="mr-2 font-semibold">{{ $t('team.director_label') }}</span>
            <Profiler
                v-if="organization?.director"
                hideSupportTag
                :user="organization.director" />
            <span v-else>
                {{ $t('Not specified') }}
            </span>
        </div>
        <div 
            class="mt-2 flex items-center ml-auto">
            <template v-if="canManage && !isDepartment">
                <a-button
                    v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }"
                    :content="$t('team.copy_identifier_tooltip')"
                    class="mr-2"
                    type="ui"
                    shape="circle"
                    flaticon
                    icon="fi-rr-copy-alt"
                    @click="orgCopyId()">
                </a-button>
                <a-button
                    v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }"
                    :content="$t('team.invite_subdivision_tooltip')"
                    type="primary"
                    shape="circle"
                    @click="openOrganizationInvite"
                    ghost
                    class="flex items-center justify-center">
                    <i class="fi fi-rr-plus"></i>
                </a-button>
            </template>
            <template v-if="canDelete">
                <a-button
                    v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }"
                    :content="labelDelete"
                    type="danger"
                    shape="circle"
                    ghost
                    @click="openDeleteModal"
                    class="ml-2 flex items-center justify-center">
                    <i :class="deleteIcon"></i>
                </a-button>
            </template>
        </div>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { mapState, mapActions } from 'vuex'
import { errorHandler } from '@/utils/index.js'
export default {
    props: {
        organization: {
            type: Object,
            required: true,
        },
        relationId: {
            type: String,
            default: null
        },
        parentId: {
            type: String,
            default: null
        },
        isDepartment: {
            type: Boolean,
            default: false
        },
    },
    computed: {
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
        canManage() {
            return this.permissions?.manage?.availability
        },
        canDelete() {
            if(this.isDepartment)
                return this.parentPermissions?.manage?.availability
            // return this.permissions?.manage?.availability
            return false
        },
        labelDelete() {
            if(this.isDepartment)
                return this.$t('team.delete_department_from_structure')
            if(this.relationId)
                return this.$t('team.delete_node_from_structure')
            return this.$t('team.delete_organization')
        },
        deleteIcon() {
            if(this.relationId)
                return 'fi fi-rr-minus'
            return 'fi fi-rr-trash'
        }
    },
    methods: {
        ...mapActions({
            deleteDepartment: 'organization/deleteDepartment',
            deleteOrganization: 'organization/deleteOrganization',
        }),
        orgCopyId() {
            try {
                navigator.clipboard.writeText(this.organization.id)
                this.$message.success(this.$t('team.organization_id_copied'))
            } catch(error) {
                console.error(error)
                this.$message.error(this.$t('team.error'))
            }
        },
        openOrganizationInvite() {
            eventBus.$emit('invite_organization', { organization: this.organization, isSubdivision: false })
        },
        openOrgInvite() {
            eventBus.$emit('invite_organization', this.organization)
        },
        untieOrganization() {
            try {
                this.$http.put(`/users/my_organizations/relations/${this.relationId}/update/`, {
                    contractor_parent: null
                })
                this.$store.commit('organization/UNTIE_ORGANIZATION', {
                    parentId: this.parentId,
                    relationId: this.relationId
                })
            } catch(error) {
                errorHandler({error})
            }
        },
        editOrganization() {
            eventBus.$emit('edit_organization', {
                organization: this.organization,
                organizationParent: this.parentId,
                isDepartment: this.isDepartment
            })
        },
        openDeleteModal() {
            const self = this
            let title = this.$t('team.confirm_delete_prefix')
            if(this.relationId) {
                title += this.$t('team.node_from_structure')
            } else if(this.isDepartment) {
                title += this.$t('team.department_question')
            } else {
                title += this.$t('team.organization_question')
            }
            this.$confirm({
                title: title,
                okText: this.$t('team.yes'),
                cancelText: this.$t('team.no'),
                onOk() {
                    if(self.relationId) {
                        self.untieOrganization()
                    } else if(self.isDepartment) {
                        self.deleteDepartment({
                            departmentId: self.organization.id,
                            parentId: self.parentId
                        })
                    } else {
                        self.deleteOrganization({
                            organizationId: self.organization.id,
                            parentId: self.parentId
                        })
                    }
                }
            })
        }
    }
}
</script>