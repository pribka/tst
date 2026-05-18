<template>
    <div :ref="`select_${code}_${field.key}`">
        <a-select 
            v-model="form[field.key]" 
            class="w-full"
            :size="fieldSize"
            :allowClear="allowClear"
            :disabled="fieldDisabled"
            :loading="loading"
            :getPopupContainer="getPopupContainer"
            @dropdownVisibleChange="dropdownVisibleChange">
            <a-select-option 
                v-for="option in selectList" 
                :key="option.code" 
                :value="option[toField]">
                {{option.string_view ? option.string_view :  option.name}}
            </a-select-option>
            <div slot="notFoundContent" class="flex justify-center p-1">
                <a-spin 
                    v-if="loading" 
                    size="small" />
                <a-empty 
                    v-else 
                    :description="$t('no_data')" />
            </div>
        </a-select>
    </div>
</template>

<script>
import fieldMixins from './fieldMixins.js'
export default {
    mixins: [
        fieldMixins
    ],
    computed: {
        params() {
            return this.field.params
        },
        allowClear() {
            return this.field.allowClear ? this.field.allowClear : false
        },
        toField() {
            if(this.field?.params?.toField) {
                return this.field.params.toField
            } else {
                return 'id'
            }
        }
    },
    data() {
        return {
            selectList: [],
            loading: false
        }
    },
    created() {
        if(this.edit)
            this.getSelectOptions()
    },
    methods: {
        getPopupContainer() {
            return this.$refs[`select_${this.code}_${this.field.key}`]
        },
        dropdownVisibleChange(val) {
            if(val) {
                this.getSelectOptions()
            }
        },
        async getSelectOptions() {
            if(!this.selectList?.length) {
                try {
                    this.loading = true
                    const {data} = await this.$http.get(this.params.dataPath)
                    if(data?.selectList?.length) {
                        this.selectList = data.selectList
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.loading = false
                }
            }
        }
    }
}
</script>