<template>
    <Drawer
        v-model="visible"
        :title="$t('project.project_templates')"
        :width="drawerWidth"
        :class="isMobile && 'mobile'"
        class="drawer"
        destroyOnClose
        :afterVisibleChange="afterVisibleChange"
        @close="visible = false">
        <div slot="body">
            <a-skeleton active :paragraph="{ rows: 4 }" :loading="loading">
                <div class="project-templates">
                    <div class="project-templates__list">
                        <ProjectTemplateCreate class="mb-8" />
                        <TemplateList 
                            class=""
                            :activeItem="selectedProjectTemplate"
                            :selectHandler="selectProjectTemplate" />
                    </div>
                    <div class="project-templates__table">
                        <TaskTable 
                            :template="selectedTemplate"
                            :loading="tableLoading"/>
                        
                        <template v-if="selectedTemplate?.is_draft">
                            <div class="mt-4 flex items-center">
                                <a-button 
                                    size="large" 
                                    type="primary" 
                                    class="ml-auto"
                                    :disabled="!selectedProjectTemplate"
                                    @click="publishTemplate">
                                    {{ $t('Publish') }}
                                </a-button>
                            </div>
                        </template>
                    </div>
                </div>
            </a-skeleton>
        </div>
    </Drawer>
</template>

<script>
import createdMethods from "./mixins/createdMethods";
import eventBus from "@/utils/eventBus";
export default {
    mixins: [createdMethods],
    components: {
        Drawer: () => import("./widgets/DrawerTemplate"),
        TaskTable: () => import('./components/TaskTable.vue'),
        TemplateList: () => import('./components/ProjectTemplates/TemplateList.vue'),
        ProjectTemplateCreate: () => import('./components/ProjectTemplates/ProjectTemplateCreate.vue')
    },
    props: {
        pageName: {
            type: String,
            default: "page_list_project_workgroups.WorkgroupModel",
        },
    },
    data() {
        return {
            selectedProjectTemplate: null,
            selectedTemplate: null,
            visible: false,
            loading: false,
            endpoint: null,
            tableLoading: false
        };
    },
    watch: {
        "$route.query": {
            immediate: true,
            handler() {
                this.getParamsQuerySet();
            }            
        },
    },
    computed: {
        id() {
            return this.$route.query.updateProject;
        },
        isMobile() {
            return this.$store.state.isMobile;
        },

        user() {
            return this.$store.state.user.user
        },
        isPublic() {
            return this.selectedTemplate?.is_public
        },
        canChange() {
            return this.user.id === this.selectedTemplate?.author?.id
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        drawerWidth() {
            if (this.windowWidth <= 1000) return '100%'
            if (this.windowWidth <= 1400) return '95%'
            return '80%'
        },
    },
    created() {
        if (this.selectedProjectTemplate) {
            this.endpoint = `/work_groups/stage_templates/?template=${this.selectedProjectTemplate}`
        }
    },
    // mounted() {
    //     eventBus.$on("open_create_project_drawer", ({ organization = null }) => {
    //         this.$router.replace({
    //             query: { createProject: true },
    //         });
    //         this.getParamsQuerySet();
    //     });
    // },
    // beforeDestroy() {
    //     eventBus.$off("open_create_project_drawer");
    // },
    methods: {
        selectProjectTemplate({ id, template }) {
            if (this.selectedProjectTemplate === id) {
                this.selectedProjectTemplate = null;
                this.selectedTemplate = null
                this.endpoint = null
                
                this.$store.dispatch('projects/clearTemplateTable')
                return;
            }
            this.selectedTemplate = template
            this.selectedProjectTemplate = id;
            this.endpoint = `/work_groups/task_templates/?template=${this.selectedProjectTemplate}`

            this.reloadTable()
        },
        reloadTable() {
            const payload = { template: this.selectedProjectTemplate, withActionRows: this.canChange }
            this.tableLoading = true
            this.$store.dispatch('projects/setTemplateTable', payload)
                .then(() => {
                })
                .catch(error => {
                    this.$message.error(this.$t('Error receiving table data'))
                    console.error(error)
                })
                .finally(() => {
                    this.tableLoading = false
                })
        },
        afterVisibleChange(vis) {
            if (!vis) {
                this.close()
            }
        },
        getParamsQuerySet() {
            const query = Object.assign({}, this.$route.query);

            if (query.hasOwnProperty("createProjectTemplate")) {
                this.init();
            }
            // if (query.updateProject) {
            //     this.init();
            //     this.initUpdate();
            // }
        },
        publishTemplate() {
            const template = this.selectedProjectTemplate 
            const url = `/work_groups/templates/${template}/`
            const payload = {
                is_draft: false
            }
            // this.loading = true
            this.$http.put(url, payload)
                .then(({ data }) => {
                    this.$notification.success({
                        message: this.$t('Template has been published'),
                    })
                    eventBus.$emit('reload_template_list')
                    this.selectedTemplate.is_draft = false
                })
                .catch(error => {
                    console.error(error)
                    this.$notification.error({
                        message: this.$t('Error'),
                    })
                })
                .finally(() => {
                    // this.loading = false
                })

        },
        close() {
            const query = Object.assign({}, this.$route.query);
            delete query["createProjectTemplate"];
            // if (query.updateProject) {
            //     const viewGroup = query.updateProject;
            //     delete query["updateProject"];
            //     query.viewGroup = viewGroup;
            // }
            this.$router.replace({ query });
        },
    },
};
</script>

<style lang="scss" scoped>
::v-deep {

    .project-templates {
        display: flex;
        flex-direction: column-reverse;
        @media (min-width: 1000px) {
            flex-direction: row;
        }
    }
    .project-templates__list {
        flex-shrink: 0;
        margin-right: 0;
        margin-top: 30px;
        @media (min-width: 1000px) {
            width: 340px;
            margin-right: 24px;
            margin-top: 0;
        }
    }
    .project-templates__table {
        flex-grow: 1;
        min-width: 0;
    }
}

</style>