<template>
    <a-form-model-item 
        :ref="field.key" 
        :label="field.name"
        class="form_item"
        :prop="field.key"
        :rules="field.rules">
        <a-select 
            :size="field.size"
            v-model="form[field.key]"
            :loading="paymentLoader"
            @dropdownVisibleChange="dropdownVisibleChange">
            <!-- && !this.contractor -->
            <a-select-option 
                v-for="item in paymentList" 
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
        item: {
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
        }
    },
    computed: {
        contractor() {
            return this.form.contractor
        }
    },
    data() {
        return {
            paymentLoader: false,
            paymentList: [],
            field: {}
        }
    },
    created() {
        this.field = this.item.fields[0]

        if(this.form[this.field.key]?.id)
            this.form[this.field.key] = this.form[this.field.key].id
        if(this.edit && !this.paymentList.length)
            this.getPayTypes()
    },
    methods: {
        dropdownVisibleChange(val) {
            if(val) {
                this.getPayTypes()
            }
        },
        async getPayTypes() {
            if(!this.paymentList?.length && this.contractor) {
                try {
                    this.paymentLoader = true
                    let params = {
                        ...this.field.params,
                    }
                    if(this.field?.filters) {
                        const filterURL = `{"${this.field.filters.name}":"${this[this.field.filters.from_field]}"}`
                        params.filters = filterURL 
                    }
                    const { data } = await this.$http.get(this.field.apiPath, { params })
                    if(data?.selectList?.length) {
                        this.paymentList = data.selectList
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.paymentLoader = false
                }
            }
        },
    },
    beforeDestroy() {
        this.form[this.field.key] = null
    }
}
</script>