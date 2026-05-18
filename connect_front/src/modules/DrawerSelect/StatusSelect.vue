<template>
    <div class="relative">
        <a-popover 
            v-model="visible" 
            transitionName=""
            ref="statusPopover"
            :placement="placement"
            overlayClassName="status_select_popover"
            :destroyTooltipOnHide="true"
            :getPopupContainer="getPopupContainer"
            :trigger="trigger"
            @visibleChange="visibleChange">
            <div v-if="value" class="w-full status_wrapper" :class="is_open && 'status_wrapper_open'">
                <a-spin :spinning="loading" class="w-full" size="small">
                    <a-tag 
                        size="large" 
                        block 
                        :color="value[statusColorKey] || 'default'" 
                        class="m-0 cursor-pointer">
                        <div class="flex items-center justify-between">
                            <span>{{ value[statusNameKey] }}</span>
                            <i class="fi fi-rr-angle-small-down ml-2 st_arrow" />
                        </div>
                    </a-tag>
                </a-spin>
            </div>
            <template #content>
                <div class="status_list">
                    <div v-if="listLoading" class="flex justify-center">
                        <a-spin size="small" />
                    </div>
                    <div 
                        v-for="item in filterStatusList" 
                        :key="item.id" 
                        class="status_list__item cursor-pointer"
                        @click="selectStatus(item)">
                        <a-badge :color="item[statusColorKey] || 'default'" />
                        {{ item[statusListNameKey] }}
                    </div>
                    <div class="pt-1">
                        <a-button type="ui_ghost" block size="small" @click="closePopover()">
                            {{ $t('Close') }}
                        </a-button>
                    </div>
                </div>
            </template>
        </a-popover>
    </div>
</template>

<script>
export default {
    props: {
        value: { type: [Object, Array, String] },
        optionViewType: {
            type: String,
            default: 'default'
        },
        placement: {
            type: String,
            default: 'bottomLeft'
        },
        trigger: {
            type: String,
            default: 'click'
        },
        statusList: {
            type: Array,
            default: () => []
        },
        statusNameKey: {
            type: String,
            default: "name"
        },
        statusListNameKey: {
            type: String,
            default: "string_view"
        },
        statusValueKey: {
            type: String,
            default: "code"
        },
        statusColorKey: {
            type: String,
            default: "color"
        },
        apiUrl: {
            type: String,
            default: ""
        },
        apiKey: {
            type: String,
            default: 'selectList'
        },
        listHideActive: {
            type: Boolean,
            default: true
        },
        loading: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        filterStatusList() {
            if(this.listHideActive && this.value)
                return this.optionList.filter(item => item.code !== this.value.code)
            return this.optionList
        },
        optionList() {
            if (this.statusList.length) {
                return this.statusList
            }
            return this.list
        }
    },
    data() {
        return {
            visible: false,
            list: [],
            listLoading: false,
            is_open: false
        }
    },
    methods: {
        closePopover() {
            this.visible = false
            this.is_open = false
        },
        visibleChange(vis) {
            if(vis) {
                if(!this.optionList.length) {
                    this.getStatusList()
                }
            }
            this.is_open = vis
        },
        async getStatusList() {
            try {
                this.listLoading = true
                const { data } = await this.$http.get(this.apiUrl)
                if(data) {
                    if(this.apiKey) {
                        this.list = data[this.apiKey]
                    } else {
                        this.list = data
                    }
                }
            } catch(e) {
                console.error(e)
            } finally {
                this.listLoading = false
            }
        },
        getPopupContainer(trigger) {
            return trigger.parentNode
        },
        selectStatus(item) {
            const itemObj = {
                ...item,
                [this.statusNameKey]: item[this.statusListNameKey] 
            }
            this.$emit('input', itemObj)
            this.$emit('change', itemObj)
            this.visible = false
        }
    }
}
</script>

<style lang="scss">
.status_select_popover{
    width: 100%;
    .ant-popover-inner-content{
        padding: 5px;
    }
    .ant-popover-arrow{
        display: none
    }
    &.ant-popover-placement-bottom, 
    &.ant-popover-placement-bottomLeft, 
    &.ant-popover-placement-bottomRight{
        padding-top: 0px
    }
}
</style>

<style lang="scss" scoped>
.status_wrapper{
    &::v-deep{
        .ant-spin-container{
            width: 100%;
        }
    }
    .st_arrow{
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    }
    &.status_wrapper_open{
        .st_arrow{
            transform: rotate(180deg);
        }
    }
}
.status_list{
    &__item{
        user-select: none;
        border-radius: 8px;
        padding: 8px 12px;
        transition: background 0.3s ease;
        &:hover{
            background-color: #f7f9fc;
        }
        &:not(:last-child){
            margin-bottom: 5px;
        }
    }
    &::v-deep{
        .ant-tag{
            margin: 0px;
        }
    }
}
</style>