<template>
    <div class="date_label" :class="!isMobile && 'l_sticky'">
        {{ label }}
    </div>
</template>

<script>
import { mapState } from 'vuex'
export default {
    props: {
        group: {
            type: Object,
            required: true
        }
    },
    computed: {
        ...mapState({
            isMobile: state => state.isMobile
        }),
        label() {
            if (this.$moment().isSame(this.group.key, 'day')) {
                return this.$t('chat.today')
            }
            if (this.$moment().add(-1, 'days').isSame(this.group.key, 'day')) {
                return this.$t('chat.yesterday')
            }

            if (this.$moment().startOf("week").isSame(this.group.key, "week")) {
                return this.$moment(this.group.key).format('dddd')
            }

            return this.$moment(this.group.key).format('DD.MM.YYYY')
        }
    }
}
</script>

<style lang="scss" scoped>
.date_label{
    padding-left: 15px;
    padding-right: 15px;
    font-weight: 300;
    padding-bottom: 5px;
    padding-top: 5px;
    color: var(--gray);
    text-transform: capitalize;
    &.l_sticky{
        background: #f7f9fc;
        position: sticky;
        top: 0;
        z-index: 5;
    }
}
</style>