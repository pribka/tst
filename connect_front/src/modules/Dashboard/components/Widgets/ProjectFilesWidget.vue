<template>
    <WidgetWrapper :widget="widget">
        <template slot="actions">
            <ProjectSelect
                ref="projectSelect"
                usePopupContainer
                inputType="avatar"
                :customPopupContainer="customPopupContainer"
                v-model="selectedProject" />
        </template>
        <div v-if="!selectedProject" class="empty_project">
            <i class="fi fi-rr-settings-sliders"></i>
            <p>{{ $t('dashboard.projectFilesEmptyMessage') }}</p>
            <a-button
                type="ui"
                size="small"
                @click="openProjectSetting()">
                {{ $t('dashboard.settings') }}
            </a-button>
        </div>
        <Files
            v-else
            :key="selectedProject.id"
            :sourceId="selectedProject.id"
            widgetEmbed
            :isFounder="fileFounder"
            :showFilter="false"
            :fileDragCreate="false"
            :isStudent="isStudent" />
    </WidgetWrapper>
</template>

<script>
export default {
    props: {
        widget: {
            type: Object,
            required: true
        }
    },
    components: {
        Files: () => import('@apps/vue2Files'),
        WidgetWrapper: () => import('../WidgetWrapper.vue'),
        ProjectSelect: () => import("@apps/DrawerSelect/ProjectSelect.vue")
    },
    data() {
        return {
            selectedProject: null,
            initComplete: false,
            projectActions: null,
            isStudent: false
        }
    },
    computed: {
        fileFounder() {
            return !!this.projectActions?.create_file
        }
    },
    watch: {
        selectedProject() {
            if(!this.initComplete)
                return
            this.saveProjectConfig()
            this.syncProjectPermissions()
        }
    },
    created() {
        if(this.widget.random_settings?.related_object)
            this.selectedProject = this.widget.random_settings.related_object
        this.initComplete = true
        if(this.selectedProject)
            this.syncProjectPermissions()
    },
    methods: {
        customPopupContainer() {
            return document.body
        },
        openProjectSetting() {
            this.$nextTick(() => {
                if(this.$refs.projectSelect)
                    this.$refs.projectSelect.openSelect()
            })
        },
        async saveProjectConfig() {
            try {
                const randomSettings = {
                    related_object: this.selectedProject || null,
                    related_model: this.selectedProject ? 'workgroups.WorkgroupModel' : null
                }
                await this.$http.patch(`/widgets/user_widgets_on_desktop/${this.widget.id}/`, {
                    random_settings: randomSettings
                })
                this.$store.commit('dashboard/UPDATE_ACTIVE_WIDGET', {
                    widgetId: this.widget.id, 
                    key: 'random_settings', 
                    value: randomSettings
                })
            } catch(error) {
                console.log(error)
            }
        },
        async syncProjectPermissions() {
            this.projectActions = null
            this.isStudent = false
            if(!this.selectedProject?.id)
                return

            const [actionsResult, rolesResult] = await Promise.allSettled([
                this.$http.get(`/work_groups/workgroups/${this.selectedProject.id}/action_info/`),
                this.$http.get(`/work_groups/workgroups/${this.selectedProject.id}/my_role/`)
            ])

            if(actionsResult.status === 'fulfilled')
                this.projectActions = actionsResult.value?.data?.actions || null

            if(rolesResult.status === 'fulfilled') {
                const roles = Array.isArray(rolesResult.value?.data) ? rolesResult.value.data : []
                this.isStudent = roles.some(item => ['FOUNDER', 'MODERATOR', 'MEMBER', 'ORG-COORDINATOR'].includes(item?.membership_role?.code))
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.empty_project{
    text-align: center;
    padding-top: 20px;
    i{
        font-size: 42px;
        color: var(--gray);
    }
    p{
        margin-top: 15px;
        margin-bottom: 20px;
        max-width: 280px;
        margin-left: auto;
        margin-right: auto;
    }
}
</style>
