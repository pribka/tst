<template>
    <div ref="color_picker">
        <div v-if="typeList" class="color_list">
            <div v-for="item in colors" :key="item.color" @click="selectColor(item)">
                <div class="drop_color" :style="`background: ${item.color};`">
                    <i v-if="selectedColor && selectedColor.color === item.color" class="fi fi-rr-check"></i>
                </div>
            </div>
        </div>
        <a-dropdown 
            v-else 
            :trigger="['click']">
            <a-menu slot="overlay" class="drop_color_picker">
                <a-menu-item v-for="item in colors" :key="item.color" @click="selectColor(item)">
                    <div class="drop_color" :style="`background: ${item.color};`">
                        <i 
                            v-if="selectedColor && selectedColor.color === item.color" 
                            :class="selectedColor.color === '#ffffff' && 'text_current'"
                            class="fi fi-rr-check" />
                    </div>
                </a-menu-item>
            </a-menu>
            <div class="color_picker ant-btn ant-btn-ui ant-btn-circle ant-btn-icon-only" :class="value !== '#ffffff' && 'ant-btn-background-ghost'">
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
            type: String
        },
        typeList: {
            type: Boolean,
            default: false
        },
        changeColor: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            colors: [
                {
                    color: '#039be5',
                    oColor: 'rgba(3, 155, 229, 0.07)'
                },
                {
                    color: '#f43c36',
                    oColor: 'rgba(244, 60, 54, 0.07)'
                },
                {
                    color: '#ff5721',
                    oColor: 'rgba(255, 87, 33, 0.07)'
                },
                {
                    color: '#ff791b',
                    oColor: 'rgba(255, 121, 27, 0.07)'
                },
                {
                    color: '#ffb400',
                    oColor: 'rgba(255, 180, 0, 0.07)'
                },
                {
                    color: '#7cb342',
                    oColor: 'rgba(124, 179, 66, 0.07)'
                },
                {
                    color: '#209653',
                    oColor: 'rgba(32, 150, 83, 0.07)'
                },
                {
                    color: '#04ada0',
                    oColor: 'rgba(4, 173, 160, 0.07)'
                },
                {
                    color: '#3761e9',
                    oColor: 'rgba(55, 97, 233, 0.07)'
                },
                {
                    color: '#794cd8',
                    oColor: 'rgba(121, 76, 216, 0.07)'
                },
                {
                    color: '#a447bf',
                    oColor: 'rgba(164, 71, 191, 0.07)'
                },
                {
                    color: '#96a3b0',
                    oColor: 'rgba(150, 163, 176, 0.07)'
                },
                {
                    color: '#ec407a',
                    oColor: 'rgba(236, 64, 122, 0.07)'
                },
                {
                    color: '#ef304c',
                    oColor: 'rgba(239, 48, 76, 0.07)'
                },
                {
                    color: '#8cadd0',
                    oColor: 'rgba(140, 173, 208, 0.07)'
                },
                {
                    color: '#ffffff',
                    oColor: '#ffffff'
                },
                {
                    color: '#000000',
                    oColor: 'rgba(0, 0, 0, 0.07)'
                }
            ],
            selectedColor: null
        }
    },
    watch: {
        value(val) {
            if(val) {
                const find = this.colors.find(f => f.color === this.value || f.oColor === this.value)
                if(find) {
                    this.selectedColor = find
                } else {
                    this.selectedColor = this.colors[0]
                }
            } else {
                this.selectedColor = this.colors[0]
            }
        }
    },
    created() {
        if(!this.selectedColor && !this.value) {
            this.selectedColor = this.colors[0]
        }
        if(!this.selectedColor && this.value) {
            const find = this.colors.find(f => f.color === this.value || f.oColor === this.value)
            if(find) {
                this.selectedColor = find
            } else {
                this.selectedColor = this.colors[0]
            }
        }
    },
    methods: {
        selectColor(item) {
            this.selectedColor = item
            this.changeColor(item.oColor || item.color)
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
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    .active{
        width: 16px;
        height: 16px;
        border-radius: 50%;
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