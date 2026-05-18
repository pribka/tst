<template>
    <a-dropdown :trigger="['click']">
        <a-button 
            type="ui"
            ghost 
            flaticon 
            shape="circle"
            icon="fi-rr-plus" />
        <a-menu slot="overlay">
            <a-menu-item key="0" @click="addTask()">
                {{ $t("add_task") }}
            </a-menu-item>
            <a-menu-item key="1" @click="$store.commit('meeting/SET_EDIT_MODAL', { show: true, model: 'main' })">
                {{ $t("add_conference") }}
            </a-menu-item>
            <a-menu-item key="2" @click="addEvent()">
                {{ $t("add_event") }}
            </a-menu-item>
            <a-menu-item key="3" @click="addOrganization()">
                {{ $t("add_organization") }}
            </a-menu-item>
        </a-menu>
    </a-dropdown>
</template>

<script>
import eventBus from '@/utils/eventBus.js'
export default {
    methods: {
        addTask() {
            this.$store.commit('task/SET_PAGE_NAME', {
                pageName: 'page_list_task_task.TaskModel'
            })
            eventBus.$emit('add_task_modal', {
                task_type: 'task'
            })
        },
        addEvent() {
            eventBus.$emit('open_event_form', null, null, null, null, 'default')
        },
        addOrganization() {
            eventBus.$emit('create_organization', { organization_type: 'organization' })
        }
    }
}
</script>
