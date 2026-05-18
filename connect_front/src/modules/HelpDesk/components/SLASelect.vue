<template>
    <div :style="!useInject && 'max-width: 300px;'" class="w-full flex items-center">
        <slot v-if="$slots.prefixIcon" name="prefixIcon" />
        <a-select 
            v-model="selectedSLA"
            size="large" 
            class="w-full sla_select"
            :class="inputType === 'ghost' && 'ant-select-ghost'"
            :loading="listLoading"
            :disabled="disabled"
            :placeholder="$t('helpdesk.select_sla')"
            @change="changeSLA" 
            :getPopupContainer="trigger => trigger.parentNode">
            <a-select-option v-for="item in list" :key="item.id" :value="item.id">
                <div class="flex items-center">
                    <a-badge :color="item.color" class="mr-2" />
                    {{ item.name }}
                </div>
            </a-select-option>
        </a-select>
    </div>
</template>

<script>
import eventBus from "@/utils/eventBus"
import { errorHandler } from '@/utils/index.js'
export default {
    props: {
        slaSelectedInfo: {
            type: Object,
            default: () => null
        },
        inputType: {
            type: String,
            default: 'default'
        },
        disabled: {
            type: Boolean,
            default: false
        },
        selectItem: {
            type: [Object, Array],
            default: () => null
        },
        pageName: {
            type: String,
            default: ""
        },
        model: {
            type: String,
            default: ""
        },
        params: {
            type: Object,
            default: () => {}
        },
        listUpdate: {
            type: Boolean,
            default: true
        },
        useInject: {
            type: Boolean,
            default: false
        },
        slaInitSelected: {
            type: String,
            default: ""
        }
    },
    data() {
        return {
            listLoading: false,
            loading: false,
            selectedSLA: null,
            oldSelect: null,
            page: 1,
            list: [],
            page_size: 15
        }
    },
    watch: {
        selectItem(value) {
            this.selectSLA(value)
        }
    },
    created() {
        this.selectSLA(this.selectItem)
        if(this.useInject)
            this.selectSLAInit()
        this.getSLAList()
    },
    methods: {
        selectSLAInit() {
            if(this.slaInitSelected) {
                this.selectedSLA = this.slaInitSelected
                this.oldSelect = this.slaInitSelected
            }
        },
        selectSLA(value) {
            if(value) {
                if(value.sla) {
                    this.oldSelect = value.sla.id
                    this.selectedSLA = value.sla.id
                    const find = this.list.find(f => f.id === value.sla.id)
                    if(!find)
                        this.list.push(value)
                } else {
                    this.selectedSLA = null
                }
            }
        },
        async getSLAList() {
            try {
                this.listLoading = true
                const { data } = await this.$http.get('/sla/', {
                    params: {
                        ...this.params,
                        page: this.page,
                        page_size: this.page_size
                    }
                })
                if(data) {
                    this.list = data.results
                }
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                this.listLoading = false
            }
        },
        changeSLA(value) {
            const find = this.list.find(f => f.id === value)
            if(this.useInject) {
                this.$emit('change', find)
            } else {
                this.$confirm({
                    title: this.$t('helpdesk.confirm_changes'),
                    content: this.$t('helpdesk.set_sla_rules', { name: find.name, name2: this.selectItem.name }),
                    cancelText: this.$t('no'),
                    okText: this.$t('yes'),
                    onOk: async () => {
                        try {
                            const { data } = await this.$http.post('/sla/set_objects/', {
                                sla: value,
                                related_objects: [this.selectItem.id]
                            })
                            if(data) {
                                this.oldSelect = value
                                if(this.listUpdate)
                                    eventBus.$emit(`update_filter_${this.model}_${this.pageName}`)
                            }
                        } catch(error) {
                            errorHandler({error})
                        }
                    },
                    onCancel: () => {
                        this.selectedSLA = JSON.parse(JSON.stringify(this.oldSelect))
                    }
                })
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.sla_select{
    &.ant-select-ghost{
        &::v-deep{
            .ant-select-selection__placeholder{
                font-size: 14px;
            }
        }
    }
}
</style>