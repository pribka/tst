<template>
    <component 
        :is="wrapperModule" 
        :pageTitle="pageTitle">
        <div class="w-full">
            <SprintCard 
                v-for="sprint in sprintList" 
                :key="sprint.id" 
                :inject="inject"
                :sprint="sprint" />
            <infinite-loading 
                ref="infiniteLoading"
                :identifier="infiniteId"
                @infinite="getSprints"
                :distance="10">
                <div 
                    slot="spinner"
                    class="flex items-center justify-center inf_spinner">
                    <a-spin />
                </div>
                <div slot="no-more"></div>
                <div slot="no-results"></div>
            </infinite-loading>
        </div>
        <div 
            v-if="showEmpty && !listLoading" 
            class="pt-8">
            <a-empty>
                <template #description>
                    {{ $t('task.sprint_empty') }}
                </template>
            </a-empty>
        </div>
        <div 
            v-if="isMobile" 
            class="float_add">
            <div class="filter_slot">
                <PageFilter 
                    :model="model"
                    :key="pageName"
                    size="large"
                    :excludeFields="excludeFields"
                    :page_name="pageName" />
            </div>
            <a-button 
                v-if="checkProjectPage"
                flaticon
                shape="circle"
                class="mb-3"
                size="large"
                icon="fi-rr-list"
                @click="openProjectPage()" />
            <a-button 
                v-if="showCreateButton"
                flaticon
                shape="circle"
                size="large"
                type="primary"
                icon="fi-rr-plus"
                @click="addSprint()"  />
        </div>
    </component>
</template>

<script>
import eventBus from '@/utils/eventBus'
import PageFilter from '@/components/PageFilter'
import ModuleWrapper from '@/components/ModuleWrapper/index.vue'
import SprintCard from './SprintCardMobile.vue'
export default {
    name: "SprintList",
    components: { 
        PageFilter,
        ModuleWrapper,
        SprintCard,
        InfiniteLoading: () => import('vue-infinite-loading')
    },
    props: {
        filters: {
            type: Object,
            default: null
        },
        pageName: {
            type: String,
            default: "sprint_list"
        },
        showCreateButton: {
            type: Boolean,
            default: true
        },
        model: {
            type: String,
            default: 'tasks.TaskSprintModel'
        },
        inject: {
            type: Boolean,
            default: false
        },
        excludeFields: {
            type: Array,
            default: () => []
        },
        injectFormParams: {
            type: Object,
            default: () => {}
        },
        showHead: {
            type: Boolean,
            default: true
        }
    },
    data(){
        return {
            sprintList: [],
            count: 0,
            listLoading: false,
            page: 1,
            pageSize: 15,
            next: true,
            infiniteId: this.pageName,
            showEmpty: false
        }
    },
    computed: {
        checkProjectPage() {
            if(this.$route.name === 'projects-sprints' && !this.inject)
                return true
            return false
        },
        isInject() {
            return this.inject ? `_inject` : ''
        },
        injectForm() {
            return {
                inject: this.inject,
                ...this.injectFormParams
            }
        },
        pageTitle() {
            return this.$route?.meta?.title || ''
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        wrapperModule() {
            if(this.inject || !this.showHead)
                return 'div'
            else
                return () => import('@/components/ModuleWrapper/index.vue')
        }
    },
    methods: {
        openProjectPage() {
            this.$router.push({
                name: 'projects-list'
            })
        },
        addSprint() {
            eventBus.$emit('add_sprint', this.injectForm)
        },
        reloadList() {
            this.page = 1
            this.next = true
            this.count = 0
            this.showEmpty = false
            this.sprintList = []
            this.infiniteId = `${this.pageName}_${Date.now()}`
            this.$nextTick(() => {
                if(this.$refs.infiniteLoading)
                    this.$refs.infiniteLoading.stateChanger.reset()
            })
        },
        async getSprints($state){
            if(this.listLoading) {
                $state.loaded()
                return
            }
            if(!this.next) {
                $state.complete()
                return
            }
            try{
                this.listLoading = true
                const params = { 
                    page: this.page,
                    page_name: this.pageName,
                    filters: this.filters,
                    page_size: this.pageSize
                }
                const { data } = await this.$http(`tasks/sprint/list/`, { params })
                if(data) {
                    if(data.results && data.results.length)
                        this.sprintList.push(...data.results)
                    this.count = data.count
                    this.next = Boolean(data.next)
                    this.showEmpty = !this.sprintList.length
                    if(this.next) {
                        this.page++
                        $state.loaded()
                    } else {
                        $state.complete()
                    }
                } else {
                    $state.complete()
                }
            }
            catch(e) {
                console.log(e)
                $state.complete()
            }
            finally{
                this.listLoading = false
            }
        }
    },
    mounted() {
        eventBus.$on('sprint_update_table', sprint => {
            const idx = this.sprintList.findIndex(el=> el.id === sprint.id)
            if(idx !== -1) {
                this.$set(this.sprintList, idx, sprint)
            }
        })
        eventBus.$on(`update_sprints_list${this.isInject}`, () => {
            this.reloadList()
        })
        eventBus.$on('update_filter_tasks.TaskSprintModel', () => {
            this.reloadList()
        })
        eventBus.$on(`update_task_data${this.isInject}`, () => {
            this.reloadList()
        })
    },
    beforeDestroy(){
        eventBus.$off(`sprint_update_table`)
        eventBus.$off('update_filter_tasks.TaskSprintModel')
        eventBus.$off(`update_sprints_list${this.isInject}`)
        eventBus.$off(`update_task_data${this.isInject}`)
    }
}
</script>
