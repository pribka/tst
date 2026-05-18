<template>
    <ActivityDrawer v-model="visible">
        <template v-if="actionsList">
            <ActivityItem
                v-if="actionsList.edit" 
                key="edit"
                @click="edit()">
                <i class="fi fi-rr-edit"></i>
                Редактировать
            </ActivityItem>
            <ActivityItem
                v-if="actionsList.invite" 
                key="invite_user"
                @click="invite()">
                <i class="fi fi-rr-user-add"></i>
                Пригласить пользователя
            </ActivityItem>
            <ActivityItem
                v-if="actionsList.invite" 
                key="invite_org"
                @click="openOrgInvite()">
                <i class="fi fi-rr-users-medical"></i>
                Пригласить организацию
            </ActivityItem>
            <ActivityItem
                v-if="!isAuthor" 
                key="leave_org"
                @click="leaveOrg()">
                <i class="fi fi-rr-delete-user"></i>
                Покинуть организацию
            </ActivityItem>
            <ActivityItem
                v-if="actionsList.invite" 
                key="invite_link"
                @click="getInviteLink()">
                <i class="fi fi-rr-link"></i>
                Ссылка для приглашения
            </ActivityItem>
            <ActivityItem
                v-if="actionsList.invite" 
                key="copy_id"
                @click="orgCopyId()">
                <i class="fi fi-rr-copy-alt"></i>
                Копировать идентификатор
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