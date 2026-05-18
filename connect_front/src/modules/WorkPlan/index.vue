<template>
    <div :class="isMobile ? 'action_btn' : 'mr-2'">
        <a-button 
            v-if="isMobile"
            type="link"
            flaticon
            class="workplan_btn work_btn"
            icon="fi-rr-play"
            @click="openHandler()" />
        <a-button 
            v-else
            class="flex items-center justify-center work_btn ml-4 work_btn_animate"
            @click="openHandler()">
            {{ $t('workplan.my_day') }}
            <i class="fi fi-rr-play ml-5" />
        </a-button>
        <component 
            :is="myPlanDrawerAsync" 
            :storeKey="storeKey"
            v-if="$route.query.my_plan" />
    </div>
</template>

<script>
import store from './store/index.js'
import { storeKeyDefault } from './utils.js'
const TASK_ICON_NAME = '\u0417\u0430\u0434\u0430\u0447\u0438'
const EVENT_ICON_NAME = '\u0421\u043e\u0431\u044b\u0442\u0438\u0435'
export default {
    data() {
        return {
            myPlanDrawerAsync: null,
            storeKey: storeKeyDefault
        }
    },
    computed: {
        isMobile() { 
            return this.$store.state.isMobile
        }
    },
    watch: {
        '$route.query.my_plan': {
            immediate: true,
            handler(v) {
                if (v && !this.myPlanDrawerAsync)
                    this.myPlanDrawerAsync = () => import(/* webpackPrefetch: true, webpackChunkName: "myplan-show-drawer" */ './Drawer/index.vue')
            }
        },
    },
    sockets: {
        notify({ data }) {
            if (data.event_type === 'new_notification') {
                const res = data.obj
                if (res.icon_name === TASK_ICON_NAME && res.message) {
                    const match = res.message.match(/data-link-query='([^']+)'/)
                    if (match && match[1]) {
                        try {
                            const parsed = JSON.parse(match[1])
                            const item = { id: parsed.task }
                            this.$store.dispatch('workplan/updateItem', {
                                item,
                                list: 'taskList'
                            })
                        } catch(e) {}
                    }
                }
                if (res.icon_name === EVENT_ICON_NAME && res.message) {
                    const match = res.message.match(/data-link-query='([^']+)'/)
                    if (match && match[1]) {
                        try {
                            const parsed = JSON.parse(match[1])
                            const item = { id: parsed.event }
                            this.$store.dispatch('workplan/updateItem', {
                                item,
                                list: 'eventList'
                            })
                        } catch(e) {}
                    }
                }
            }
        }
    },
    created() {
        if (!this.$store.hasModule('workplan'))
            this.$store.registerModule('workplan', store)
    },
    methods: {
        openHandler() {
            const query = JSON.parse(JSON.stringify(this.$route.query))
            query.my_plan = true
            this.$router.replace({query})
        }
    }
}
</script>

<style lang="scss" scoped>
.work_btn{
    min-height: 32px;
    background-color: #6eb14d!important;
    border-color: #6eb14d!important;
    color: #fff!important;
    &.work_btn_animate{
        transition: box-shadow 0.3s ease;
        i{
            transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
        }
        &:hover{
            animation: work-btn-shadow-pulse 1.4s ease-in-out infinite;
            i{
                transform: scale(1.2);
            }
        }
    }
}

@keyframes work-btn-shadow-pulse{
    0%{
        box-shadow: 0 0 0 0 rgba(128, 192, 97, 0.45);
    }
    70%{
        box-shadow: 0 0 0 8px rgba(128, 192, 97, 0);
    }
    100%{
        box-shadow: 0 0 0 0 rgba(128, 192, 97, 0);
    }
}
</style>
