<template>
    <div :class="!isMobile ? 'h-full flex flex-col' : 'h-full flex flex-col'">
        <div class="mb-2 flex flex-col-reverse xl:flex-row xl:items-center justify-between">
            <div :class="!isMobile ? 'flex' : 'flex float_add'">
                
                <div 
                    v-if="isMobile">
                    
                    <DropdownSort 
                        :model="model" 
                        :pageName ="pageName"
                        type="default">
                        <slot name="pageSorting"></slot>
                    </DropdownSort>
                    <div 
                        v-if="$slots.pageFilter"
                        class="filter_slot">
                        <slot name="pageFilter"></slot>
                    </div>
                    <a-button
                        type="primary"
                        flaticon
                        :shape="isMobile ? 'circle' : ''"
                        icon="fi-rr-plus"
                        size="large"
                        class="mr-2"
                        @click="addClients">
                        {{ !isMobile ? `Добавить ${isLead ? 'лид' : 'клиента'}` :''}}
                    </a-button>
                </div>

                <div 
                    v-else 
                    class="flex">
                    <a-button
                        type="primary"
                        flaticon
                        icon="fi-rr-plus"
                        size="large"
                        class="mr-2"
                        @click="addClients">
                        {{ !isMobile ? `Добавить ${isLead ? 'лид' : 'клиента'}` :''}}
                    </a-button>
                    <div 
                        v-if="$slots.pageFilter"
                        class="filter_slot">
                        <slot name="pageFilter"></slot>
                    </div>
                </div>
                
            </div>
            <div :class="!isMobile && 'mb-4 xl:mb-0'">
                <span
                    class="text-lg text_hover cursor-pointer mr-2"
                    :class="(contractorsType === 'contractors') && 'blue_color font-semibold'" 
                    @click="changeContractorsType('contractors')">
                    Клиенты
                </span>
                <span 
                    class="text-lg text_hover cursor-pointer"
                    :class="(contractorsType === 'leads') && 'blue_color font-semibold'"
                    @click="changeContractorsType('leads')">
                    Лиды
                </span>
            </div>
        </div>
        <div class="mb-4 flex justify-between">
            <div class="flex">
                <template v-if="isTable && !isMobile">
                    <SettingsButton
                        class="mr-2"
                        :pageName="pageName" />
                </template>
                <DropdownSort
                    v-if="!isMobile"
                    :model="model" 
                    :pageName ="pageName"
                    type="default" />
            </div>
            <GridType v-if="!isMobile" />
        </div>
        <component 
            :key="contractorsType"
            :is="viewWidget"
            :pageName="pageName">
        </component>
        <ClientForm
            v-show="false"
            ref="widgetClientForm"
            class="ml-2"
            :contractor="contractor"
            :pageName="pageName"
            :mainForm={}
            :item="item"
            :contractorsType="contractorsType" />
    </div>
</template>

<script>
import ClientForm from '@apps/Orders/views/CreateOrder/widgets/OrderType/ClientForm.vue'
import SettingsButton from '@/components/TableWidgets/SettingsButton'

import eventBus from '@/utils/eventBus.js'
import DropdownSort from '../DropdownSort.vue'
import GridType from '../GridType.vue'
import { mapState } from 'vuex'
export default {
    components: {
        ClientForm,
        SettingsButton,
        DropdownSort,
        GridType,
    },
    props: {
        pageName: {
            type: String,
            required: true
        }
    },
    data() {
        return {
            contractor: '',
            item: {},
            formInfoURL : {
                'contractors': 'catalogs/contractors/form_info/',
                'leads': 'catalogs/leads/form_info/',
            }
        }
    },
    computed: {
        ...mapState({
            models: state => state.contractors.models,
            contractorsType: state => state.contractors.contractorsType,
            listType: state => state.contractors.activeGridType,
            isMobile: state => state.isMobile,
        }),
        viewWidget() {
            const type = this.listType
            if(this.isMobile)
                return () => import('./ContractorsViewGrid.vue')

            return () => import(`./${type}.vue`)
                .then(module => {
                    return module
                })
                .catch(e => {
                    console.log('error')
                    return import(`./NotWidget.vue`)
                })
        },
        model() {
            return this.models[this.contractorsType]
        },
        isLead() {
            return this.contractorsType === 'leads'
        },
        isTable() {
            return true
        }
    },
    mounted() {
        eventBus.$on('need_update_contractor_list', () => {
            this.$store.commit('dashboard/CLEAR_CONTRACTORS_LIST')
            this.paginatorNext = true
            this.paginatorPageNumber = 1
        })
        eventBus.$on('edit_contractor', async (contractorID) => {
            await this.getForm()
            this.contractor = contractorID
            this.$nextTick(() => {
                if(this.$refs?.['widgetClientForm']) {
                    this.$refs['widgetClientForm'].openEdit()
                }
            })
        })
        eventBus.$on('need_update_contractor', (data) => {
            this.$store.commit('contractors/UPDATE_CONTRACTOR', { contractor: data })
        })
        eventBus.$on('need_add_contractor', (data) => {
            this.$store.commit('contractors/ADD_CONTRACTOR', { newContractor: data })
        })
        eventBus.$on('lead_convert_to_contractor', (data) => {
            this.$store.commit('contractors/ADD_ONLY_CONTRACTOR', { newContractor: data })
        })
    },
    beforeDestroy() {
        eventBus.$off('edit_contractor')
        eventBus.$off('need_update_contractor_list')
        eventBus.$off('need_update_contractor')
        eventBus.$off('need_add_contractor')
        eventBus.$off('lead_convert_to_contractor')
    },
    methods: {
        changeContractorsType(contractorsType) {
            this.$store.state.contractors.contractorsType = contractorsType
            localStorage.setItem('contractorsType', contractorsType)
        },
        async addClients() {
            await this.getForm()
            this.$nextTick(() => {
                if(this.$refs?.['widgetClientForm']) {
                    this.$refs['widgetClientForm'].openModal()
                }
            })
        },
        async getForm() {
            try {
                let url = this.formInfoURL[this.contractorsType]

                const { data } = await this.$http.get(url)
                if (data) {
                    this.item = data
                }
            } catch(error) {
                console.error(error)
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.text_hover {
    transition: color 0.15s ease-in;
    &:hover {
        color: var(--blue);
    }
}
</style>