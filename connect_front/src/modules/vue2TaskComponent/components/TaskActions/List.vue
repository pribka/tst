<template>
    <span>
        <UserDrawer
            id="changeUser"
            ref="changeUserRef"
            @input="changeUser"
            hide
            :title="$t('task.select_user')"/>

        <a-dropdown
            :disabled="disabled"
            :trigger="dropTrigger"
            :destroyPopupOnHide="false"
            @visibleChange="visibleChange">
            <a-button 
                :loading="loading" 
                icon="fi-rr-menu-dots-vertical" 
                flaticon
                :shape="shape"
                style="color: var(--text);"
                :ghost="btnGhost"
                :class="btnClass"
                :size="btnSize"
                :type="btnType" />
    
            <a-menu slot="overlay">
                <a-menu-item 
                    v-if="!dropActions && actionLoading"
                    key="menu_loader"
                    class="flex justify-center">
                    <a-spin size="small" />
                </a-menu-item>
                <template v-if="dropActions">
                    <template v-if="changeStatusVisible">
                        <a-menu-item 
                            v-if="statusLoader"
                            key="loader"
                            class="flex justify-center">
                            <a-spin size="small" />
                        </a-menu-item>
                        <template v-else>
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
                                    <a-badge 
                                        v-if="status.color !== 'default'" 
                                        :color="status.color" />
                                    {{ status.btn_title ? status.btn_title : status.name }}
                                </a-menu-item>
                            </a-sub-menu>
                        </template>
                        <a-menu-divider />
                    </template>
                    <template v-for="button in actionButtons">
                        <a-sub-menu v-if="button.children && button.children.length" :key="button.key">
                            <template #title>
                                <i class="fi mr-2" :class="button.icon" />
                                {{ button.label }}
                            </template>
                            <a-menu-item
                                v-for="cButton in button.children"
                                :key="cButton.key"
                                class="flex items-center"
                                @click="cButton.handler">
                                <i class="fi mr-2" :class="cButton.icon" />
                                {{ cButton.label }}
                            </a-menu-item>
                        </a-sub-menu>
                        <a-menu-item
                            v-else
                            :key="button.key"
                            class="flex items-center"
                            @click="button.handler">
                            <i class="fi mr-2" :class="button.icon" />
                            {{ button.label }}
                        </a-menu-item>
                    </template>
                    <template v-if="dropActions.delete && !item.children_count">
                        <a-menu-divider />
                        <a-menu-item
                            class="text-red-500 flex items-center" 
                            key="delete" 
                            @click="deleteTask()">
                            <i class="fi fi-rr-trash mr-2" />
                            {{$t('task.remove')}}
                        </a-menu-item>
                    </template>
                </template>
            </a-menu>
        </a-dropdown>
    </span>
</template>

<script>
import mixins from './mixins.js'
export default {
    components: {
        UserDrawer: () => import("@apps/DrawerSelect/index.vue")
    },
    props: {
        shape: {
            type: String,
            default: "circle"
        },
        btnSize: {
            type: String,
            default: "default"
        },
        btnType: {
            type: String,
            default: "ui"
        },
        btnClass: {
            type: String,
            default: ""
        },
        btnGhost: {
            type: Boolean,
            default: true
        }
    },
    mixins: [
        mixins
    ],
    computed: {
        changeStatusVisible() {
            return !this.item.is_auction && (this.dropActions.change_status || this.dropActions.change_cooperator_status) && this.showStatus && this.cStatusFiltered.length
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
        isMobile() {
            return this.$store.state.isMobile
        }
    }
}
</script>