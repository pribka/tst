<template>
    <Files
        :sourceId="event.id"
        :isFounder="isAuthor"
        widgetEmbed
        isStudent />
</template>

<script>
import { mapState } from 'vuex'
export default {
    props: {
        event: {
            type: Object,
            required: true
        }
    },
    components: {
        Files: () => import('@apps/vue2Files')
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        isAuthor() {
            return this.user?.id === this.event?.author?.id
        }
    }
}
</script>