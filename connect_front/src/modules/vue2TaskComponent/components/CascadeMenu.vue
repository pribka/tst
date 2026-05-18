<template>
    <a-menu
        v-model="current"
        mode="horizontal"
        class="cascade_menu select-none">
        <a-menu-item
            v-for="menu in router"
            :key="menu.name"
            @click="menuClick">
            {{ $t(`task.${menu.name}`) }}
        </a-menu-item>
    </a-menu>
</template>

<script>
import router from '../config/router'
export default {
    data() {
        return {
            router: router({state: this.$store.state}),
            current: ['task-list-page']
        }
    },
    created() {
        this.current = [this.$route.name]
    },
    methods: {
        menuClick(val) {
            if(this.$route.name !== val.key)
                this.$router.push({name: val.key})
        }
    }
}
</script>