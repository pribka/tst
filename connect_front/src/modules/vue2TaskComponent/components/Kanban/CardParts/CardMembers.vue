<template>
    <div class="flex items-center">
        <div class="member flex items-center">
            <Profiler
                :avatarSize="22"
                nameClass="text-sm"
                :showUserName="false"
                :user="person" />
        </div>
        <div 
            v-if="participantCount > 1" 
            class="member">
            <a-avatar 
                :size="22" 
                style="backgroundColor:#87d068">
                +{{ participantCount-1 }}
            </a-avatar>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        person: {
            type: Object,
            required: true
        },
        participantCount: {
            type: Number,
            default: 1
        }
    },
}
</script>

<style lang="scss" scoped>
.member{
    &:not(:last-child){
        margin-right: 3px;
    }
}
</style>