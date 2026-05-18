<template>
    <div class="wrapper">
        <a-dropdown
            :trigger="['click']"
            :getPopupContainer="trigger => trigger.parentElement" >
            <a-button 
                type="ui" 
                size="small" 
                ghost
                flaticon
                class="ml-1"
                shape="circle"
                icon="fi-rr-menu-dots-vertical" />
            <a-menu slot="overlay">
                <a-menu-item v-if="showEditOption" @click="editObjective()">
                    {{ $t('okr.edit') }}
                </a-menu-item>
                <a-menu-item v-if="showDeleteOption" class="text_red" @click="deleteObjective()">
                    {{ $t('okr.delete') }}
                </a-menu-item>
            </a-menu>
        </a-dropdown>
    </div>
</template>
<script>
export default {
    name: 'ObjectiveActionMenu',
    props: {
        objective: {
            type: Object,
            required: true
        },
        editObjective: {
            type: Function,
            default: () => {}
        },
        deleteObjective: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        showEditOption() {
            return this.objective.actions.edit
        },
        showDeleteOption() {
            return this.objective.actions.delete
        }
    },
    methods: {
        getPopupContainer() {
            return this.$refs.wrapper
        }
    }
}
</script>