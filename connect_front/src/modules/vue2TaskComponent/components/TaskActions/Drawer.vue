<template>
    <div :class="isMobile && 'w-full'" ref="actionButton">
        <UserDrawer
            id="changeUser"
            ref="changeUserRef"
            @input="changeUser"
            hide
            :title="$t('task.select_user')"/>

        <div v-if="isMobile" class="flex items-center w-full">
            <a-button
                v-if="dropActions && dropActions.change_status && currentStatus"
                type="primary"
                class="md:px-6 lg:px-6"
                block
                size="large"
                :loading="loading"
                @click="changeStatus(currentStatus)">
                {{ currentStatus.btn_title || currentStatus.name }}
            </a-button>
            <div class="w-full" v-else></div>
            <a-button
                type="primary"
                :loading="actionLoading"
                :disabled="loading"
                size="large"
                class="ml-1 dots_btn"
                flaticon
                icon="fi-rr-menu-dots-vertical"
                @click="openDrawer" />
            <ActivityDrawer v-model="visible">
                <ActivityItem
                    v-if="!dropActions && actionLoading"
                    key="menu_loader">
                    <div class="w-full flex justify-center">
                        <a-spin size="small" />
                    </div>
                </ActivityItem>
                <template v-if="dropActions">
                    <template v-if="changeStatusVisible">
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
                                <div v-if="status.color !== 'default'" class="mob_badge">
                                    <a-badge :color="status.color" />
                                </div>
                                {{ status.btn_title ? status.btn_title : status.name }}
                            </ActivityItem>
                        </template>
                    </template>
                    <ActivityItem
                        v-for="item in menuItems"
                        :key="item.key"
                        @click="item.handler">
                        <i class="fi mr-2" :class="item.icon"></i>
                        {{ item.label}}
                    </ActivityItem>
                    <ActivityItem 
                        v-if="dropActions.delete && !item.children_count"
                        key="delete" 
                        @click="deleteFunc()">
                        <div class="text-red-500">
                            <i class="fi fi-rr-trash mr-2"></i>
                            {{$t('task.remove')}}
                        </div>
                    </ActivityItem>
                </template>
            </ActivityDrawer>
        </div>
        <a-button-group v-else class="w-full md:w-auto lg:w-auto mr-2">
            <a-button
                v-if="dropActions && dropActions.change_status && currentStatus"
                type="primary"
                class="md:px-6 lg:px-6"
                :size="isFull ? 'large' : 'default'"
                :loading="loading"
                @click="changeStatus(currentStatus)">
                {{ currentStatus.btn_title || currentStatus.name }}
            </a-button>
            <a-dropdown 
                :trigger="dropTrigger" 
                :disabled="actionLoading"
                @visibleChange="dropdownVisibleChange"
                :getPopupContainer="() => $refs.actionButton">
                <a-button
                    type="primary"
                    :loading="actionLoading"
                    flaticon
                    class="flex items-center justify-center"
                    :size="isFull ? 'large' : 'default'"
                    icon="fi-rr-menu-dots-vertical" />
                <a-menu slot="overlay">
                    <template v-if="dropActions">
                        <a-menu-item 
                            v-if="statusLoader"
                            key="loader"
                            class="flex justify-center">
                            <a-spin size="small" />
                        </a-menu-item>
                        <template v-if="changeStatusVisible">
                            <a-sub-menu>
                                <template #title>
                                    <i class="fi fi-rr-check-circle mr-2" />
                                    {{ $t('task.change_status') }}
                                </template>
                                <a-menu-item 
                                    v-for="status in cStatusFiltered"
                                    :key="status.code"
                                    class="flex items-center"
                                    @click="changeStatus(status)">
                                    <a-badge :color="status.color" />
                                    {{ status.btn_title ? status.btn_title : status.name }}
                                </a-menu-item>
                            </a-sub-menu>
                            <a-menu-divider />
                        </template>

                        <template v-for="item in menuItems">
                            <a-sub-menu v-if="item.children && item.children.length" :key="item.key">
                                <template #title>
                                    <i class="fi mr-2" :class="item.icon" />
                                    {{ item.label }}
                                </template>
                                <a-menu-item
                                    v-for="cButton in item.children"
                                    :key="cButton.key"
                                    class="flex items-center"
                                    @click="cButton.handler">
                                    <i class="fi mr-2" :class="cButton.icon" />
                                    {{ cButton.label }}
                                </a-menu-item>
                            </a-sub-menu>
                            <a-menu-item
                                v-else
                                :key="item.key"
                                class="flex items-center"
                                @click="item.handler">
                                <i class="fi mr-2" :class="item.icon"></i>
                                {{ item.label}}
                            </a-menu-item>
                        </template>
                        <template v-if="dropActions.delete && !item.children_count">
                            <a-menu-divider />
                            <a-menu-item
                                class="text-red-500 flex items-center" 
                                key="delete" 
                                @click="deleteFunc()">
                                <i class="fi fi-rr-trash mr-2"></i>
                                {{$t('task.remove')}}
                            </a-menu-item>
                        </template>
                    </template>
                </a-menu>
            </a-dropdown>
        </a-button-group>
    </div>
</template>


