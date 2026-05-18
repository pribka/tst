<template>
    <div>
        <a-dropdown 
            :destroyPopupOnHide="true"
            :loading="loading"
            @visibleChange="visibleChange">
            <a-button 
                icon="menu" 
                type="link" />
            <a-menu slot="overlay">
                <template v-if="actionsLoading">
                    <a-menu-item 
                        key="menu_loader"
                        class="flex justify-center">
                        <a-spin size="small" />
                    </a-menu-item>
                </template>
                <template v-else>
                    <template v-if="permissions?.actions?.edit?.availability">
                        <a-menu-item 
                            key="edit"
                            class="flex items-center"
                            @click="openEdit('edit')">
                            <i class="fi fi-rr-edit mr-2"></i>
                            Редактировать
                        </a-menu-item>
                    </template>
                    <template v-if="permissions?.actions?.set_archive?.availability">
                        <a-menu-item 
                            key="setArchive"
                            class="flex items-center"
                            @click="setArchive()">
                            <i class="fi fi-rr-archive mr-2"></i>
                            Архивировать
                        </a-menu-item>
                    </template>
                    <template v-if="permissions?.actions?.convert_to_contractor?.availability">
                        <a-menu-item 
                            key="convert_to_contractor"
                            class="flex items-center"
                            @click="convert_to_contractor('edit')">
                            <i class="fi fi-rr-user-add mr-2"></i>
                            Конвертировать в клиента
                        </a-menu-item>
                    </template>
                </template>
            </a-menu>
        </a-dropdown>
        <ClientForm
            v-show="false"
            ref="widgetClientForm"
            class="ml-2"
            :mainForm={}
            :item="item" />
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import ClientForm from '@apps/Orders/views/CreateOrder/widgets/OrderType/ClientForm.vue'

import { mapActions, mapState } from 'vuex'

export default {
    components: {
        ClientForm,
    },
    props: {
        record: {
            type: Object,
            required: true
        },
        pageName: {
            type: String,
            default: null
        }
    },
    data() {
        return {
            actionsLoading: true,
            permissions: [],
            loading: false,
            item: {},
            contractor: {},
        }
    },
    computed: {
        ...mapState({
            contractorsType: state => state.contractors.contractorsType,
            activeGridType: state => state.contractors.activeGridType
        }),
    },
    methods: {
        async setArchive() {
            let payload = {}
            if(this.contractorsType === 'contractors') {
                payload = {
                    is_archived: true,
                    inn: this.record.inn,
                    registered: this.record.registered,
                    email: this.record.email,
                }
            }
            if(this.contractorsType === 'leads') {
                payload = {
                    is_archived: true,
                }
            }
            try {
                this.loading = true

                const { data } = await this.$http.put(
                    `/catalogs/${this.contractorsType}/${this.record.id}/`, payload
                )
                if(data) {
                    this.$store.commit('contractors/UPDATE_CONTRACTOR', { contractor: data })

                    eventBus.$emit(`table_row_${this.pageName}`, {
                        action: 'update',
                        row: data
                    })
                } 
            } catch(e) {
                this.$message.error(e)
                console.log(e)
            } finally {
                this.loading = false
            }
        },
        async convert_to_contractor() {
            let newContractor = {}
            try {
                const { data } = await this.$http.get('catalogs/contractors/form_info/')
                if (data) {
                    this.item = data
                    newContractor = data.clientForm.form
                }
            } catch(error) {
                console.error(error)
            }
            newContractor.name = this.record.company_name,
            newContractor.phone = this.record.phone,
            newContractor.registered = true,
            newContractor.email = this.record.email,
            newContractor.first_name = this.record.name,
            newContractor.source_lead = this.record.id,
            this.$nextTick(() => {
                if(this.$refs?.['widgetClientForm']) {
                    this.$refs['widgetClientForm'].createContractorFromLead(newContractor, this.record.id)
                }
            })
        },
        async visibleChange(visible) {
            if(visible) {
                this.actionsLoading = true
                await this.$http(`catalogs/${this.contractorsType}/${this.record.id}/action_info/`)
                    .then(({ data }) => {
                        this.permissions = data
                    })
                    .catch(error => console.error(error))
                this.actionsLoading = false
            }
            
        },
        openEdit(mode) {
            eventBus.$emit('edit_contractor', this.record.id)
        },
    },
    mounted() {
        eventBus.$on('set_arhive_to_lead', (leadID) => {
            if(leadID === this.record.id) {
                this.setArchive()
            }
        })
    },
    beforeDestroy() {
        eventBus.$off('set_arhive_to_lead')
    }
}
</script>