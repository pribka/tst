<template>
    <ActivityDrawer v-model="visible">
        <template v-if="actionsList">
            <ActivityItem
                v-if="actionsList.edit" 
                key="edit"
                @click="edit()">
                <i class="fi fi-rr-edit"></i>
                {{ $t('team.edit') }}
            </ActivityItem>
            <ActivityItem
                v-if="actionsList.invite" 
                key="invite_user"
                @click="invite()">
                <i class="fi fi-rr-user-add"></i>
                {{ $t('team.invite_user') }}
            </ActivityItem>
            <ActivityItem
                v-if="actionsList.invite" 
                key="invite_org"
                @click="openOrgInvite()">
                <i class="fi fi-rr-users-medical"></i>
                {{ $t('team.invite_organization') }}
            </ActivityItem>
            <!-- <ActivityItem             !! Заглушка. Кнопка Скрыта Т.к. не проработан функционал
                                              когда пользователь не принадлежит ни к какой организации. (Задача 10819)
                v-if="!isAuthor" 
                key="leave_org"
                @click="leaveOrg()">
                <i class="fi fi-rr-delete-user"></i>
                {{ $t('team.leave_organization') }}
            </ActivityItem> -->
            <ActivityItem
                v-if="actionsList.invite" 
                key="invite_link"
                @click="getInviteLink()">
                <i class="fi fi-rr-link"></i>
                {{ $t('team.invite_link') }}
            </ActivityItem>
            <ActivityItem
                v-if="actionsList.invite" 
                key="copy_id"
                @click="orgCopyId()">
                <i class="fi fi-rr-copy-alt"></i>
                {{ $t('team.copy_identifier') }}
            </ActivityItem>
        </template>
    </ActivityDrawer>
</template>

<script>
import { ActivityItem, ActivityDrawer } from '@/components/ActivitySelect'
import mixins from './mixins'
export default {
    components: {
        ActivityItem,
        ActivityDrawer
    },
    mixins: [mixins]
}
</script>