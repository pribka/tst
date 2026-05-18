<template>
    <div class="action_btn">
        <a-button 
            @click="openSupport()" 
            type="link" 
            v-tippy
            :content="$t('support.knowledgeBase')"
            class="text-current">
            <i class="fi fi-rr-interrogation" />
        </a-button>
    </div>
</template>

<script>
export default {
    methods: {
        openSupport() {
            const query = JSON.parse(JSON.stringify(this.$route.query))
            query.help = true
            if(query.newList)
                delete query.newList
            this.$router.push({ query })
        }
    }
}
</script>
