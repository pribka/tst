<template>
    <div>
        <ActivityDrawer 
            v-model="visible">
            <template v-if="showLeaveButton || showRemoveEmployeeButton">
                <ActivityItem
                    v-if="showLeaveButton" 
                    key="leave"
                    @click="addSubtask()">
                    <i class="fi fi-rr-remove-user mr-2"></i>
                    {{ $t('team.leave_organization') }}
                </ActivityItem>
                <ActivityItem
                    v-if="showRemoveEmployeeButton"
                    key="removeUser"
                    @click="share()">
                    <i class="fi-rr-remove-user mr-2"></i>
                    {{ $t('team.exclude_user') }}
                </ActivityItem>
            </template>
            <template v-else>
                <ActivityItem
                    key="noActions">
                    {{ $t('team.no_available_actions') }}
                </ActivityItem>
            </template>
        </ActivityDrawer>
    </div>
</template>

<script>
import { ActivityItem, ActivityDrawer } from '@/components/ActivitySelect'
export default {
    components: {
        ActivityItem, 
        ActivityDrawer
    },
    props: {
        item: {
            type: Object,
            required: true
        },
        actions: {
            type: Object,
            default: () => null
        },
        organization: {
            type: Object,
            required: true
        },
    },
    data() {
        return {
            visible: false,
        }
    },
    computed: {
        user() {
            return this.$store.state.user.user
        },
        isAuthor() {
            return this.organization?.director?.id === this.item.id
        },
        showLeaveButton() {
            return false // !! Заглушка. Кнопка Скрыта Т.к. не проработан функционал
            // когда пользователь не принадлежит ни к какой организации. (Задача 10819)
            return (this.user?.id === this.item.id) && !this.actions?.edit
        },
        showRemoveEmployeeButton() {
            return false // !! Заглушка. Кнопка Скрыта Т.к. не проработан функционал
            // когда пользователь не принадлежит ни к какой организации. (Задача 10819)
            return !this.isAuthor && (this.actions?.edit) && (this.user?.id !== this.item.id)
        },
    },
    methods: {
        openDrawer() {
            this.visible = true
        }
    }
}
</script>

<style scoped lang="scss">
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