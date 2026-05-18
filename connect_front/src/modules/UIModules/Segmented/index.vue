<template>
    <div 
        class="segmented" 
        :class="[bgInvert && 'segmented_invert', block && 'segmented_block']">
        <div 
            v-for="(option, index) in options" 
            :key="option[labelAndKey.key]"
            class="segmented__item"
            :class="checkActive(option) && 'active'"
            @click="selectOption(option)">
            <slot v-if="$scopedSlots.default" :option="option" :index="index" />
            <template v-else>
                <template v-if="option[labelAndKey.title]">
                    {{ option[labelAndKey.title] }}
                </template>
                <transition name="badge-fade-slide">
                    <template v-if="option[labelAndKey.count]">
                        <a-badge 
                            :count="option[labelAndKey.count]" 
                            :overflow-count="9999"
                            :class="option[labelAndKey.color] && `b-color-${option[labelAndKey.color]}`" />
                    </template>
                </transition>
            </template>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        value: {
            type: [String, Number, Object, Array],
            default: () => null
        },
        options: {
            type: Array,
            default: () => []
        },
        labelAndKey: {
            type: Object,
            default: () => ({
                title: 'title',
                key: 'key',
                count: 'count',
                color: 'color'
            })
        },
        multiselect: {
            type: Boolean,
            default: false
        },
        deselectable: {
            type: Boolean,
            default: false
        },
        useLocalStorageSave: {
            type: Boolean,
            default: false
        },
        localStorageKey: {
            type: [String, Number],
            default: ''
        },
        bgInvert: {
            type: Boolean,
            default: false
        },
        block: {
            type: Boolean,
            default: false
        }
    },
    methods: {
        getOptionKey(option) {
            return option[this.labelAndKey.key]
        },
        isActive(optionKey) {
            if(this.multiselect && Array.isArray(this.value)) {
                return this.value.includes(optionKey)
            } else {
                return this.value === optionKey
            }
        },
        checkActive(option) {
            return this.isActive(this.getOptionKey(option))
        },
        selectOption(option) {
            const key = this.getOptionKey(option)
            const isSelected = this.isActive(key)

            if(this.multiselect) {
                const currentValue = Array.isArray(this.value) ? [...this.value] : []

                if(option.single) {
                    const nonSingle = currentValue.filter(k => {
                        const opt = this.options.find(o => this.getOptionKey(o) === k)
                        return !(opt && opt.single)
                    })

                    if(isSelected) {
                        if(this.deselectable) {
                            this.updateValue(nonSingle)
                        }
                    } else {
                        this.updateValue([...nonSingle, key])
                    }
                } else {
                    if(isSelected) {
                        if(this.deselectable) {
                            this.updateValue(currentValue.filter(k => k !== key))
                        }
                    } else {
                        this.updateValue([...currentValue, key])
                    }
                }
            } else {
                if(isSelected) {
                    if(this.deselectable) {
                        this.updateValue(null)
                    }
                } else {
                    this.updateValue(key)
                }
            }
        },
        updateValue(newValue) {
            this.$emit('input', newValue)
            this.$emit('change', newValue)
            if(this.useLocalStorageSave && !this.multiselect) {
                localStorage.setItem(this.localStorageKey, newValue)
            }
        }
    },
    created() {
        if(this.useLocalStorageSave && !this.multiselect) {
            const lKey = localStorage.getItem(this.localStorageKey)
            if(lKey) {
                this.$emit('input', lKey)
                this.$emit('change', lKey)
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.segmented{
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    background: #fff;
    border-radius: 8px;
    padding: 5px;
    gap: 5px;
    user-select: none;
    &__item{
        padding: 0 10px;
        height: 28px;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
        display: flex;
        align-items: center;
        text-align: left;
        font-size: 14px;
        &:hover{
            color: #4777FF;
        }
        &::v-deep{
            .ant-badge{
                margin-left: 8px;
                .ant-badge-count{
                    background: #F0F1F7;
                    color: var(--text1);
                    box-shadow: initial;
                    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
                }
                &.b-color-danger{
                    .ant-badge-count{
                        background: #fed4d4!important;
                        color: #FF5C5C!important;
                    }
                }
            }
        }
        &.active{
            background: #e8ecfa;
            color: #4777FF;
            &::v-deep{
                .ant-badge{
                    .ant-badge-count{
                        background: #fff;
                    }
                }
            }
        }
    }
    &.segmented_invert{
        background: #f7f9fc;
    }
    &.segmented_block{
        flex-wrap: nowrap;
        .segmented__item{
            width: 100%;
            justify-content: center;
        }
    }
}
.badge-fade-slide-enter-active, .badge-fade-slide-leave-active {
    transition: all 0.3s ease
}
.badge-fade-slide-enter, .badge-fade-slide-leave-to {
    transform: translateX(-8px);
    opacity: 0
}

</style>