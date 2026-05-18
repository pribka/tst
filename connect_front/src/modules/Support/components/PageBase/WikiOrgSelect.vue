<template>
    <div ref="selectWrap">
        <a-select
        :value="selectedValue"
        :placeholder="$t('support.selectOrganization')"
        size="large"
        show-search
        allow-clear
        :loading="loading"
        :filter-option="filterOption"
        :getPopupContainer="getPopupContainer"
        style="width: 100%;"
        @change="changeValue">
            <a-select-option v-for="item in options" :key="item.id" :value="item.id">
                {{ item.name || item.full_name }}
            </a-select-option>
        </a-select>
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'

export default {
    props: {
        value: {
            type: [Object, String],
            default: null
        }
    },
    computed: {
        selectedValue() {
            if(!this.value)
                return undefined
            if(typeof this.value === 'object')
                return this.value.id
            return this.value
        }
    },
    data() {
        return {
            loading: false,
            options: []
        }
    },
    methods: {
        getPopupContainer() {
            return this.$refs.selectWrap
        },
        filterOption(input, option) {
            return option.componentOptions.children[0].text.toLowerCase().includes(input.toLowerCase())
        },
        changeValue(value) {
            const find = this.options.find(item => item.id === value)
            this.$emit('input', find || null)
        },
        async getOrganizations() {
            try {
                this.loading = true
                const { data } = await this.$http.get('/contractor_permissions/organizations/', {
                    params: {
                        permission_type: 'contractor_wiki_admin'
                    }
                })

                if(Array.isArray(data)) {
                    this.options = data
                } else if(data?.results?.length) {
                    this.options = data.results
                }

                if(!this.value && this.options.length) {
                    this.$emit('input', this.options[0])
                }
            } catch(error) {
                errorHandler({ error, show: false })
            } finally {
                this.loading = false
            }
        }
    },
    mounted() {
        this.getOrganizations()
    }
}
</script>
