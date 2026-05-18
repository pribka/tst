<template>
    <DrawerTemplate
        :title="$t('team.invitation_list')"
        v-model="visible"
        class="in_list_drawer"
        @close="visible = false"
        destroyOnClose
        :zIndex="zIndex"
        :width="drawerWidth"
        placement="right">
        <template v-if="orgId" #tabs>
            <a-tabs v-model="currentTab" :showContent="false" class="header_tab">
                <a-tab-pane key="1" :tab="$t('team.users')">
                    <Users :org="org" :closeDrawer="closeDrawer" />
                </a-tab-pane>
                <a-tab-pane key="2" :tab="$t('team.organizations')">
                    <Organizations :org="org" :closeDrawer="closeDrawer" />
                </a-tab-pane>
            </a-tabs>
        </template>
        <template v-if="orgId">
            <a-tabs :activeKey="currentTab" :showBar="false" class="body_tab">
                <a-tab-pane key="1">
                    <Users :org="org" :closeDrawer="closeDrawer" />
                </a-tab-pane>
                <a-tab-pane key="2">
                    <Organizations :org="org" :closeDrawer="closeDrawer" />
                </a-tab-pane>
            </a-tabs>
        </template>
    </DrawerTemplate>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    name: "InvitationListDrawer",
    components: {
        Users: () => import('./Users.vue'),
        Organizations: () => import('./Organizations.vue'),
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue')
    },
    props: {
        zIndex: {
            type: Number,
            default: 1050
        },
        org: {
            type: [Object],
            required: true
        }
    },
    computed: {
        windowWidth() {
            return this.$store.state.windowWidth
        },
        drawerWidth() {
            if(this.windowWidth > 600)
                return 600
            else {
                return '100%'
            }
        }
    },
    created() {
        eventBus.$on(`open_inv_list_${this.org.id}`, id => {
            this.orgId = id
            this.visible = true
        })
    },
    data() {
        return {
            currentTab: "1",
            orgId: null,
            visible: false
        }
    },
    methods: {
        closeDrawer() {
            this.visible = false
        }
    },
    beforeDestroy() {
        eventBus.$off(`open_inv_list_${this.org.id}`)
    }
}
</script>