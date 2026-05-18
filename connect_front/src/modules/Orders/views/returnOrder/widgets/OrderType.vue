<template>
    <div class="form">
        <a-form-model-item 
            ref="contractor" 
            label="Клиент"
            class="form_item"
            prop="contractor"
            :rules="{
                required: true,
                message: 'Обязательно для заполнения',
                trigger: 'blur'
            }">
            <a-select 
                size="large"
                :loading="typeLoader"
                v-model="form.contractor">
                <a-select-option 
                    v-for="item in contractorList" 
                    :value="item.id" 
                    :key="item.id">
                    {{ item.string_view }}
                </a-select-option>
            </a-select>
        </a-form-model-item>
        <a-form-model-item 
            ref="contractor_member" 
            label="Контрагент"
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
        <a-form-model-item 
            ref="contract" 
            label="Соглашение"
            class="form_item"
            help="При изменении соглашения цена в заказе будет пересчитана"
            prop="contract"
            :rules="{
                required: true,
                message: 'Обязательно для заполнения',
                trigger: 'blur'
            }">
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
    </div>
</template>

<script>
export default {
    props: {
        form: {
            type: Object,
            required: true
        },
        changeContract: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        visibleOrderType() {
            if(this.contractorList?.length > 1)
                return true
            else
                return false
        },
        isMobile() {
            return this.$store.state.isMobile
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
            memberLoader: false
        }
    },
    watch: {
        'form.contractor'() {
            this.getMember()
            this.getContract()
        }
    },
    created() {
        this.getContractor()
    },
    methods: {
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
        async getContractor() {
            try {
                this.typeLoader = true
                const { data } = await this.$http.get('/app_info/filtered_select_list/', {
                    params: {
                        model: 'catalogs.ContractorModel',
                        search: 'my_contractors',
                        ordering: '-created_at'
                    }
                })
                
                if(data?.filteredSelectList?.length) {
                    this.contractorList = data.filteredSelectList
                    this.form.contractor = this.contractorList[0].id
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.typeLoader = false
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
                    this.form.contract = null
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