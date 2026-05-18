<template>
    <div ref="color_picker">
        <div v-if="typeList" class="color_list">
            <div v-for="item in colors" :key="item.color" @click="selectColor(item)">
                <div class="drop_color" :style="`background: ${item.color};`">
                    <i v-if="selectedColor && selectedColor.color === item.color" class="fi fi-rr-check" />
                </div>
            </div>
            <div v-if="customColor && customColor.color && checkColor" class="drop_color" :style="`background: ${customColor.color};`" @click="selectColor(customColor)">
                <i v-if="selectedColor === customColor.color" class="fi fi-rr-check" />
            </div>
        </div>
        <a-dropdown 
            v-else 
            :trigger="['click']" 
            :getPopupContainer="getPopupContainer">
            <a-menu slot="overlay" class="drop_color_picker">
                <a-menu-item v-for="item in colors" :key="item.color" @click="selectColor(item)">
                    <div class="drop_color" :style="`background: ${item.color};`">
                        <i v-if="selectedColor && selectedColor.color === item.color" class="fi fi-rr-check" />
                    </div>
                </a-menu-item>
            </a-menu>
            <div class="color_picker ant-input ant-input-lg cursor-pointer flex items-center">
                <div 
                    class="active" 
                    :style="`background: ${selectedColor.color};`"></div>
                <div class="ml-2">
                    <i class="fi fi-rr-angle-small-down" />
                </div>
            </div>
        </a-dropdown>
    </div>
</template>

<script>
export default {
    props: {
        value: {
            type: String
        },
        typeList: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            colors: [
                {
                    color: '#039be5'
                },
                {
                    color: '#f43c36'
                },
                {
                    color: '#ff5721'
                },
                {
                    color: '#ff791b'
                },
                {
                    color: '#ffb400'
                },
                {
                    color: '#7cb342'
                },
                {
                    color: '#209653'
                },
                {
                    color: '#04ada0'
                },
                {
                    color: '#3761e9'
                },
                {
                    color: '#794cd8'
                },
                {
                    color: '#a447bf'
                },
                {
                    color: '#96a3b0'
                },
                {
                    color: '#13b1e7'
                },
                {
                    color: '#ec407a'
                },
                {
                    color: '#ef304c'
                },
                {
                    color: '#8cadd0'
                }
            ],
            selectedColor: null,
            customColor: null,
        }
    },
    computed: {
        checkColor() {
            const find = this.colors.find(f => f.color === this.customColor?.color)
            return find ? false : true
        }
    },
    watch: {
        value(val) {
            if(val) {
                this.setColor()
            } else {
                this.selectedColor = this.colors[0]
                this.$emit('input', this.colors[0].color)
            }
        }
    },
    created() {
        if(!this.selectedColor && !this.value) {
            this.customColor = { color:  this.value}
            this.selectedColor = this.value
            this.$emit('input', this.value)
        }
        if(!this.selectedColor && this.value)
            this.setColor()
        if(this.value)
            this.selectedColor = { color: this.value }
    },
    methods: {
        updateColor(color) {
            this.customColor = { color }
        },
        setColor() {
            const find = this.colors.find(f => f.color === this.value)
            if(find) {
                this.selectedColor = find
            } else {
                this.customColor = { color:  this.value}
                this.selectedColor = this.value
                this.$emit('input', this.value)
            }
        },
        selectColor(item) {
            this.selectedColor = item
            this.$emit('input', item.color)
            this.$emit('change', item.color)
        },
        getPopupContainer() {
            return this.$refs['color_picker']
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
    }
}
.color_picker{
    .active{
        height: 100%;
        width: 26px;
        border-radius: var(--borderRadius);
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
    }
}
</style>