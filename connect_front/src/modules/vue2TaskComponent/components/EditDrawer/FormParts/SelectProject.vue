<template>
    <div>
        <a-form-model-item
            v-if="formInfo.organization"
            :rules="formInfo.organization.rules"
            :label="formInfo.organization.title"
            prop="organization">
            <OrgSelect 
                inputType="defaultInput"
                :opnUserSetting="opnUserSetting"
                v-model="value.organization" />

            <!-- <OrganizationsDrawer
                v-model="value.organization"
                :defaultActiveFirstOption="!value.organization && !edit"
                :title="
                    formInfo.organization.drawerTitle ||
                        $t('task.select_organization')
                "
                inputSize="large"/> -->
        </a-form-model-item>

        <a-form-model-item
            v-if="formInfo.project"
            :rules="formInfo.project.rules"
            :label="formInfo.project.title"
            prop="project">
            <ProjectSelect 
                inputType="defaultInput"
                ref="projectSelect"
                v-model="value.project"
                @change="onProjectChange" />
            <!-- <ProjectDrawer
                v-model=""
                :selectProject="selectProject"
                :title="
                    formInfo.project.drawerTitle ||
                        $t('task.select_project')
                "
                inputSize="large"/> -->
        </a-form-model-item>
        <a-form-model-item
            v-if="formInfo.contract || value.project"
            :rules="(formInfo.contract && formInfo.contract.rules) || null"
            :label="(formInfo.contract && formInfo.contract.title) || 'Контракт'"
            prop="contract">
            <ContractSelect
                :key="`task_contract_select_${contractSelectKey}_${resolvedProjectId || 'empty'}`"
                :apiUrl="getContractSelectApiUrl()"
                :params="getContractSelectParams()"
                :value="value.contract"
                :disabled="!resolvedProjectId"
                listObject="filteredSelectList"
                inputType="defaultInput"
                :title="contractPlaceholder"
                valueKey="id"
                labelKey="string_view"
                searchKey="search"
                :showSearch="true"
                :showRecent="false"
                :showClear="true"
                :showArrow="true"
                :initList="Boolean(resolvedProjectId)"
                :useSearchApi="false"
                :placeholder="contractPlaceholder"
                @change="onContractChange" />
        </a-form-model-item>
        <a-form-model-item
            v-if="value.contract || customerCardOptions.length"
            :label="$t('task.client')"
            prop="customer_card">
            <DSelect
                :key="`task_customer_card_select_${customerCardSelectKey}`"
                :value="resolvedCustomerCardId"
                class="w-full"
                size="large"
                :initList="false"
                :showSearch="false"
                :useSearchApi="false"
                :allowClear="true"
                :disabled="!value.contract"
                :initOptionList="customerCardOptions"
                valueKey="id"
                labelKey="name"
                :placeholder="$t('task.client')"
                @change="onCustomerCardChange" />
        </a-form-model-item>

        <a-form-model-item
            v-if="formInfo.workgroup"
            :rules="formInfo.workgroup.rules"
            :label="formInfo.workgroup.title"
            class="mb-0"
            prop="workgroup">
            <GroupSelect 
                inputType="defaultInput"
                v-model="value.workgroup"
                @change="groupChange"  /> 
        </a-form-model-item>

        <a-form-model-item
            v-if="formInfo.parent"
            :rules="formInfo.parent.rules"
            :label="formInfo.parent.title"
            style="margin-bottom: 0px;"
            prop="parent">
            <div
                class="popover_input ant-input flex items-center relative ant-input-lg truncate"
                :class="changeParentDisabled && 'ant-input-disabled'">
                <a-tooltip
                    v-if="value.parent"
                    destroyTooltipOnHide
                    :title="value.parent.name"
                    class="mr-2 truncate">
                    <a-tag
                        color="blue"
                        class="tag_block truncate"
                        @click="openSubtaskSelection">
                        {{ value.parent.name }}
                    </a-tag>
                </a-tooltip>
                <a-button
                    @click="openSubtaskSelection"
                    type="link"
                    :icon="!value.parent && 'plus'"
                    class="px-0">
                    {{
                        value.parent ? $t("task.change") : $t("task.select")
                    }}
                </a-button>
                <a-button
                    v-if="value.parent"
                    @click="selectParentTask()"
                    type="link"
                    icon="close-circle"
                    class="px-0 text-current remove_parent"/>
            </div>
        </a-form-model-item>

    </div>
