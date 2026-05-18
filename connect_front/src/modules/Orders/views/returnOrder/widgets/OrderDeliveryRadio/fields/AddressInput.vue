<template>
    <a-form-model-item 
        :ref="field.key" 
        :label="field.name"
        class="form_item"
        :prop="field.key"
        :rules="{
            required: true,
            message: 'Обязательно для заполнения',
            trigger: 'blur'
        }">
        <a-select 
            size="large"
            v-model="form[field.key]"
            :loading="addressLoader && !this.contractor"
            @dropdownVisibleChange="dropdownVisibleChange">
            <a-select-option 
                v-for="item in addressList" 
                :value="item.id" 
                :key="item.id">
                {{ item.string_view }}
            </a-select-option>
        </a-select>
    </a-form-model-item>
</template>

<script>
export default {
    props: {
        field: {
            type: Object,
            required: true
        },
        form: {
            type: Object,
            required: true
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
    methods: {
        dropdownVisibleChange(val) {
            if(val) {
                this.getAddress()
            }
        },
        async getAddress() {
            if(!this.addressList?.length && this.contractor) {
                try {
                    this.addressLoader = true
                    let params = {
                        model: 'catalogs.DeliveryAddress',
                        filters: {
                            "contractor": this.contractor
                        }
                    }
                    const { data } = await this.$http.get(this.field.apiPath, { params })
                    if(data?.selectList?.length) {
                        this.addressList = data.selectList
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.addressLoader = false
                }
            }
        },
    },
    beforeDestroy() {
        this.form[this.field.key] = null
    }
}
</script>