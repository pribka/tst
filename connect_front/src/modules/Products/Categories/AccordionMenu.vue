<template>
    <ul>
        <li 
            v-for="item in menuItem" 
            :key="item.key">
            <div 
                class="flex justify-between items-center w-full menu_item"
                :class="{'active_item': isExpand(item.key) || isActive(item.key)}"
                @click="selectKey(item.key, item.is_endpoint)">
                <div 
                    :style="'padding-left:' + deepIndent">
                    <span>{{ item.title }}</span>  
                    <span class="item_count ml-1">({{ item.goods_count }})</span>
                </div>
                <a-button 
                    v-if="!item.is_endpoint"
                    type="circle"
                    size="small"
                    class="expand_button"
                    :class="{'active_button': isExpand(item.key) | isActive(item.key)}">
                    <i :class="isExpand(item.key) ? 'fi fi-rr-minus' : 'fi fi-rr-plus'"></i>
                </a-button>
            </div>
            <transition
                name="expand"
                @enter="enter"
                @after-enter="afterEnter"
                @leave="leave">
                <ul 
                    v-if="!item.is_endpoint"
                    v-show="isExpand(item.key)">
                    <Menu 
                        :selectMobileEl="selectMobileEl"
                        :onExpand="onExpand"
                        :activeEl="activeEl"
                        :menuItem="item.children"
                        :expandedKeys="expandedKeys"
                        :selectedKeys="selectedKeys"
                        :parentKeys="parentKeys.concat(item.key)" />
                </ul>
            </transition>
        </li>
    </ul>
</template>

<script>
export default {
    name: "Menu",
    props: {
        menuItem: {
            type: [Array, Object],
            required: true
        },
        expandedKeys: {
            type: Array,
            default: () => []
        },
        parentKeys: {
            type: Array,
            default: () => []
        },
        selectedKeys: {
            type: Array,
            default: () => []
        },
        activeEl: {
            type: Array,
            default: () => []
        },
        onExpand: {
            type: Function,
            default: () => {}
        },
        selectMobileEl: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        deepIndent() {
            return `${this.parentKeys.length * 15}px`
        }
    },
    methods: {
        isExpand(key) {
            if(this.expandedKeys.length)
                return this.expandedKeys.includes(key)
            return false
        },
        isActive(key) {
            if(this.activeEl.length)
                return this.activeEl.includes(key)
            return false
        },
        selectKey(key, is_endpoint) {
            this.activeEl.splice(0)
            this.activeEl.push(key) 

            this.selectedKeys.splice(0)
            this.selectedKeys.push(key) 
        
            const isExpand = this.isExpand(key)
            this.expandedKeys.splice(0)
            this.expandedKeys.push(...this.parentKeys)
            if(!is_endpoint && !isExpand)
                this.expandedKeys.push(key)  

            this.onExpand(this.expandedKeys)
            this.selectMobileEl(this.selectedKeys)
        },
        // Animations
        enter(el) {
            el.style.height = 'auto'
            const height = getComputedStyle(el).height
            el.style.height = 0
            setTimeout(() => {
                el.style.height = height
            })
        },
        afterEnter(el) {
            el.style.height = 'auto'
        },
        leave(el) {
            el.style.height = getComputedStyle(el).height
            setTimeout(() => {
                el.style.height = 0
            })
        }
    },
    beforeDestroy() {
        this.activeEl.splice(0)
    }
}
</script>

<style lang="scss" scoped>
    .menu_item {
        padding: 15px;
        cursor: pointer;
    }
    .active_item {
        background-color: rgb(244, 244, 244);
        color: #3f83cc;
    }
    .expand_button {
        display: flex;
        justify-content: center;
        align-items: center;
        
        line-height: 100%;
    }
    .active_button {
        color: #3f83cc;
        border-color: #3f83cc;
    }
    // Animation
    .expand-enter-active, .expand-leave-active {
        transition: height 0.2s;
        overflow: hidden;
    }
    .item_count{
        color: #999;
        font-size: 11px;
    }
</style>