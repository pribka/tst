<template>
    <a-spin :spinning="loading" size="small">
        <span
            class="cursor-pointer item_name blue_color"
            @click="checkOpenOrder(record)">
            <span
                v-if="record.logistic_task"
                class="mr-1"
                v-tippy="{ inertia : true}"
                content="Добавлен в задание на доставку">
                <i class="fi fi-rr-map-marker-plus text_green"></i>
            </span>
            {{ record.counter }}
        </span>
    </a-spin>
</template>

<script>
import eventBus from '@/utils/eventBus.js'
export default {
    props: {
        record: {
            type: Object,
            required: true
        }
    },
    data () {
        return {
            loading: false
        }
    },
    methods: {
        openOrder() {
            let query = Object.assign({}, this.$route.query)
            if(!query?.order || query.order !== this.record.id) {
                query.order = this.record.id
                this.$router.push({query})
            }
        },
        async checkOpenOrder(){
            try {
                this.loading = true
                const { data } = await this.$http.get(`/crm/orders/${this.record.id}/action_info/`)
                if(data?.actions?.edit && data?.actions?.open_edit) {
                    eventBus.$emit('orderEdit', this.record)
                } else {
                    this.openOrder()
                }
            } catch(e) {
                console.log(e)
                this.openOrder()
            } finally {
                this.loading = false
            }
        }
    }
}
</script>