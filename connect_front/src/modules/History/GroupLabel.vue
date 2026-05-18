<template>
    <div class="cg_label" :class="!isMobile && 'l_sticky'">
        <div class="label_wrp">
            {{ label }}
        </div>
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
                return this.$t('history.today')
            }
            if (this.$moment().add(-1, 'days').isSame(this.group.key, 'day')) {
                return this.$t('history.yesterday')
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
.cg_label{
    display: flex;
    justify-content: center;
    padding-bottom: 15px;
    color: var(--gray);
    text-transform: capitalize;
    font-weight: 300;
    position: sticky;
    top: 5px;
    z-index: 10;
    .label_wrp{
        -webkit-backdrop-filter: saturate(180%) blur(20px);
        backdrop-filter: saturate(180%) blur(20px);
        background: rgba(255,255,255,0.8);
        padding: 0px 8px;
        border-radius: 20px;
    }
}
</style>