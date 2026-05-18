<template>
    <div 
        v-touch:longtap="longtapHandler"
        class="wrg_card" 
        :class="isMobile && 'is_mobile'"
        @click="openHandler(item.id)">
        <div class="flex items-center truncate justify-between">
            <div class="flex items-center truncate">
                <div class="pr-2">
                    <a-avatar 
                        :size="26" 
                        icon="team" 
                        :key="workgroupLogoPath"
                        :src="workgroupLogoPath" />
                </div>
                <span class="truncate font-medium">
                    {{ item.name }}
                </span>
            </div>
        </div>
        <div class="flex items-center justify-between mt-2">
            <CardDeadStart 
                :item="item" 
                :listProject="listProject" />
            <Members 
                :item="item"
                :visibleCount="1" />
        </div>
        <ActionsList
            ref="actionList"
            :item="item"
            :reloadList="reloadList" />
    </div>
</template>

<script>
export default {
    components: {
        CardDeadStart: () => import('./CardDeadStart.vue'),
        Members: () => import('./Members.vue'),
        ActionsList: () => import('./ActionsList.vue')
    },
    props: {
        item: {
            type: Object,
            required: true
        },
        listProject: {
            type: Boolean,
            default: true
        },
        reloadList: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        workgroupLogoPath() {
            return this.item?.workgroup_logo?.path || null
        }
    },
    methods: {
        longtapHandler() {
            this.$refs.actionList.openActionsDrawer()
        },
        openHandler(id) { 
            const query = Object.assign({}, this.$route.query)
            if(query.viewProject && Number(query.viewProject) !== id || !query.viewProject) {
                query.viewProject = id
                this.$router.push({query})
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.wrg_card{
    background: #f7f9fc;
    padding: 12px;
    cursor: pointer;
    border-radius: var(--borderRadius);
    &.is_mobile{
        background: #fff;
    }
    .green{
        color: #87d068;
    }
    &:not(:last-child){
        margin-bottom: 10px;
    }
    .tasks_count{
        font-size: 13px;
        color: #656565;
    }
}
</style>
