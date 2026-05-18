<template>
    <UserDrawer
        v-model="form.user"
        hide
        inputSize="large"
        :title="$t('task.choose')"/>
</template>

<script>
import { mapState } from 'vuex';

export default {
    components: {
        UserDrawer: () => import("@apps/DrawerSelect/index.vue")
    },
    data() {
        return {
            visible: false,
            form: {
                user: null
            }
        }
    },
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth,
        }),

        drawerWidth() {
            if(this.windowWidth > 530)
                return 500
            return this.windowWidth
        },
    },
    methods: {
        closeDrawer() {
            this.visible = false
        },
        open() {
            this.visible = true
        }
    }
}
</script>