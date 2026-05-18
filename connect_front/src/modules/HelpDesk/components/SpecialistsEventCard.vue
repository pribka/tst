<template>
    <div class="spec_event truncate flex items-center">
        <div class="mr-2">
            <a-avatar
                :size="16" 
                :src="user && user.avatar && user.avatar.path ? user.avatar.path : ''"
                icon="user" />
        </div>
        {{ event.title }}
    </div>
</template>

<script>
export default {
    props: {
        event: {
            type: Object,
            required: true
        },
    },
    computed: {
        user() {
            return this.event?.extendedProps?.user
        }
    }
}
</script>

<style lang="scss" scoped>
.spec_event{
    border-left: 0px;
    border-radius: 4px;
    position: relative;
    overflow: hidden;
    width: 100%;
    height: 100%;
    background: rgba(3, 155, 229, 0.25);
    color: #000;
    padding: 3px 5px;
}
</style>