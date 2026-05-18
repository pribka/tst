<template>
    <div class="client_card" @click="openClient()">
        <TagsList :tags="client.tags" />
        <div class="card_divider"></div>
        <div class="client_card__item">
            {{ client.name }}
        </div>
        <div v-if="client.inn" class="client_card__item">
            <div class="item_label">
                {{ $t('helpdesk.bin') }}
            </div>
            <div class="item_value">
                {{ client.inn }}
            </div>
        </div>
        <div v-if="client.legal_address" class="client_card__item">
            <div class="item_label">
                {{ $t('helpdesk.legal_address') }}
            </div>
            <div class="item_value">
                {{ client.legal_address }}
            </div>
        </div>
    </div>
</template>

<script>
export default {
    components: {
        TagsList: () => import('./TagsList.vue')
    },
    props: {
        client: {
            type: Object,
            required: true
        }
    },
    methods: {
        openClient() {
            const query = Object.assign({}, this.$route.query)
            if(query.client && Number(query.client) !== this.client.id || !query.client) {
                query.client = this.client.id
                this.$router.push({query})
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.client_card{
    background: #fff;
    border-radius: 6px;
    padding: 20px;
    cursor: pointer;
    &__item{
        word-break: break-word;
        &:not(:last-child){
            margin-bottom: 10px;
        }
        .item_label{
            opacity: 0.6;
            font-size: 14px;
        }
    }
}
.card_divider{
    margin-top: 10px;
    margin-bottom: 10px;
    border-bottom: 1px solid #dfe0e4;
}
</style>