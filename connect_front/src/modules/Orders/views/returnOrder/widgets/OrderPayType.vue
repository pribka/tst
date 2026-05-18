<template>
    <div class="payment_form">
        <a-spin :spinning="loading">
            <div 
                v-if="paymentForm" 
                class="payment_title">
                <span class="font-light">Форма оплаты:</span> 
                {{ paymentForm.name }}
            </div>
            <div 
                v-if="stages && stages.length" 
                class="stages mt-3">
                <div 
                    v-for="item in stages" 
                    :key="item.id" 
                    class="stages_item">
                    <div 
                        v-if="item.payment_option && item.payment_option.name" 
                        class="name font-semibold mb-1">
                        {{ item.payment_option.name }}
                    </div>
                    <div 
                        v-if="item.duration" 
                        class="duration mb-1">
                        <span class="font-light">Срок оплаты:</span> {{ payDuration(item.duration) }}
                    </div>
                    <div 
                        v-if="item.payment_percent" 
                        class="duration">
                        <span class="font-light">Процент оплаты:</span> {{ item.payment_percent }}%
                    </div>
                </div>
            </div>
        </a-spin>
    </div>
</template>

<script>
import { declOfNum } from '@/utils/utils.js'
export default {
    props: {
        form: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            loading: false,
            paymentForm: null,
            stages: []
        }
    },
    watch: {
        'form.contract'(val) {
            if(val) {
                this.getPayType(val)
            }
        }
    },
    methods: {
        payDuration(duration) {
            return `${duration} ${declOfNum(duration, ['день', 'дня', 'дней'])}`
        },
        async getPayType(code) {
            try {
                this.loading = true
                const { data } = await this.$http.get('/catalogs/contracts/payment/', {
                    params: {
                        code
                    }
                })
                if(data) {
                    if(data.payment_form?.name) {
                        this.paymentForm = data.payment_form
                    } else {
                        this.paymentForm = {}
                        this.paymentForm.name = 'Любая'
                    }
                    this.stages = data.stages
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.payment_title{
    font-size: 16px;
}
.stages{
    .stages_item{
        &:not(:last-child){
            border-bottom: 1px solid var(--border2);
            padding-bottom: 10px;
            margin-bottom: 10px;
        }
    }
}
</style>