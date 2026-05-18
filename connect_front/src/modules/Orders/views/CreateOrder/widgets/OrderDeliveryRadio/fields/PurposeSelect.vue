<template>
    <!-- comment -->
    <div class="delivery_details" :id="`field_${field.key}`">
        <a-form-model-item
            :ref="field.key"
            :label="field.name"
            class="form_item"
            :prop="field.key"
            :rules="field.rules">
            <div class="flex items-center">
                <a-select
                    :ref="field.key"
                    :size="field.size"
                    v-model="form[field.key]"
                    :loading="addressLoader"
                    @change="onChange"
                    :getPopupContainer="getPopupContainer"
                    @dropdownVisibleChange="dropdownVisibleChange">
                    <a-select-option
                        v-for="item in addressList"
                        :value="item.id"
                        :key="item.id">
                        {{ item.string_view }}
                    </a-select-option>
                </a-select>
                <a-button 
                    v-if="user && user.can_edit_goods_price && form[field.key]"
                    size="large"
                    class="ant-btn-icon-only ml-2"
                    @click="modalOpen(true, form[field.key])">
                    <i class="fi fi-rr-edit"></i>
                </a-button>
            </div>
            <div
                v-if="user && user.can_edit_goods_price"
                class="flex mt-2">
                <span 
                    class="blue_color cursor-pointer flex items-center text-xs"
                    @click="modalOpen()">
                    <a-icon 
                        type="plus" 
                        class="mr-1" />
                    Добавить
                </span>
            </div>
        </a-form-model-item>
        <a-modal
            v-if="user && user.can_edit_goods_price"
            :title="modalTitle"
            :footer="null"
            :zIndex="2000"
            @cancel="visible = false"
            :visible="visible">
            <a-form-model
                ref="purposeForm"
                :model="purposeForm"
                :rules="purposeRules">
                <a-form-model-item label="Название" prop="purpose">
                    <a-input size="large" v-model="purposeForm.purpose" />
                </a-form-model-item>
                <a-form-model-item>
                    <div class="flex items-center">
                        <a-button block type="primary" size="large" :loading="formLoading" @click="onSubmit()">
                            Сохранить
                        </a-button>
                        <a-button v-if="editItem" ghost type="danger" size="large" :loading="deleteLoader" class="ant-btn-icon-only ml-1" @click="deleteItem()">
                            <i class="fi fi-rr-trash"></i>
                        </a-button>
                    </div>
                </a-form-model-item>
            </a-form-model>
        </a-modal>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus.js'
export default {
    props: {
        field: {
            type: Object,
            required: true
        },
        form: {
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
        // setOrderFormCalculated: {
        //     type: Function,
        //     default: () => {}
        // }
    },
    computed: {
        contractor() {
            return this.form.contractor
        },
        user() {
            return this.$store.state.user.user
        },
        defaultFirstValue() {
            return this.field?.defaultFirstValue ? this.field.defaultFirstValue : false
        }
    },
    data() {
        return {
            addressLoader: false,
            addressList: [],
            visible: false,
            modalTitle: 'Добавить назначение',
            formLoading: false,
            deleteLoader: false,
            editItem: false,
            purposeForm: {
                purpose: ''
            },
            purposeRules: {
                purpose: [
                    { required: true, message: 'Обязательно для заполнения', trigger: 'blur' }
                ]
            }
        }
    },
    created() {
        if(this.form[this.field.key]?.id) {
            this.form[this.field.key] = this.form[this.field.key].id
        }
    },
    methods: {
        async deleteItem() {
            try {
                this.deleteLoader = true
                const { data } = await this.$http.post(`/table_actions/update_is_active/`, {
                    id: this.purposeForm.id,
                    is_active: false
                })
                this.form[this.field.key] = null
                const index = this.addressList.findIndex(f => f.id === this.purposeForm.id)
                if(index !== -1) {
                    this.addressList.splice(index, 1)
                }

                this.editItem = false
                this.visible = false
            } catch(e) {
                console.log(e)
                this.$message.error('Ошибка удаления')
            } finally {
                this.deleteLoader = false
            }
        },
        onSubmit() {
            this.$refs.purposeForm.validate(async valid => {
                if (valid) {
                    try {
                        this.formLoading = true
                        if(this.editItem) {
                            const { data } = await this.$http.put(`/catalogs/delivery_purpose/${this.purposeForm.id}/`, this.purposeForm)
                            if(data) {
                                const index = this.addressList.findIndex(f => f.id === this.purposeForm.id)
                                if(index !== -1) {
                                    this.$set(this.addressList, index, {
                                        ...data,
                                        string_view: data.purpose
                                    })
                                }
                            }
                        } else {
                            const { data } = await this.$http.post(`/catalogs/delivery_purpose/`, this.purposeForm)
                            if(data) {
                                this.addressList.unshift({
                                    id: data.id,
                                    string_view: data.purpose
                                })
                                this.form[this.field.key] = data.id
                            }
                        }

                        this.editItem = false
                        this.visible = false
                    } catch(e) {
                        console.log(e)
                        this.$message.error('Ошибка сохранения')
                    } finally {
                        this.formLoading = false
                    }
                } else {
                    this.$message.warning('Заполните обязательные поля')
                    return false
                }
            })
        },
        modalOpen(edit = false, item = null) {
            if(edit) {
                this.modalTitle = 'Редактировать назначение'
                const find = this.addressList.find(f => f.id === item)
                if(find) {
                    this.purposeForm = {
                        ...find,
                        purpose: find.string_view
                    }
                }
                this.editItem = true
            } else {
                this.modalTitle = 'Добавить назначение'
                this.editItem = false
                this.purposeForm = {}
            }

            this.visible = true
        },
        getPopupContainer() {
            return document.querySelector('.delivery_details')
        },
        createDeliveryPoint() {
            eventBus.$emit('open_delivery_points_drawer', this.form.contractor)
        },
        dropdownVisibleChange(val) {
            if(val) {
                this.getAddress()
            }
        },
        async getAddress() {
            if(this.contractor) {
                try {
                    this.addressLoader = true
                    let params = {
                        ...this.field.params,
                    }

                    if(this.field?.filters?.length) {
                        let filters = {}

                        this.field.filters.forEach(filter => {
                            if(filter.type === 'related') {
                                filters[filter.name] = this[filter.from_field]
                            }
                            if(filter.type === 'static') {
                                filters[filter.name] = filter.value
                            }
                        })

                        if(Object.keys(filters).length)
                            params.filters = filters
                    }
                    const { data } = await this.$http.get(this.field.apiPath, { params })
                    if(data?.selectList?.length || data?.filteredSelectList?.length) {
                        this.addressList = data.selectList || data.filteredSelectList

                        if(this.defaultFirstValue && !this.form[this.field.key] && this.addressList[0]?.id) {
                            this.form[this.field.key] = this.addressList[0].id
                        }
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.addressLoader = false
                }
            }
        },
        onChange(e) {
            // if(this.edit)
            //     this.setOrderFormCalculated(false)
        }
    },
    mounted() {
        eventBus.$on('contractor_is_change', () => {
            this.addressList = []
            this.form[this.field.key] = null
        })
        eventBus.$on('update_address_list', () => {
            this.addressList = []
            this.form[this.field.key] = null
            this.getAddress()
        })
        this.getAddress()
    },
    beforeDestroy() {
        eventBus.$off('contractor_is_change')
        eventBus.$off('update_address_list')
        this.form[this.field.key] = null
    }
}
</script>