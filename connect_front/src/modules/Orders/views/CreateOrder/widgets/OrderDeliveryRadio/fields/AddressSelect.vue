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
                    <!-- && !this.contractor -->
                    <a-select-option
                        v-for="item in addressList"
                        :value="item.id"
                        :key="item.id">
                        {{ item.string_view }}
                    </a-select-option>
                </a-select>
                <template v-if="field.delivery_point_create_button">
                    <a-button 
                        size="large"
                        class="ant-btn-icon-only ml-2"
                        @click="createDeliveryPoint">
                        <i class="fi fi-rr-edit"></i>
                    </a-button>
                </template>
            </div>
        </a-form-model-item>
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
        defaultFirstValue() {
            return this.field?.defaultFirstValue ? this.field.defaultFirstValue : false
        }
    },
    data() {
        return {
            addressLoader: false,
            addressList: [],
        }
    },
    created() {
        if(this.form[this.field.key]?.id) {
            this.form[this.field.key] = this.form[this.field.key].id
        }
    },
    methods: {
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
            this.getAddress()
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