import { errorHandler } from '@/utils/index.js'
export default {
    data() {
        return {
            appConfig: null,
            workPlanShow: null,
            notification: null,
            calendar: null,
            aiButton: null,
            cart: null,
            workPlan: null,
            support: null
        }
    },
    created() {
        this.getWorkPlan()

        this.appConfig = JSON.parse(JSON.stringify(this.config))
        if(this.appConfig?.header_setting?.notification)
            this.notification = () => import(`./Notification`)
        if(this.appConfig?.header_setting?.calendar)
            this.calendar = () => import(`./Calendar`)
        if(this.user?.use_ai_bot)
            this.aiButton = () => import(`@apps/AIAssistant/AIButton.vue`)
        if(this.appConfig?.header_setting?.product_cart)
            this.cart = () => import('./Cart.vue')
        if(this.appConfig?.header_setting?.support)
            this.support = () => import('./Support.vue')
    },
    methods: {
        async deleteDemoData() {
            this.$confirm({
                title: this.$t('delete_demodata_q'),
                content: '',
                okText: this.$t('remove'),
                okType: 'danger',
                zIndex: 2000,
                closable: true,
                maskClosable: true,
                cancelText: this.$t('Close'),
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post('/demo/delete/')
                            .then(({data}) => {
                                if(data?.message) {
                                    this.$message.success(data.message)
                                    setTimeout(() => {
                                        window.location.reload()
                                    }, 1500)
                                }
                                resolve()
                            })
                            .catch(error => {
                                errorHandler({error})
                                reject(e)
                            })
                    })
                }
            })
        },
        async getWorkPlan() {
            try {
                const { data } = await this.$http.get('/personal_planes/work_plan_show/')
                if(data) {
                    this.workPlanShow = data
                    if(this.workPlanShow?.WorkPlanShow)
                        this.workPlan = () => import(`./WorkPlan`)
                }
            } catch(error) {
                errorHandler({error, show: false})
            }
        }
    }
}