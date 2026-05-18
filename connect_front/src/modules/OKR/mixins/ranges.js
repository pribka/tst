export default {
    computed: {
        ranges() {
            return { 
                [this.$t('okr.year')]: [
                    this.$moment().startOf('year'),
                    this.$moment().endOf('year')
                ],
                [this.$t('okr.firstHalf')]: [
                    this.$moment().startOf('year'),
                    this.$moment().month(5).endOf('month')
                ],
                [this.$t('okr.secondHalf')]: [
                    this.$moment().month(6).startOf('month'),
                    this.$moment().endOf('year')
                ],
                [`1 ${this.$t('okr.quarter')}`]: [
                    this.$moment().startOf('year'),
                    this.$moment().month(2).endOf('month')
                ],
                [`2 ${this.$t('okr.quarter')}`]: [
                    this.$moment().month(3).startOf('month'),
                    this.$moment().month(5).endOf('month')
                ],
                [`3 ${this.$t('okr.quarter')}`]: [
                    this.$moment().month(6).startOf('month'),
                    this.$moment().month(8).endOf('month')
                ],
                [`4 ${this.$t('okr.quarter')}`]: [
                    this.$moment().month(9).startOf('month'),
                    this.$moment().endOf('year')
                ]
            }
        }
    }
}