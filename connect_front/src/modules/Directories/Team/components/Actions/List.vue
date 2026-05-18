<template>
    <a-dropdown 
        :trigger="dropTrigger"
        :destroyPopupOnHide="true"
        @visibleChange="visibleChange">
        <a-button 
            :loading="loading" 
            icon="menu" 
            type="link" />
        <a-menu slot="overlay">
            <a-menu-item 
                v-if="!actionsList && actionLoading"
                key="menu_loader"
                class="flex justify-center">
                <a-spin size="small" />
            </a-menu-item>
            <template v-if="actionsList">
                <a-menu-item 
                    v-if="actionsList.edit" 
                    key="edit"
                    class="flex items-center"
                    @click="edit()">
                    <i class="fi fi-rr-edit mr-2"></i>
                    {{ $t('team.edit') }}
                </a-menu-item>
                <a-menu-item 
                    v-if="actionsList.invite" 
                    key="invite"
                    class="flex items-center"
                    @click="invite()">
                    <i class="fi fi-rr-user-add mr-2"></i>
                    {{ $t('team.invite_user') }}
                </a-menu-item>
                <a-menu-item 
                    v-if="actionsList.invite" 
                    key="invite_org"
                    class="flex items-center"
                    @click="openOrgInvite()">
                    <i class="fi fi-rr-users-medical mr-2"></i>
                    {{ $t('team.invite_organization') }}
                </a-menu-item>
                <a-menu-item 
                    key="user_list"
                    class="flex items-center"
                    @click="userList()">
                    <i class="fi fi-rr-users-alt mr-2"></i>
                    {{ $t('team.user_list') }}
                </a-menu-item>
                <!-- <a-menu-item             !! Заглушка. Кнопка Скрыта Т.к. не проработан функционал
                                                 когда пользователь не принадлежит ни к какой организации. (Задача 10819)
                    v-if="!isAuthor" 
                    key="invite_link"
                    class="flex items-center"
                    @click="leaveOrg()">
                    <i class="fi fi-rr-delete-user mr-2"></i>
                    {{ $t('team.leave_organization') }}
                </a-menu-item> -->
                <!--<a-menu-item 
                    v-if="actionsList.invite" 
                    key="enter_org"
                    class="flex items-center"
                    @click="openOrgEnter()">
                    <i class="fi fi-rr-user-add mr-2"></i>
                    Вступить в организацию
                </a-menu-item>-->
                <a-menu-item 
                    v-if="actionsList.invite" 
                    key="invite_link"
                    class="flex items-center"
                    @click="getInviteLink()">
                    <i class="fi fi-rr-link mr-2"></i>
                    {{ $t('team.invite_link') }}
                </a-menu-item>
                <a-menu-item 
                    v-if="actionsList.invite" 
                    key="org_id"
                    class="flex items-center"
                    @click="orgCopyId()">
                    <i class="fi fi-rr-copy-alt mr-2"></i>
                    {{ $t('team.copy_identifier') }}
                </a-menu-item>
                <!--<a-menu-item 
                    key="map_org"
                    class="flex items-center"
                    @click="openOrgMap()">
                    <i class="fi fi-rr-chart-tree mr-2"></i>
                    Карта организации
                </a-menu-item>-->
            </template>
        </a-menu>
    </a-dropdown>
</template>

<script>
import mixins from './mixins'
export default {
    mixins: [mixins]
}
</script>