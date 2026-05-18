<template>
    <div ref="color_picker">
        <div v-if="typeList" class="color_list">
            <div v-for="item in colorList" :key="item.color" @click="selectColor(item)">
                <div class="drop_color" :style="`background: ${item.color};`">
                    <i v-if="selectedColor && selectedColor.color === item.color" class="fi fi-rr-check"></i>
                </div>
            </div>
        </div>
        <a-dropdown 
            v-else 
            :trigger="['click']">
            <a-menu slot="overlay" class="drop_color_picker">
                <a-menu-item v-for="item in colorList" :key="item.color" @click="selectColor(item)">
                    <div class="drop_color" :style="`background: ${item.color};`">
                        <i 
                            v-if="selectedColor && selectedColor.color === item.color" 
                            :class="selectedColor.color === '#ffffff' && 'text_current'"
                            class="fi fi-rr-check" />
                    </div>
                </a-menu-item>
            </a-menu>
            <div class="color_picker ant-btn ant-btn-ui ant-btn-circle ant-btn-icon-only" :class="value && value.color !== '#ffffff' && 'ant-btn-background-ghost'">
                <div 
                    class="active" 
                    :style="`background: ${selectedColor.color};`"></div>
            </div>
        </a-dropdown>
    </div>
</template>

<script>
export default {
    props: {
        value: {
            type: [Object, String]
        },
        typeList: {
            type: Boolean,
            default: false
        },
        changeColor: {
            type: Function,
            default: () => {}
        },
        colorList: {
            type: Array,
            default: () => {}
        }
    },
    data() {
        return {
            selectedColor: null
        }
    },
    watch: {
        value(val) {
            if(val) {
                const find = this.colorList.find(f => f.color === this.value?.color || f.oColor === this.value?.oColor)
                if(find) {
                    this.selectedColor = find
                } else {
                    this.selectedColor = this.colorList[0]
                }
            } else {
                this.selectedColor = this.colorList.find(f => f.color === '#ffffff')
                this.changeColor(this.selectedColor)
            }
        }
    },
    created() {
        if(!this.selectedColor?.color && !this.value?.color) {
            this.selectedColor = this.colorList.find(f => f.color === '#ffffff')
            this.changeColor(this.selectedColor)
        }
        if(!this.selectedColor?.color && this.value?.color) {
            const find = this.colorList.find(f => f.color === this.value?.color || f.oColor === this.value?.oColor)
            if(find) {
                this.selectedColor = find
            } else {
                this.selectedColor = this.colorList.find(f => f.color === '#ffffff')
                this.changeColor(this.selectedColor)
            }
        }
    },
    methods: {
        selectColor(item) {
            this.selectedColor = item
            this.changeColor(item)
        }
    }
}
</script>

<style lang="scss" scoped>
.color_list{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(32px, 1fr));
    grid-gap: 8px;
    flex: 1;
    .drop_color{
        width: 34px;
        border-radius: var(--borderRadius);
        height: 34px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #ffffff;
        font-size: 20px;
        border: 1px solid var(--border2);
    }
}
.color_picker{
    width: 22px;
    height: 22px;
    display: flex;
    align-items: center;
    justify-content: center;
    max-width: 22px;
    max-height: 22px;
    min-height: 22px;
    .active{
        width: 14px;
        height: 14px;
        border-radius: 50%;
    }
    &.ant-btn-circle, 
    &.ant-btn-circle-outline{
        min-width: 22px;
    }
}
.drop_color_picker{
    display: grid;
    gap: 7px;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    padding: 10px;
    min-width: 250px;
    &::v-deep{
        .ant-dropdown-menu-item{
            padding: 0px;
        }
    }
    .drop_color{
        width: 38px;
        border-radius: var(--borderRadius);
        height: 38px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #ffffff;
        font-size: 20px;
        border: 1px solid var(--border2);
    }
}
</style>