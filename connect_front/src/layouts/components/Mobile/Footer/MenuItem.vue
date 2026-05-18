<template>
    <li class="truncate footer_item">
        <router-link 
            class="link"
            :to="{name: link.name}">
            <div class="icon">
                <i class="fi" :class="link.icon" />
                <a-badge 
                    v-if="link.badge && getCounter"
                    class="link_badge"
                    :count="getCounter.count"
                    :number-style="{
                        boxShadow: '0 0 0 0',
                        backgroundColor: primaryColor
                    }"/>
            </div>
            <div class="label truncate">
                {{ link.title }}
            </div>
        </router-link>
    </li>
</template>

<script>
export default {
    props: {
        link: {
            type: Object,
            required: true
        }
    },
    computed: {
        primaryColor() {
            return this.$store.state.config.primaryColor
        },
        getCounter() {
            return this.$store.getters['navigation/getMenuCounter'](this.link.name)
        }
    }
}
</script>