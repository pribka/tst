<template>
    <div class="form">
        <a-form-model-item 
            v-if="item.showContractor"
            ref="contractor" 
            :label="isCrmContractOrder ? 'Организация учета' : 'Клиент'"
            class="form_item"
            prop="contractor"
            :rules="{
                required: true,
                message: 'Обязательно для заполнения',
                trigger: 'blur'
            }">
            <div class="flex items-center">
                <a-select 
                    size="large"
                    style="width:100%;"
                    :loading="typeLoader"
                    show-search
                    :filter-option="false"
                    v-model="form.contractor"
                    :getPopupContainer="getPopupContainer"
                    class="contractor_select"
                    @change="selectContractor"
                    @popupScroll="getDataScrollHandler"
                    @search="contractorSearchHandler">
                    <a-select-option 
                        v-for="item in contractorList" 
                        :value="item.id" 
                        :key="item.id">
                        {{ item.string_view }}
                    </a-select-option>
                    <div 
                        slot="notFoundContent" 
                        class="flex justify-center">
                        <a-empty 
                            v-if="!typeLoader" 
                            :description="$t('no_data')" />
                    </div>
                    <div 
                        slot="dropdownRender" 
                        slot-scope="items">
                        <v-nodes :vnodes="items" />
                        <div 
                            v-if="typeLoader" 
                            class="flex justify-center">
                            <a-spin size="small" />
                        </div>
                    </div>
                </a-select>
                <component
                    ref="clientForm"
                    class="ml-2"
                    :updateContractor="updateContractor"
                    :contractor="form.contractor"
                    :is="clientFormWidget"
                    :mainForm="form"
                    :item="item" />
            </div>
            <div 
                v-if="clientFormWidget" 
                class="flex mt-2">
                <span 
                    class="blue_color cursor-pointer flex items-center text-xs"
                    @click="addClients()">
                    <a-icon 
                        type="plus" 
                        class="mr-1" />
                    Добавить клиента
                </span>
            </div>
        </a-form-model-item>
        <template v-if="item.showContractorMember">
            <a-form-model-item 
                v-show="visibleContractorMember"
                ref="contractor_member" 
                :label="isCrmContractOrder ? 'Учетный контрагент' : 'Контрагент'"
                class="form_item"
                prop="contractor_member"
                :rules="{
                    required: true,
                    message: 'Обязательно для заполнения',
                    trigger: 'blur'
                }">
                <a-select 
                    size="large"
                    :loading="memberLoader"
                    v-model="form.contractor_member">
                    <a-select-option 
                        v-for="item in memberList" 
                        :value="item.id" 
                        :key="item.id">
                        {{ item.string_view }}
                    </a-select-option>
                </a-select>
            </a-form-model-item>
        </template>
        <template v-if="item.showContract">
            <a-form-model-item 
                v-show="visibleContract"
                ref="contract" 
                label="Соглашение"
                class="form_item"
                help="При изменении соглашения цена в заказе будет пересчитана"
                prop="contract"
                :rules="contractRules">
                <a-select 
                    size="large"
                    :loading="contractLoading"
                    v-model="form.contract"
                    @change="changeContract($event, contractList)">
                    <a-select-option 
                        v-for="item in contractList" 
                        :value="item.code" 
                        :key="item.id">
                        {{ item.string_view }}
                    </a-select-option>
                </a-select>
            </a-form-model-item>
        </template>
    </div>
</template>

