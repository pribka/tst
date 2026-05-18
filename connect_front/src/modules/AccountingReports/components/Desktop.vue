<template>
    <ModuleWrapper :pageTitle="pageTitle">
        <template v-slot:h_left>
            <slot name="pageFilter" />
        </template>
        <template v-slot:h_right>
            <slot name="addButton" />
        </template>
        <Table />
    </ModuleWrapper>
</template>

<script>
import ModuleWrapper from '@/components/ModuleWrapper/index.vue'
import Table from './Table'
import { mapState } from 'vuex'

export default {
    components: {
        ModuleWrapper,
        Table
    },
    computed: {
        ...mapState({
        }),
        pageTitle() {
            return this.$route?.meta?.title || ''
        },
    }
}
</script>