<template>
    <div class="tags_list items-center" :class="showBorder && 'bordered'">
        <a-spin v-if="tagLoading" size="small" class="mr-1" />
        <a-tag 
            v-for="(tag, index) in tagsList" 
            :color="tag.color === 'default' ? '' : tag.color"
            :closable="useAction"
            contrastText
            :key="tag.id"
            :useTextColor="false"
            @close="() => deleteTag(tag, index)">
            {{ tag.name }}
        </a-tag>
        <template v-if="showNoDataText">
            {{ noDataText }}
        </template>
        <div v-if="useAction">
            <a-button 
                v-if="!tagAdd"
                type="ui" 
                size="small" 
                class="add_tag_btn"
                style="border-radius: 8px;"
                @click="addTag()">
                <div class="flex items-center">
                    <i class="fi fi-rr-plus-small mr-1" />
                    {{ $t('Add') }}
                </div>
            </a-button>
            <div v-else ref="tagInputWrapper" class="flex h-full">
                <a-spin v-if="createTagLoading" size="small" />
                <template v-else>
                    <a-select
                        v-if="useSelect"
                        ref="selectInput"
                        :value="selectedObject.value"
                        @select="selectHandler"
                        @keyup.enter.native="selectHandleEnter"
                        @change="selectChange"
                        :style="selectMinWidthStyle"
                        defaultOpen
                        :placeholder="selectPlaceholder"
                        :getPopupContainer="getPopupContainer"
                        class="tag-select"
                        size="small">
                        <!-- mode="combobox" -->
                        <a-select-option
                            v-for="option in availableSelectOptions"
                            :key="option.value"
                            :value="option.value">
                            {{ option.label }}
                        </a-select-option>
                    </a-select>
                    <a-popover
                        v-else
                        :getPopupContainer="getPopupContainer"
                        overlayClassName="color_selector"
                        visible
                        placement="bottom"
                        @visibleChange="visibleChange">
                        <template slot="content">
                            <div class="flex items-center">
                                <div 
                                    v-for="(color, index) in tagColorList" 
                                    :key="color.key" 
                                    :class="[activeColor.key === color.key && 'active', color.key]"
                                    class="color_item"
                                    :style="`
                                                    background: ${color.color};
                                                    border-color: ${color.color};
                                                    animation-delay: ${index * 50}ms;
                                                `"
                                    @click="selectColor(color)">
                                    <i v-if="activeColor.key === color.key" class="fi fi-rr-check" />
                                </div>
                            </div>
                        </template>
                        <a-input 
                            v-model="tagText"
                            ref="tagInput"
                            class="tag_input"
                            :style="`border-color: ${activeColor.color};`"
                            size="small" 
                            style="max-width: 98px;"
                            @pressEnter="createTag()" />
                    </a-popover>
                </template>
            </div>
        </div>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { onClickOutside } from '@vueuse/core'
import { errorHandler } from '@/utils/index.js'
let deleteTimer;
export default {
    props: {
        model: {
            type: String,
            default: ""
        },
        pageName: {
            type: String,
            default: ""
        },
        related_object: {
            type: [String, Number],
            required: true
        },
        contractor: {
            type: [String, Number],
            required: true
        },
        useAction: {
            type: Boolean,
            default: false
        },
        useSelect: {
            type: Boolean,
            default: false
        },
        selectOptions: {
            type: Array,
            default: () => []
        },
        uniqueSelectOptions: {
            type: Boolean,
            default: false
        },
        showBorder: {
            type: Boolean,
            default: false
        },
        noDataText: {
            type: String,
            default: ''
        },
        selectPlaceholder: {
            type: String,
            default: ''
        },
        selectMinWidth: {
            type: Number,
            default: null
        },
        workplanUpdate: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            selectedObject: { value: null },
            tagAdd: false,
            createTagLoading: false,
            tagLoading: false,
            tagText: "",
            tagsList: [],
            stopOutside: null,
            stopInit: false,
            activeColor: {
                key: 'default',
                color: '#d9d9d9'
            },
            tagColorList: [
                {
                    key: 'default',
                    color: '#d9d9d9'
                },
                {
                    key: 'pink',
                    color: '#eb2f96'
                },
                {
                    key: 'red',
                    color: '#f5222d'
                },
                {
                    key: 'orange',
                    color: '#fa8c16'
                },
                {
                    key: 'green',
                    color: '#52c41a'
                },
                {
                    key: 'cyan',
                    color: '#13c2c2'
                },
                {
                    key: 'blue',
                    color: '#1890ff'
                },
                {
                    key: 'purple',
                    color: '#722ed1'
                }
            ]
        }
    },
    computed: {
        selectMinWidthStyle() {
            if (this.selectMinWidth)
                return `min-width: ${this.selectMinWidth}px`
            return ''
        },
        showNoDataText() {
            return !this.useAction && this.noDataText && this.tagsList.length === 0
        },
        payload() {
            const value = {
                name: this.tagText,
                related_object: this.related_object,
                contractor: this.contractor,
                color: this.activeColor.key
            }
            if (this.useSelect) {
                value.name = this.selectedObject.label || this.selectedObject.value
                value.color = this.selectedObject.color
            }
            return value 
        },
        availableSelectOptions() {
            if (this.uniqueSelectOptions) {
                return this.selectOptions.
                    filter(option => !this.tagsList.find(tag => tag.name.toLowerCase() === option.label.toLowerCase()))
            }
            return this.selectOptions
        },

    },
    methods: {
        selectHandleEnter() {
            this.selectedObject.color = 'default'
            this.createTag()
                .then(() => {
                    this.selectedObject = { value: null }
                })
        },
        selectChange(value) {
            this.selectedObject.value = value
        },
        selectHandler(value) {
            const valueObj = this.selectOptions.find(option => value === option.value)
            this.selectedObject = valueObj
            this.createTag()
                .then(() => {
                    this.selectedObject = { value: null }
                })
        },
        selectColor(color) {
            this.activeColor = color
            this.$nextTick(() => {
                this.$refs?.tagInput?.focus()
            })
        },
        async deleteTag(tag, index) {
            try {
                this.tagsList.splice(index, 1)
                await this.$http.post(`/tags/${tag.id}/discard/`, {
                    related_object: this.related_object
                })
                clearTimeout(deleteTimer)
                if (this.$store.hasModule('workplan') && this.related_object && this.workplanUpdate) {
                    this.$store.dispatch('workplan/updateItem', {
                        item: {
                            id: this.related_object
                        },
                        list: 'taskList'
                    })
                }
                deleteTimer = setTimeout(() => {
                    eventBus.$emit(`update_filter_${this.model}_${this.pageName}`)
                }, 900)
            } catch(error) {
                errorHandler({error})
            }
        },
        async getTags() {
            try {
                this.tagLoading = true
                const { data } = await this.$http.get('/tags/', {
                    params: {
                        related_object: this.related_object,
                        contractor: this.contractor,
                        model: this.model,
                        page_size: 'all'
                    }
                })
                if(data) {
                    this.tagsList = data.results
                }
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                this.tagLoading = false
            }
        },
        async createTag() {
            if(this.tagText.length || this.useSelect) {
                try {
                    this.createTagLoading = true
                    
                    const { data } = await this.$http.post('/tags/', this.payload)
                    if(data) {
                        this.tagsList.push(data)
                        this.closeTagCreate()
                        if (this.$store.hasModule('workplan') && this.related_object && this.workplanUpdate) {
                            this.$store.dispatch('workplan/updateItem', {
                                item: {
                                    id: this.related_object
                                },
                                list: 'taskList'
                            })
                        }
                        eventBus.$emit(`update_filter_${this.model}_${this.pageName}`)
                    }
                } catch(error) {
                    errorHandler({error})
                    this.stopInit = false
                } finally {
                    this.createTagLoading = false
                }
            } else {
                this.closeTagCreate()
            }
        },
        closeTagCreate() {
            this.tagText = ""
            this.activeColor = {
                key: 'default',
                color: '#d9d9d9'
            }
            this.stopInit = false
            this.tagAdd = false
            if(this.stopOutside) {
                this.stopOutside()
            }
        },
        visibleChange(vis) {
            
        },
        getPopupContainer() {
            return this.$refs.tagInputWrapper
        },
        addTag() {
            this.tagText = ""
            this.activeColor = {
                key: 'default',
                color: '#d9d9d9'
            }
            this.tagAdd = true
            this.$nextTick(() => {
                if (!this.useSelect) {
                    this.$refs.tagInput?.focus()
                }
                if(this.$refs.tagInputWrapper) {
                    this.stopOutside = onClickOutside(this.$refs.tagInputWrapper, () => {
                        if(this.tagAdd && !this.stopInit) {
                            this.stopInit = true
                            if (!this.useSelect) {
                                this.createTag()
                            }
                        }
                    })
                }
            })
        },
    },
    mounted() {
        this.getTags()
    }
}
</script>

<style lang="scss" scoped>
.add_tag_btn{
    &.ant-btn-sm{
        height: 28px;
        font-size: 14px;
    }
}
.tag_input{
    &:focus{
        box-shadow: initial!important;
    }
}
.color_item{
    width: 20px;
    height: 20px;
    border-radius: 50%;
    cursor: pointer;
    border: 1px solid transparent;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    animation: fade-in-up 0.3s ease forwards;
    &:not(:last-child){
        margin-right: 5px;
    }
    &.active{
        
    }
    i{
        color: #fff;
        font-size: 12px;
    }
    &.default{
        i{
            color: #000;
        }
    }
}
.tags_list{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    &::v-deep{
        .ant-tag{
            display: flex;
            align-items: center;
            margin-bottom: 0px;
            margin-right: 0px;
        }
    }
}
.tags_list.bordered {
    border-bottom: 1px solid #dfe0e4;
    padding-bottom: 10px;
    margin-bottom: 13px;
}
:deep .tag-select {
    min-width: 120px;
    .ant-select-selection {
        height: 100%;
    }
}
.text-white {
    color: #fff;
}
.text-black {
    color: #000;
}

:deep {
    .ant-tag .icon-close {
        color: inherit;
    }
}
</style>