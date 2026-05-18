<template>
    <div>
        <a-button 
            size="large"
            class="open_button"
            :loading="loading" 
            @click="visible = true">
            <i 
                class="fi" 
                :class="activeIcon || 'fi-rr-apps'"></i>
        </a-button>
        <ActivityDrawer v-model="visible">
            <ActivityItem 
                :class="{'active_option': item.type === active}"
                v-for="item in gridType" 
                :key="item.type"
                @click="active = item.type">
                <i 
                    class="fi mr-2" 
                    :class="item.icon"></i>
                {{item.title}}
            </ActivityItem>
        </ActivityDrawer>
    </div>
</template>

<script>

import { ActivityItem, ActivityDrawer } from '@/components/ActivitySelect'

export default {
    components: {
        ActivityItem, 
        ActivityDrawer
    },
    computed: {
        active: {
            get() {
                return this.$store.state.products.activeGridType
            },
            set(val) {
                this.$store.commit('products/CHANGE_ACTIVE_TYPE', val)
            }
        },
        activeIcon() {
            const active = this.active
            if(active && this.gridType?.length)
                return this.gridType.find(item => item.type === active).icon
            return null
        },
        gridType() {
            return this.$store.state.products.gridType
        }
    },
    data() {
        return {
            loading: false,
            visible: false,
        }
    },
    async created() {
        if(!this.gridType?.length)
            await this.getType()
        this.$store.commit('products/SET_DEFAULT_GRID_TYPE')
    },
    methods: {
        async getType() {
            try {
                this.loading = true
                await this.$store.dispatch('products/getGridType')
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        }
    }
}
</script>

<style scoped>
.open_button {
    display: flex;
    justify-content: center;
    align-items: center;

    line-height: 100%;
}
.active_option {
    color: var(--blue);
}
</style>