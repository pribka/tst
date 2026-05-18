<template>
    <div 
        class="cursor-pointer reply_message truncate w-full mt-2 mb-2 pt-1 lg:pt-3 pb-1 lg:pb-3 pr-2" 
        @click="open()">
        <div class="label font-semibold truncate">
            {{ $t('chat.ticket') }}: 
        </div>
        <div class="truncate">
            {{ $t('chat.author') }}: {{ ticketAuthor }}
        </div>
        <div class="truncate">
            {{ $t('chat.configuration') }}: {{ ticketConfig }}
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
        ticketAuthor() {
            return this.ticket.author.full_name
        },
        ticketConfig() {
            return this.ticket.config_1c.name
        },
        ticket() {
            return this.message.share
        }
    },
    methods: {
        open() {
            let query = Object.assign({}, this.$route.query)
            if(query.ticket && query.ticket !== this.ticket.id || !query.ticket) {
                query.ticket = this.ticket.id
                this.$router.push({query})
            }
        }
    }
}
</script>