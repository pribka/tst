<template>
    <a-dropdown 
        destroyPopupOnHide
        @visibleChange="visibleChange"
        :trigger="['click']">
        <a-button 
            :loading="loading" 
            icon="menu" 
            class="text-right or_menu_btn"
            type="link"/>
        <a-menu slot="overlay">
            <a-menu-item 
                v-if="!actionsList && listLoading"
                key="menu_loader"
                class="flex justify-center">
                <a-spin size="small" />
            </a-menu-item>
            <template v-if="actionsList">
                <template v-if="actionsList.change_status">
                    <a-menu-item 
                        v-if="record.status === 'new'" 
                        key="start" 
                        @click="$emit('start')">
                        Начать
                    </a-menu-item>
                    <a-menu-item 
                        v-if="record.status === 'in_process'" 
                        key="end" 
                        @click="$emit('end')">
                        Завершить
                    </a-menu-item>
                </template>
                <a-menu-item 
                    v-if="actionsList.edit" 
                    key="edit" 
                    @click="orderEdit()">
                    Редактировать
                </a-menu-item>
                <a-menu-item 
                    v-if="actionsList.share" 
                    key="share" 
                    @click="$emit('share')">
                    {{$t('task.share_to_chat')}}
                </a-menu-item>
                <a-menu-item 
                    v-if="actionsList.add_task && canAddTask"
                    key="addTask"
                    @click="$emit('addTask')">
                    {{$t('task.add_task')}}
                </a-menu-item>
            </template>
        </a-menu>
    </a-dropdown>
</template>

<script>
import mixins from './mixins.js'
export default {
    mixins: [mixins]
}
</script>

<style lang="scss">
.or_menu_btn{
    width: 22px;
}
</style>