<template>
    <div>
        <div 
            class="great_loader" 
            v-show="loadingMain">
            <a-spin color="primary" />
        </div>
        <div 
            class="flex items-center pb-4"
            :class="isMobile && 'list_group_header'">
            <a-button 
                :size="buttonSize" 
                @click="createGroup" 
                icon="plus"
                class="mr-2"
                type="primary">
                {{$t("wgr.create_group")}}
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
                :comments="item.comments"
                :members_count="item.members_count"
                :alltask="item.tasks"
                :public_or_private="item.public_or_private"
                :completetask="item.complete_tasks"
                @eventMore="goMain(item)"/>
        </div>

        <div 
            v-if="loaded && !loadingMain && workgroups.length === 0"
            class="mt-5">
            <a-empty :description="$t('wgr.group_not')" />
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

        <!--<div 
            v-show="more" 
            class="flex justify-center items-center mt-4">
            <a-button
                :loading="loadingMain"
                type="dashed"
                @click="getAllGroups">
                {{ $t("wgr.load_more") }}
            </a-button> 
        </div>-->
    </div>
</template>

<script>
import { mapActions, mapGetters, mapMutations } from "vuex"
import eventBus from "@/utils/eventBus"
import InfiniteLoading from 'vue-infinite-loading'
let searchTimer;
export default {
    name: "GroupsAndProjectsListGroup",
    props: {
        buttonSize: {
            type: String,
            default: 'default'
        }
    },
    components: {
        ListCard: () => import("./СardGroup"),
        PageFilter: () => import('@/components/PageFilter'),
        InfiniteLoading
    },
    computed: {
        ...mapGetters({
            loadingMain: "workgroups/loading"
        }),
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return {
            workgroups: [],
            search: "",
            page: 0,
            loading: false,
            more: false,
            createGr: false,
            loaded: false,
            next: true,
            page_name: 'page_list_workgroup_workgroups.WorkgroupModel',
            pageModel: 'workgroups.WorkgroupModel'
        }
    },
    methods: {
        ...mapMutations({
            setLoading: "workgroups/setLoading",
            clearGroups: "workgroups/clearGroups"
        }),
        ...mapActions({
            getAllGroupsS: "workgroups/getMyGroups"
        }),
        // Поучение всех клубов
        async getAllGroups($state) {
            if(this.next) {
                if(!this.loading) {
                    try {
                        this.loading = true
                        this.page += 1
                        const res = await this.getAllGroupsS({ page: this.page, page_name: this.page_name })
                        
                        if(res.results?.length) {
                            this.workgroups = this.workgroups.concat(res.results)
                        }

                        if (!res.next) {
                            $state.complete()
                        } else {
                            $state.loaded()
                        }
                    } catch (error) {
                        this.$message.error(this.$t("wgr.error") )
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
            const query = {...this.$route.query}
            query.viewGroup = item.id
            this.$router.replace({query})
        },
        createGroup() {
            this.setLoading(true)
            const query = {...this.$route.query}
            if(!query.createGroup) {
                query.createGroup = true
                this.$router.replace({query})
            }
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
        eventBus.$on('update_list_group', () => {
            this.reloadList()
        })
        eventBus.$on(`update_filter_${this.pageModel}`, () => {
            this.reloadList()
        })
    },
    beforeDestroy() {
        eventBus.$off('update_list_group')
        eventBus.$off(`update_filter_${this.pageModel}`)
    }
}
</script>

<style lang="scss">
.group_grid{
    margin-top: 10px;
}
</style>

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