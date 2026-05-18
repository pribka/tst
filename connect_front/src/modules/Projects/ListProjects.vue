<template>
    <div>
        <template v-if="page === 1">
            <div
                class="great_loader" 
                v-show="loadingMain">
                <a-spin color="primary" />
            </div>
        </template>
        <div 
            class=" flex items-center pb-4"
            :class="isMobile && 'list_group_header'">
            <a-button 
                @click="createProject" 
                icon="plus" 
                :size="buttonSize" 
                class="mr-2"
                type="primary">
                {{$t('project.add_project')}}
            </a-button>
            <PageFilter 
                :model="pageModel"
                :key="page_name"
                size="large"
                :page_name="page_name" />
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-4 group_grid">
            <list-card
                v-for="(item, key) in workgroups" 
                :key="key"
                :image="workgroupLogoPath(item)"
                :title="item.name"
                :description="item.description"
                :director="item.founder.member"
                :participants="item.workgroup_members.slice(0, 7)"
                :type="item.workgroup_type.name"
                :status="item.public_or_private"
                :dead_line="item.dead_line"
                :members_count="item.members_count"
                :comments="item.comments"
                :date_start_plan="item.date_start_plan"
                :alltask="item.tasks"
                :completetask="item.complete_tasks"
                @eventMore="goMain(item)"/>
        </div>

        <div 
            v-if="loaded && !loading && !loadingMain && workgroups.length === 0" 
            class="mt-5">
            <a-empty :description="$t('project.project_not')" />
        </div>

        <infinite-loading 
            @infinite="getAllGroups"
            v-bind:distance="50"
            ref="group_infinity">
            <div 
                slot="spinner"
                class="flex items-center justify-center inf_spinner mt-3">
                <a-spin />
            </div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
    </div>
</template>

<script>
import { mapActions, mapGetters, mapMutations } from 'vuex';
import eventBus from "@/utils/eventBus"
import InfiniteLoading from 'vue-infinite-loading'
export default {
    name: "GroupsAndProjectListProjects",
    props: {
        buttonSize: {
            type: String,
            default: 'default'
        }
    },
    components: {
        ListCard: () => import("./СardProject"),
        PageFilter: () => import('@/components/PageFilter'),
        InfiniteLoading
    },
    data() {
        return {
            loaded: false,
            workgroups: [],
            search: "",
            page: 0,
            next: true,
            loading: false,
            more: false,
            createPr: false,
            pageModel: 'workgroups.WorkgroupModel',
            page_name: 'page_list_project_workgroups.WorkgroupModel'
        }
    },
    computed: {
        ...mapGetters({
            loadingMain: "projects/loading"
        }),
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    methods: {
        ...mapActions({
            getAllGroupsS: "projects/getMyGroups",

        }),
        ...mapMutations({
            setLoading: "projects/setLoading"
        }),
        // Поучение всех проектов
        async getAllGroups($state) {
            if(this.next) {
                if(!this.loading) {
                    try {
                        this.loading = true
                        this.page += 1
                        const res = await this.getAllGroupsS({ page: this.page, is_project: 1, page_name: this.page_name })
                        
                        if(res.results?.length) {
                            this.workgroups = this.workgroups.concat(res.results)
                        }

                        if (!res.next) {
                            $state.complete()
                        } else {
                            $state.loaded()
                        }
                    } catch (error) {
                        this.$message.error(this.$t("Error") )
                    } finally {
                        this.loading = false
                    }
                }
            } else {
                $state.complete()
            }
        },
        goMain(item) {
            this.setLoading(true)
            this.$router.replace({
                query: { viewProject: item.id },
            });
        },
        createProject() {
            this.setLoading(true)
            eventBus.$emit('add_proejct_modal')
        },
        reloadList() {
            this.page = 0
            this.workgroups = []
            this.next = true
            this.$nextTick(() => {
                this.$refs['group_infinity'].stateChanger.reset()
            })
        },
        workgroupLogoPath(workgroup) {
            return workgroup?.workgroup_logo?.path || ''
        },

    },
    mounted() {
        eventBus.$on(`update_filter_${this.pageModel}`, () => {
            this.reloadList()
        })
        eventBus.$on('update_list_project', () => {
            this.reloadList()
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.pageModel}`)
        eventBus.$off('update_list_project')
    }
}
</script>


<style lang="scss" scoped>
.list_group_header{
    margin-top: -10px;
    padding-top: 10px;
    padding-bottom: 10px;
    position: sticky;
    z-index: 30;
    top: var(--headerHeight);
    background: var(--eBg);
}
</style>