</template>

<script>
// import ProjectDrawer from "../../ProjectDrawer.vue";
// import OrganizationsDrawer from "../../OrganizationsDrawer.vue";
// import WorkGroupDrawer from "../../WorkGroupDrawer.vue";
export default {
    components: { 
        ProjectSelect: () => import("@apps/DrawerSelect/ProjectSelect.vue"), 
        ContractSelect: () => import("@apps/DrawerSelect/ContractSelect.vue"),
        DSelect: () => import("@apps/DrawerSelect/Select.vue"),
        // OrganizationsDrawer, 
        GroupSelect: () => import("@apps/DrawerSelect/GroupSelect.vue"),   
        OrgSelect: () => import("@apps/DrawerSelect/OrgSelect.vue")
    },
    props: {
        value: { // form
            type: Object,
            required: true
        },
        formInfo: {
            type: Object,
            required: true
        },
        edit: {
            type: Boolean,
            required: true
        },
        selectProject: {
            type: Function,
            required: true
        },
        getContractSelectApiUrl: {
            type: Function,
            default: () => '/customer_contracts/analytics_keys/by_project/'
        },
        getContractSelectParams: {
            type: Function,
            default: () => ({})
        },
        contractSelectKey: {
            type: [Number, String],
            default: 0
        },
        groupChange: {
            type: Function,
            required: true
        },
        openSubtaskSelection: {
            type: Function,
            required: true
        },
        selectParentTask: {
            type: Function,
            required: true
        },
        changeParentDisabled: {
            type: Boolean,
            default: false
        },
        opnUserSetting: {
            type: Function,
            required: true
        }

    },
    computed: {
        resolvedProjectId() {
            if (!this.value?.project) return null
            return typeof this.value.project === 'object'
                ? this.value.project.id || null
                : this.value.project
        },
        resolvedCustomerCardId() {
            if (!this.value?.customer_card) return null
            return typeof this.value.customer_card === 'object'
                ? this.value.customer_card.id || null
                : this.value.customer_card
        },
        contractPlaceholder() {
            return (this.formInfo.contract && this.formInfo.contract.title) || 'Контракт'
        }
    },
    data() {
        return {
            customerCardOptions: [],
            customerCardSelectKey: Date.now()
        }
    },
    watch: {
        'value.contract': {
            immediate: true,
            handler(contract) {
                this.syncCustomerCardOptions(contract, true)
            }
        }
    },
    methods: {
        onProjectChange(project) {
            this.$set(this.value, 'contract', null)
            this.$set(this.value, 'customer_card', null)
            this.customerCardOptions = []
            this.customerCardSelectKey = Date.now()
            this.selectProject(project)
        },
        async syncCustomerCardOptions(contract, preserveCurrent = false) {
            const contractId = contract && (typeof contract === 'object' ? contract.id : contract)
            this.customerCardOptions = []
            this.customerCardSelectKey = Date.now()

            if (!contractId) {
                this.$set(this.value, 'customer_card', null)
                return
            }

            try {
                const { data } = await this.$http.get(`/customer_contracts/${contractId}/service_cards/`, {
                    params: { page: 1, page_size: 100 }
                })
                const results = Array.isArray(data?.results) ? data.results : []
                this.customerCardOptions = results

                const currentId = this.resolvedCustomerCardId
                if (results.length === 1) {
                    this.$set(this.value, 'customer_card', results[0].id)
                } else if (!preserveCurrent || !results.some(item => item.id === currentId)) {
                    this.$set(this.value, 'customer_card', null)
                }
            } catch (error) {
                this.$set(this.value, 'customer_card', null)
            } finally {
                this.customerCardSelectKey = Date.now()
            }
        },
        async onContractChange(contract) {
            this.$set(this.value, 'contract', contract || null)
            await this.syncCustomerCardOptions(this.value.contract)
        },
        onCustomerCardChange(customerCardId) {
            this.$set(this.value, 'customer_card', customerCardId || null)
        },
        projectSelect() {
            this.$nextTick(() => {
                if(this.$refs.projectSelect)
                    this.$refs.projectSelect.openSelect()
            })
        }
    }
}
</script>
