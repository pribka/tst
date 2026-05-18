<template>
    <div>
        <a-button 
            type="ui" 
            ghost 
            flaticon 
            :loading="actionLoading"
            shape="circle"
            icon="fi-rr-menu-dots-vertical"
            @click="visible = true" />
        <ActivityDrawer 
            v-model="visible" 
            useVis
            :visibleChange="visibleChange"
            :cDrawer="closeDrawer">
            <ActivityItem v-if="loading">
                <div class="flex justify-center w-full">
                    <a-spin size="small" />
                </div>
            </ActivityItem>
            <template v-if="actions && !loading">
                <ActivityItem v-if="actions.config && actions.config.availability" @click="openWidgetSetting()">
                    <div class="flex items-center">
                        <i class="fi fi-rr-settings icon"></i> {{ $t('dashboard.settings') }}
                    </div>
                </ActivityItem>
                <ActivityItem @click="editNameHandler()">
                    <div class="flex items-center">
                        <i class="fi fi-rr-pencil icon"></i> {{ $t('dashboard.rename_widget') }}
                    </div>
                </ActivityItem>
                <template v-if="widgets.length > 1">
                    <ActivityItem v-if="widgetsLength" @click="moveDown()">
                        <div class="flex items-center">
                            <i class="fi fi-rr-arrow-circle-down icon"></i> {{ $t('dashboard.move_down') }}
                        </div>
                    </ActivityItem>
                    <ActivityItem v-if="widget.mobile_index > 0" @click="moveUp()">
                        <div class="flex items-center">
                            <i class="fi fi-rr-arrow-circle-up icon"></i> {{ $t('dashboard.move_up') }}
                        </div>
                    </ActivityItem>
                </template>
                <template v-if="widget.showDesktop">
                    <ActivityItem v-if="widget.is_desktop" @click="showDesctopVersion(false)">
                        <div class="flex items-center">
                            <i class="fi fi-rr-computer"></i> {{ $t('dashboard.hide_pc') }}
                        </div>
                    </ActivityItem>
                    <ActivityItem v-else @click="showDesctopVersion(true)">
                        <div class="flex items-center">
                            <i class="fi fi-rr-computer"></i> {{ $t('dashboard.show_pc') }}
                        </div>
                    </ActivityItem>
                </template>
                <ActivityItem v-if="actions.delete && actions.delete.availability" @click="deleteWidgetMobile()">
                    <div class="text-red-500 flex items-center">
                        <i class="fi fi-rr-trash icon"></i> {{ $t('dashboard.delete') }}
                    </div>
                </ActivityItem>
            </template>
        </ActivityDrawer>
    </div>
</template>

<script>
import mixins from './mixins.js'
import { ActivityItem, ActivityDrawer } from '@/components/ActivitySelect'
export default {
    mixins: [mixins],
    components: {
        ActivityItem,
        ActivityDrawer
    },
    computed: {
        widgetsLength() {
            const wLength = this.widgets.length - 1
            return wLength !== this.widget.mobile_index ? true : false
        }
    },
    methods: {
        closeDrawer() {
            this.visible = false
        },
        async moveDown() {
            try {
                await this.$store.dispatch('dashboard/moveActiveWidget', {
                    widget: this.widget,
                    type: 'down'
                })
            } catch(e) {
                console.log(e)
            }
        },
        async moveUp() {
            if(this.widget.mobile_index > 0) {
                try {
                    await this.$store.dispatch('dashboard/moveActiveWidget', {
                        widget: this.widget,
                        type: 'up'
                    })
                } catch(e) {
                    console.log(e)
                }
            }
        }
    }
}
</script>