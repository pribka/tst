<template>
    <div :id="`field_${field.key}`">
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
                :not-found-content="null"
                @dropdownVisibleChange="dropdownVisibleChange">
                <!-- && !this.contractor -->
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
                        ...this.field.params,
                    }
                    if(this.field?.filters) {
                        const filterURL = `{"${this.field.filters.name}":"${this[this.field.filters.from_field]}"}`
                        params.filters = filterURL
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