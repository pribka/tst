<template>
    <WidgetWrapper :widget="widget" :class="isMobile && 'mobile_widget'">
        <template slot="actions">
            <component 
                v-if="!isMobile"
                :is="rangeInputComp" 
                :storeKey="storeKey" 
                useInject
                style="min-width: 230px;"
                :reloadAllData="reloadAllData" />
        </template>
        <div class="h-full overflow-y-auto">
            <component 
                :is="workPlanInit" 
                ref="workPlan"
                useInject
                :showHeader="false"
                :storeKey="storeKey" />
        </div>
    </WidgetWrapper>
</template>

<script>
export default {
    components: {
        WidgetWrapper: () => import('../WidgetWrapper.vue')
    },
    props: {
        widget: {
            type: Object,
            required: true
        }
    },
    computed: {
        isMobile() { 
            return this.$store.state.isMobile
        },
        rangeInputComp() {
            if(!this.init)
                return null
            return () => import("@apps/WorkPlan/Drawer/RangeInput.vue")
        },
        workPlanInit() {
            if(this.init)
                return () => import('@apps/WorkPlan/Drawer/index.vue')
            return null
        }
    },
    data() {
        return {
            init: false,
            storeKey: 'main'
        }
    },
    methods: {
        reloadAllData() {
            if(this.$refs.workPlan)
                this.$refs.workPlan.reloadAllData()
        }
    },
    mounted() {
        const hasInitializedKey = Boolean(this.$store.state.workplan?.mainDate?.[this.storeKey])
        if(!hasInitializedKey) {
            this.$store.commit('workplan/INIT_WORK_PLAN_BY_KEY', { storeKey: this.storeKey })
        }
        setTimeout(() => {
            this.init = true
        }, 500)
    },
}
</script>