<script>
import { mapState } from 'vuex'
import eventBus from '@/utils/eventBus.js'
let timer;
export default {
    components: {
        VNodes: {
            functional: true,
            render: (h, ctx) => ctx.props.vnodes,
        }
    },
    props: {
        form: {
            type: Object,
            required: true
        },
        changeContract: {
            type: Function,
            default: () => {}
        },
        // setOrderFormCalculated: {
        //     type: Function,
        //     default: () => {}
        // },
        item: {
            type: Object,
            required: true
        },
        edit: {
            type: Boolean,
            default: false
        },
        isOrderDrawer: {
            type: Boolean,
            default: false
        },
        injectContractorFilter: {
            type: Object,
            default: () => {}
        },
        sourceCustomerContractId: {
            type: String,
            default: ''
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        visibleOrderType() {
            if(this.contractorList?.length > 1)
                return true
            else
                return false
        },
        visibleContract() {
            if(this.isCrmContractOrder) {
                return false
            }
            return !(this.contractList?.length === 1)
        },
        visibleContractorMember() {
            return !(this.memberList?.length === 1)
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        clientFormWidget() {
            if(this.item.clientForm && this.user && this.user.has_full_access_to_order_editing)
                return () => import('./ClientForm.vue')
            else
                return null
        },
        isCrmContractOrder() {
            return Boolean(this.sourceCustomerContractId)
        },
        contractRules() {
            if(this.isCrmContractOrder) {
                return {
                    required: false,
                    trigger: 'blur'
                }
            }
            return {
                required: true,
                message: 'Обязательно для заполнения',
                trigger: 'blur'
            }
        }
    },
    data() {
        return {
            contractorList: [],
            contractList: [],
            memberList: [],
            typeLoader: false,
            contractorLoading: false,
            contractLoading: false,
            memberLoader: false,
            clientNext: true,
            clientPage: 1,
            contractorSearch: ''
        }
    },
    watch: {
        'form.contractor'() {
            this.getMember()
            this.getContract()
        }
    },
    created() {

        if(this.edit || this.isOrderDrawer) {
            if(this.form.contractor?.id) {
                this.form.contractor = this.form.contractor.id
            }
            if(this.form.contractor_member?.id) {
                this.form.contractor_member = this.form.contractor_member.id
            }
            if(this.form.contract?.id) {
                this.form.contract = this.form.contract.id
            }
        }
        this.ensureCrmDefaultContract()

        this.getContractor()
    },
    methods: {
        ensureCrmDefaultContract() {
            if(this.isCrmContractOrder && !this.form.contract) {
                this.$set(this.form, 'contract', 'default')
            }
        },
        getPopupContainer() {
            return document.querySelector('.form')
        },
        contractorSearchHandler(val) {
            clearTimeout(timer)
            timer = setTimeout(() => {
                this.contractorSearch = val
                this.contractorList = []
                this.clientNext = true
                this.getContractor()
            }, 600)
        },
        getDataScrollHandler(event) {
            const target = event.target
            if(target.scrollTop + target.offsetHeight >= target.scrollHeight) {
                this.clientPage = this.clientPage + 1
                this.getContractor()
            }
        },
        async getContractor(contractor=null) {
            let params

            params = {
                model: 'catalogs.ContractorModel',
                ordering: '-created_at',
                page_size: 10,
                page: this.clientPage,
                first: this.form?.contractor,
                filters: {
                    "is_carrier": false,
                    ...this.injectContractorFilter
                },
                search: this.contractorSearch
            }
            
            if((!this.typeLoader && this.clientNext)) {
                try {
                    this.typeLoader = true
                    const { data } = await this.$http.get('/app_info/filtered_select_list/', {
                        params
                    })
                    if(data)
                        this.clientNext = data.next
            
                    if(data?.filteredSelectList?.length) {
                        this.contractorList = this.contractorList.concat(data.filteredSelectList)
                        if(!this.form.contractor) {
                            this.form.contractor = this.contractorList[0].id
                            eventBus.$emit('contractor_is_change')
                        }
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.typeLoader = false
                }
            }
        },
        updateContractorList() {
            this.contractorList = []
            this.clientPage = 1
            this.clientNext = true
            this.contractorSearch = ''
            this.getContractor()
        },
        selectContractor () {
            eventBus.$emit('contractor_is_change')
            eventBus.$emit('update_address_list')
            this.updateContractorList()
            // this.setOrderFormCalculated(false)
        },
        updateContractor(data, edit = false) {
            if(edit) {
                const index = this.contractorList.findIndex(f => f.id === data.id)
                if(index !== -1) {
                    this.contractorList[index].string_view = data.name
                }
            } else {
                this.contractorList.unshift({
                    code: data.id,
                    id: data.id,
                    string_view: data.name
                })
                this.form.contractor = data.id
                this.memberList = []
                this.form.contractor_member = null
                this.form.contract = null
                this.contractList = []

                this.getMember()
                this.getContract()
            }
        },
        addClients() {
            this.$nextTick(() => {
                if(this.$refs?.['clientForm']) {
                    this.$refs['clientForm'].openModal()
                }
            })
        },
        async getMember() {
            try {
                this.memberLoader = true
                const { data } = await this.$http.get('/app_info/filtered_select_list/', {
                    params: {
                        model: 'catalogs.ContractorMemberModel',
                        search: this.form.contractor
                    }
                })
                
                if(data?.filteredSelectList?.length) {
                    this.memberList = data.filteredSelectList
                    this.form.contractor_member = this.memberList[0].id
                } else {
                    this.memberList = []
                    this.form.contractor_member = null
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.memberLoader = false
            }
        },
        async getContract() {
            try {
                this.contractLoading = true
                let params = {
                    model: 'catalogs.ContractModel',
                    search: this.form.contractor
                        
                }
                const { data } = await this.$http.get('/app_info/filtered_select_list/', { params })
                if(data?.filteredSelectList?.length) {
                    this.contractList = data.filteredSelectList
                    this.form.contract = this.contractList[0].code
                } else {
                    this.contractList = []
                    this.form.contract = this.isCrmContractOrder ? 'default' : null
                }
            } catch(e) {
                console.log(e)
            }
            finally{
                this.contractLoading = false
            }
        }
    }
}
</script>
