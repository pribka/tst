<template>
    <div class="delivery_details" :id="`field_${field.key}`">
        <a-form-model-item
            :ref="field.key"
            :label="field.name"
            class="form_item"
            :prop="field.key"
            :rules="field.rules">
            <a-select
                :size="field.size"
                v-model="form[field.key]"
                :loading="addressLoader"
                :getPopupContainer="getPopupContainer"
                @dropdownVisibleChange="dropdownVisibleChange">
                <!-- && !this.contractor -->
                <div 
                    v-if="!addressList.length" 
                    slot="notFoundContent" 
                    value="loading" 
                    class="flex justify-center">
                    <a-spin size="small" />
                </div>
                <a-select-option
                    v-for="item in addressList"
                    :value="item.id"
                    :key="item.id">
                    {{ item.string_view }}
                </a-select-option>
            </a-select>
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
        }
    },
    computed: {
        contractor() {
            return this.form.contractor
        }
    },
    data() {
        return {
            addressLoader: false,
            addressList: []
        }
    },
    created() {
        if(this.form[this.field.key]?.id) {
            this.form[this.field.key] = this.form[this.field.key].id
        }

        if((this.edit || this.isOrderDrawer) && !this.addressList.length)
            this.getAddress()
    },
    methods: {
        getPopupContainer() {
            return document.querySelector('.delivery_details')
        },
        dropdownVisibleChange(val) {
            if(val) {
                this.getAddress()
            }
        },
        async getAddress() {
            if(!this.addressList?.length) {
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
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.addressLoader = false
                }
            }
        }
    },
    mounted() {
        eventBus.$on('contractor_is_change', () => {
            this.addressList = []
            this.form[this.field.key] = null
        })
    },
    beforeDestroy() {
        eventBus.$off('contractor_is_change')
        this.form[this.field.key] = null
    }
}
</script>