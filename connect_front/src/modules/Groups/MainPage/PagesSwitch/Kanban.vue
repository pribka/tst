<template>
    <div class="wrg_kanban">
        <Kanban 
            :implementId="id"
            :formParams="formParams"
            :pageConfig="pageConfig"
            :extendDrawer="true"
            taskType="task"
            :queryParams="{ 'page_name': pageName }"
            :implementType="is_project ? 'project' : 'workgroup'">
            <PageFilter 
                model="tasks.TaskModel"
                :key="pageName"
                size="large"
                :excludeFields="excludeFields"
                :page_name="pageName"/>
        </Kanban>
    </div>
</template>

<script>
import { mapGetters } from 'vuex'
export default {
    components: {
        Kanban: () => import('@apps/vue2TaskComponent/components/Kanban'),
        PageFilter: () => import('@/components/PageFilter')
    },
    props: {
        id: {
            type: [String, Number],
            required: true
        },
        is_project: {
            type: Boolean,
            default: false
        },
        actions: {
            type: Object,
            default: () => null
        }
    },
    computed: {
        ...mapGetters({
            requestData : "workgroups/info"
        }),
        pageName() {
            return `tasks.groups_and_project_${this.id}`
        }
    },
    data() {
        return {
            formParams: {},
            excludeFields: ['status'],
            pageConfig: {
                showFilter: true
            }
        }
    },
    created() {
        if(this.actions?.create_task) {
            this.pageConfig.headerButtons = {
                createButton: {
                    fastCreate: true,
                    icon: "plus",
                    show: true,
                    size: "large",
                    title: this.$t('wgr.add_task'),
                    type: "primary"
                }
            }
        }

        if(this.requestData.is_project) {
            this.formParams = { 
                project: {
                    name: this.requestData.name, 
                    id: this.id,
                    workgroup_logo: this.requestData.workgroup_logo?.is_image ? this.requestData.workgroup_logo : null,
                    date_start_plan: this.requestData.date_start_plan,
                    dead_line: this.requestData.dead_line
                },
            }
            this.excludeFields.push('project')
        } else {
            this.formParams = {  
                workgroup: {
                    name: this.requestData.name, 
                    id: this.id,
                    workgroup_logo: this.requestData.workgroup_logo?.is_image ? this.requestData.workgroup_logo : null
                }
            }
            this.excludeFields.push('workgroup')
        }
    }
}
</script>

<style lang="scss">
.wrg_kanban{
    height: 100%;
    position: relative;
}
</style>