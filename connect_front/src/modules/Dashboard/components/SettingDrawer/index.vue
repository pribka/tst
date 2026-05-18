<template>
    <DrawerTemplate
        placement="right"
        v-model="visible"
        class="w_setting_drawer"
        :class="isMobile && 'mobile'"
        :width="drawerWidth"
        destroyOnClose
        @afterVisibleChange="afterVisibleChange"
        @close="visible = false">
        <template #title>
            <div class="drawer_title">{{ $t('dashboard.widget_settings') }}</div>
        </template>
        <div class="drawer_body">
            <component 
                v-if="widget" 
                ref="widgetConfig"
                :is="widgetComponent"
                :closeSettingDrawer="closeSettingDrawer"
                :widget="widget" />
        </div>
        <template #footer>
            <div class="items-center" :class="!isMobile && 'flex'">
                <a-button 
                    type="primary" 
                    :block="isMobile"
                    size="large"
                    @click="saveConfig()">
                    {{ $t('dashboard.save') }}
                </a-button>
                <a-button 
                    type="ui" 
                    :class="isMobile ? 'mt-1' : 'ml-2'" 
                    :ghost="isMobile"
                    size="large"
                    :block="isMobile"
                    @click="resetConfig()">
                    {{ $t('dashboard.reset') }}
                </a-button>
            </div>
        </template>
    </DrawerTemplate>
</template>

<script>
import eventBus from '@/utils/eventBus'
import DrawerTemplate from '@/components/DrawerTemplate.vue'
export default {
    components: {
        DrawerTemplate
    },
    data() {
        return {
            visible: false,
            widget: null
        }
    },
    computed: {
        windowWidth() {
            return this.$store.state.windowWidth
        },
        drawerWidth() {
            return this.windowWidth >= 700 ? 700 : this.windowWidth
        },
        widgetComponent() {
            if(this.widget?.widget?.setting_component) {
                return () => import(`./SettingWidgets/${this.widget.widget.setting_component}.vue`)
                    .then(module => {
                        return module
                    })
                    .catch(e => {
                        console.log('error')
                        return import(`./SettingWidgets/NotWidget.vue`)
                    })
            }
            return null
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    methods: {
        closeSettingDrawer() {
            this.visible = false
        },
        afterVisibleChange(vis) {
            if(!vis) {
                this.widget = null
            }
        },
        resetConfig() {
            this.$nextTick(() => {
                this.$refs.widgetConfig.resetConfig()
            })
        },
        saveConfig() {
            this.$nextTick(() => {
                this.$refs.widgetConfig.saveConfig()
            })
        }
    },
    mounted() {
        eventBus.$on('openSetting', widget => {
            this.widget = widget
            this.visible = true
        })
    },
    beforeDestroy() {
        eventBus.$off('openSetting')
    }
}
</script>