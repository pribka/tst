<template>
    <div
        class="user_card"
        :key="user.id">
        <div class="user_info flex items-center">
            <div class="awatar_wrapper">
                <a-badge :color="userStatusColor(user.online, user.last_activity)">
                    <Profiler
                        :avatarSize="38"
                        nameClass="text-sm"
                        :showUserName="false"
                        :user="user"/>
                </a-badge>
            </div>
            <div class="user_item__body w-full pl-2 overflow-hidden">
                <div class="flex justify-between ">
                    <div
                        :class="user.temporary_blocked == true ?
                            'line-through name font-medium truncate' :
                            'no-underline name font-medium truncate'">
                        {{ `${ user.last_name } ${ user.first_name}` }}
                    </div>
                    <a-tooltip class="ml-2" :title="$t('In work')">
                        <a-tag color="purple">
                            {{ user.tasks_in_work }}
                        </a-tag>
                    </a-tooltip>
                </div>
                <div class="flex items-center">
                    <div v-if="!user.online && user.last_activity">
                        <span v-if="fromNowDate">{{ $t('dashboard.user.last_seen', { date: $moment(user.last_activity).format('DD.MM.YY в HH:mm') }) }}</span>
                        <span v-else>{{ $t('dashboard.user.last_seen_ago', { time: $moment(user.last_activity).fromNow() }) }}</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        user: {
            type: Object,
            required: true
        },
        userStatusColor: {
            type: Function,
            default: () => {}
        },
        fromNowDate: {
            type: Function,
            default: () => {}
        }
    }
}
</script>

<style lang="scss" scoped>
.user_card {
    padding-bottom: 5px;
    padding-top: 5px;
    &.select_contact {
        cursor: pointer;
    }
    ::v-deep{
        .ant-badge-dot {
            top: 5px;
            right: 3px;

            width: 8px !important;
            height: 8px !important;
        }
        .ant-popover-placement-bottomRight .ant-popover-inner-content{
            padding: 12px 16px;
        }
    }
}
</style>
