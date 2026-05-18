<template>
    <a-button 
        v-if="getRouteInfo && getRouteInfo.pageActions && getRouteInfo.pageActions.add"
        type="primary" 
        icon="fi-rr-plus-small"
        flaticon
        @click="$store.commit('meeting/SET_EDIT_MODAL', { show: true, model: model })">
        {{ $t('meeting.createConference') }}
    </a-button>
</template>

<script>
export default {
    name: "MeetingAddButton",
    props: {
        model: {
            type: String,
            default: 'main'
        },
        getRouteInfo: {
            type: Object,
            default: () => null
        }
    }
}
</script>