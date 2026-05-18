<template>
    <div class="page_block">
        <Gallery :sourceId="$route.params.id" :isAuthor="checkActions" />
    </div>
</template>

<script>
import { mapState } from 'vuex'
export default {
    components: {
        Gallery: () => import('@apps/UIModules/Gallery')
    },
    computed: {
        ...mapState({
            actions: state => state.facilities.projectActions
        }),
        checkActions() {
            return this.actions?.gallery?.availability || false
        }
    }
}
</script>