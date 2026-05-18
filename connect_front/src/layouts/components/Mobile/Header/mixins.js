import { errorHandler } from '@/utils/index.js'
export default {
    data() {
        return {
            workPlanShow: false,
            notification: null,
            aiButton: null,
            cart: null,
            workPlan2: null,
            workPlan: null,
            loading: false
        }
    },
    created() {
        this.getWorkPlan()

        this.setNotification()
        if(this.user?.use_ai_bot)
            this.aiButton = () => import(`@apps/AIAssistant/AIButton.vue`)
        if(this.config?.header_setting?.product_cart)
            this.cart = () => import('./Cart.vue')
    },
    watch: {
        'config.header_setting.notification': {
            handler() {
                this.setNotification()
            },
            immediate: true
        }
    },
    methods: {
        setNotification() {
            this.notification = this.config?.header_setting?.notification
                ? () => import(`./Notification`)
                : null
        },
        async getWorkPlan() {
            try {
                //this.$store.commit('SET_WORK_PLAN_LOADING', true)
                const { data } = await this.$http.get('/personal_planes/work_plan_show/')
                if(data) {
                    this.workPlanShow = data.WorkPlanShowV2
                    if(this.workPlanShow)
                        this.workPlan2 = () => import(`./WorkPlan`)
                }
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                //this.$store.commit('SET_WORK_PLAN_LOADING', true)
            }
        }
    }
}