<script>
import mixins from './mixins.js'
import { ActivityItem, ActivityDrawer } from '@/components/ActivitySelect'
export default {
    mixins: [
        mixins
    ],
    components: {
        ActivityItem,
        ActivityDrawer,
        UserDrawer: () => import("@apps/DrawerSelect/index.vue")
    },
    computed: {
        changeStatusVisible() {
            return !this.item.is_auction && (this.dropActions.change_status || this.dropActions.change_cooperator_status) && this.showStatus && this.cStatusFiltered?.length
        },
        menuItems() {
            let buttons = []
            if(this.isMobile) {
                buttons = [
                    {
                        key: 'add_subtask',
                        visible: this.dropActions.add_subtask && this.item.level < 3,
                        handler: this.addSubtaskFunc,
                        icon: 'fi-rr-folder-tree',
                        label: this.$t('task.add_subtask')
                    },
                    {
                        key: 'addTask',
                        visible: this.dropActions.add_task,
                        handler: this.addTaskFunc,
                        icon: 'fi-rr-list-check',
                        label: this.$t('task.add_task')
                    },
                    {
                        key: 'set_sprint',
                        visible: this.dropActions.set_sprint,
                        handler: this.addToSprint,
                        icon: 'fi-rr-arrow-turn-down-right',
                        label: this.$t('task.add_to_sprint')
                    },
                    {
                        key: 'unset_sprint',
                        visible: this.dropActions.unset_sprint,
                        handler: this.removeToSprint,
                        icon: 'fi-rr-cross-circle',
                        label: this.$t('task.remove_from_sprint')
                    },

                    {
                        key: 'update_operator',
                        visible: this.dropActions?.update_operator?.availability,
                        handler: this.updateOperator,
                        icon: 'fi-rr-refresh',
                        label: this.$t('task.change_person')
                    },
                    {
                        key: 'update_owner',
                        visible: this.dropActions?.update_owner?.availability,
                        handler: this.updateOwner,
                        icon: 'fi-rr-user-add',
                        label: this.$t('task.delegate_task')
                    },
                    {
                        key: 'share',
                        visible: this.dropActions.share,
                        handler: this.share,
                        icon: 'fi-rr-share',
                        label: this.$t('task.share_to_chat')
                    },
                    {
                        key: 'edit',
                        visible: this.dropActions.edit,
                        handler: this.editFull,
                        icon: 'fi-rr-edit',
                        label: this.$t('task.edit')
                    },
                    {
                        key: 'copy',
                        visible: this.dropActions.copy,
                        handler: this.copyFunc,
                        icon: 'fi-rr-copy-alt',
                        label: this.$t('task.copy')
                    },
                ]
            } else {
                buttons = [
                    {
                        key: 'add_subtask',
                        visible: this.dropActions.add_subtask && this.item.level < 3,
                        handler: this.addSubtaskFunc,
                        icon: 'fi-rr-folder-tree',
                        label: this.$t('task.add_subtask')
                    },
                    {
                        key: 'addTask',
                        visible: this.dropActions.add_task,
                        handler: this.addTaskFunc,
                        icon: 'fi-rr-list-check',
                        label: this.$t('task.add_task')
                    },
                    {
                        key: 'set_sprint',
                        visible: this.dropActions.set_sprint,
                        handler: this.addToSprint,
                        icon: 'fi-rr-arrow-turn-down-right',
                        label: this.$t('task.add_to_sprint')
                    },
                    {
                        key: 'unset_sprint',
                        visible: this.dropActions.unset_sprint,
                        handler: this.removeToSprint,
                        icon: 'fi-rr-cross-circle',
                        label: this.$t('task.remove_from_sprint')
                    },

                    {
                        key: 'update_operator',
                        visible: this.dropActions?.update_operator?.availability,
                        handler: this.updateOperator,
                        icon: 'fi-rr-refresh',
                        label: this.$t('task.change_person')
                    },
                    {
                        key: 'update_owner',
                        visible: this.dropActions?.update_owner?.availability,
                        handler: this.updateOwner,
                        icon: 'fi-rr-user-add',
                        label: this.$t('task.delegate_task')
                    },
                    {
                        key: 'share',
                        visible: this.dropActions.share,
                        handler: this.share,
                        icon: 'fi-rr-share',
                        label: this.$t('task.share_to_chat')
                    },
                    {
                        key: 'edit',
                        visible: this.dropActions.edit,
                        handler: this.editFull,
                        icon: 'fi-rr-edit',
                        label: this.$t('task.edit')
                    },
                    {
                        key: 'copy',
                        visible: this.dropActions.copy,
                        handler: this.copyFunc,
                        icon: 'fi-rr-copy-alt',
                        label: this.$t('task.copy')
                    },
                ]
            }
            
            return buttons.filter(button => button.visible)
        },

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
        currentStatus() {
            const nextStatus = this.dropActions?.change_status?.next_status
            if (nextStatus) {
                const status = this.filteredList.find(status => status.code === nextStatus)
                if (status) { return status }
            }

            if(this.filteredList?.length && this.item) {
                if(this.item.status.is_complete)
                    return null
                else {
                    const find = this.filteredList.find(f => f.depends?.find(fn => fn === this.item.status.code))
                    if(find?.is_complete) {
                        if(this.isAuthor)
                            return find ? find : null
                        else
                            return null
                    } else
                        return find ? find : null
                }
            } else
                return null
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
    created() {
        this.getTaskActions()
    },
    methods: {
        dropdownVisibleChange(visible) {
            if (visible) {
                this.getTaskActions()
            }
        },
        openDrawer() {
            this.visible = true
        }
    }
}
</script>

<style lang="scss" scoped>
.edit_icon_wrap {
    display: flex;
    justify-content: center;
    align-items: center;
    
    line-height: 100%;
    font-size: 1rem;
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