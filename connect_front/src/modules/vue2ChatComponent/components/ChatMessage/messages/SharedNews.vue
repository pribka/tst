<template>
    <div 
        class="cursor-pointer reply_message truncate w-full mt-2 mb-2 pt-1 lg:pt-3 pb-1 lg:pb-3 pr-2" 
        @click="open()">
        <div class="label font-semibold truncate">
            {{ $t('chat.news') }}: {{ stringView }}
        </div>
    </div>
</template>

<script>
export default {
    props: {
        message: {
            type: Object,
            required: true
        }
    },
    computed: {
        stringView() {
            return this.message.share.string_view
        }
    },
    methods: {
        open() {
            let query = Object.assign({}, this.$route.query)
            if(query.news && query.news !== this.news.id || !query.news) {
                query.news = this.message.share.id
                this.$router.push({query})
            }
        }
        
    }
}
</script>