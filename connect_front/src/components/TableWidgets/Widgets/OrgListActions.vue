<template>
    <a-dropdown 
        :trigger="['click']" 
        @visibleChange="visibleChange"
        :getPopupContainer="getPopupContainer">
        <a-button 
            type="ui" 
            ghost 
            flaticon 
            shape="circle"
            :loading="loading"
            size="small"
            icon="fi-rr-menu-dots-vertical"
            :destroyPopupOnHide="false" />
        <a-menu slot="overlay">
            <a-spin v-if="loading" size="small" class="w-full" />
            <template v-else>
                <a-menu-item key="open" class="flex items-center" @click="openOrg()">
                    <i class="fi fi-rr-link-alt mr-2" />
                    {{ $t('open') }}
                </a-menu-item>
                <a-menu-item
                    v-if="actions && actions.manage && actions.manage.availability && !recordIsDepartment"
                    key="copy-id"
                    class="flex items-center"
                    @click="orgCopyId()">
                    <i class="fi fi-rr-copy-alt mr-2" />
                    {{ $t('team.copy_identifier_tooltip') }}
                </a-menu-item>
                <a-menu-item
                    v-if="actions && actions.manage && actions.manage.availability && !recordIsDepartment"
                    key="invite-subdivision"
                    class="flex items-center"
                    @click="openOrganizationInvite()">
                    <i class="fi fi-rr-plus mr-2" />
                    {{ $t('team.invite_subdivision_tooltip') }}
                </a-menu-item>
                <a-menu-item v-if="actions && actions.edit && actions.edit.availability" key="edit" class="flex items-center" @click="editOrg()">
                    <i class="fi fi-rr-edit mr-2" />
                    {{ $t('edit') }}
                </a-menu-item>
            </template>
        </a-menu>
    </a-dropdown>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'
export default {
    props: {
        record: {
            type: Object,
            required: true
        },
        text: {
            type: [Object, Number, String],
        },
        pageName: {
            type: String,
            default: ''
        },
        colParams: {
            type: Object,
            default: () => null
        }
    },
    data() {
        return {
            loading: false,
            listLoading: false,
            actions: null,
            statusList: [],
            listModel: "catalogs.ContractorModel",
        }
    },
    computed: {
        recordIsDepartment() {
            return Boolean(this.record?.is_department)
        }
    },
    methods: {
        orgCopyId() {
            try {
                navigator.clipboard.writeText(this.record.id)
                this.$message.success(this.$t('team.organization_id_copied'))
            } catch(error) {
                console.error(error)
                this.$message.error(this.$t('team.error'))
            }
        },
        openOrganizationInvite() {
            eventBus.$emit('invite_organization', { organization: this.record, isSubdivision: false })
        },
        editOrg() {
            const organizationParent = this.record?.parent_expand
                || this.record?.contractor_parent?.id
                || this.record?.contractor_parent
                || null
            const isDepartment = this.recordIsDepartment

            eventBus.$emit('edit_organization', {
                organization: this.record,
                organizationParent,
                organizationType: organizationParent && !isDepartment ? 'subdivision' : null,
                isDepartment
            })
        },
        openOrg() {
            const query = {
                organization_drawer: 'detail',
                organization_id: this.record.id
            }

            if (this.record?.parent_expand) {
                query.parent_id = this.record.parent_expand
            }

            this.$router.push({ query })
        },
        getPopupContainer() {
            return this.colParams.getPopupContainer()
        },
        async getActions() {
            if(!this.actions) {
                try {
                    this.loading = true
                    this.listLoading = true
                    const { data } = await this.$http.get(`/users/my_organizations/${this.record.id}/action_info/`)
                    if(data?.actions) {
                        this.actions = data.actions
                    }
                } catch(error) {
                    errorHandler({error, show: false})
                } finally {
                    this.loading = false
                    this.listLoading = false
                }
            }
        },
        visibleChange(visible) {
            if(visible) {
                this.getActions()
            }
        }
    }
}
</script>
