<template>
    <div v-if="getAsideStat">
        <span class="font-semibold">{{ $t('task.total_sum') }}</span> <span>{{ getAsideStat.total_sum }} {{ currency }}</span>
    </div>
</template>

<script>
import headerMixins from './headerMixins.js'
import { priceFormatter } from '@/utils'
export default {
    mixins: [
        headerMixins
    ],
    computed: {
        getAsideStat() {
            return this.$store.getters['task/getAsideStat'](this.task.id, 'budget')
        },
        data() {
            if(this.getAsideStat?.total_sum)
                return this.getAsideStat
            else
                return null
        },
        currency() {
            if(this.data.currency)
                return this.data.currency.icon
            else
                return ''
        }
    },
    created() {
        this.getInfo()
    },
    methods: {
        priceFormat(price) {
            return priceFormatter(String(price))
        },
        async getInfo() {
            if(!this.data) {
                try {
                    this.loading = true
                    await this.$store.dispatch('task/getAsideStat', {
                        task: this.task,
                        part: 'budget'
                    })
                } catch(e) {
                    console.log(e)
                } finally {
                    this.loading = false
                }
            }
        }
    }
}
</script>