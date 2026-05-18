<template>
    <div v-if="noEmpty" class="flex items-center members_list">
        <Profiler 
            v-for="user in relatedUsers"
            :key="user.id"
            class="member"
            :avatarSize="20"
            :user="user"
            :showUserName="false" />
    </div>
</template>

<script>
export default {
    props: {
        relatedUsers: {
            type: [Array, Object],
            default: () => {}
        },
        storeKey: {
            type: String,
            required: true
        }
    },
    computed: {
        noEmpty() {
            return this.user.length || false
        },
        user: {
            get() {
                return this.$store.state.workplan.user?.[this.storeKey] || null
            },
            set(value) {
                this.$store.commit('workplan/CHANGE_FIELD', {
                    value,
                    field: 'user',
                    storeKey: this.storeKey
                })
            }
        },
    }
}
</script>

<style lang="scss" scoped>
.members_list{
    &::v-deep{
        .user_profile{
            &:not(:first-child){
                margin-left: -5px;
            }
        }
    }
}
</style>