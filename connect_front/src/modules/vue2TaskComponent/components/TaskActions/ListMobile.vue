<template>
    <div>
        <UserDrawer
            id="changeUser"
            ref="changeUserRef"
            @input="changeUser"
            hide
            :submitButtonText="$t('Save')"
            :title="$t('task.select')"/>

        <a-button
            v-if="showButton"
            size="default"
            class="open_button"
            type="link"
            :loading="loading" 
            @click="openDrawer">
            <i class="fi fi-rr-menu-burger"></i>
        </a-button>
        <ActivityDrawer 
            v-model="visible" 
            @afterVisibleChange="visibleChange">
            <ActivityItem
                v-if="!dropActions && actionLoading"
                key="menu_loader">
                <div class="w-full flex justify-center">
                    <a-spin size="small" />
                </div>
            </ActivityItem>
            <template v-if="dropActions">
                <template v-if="!item.is_auction && dropActions.change_status && showStatus && cStatusFiltered.length">
                    <ActivityItem
                        v-if="statusLoader"
                        key="loader">
                        <a-spin size="small" />
                    </ActivityItem>
                    <template v-else>
                        <ActivityItem
                            v-for="status in cStatusFiltered"
                            :key="status.code"
                            @click="changeStatus(status)">
                            <div v-if="status.color !== 'default'"  class="mob_badge">
                                <a-badge :color="status.color" />
                            </div>
                            {{ status.btn_title || status.name }}
                        </ActivityItem>
                    </template>
                </template>
                <ActivityItem
                    v-for="button in actionButtons"
                    :key="button.key"
                    @click="button.handler">
                    <i class="fi mr-2" :class="button.icon"></i>
                    {{ button.label }}
                </ActivityItem>

                <ActivityItem 
                    v-if="dropActions.delete && !item.children_count"
                    key="delete" 
                    @click="deleteTask()">
                    <div class="text-red-500">
                        <i class="fi fi-rr-trash mr-2"></i>
                        {{$t('task.remove')}}
                    </div>
                </ActivityItem>
            </template>
        </ActivityDrawer>
    </div>
</template>

<script>
import { ActivityItem, ActivityDrawer } from '@/components/ActivitySelect'
import mixins from './mixins.js'
export default {
    components: {
        ActivityItem, 
        ActivityDrawer,
        UserDrawer: () => import("@apps/DrawerSelect/index.vue")
    },
    mixins: [
        mixins
    ],
    computed: {
        cStatusFiltered() {
            const changeCooperatorStatuses = this.dropActions?.change_cooperator_status?.available_statuses
            const onlyCooperator = this.dropActions?.change_cooperator_status?.only_coop
            if (onlyCooperator && changeCooperatorStatuses?.length) {
                return changeCooperatorStatuses
            }

            const availableStatuses = this.dropActions?.change_status?.available_statuses
            if (availableStatuses?.length) {
                return availableStatuses
            }
            return []
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return {
            visible: false,
        }
    },
    methods: {
        openDrawer() {
            this.visible = true
        }
    }
}
</script>

<style scoped>
.open_button {
    display: flex;
    justify-content: center;
    align-items: center;

    line-height: 100%;
}
.active_option {
    color: var(--blue);
}
.mob_badge{
    width: 22px;
    height: 22px;
    margin-right: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    &::v-deep{
        .ant-badge{
            .ant-badge-status-dot{
                width: 10px;
                height: 10px;
            }
        }
    }
}
</style>