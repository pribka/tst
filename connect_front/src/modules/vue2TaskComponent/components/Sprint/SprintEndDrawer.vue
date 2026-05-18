<template>
    <a-drawer
        :width="drawerWidth"
        class="sprint_end_drawer"
        :visible="visible"
        :closable="false"
        :zIndex="999999"
        destroyOnClose
        :afterVisibleChange="afterVisibleChange"
        @close="visible = false">
        <div ref="drawerBody" class="drawer_body">
            <div class="flex items-center justify-between mb-2">
                <div class="drawer_title">{{ $t('task.sprint_completion') }}</div>
                <a-button 
                    type="ui" 
                    ghost
                    flaticon
                    shape="circle"
                    icon="fi-rr-cross"
                    @click="visible = false" />
            </div>
            <a-spin :spinning="infoLoading" class="w-full">
                <template v-if="sprint">
                    <div class="sprint_name mb-5">
                        {{ sprint.name }}
                    </div>
                    <div class="sprint_stat grid gap-3 md:gap-8 grid-cols-1 md:grid-cols-2 mb-5">
                        <div class="sprint_stat__card green">
                            <div class="count">{{ sprint.completed_task_count }}</div>
                            <div class="label">{{ $t('task.completed_tasks') }}</div>
                        </div>
                        <div class="sprint_stat__card red">
                            <div class="count">{{ openetTasks }}</div>
                            <div class="label">{{ $t('task.open_tasks') }}</div>
                        </div>
                    </div>
                    <div v-if="openetTasks" class="mb-6">
                        <div class="mb-1" style="color: #000;opacity: 0.6;">{{ $t('task.move_open_tasks_to') }}</div>
                        <DSelect
                            v-model="selectSprint" 
                            size="large"
                            class="w-full sprint_search"
                            :class="selectSprint && 'selected'"
                            valueKey="id"
                            apiUrl="tasks/sprint/list/"
                            :params="selectParams"
                            labelKey="name"
                            :placeholder="$t('task.enter_sprint_name')"
                            :allowClear="selectSprint ? true : false"
                            infinity
                            showSearch
                            useSearchApi
                            suffixIcon="fi-rr-search"
                            :getPopupContainer="getPopupContainer"
                            :default-active-first-option="false"
                            :filter-option="false"
                            :not-found-content="null" />
                        <a-alert 
                            :message="$t('task.open_tasks_removal_warning')" 
                            banner
                            class="mt-2"
                            type="info" />
                    </div>
                    <div class="grid gap-2 md:gap-4 grid-cols-1 md:grid-cols-[1fr,250px]">
                        <a-button 
                            type="primary" 
                            size="large"
                            block
                            :loading="loading"
                            @click="formSubmit()">
                            {{ $t('task.complete_sprint') }}
                        </a-button>
                        <a-button 
                            type="primary" 
                            ghost
                            block
                            size="large"
                            @click="visible = false">
                            {{ $t('task.cancel') }}
                        </a-button>
                    </div>
                </template>
            </a-spin>
        </div>
    </a-drawer>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { mapGetters } from 'vuex'
import { errorHandler } from '@/utils/index.js'
export default {
    components: {
        DSelect: () => import('@apps/DrawerSelect/Select.vue')
    },
    computed: {
        ...mapGetters({
            requestData : "projects/info"
        }),
        isInject() {
            return this.inject ? `_inject` : ''
        },
        openetTasks() {
            return this.sprint.in_work_task_count+this.sprint.new_task_count
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        drawerWidth() {
            if(this.windowWidth > 821)
                return 821
            else {
                return '100%'
            }
        },
        selectParams() {
            const params = {
                exclude: this.sprint.id,
                filters: {
                    status__in: ["new", "in_process"],
                }

            }
            if(this.sprint.projects?.length) {
                params.filters.projects__in = this.sprint.projects.map(item => item.id)
            }
            return params
        }
    },
    data() {
        return {
            visible: false,
            sprint: null,
            infoLoading: false,
            selectSprint: null,
            loading: false,
            inject: false
        }
    },
    methods: {
        async formSubmit() {
            try {
                this.loading = true
                await this.$http.put(`tasks/sprint/${this.sprint.id}/update_status/`, {
                    status: 'completed',
                    move_tasks_to: this.selectSprint
                })
                this.$message.success(this.$t('task.sprint_completed'))
                eventBus.$emit(`update_sprints_list${this.isInject}`)
                eventBus.$emit(`update_sprint_${this.sprint.id}`)
                this.visible = false
            } catch(error) {
                errorHandler({error})
            } finally {
                this.loading = false
            }
        },
        getPopupContainer() {
            return this.$refs.drawerBody
        },
        async getSprint(item) {
            try {
                this.infoLoading = true
                const { data } = await this.$http.get(`/tasks/sprint/${item.id}/`)
                if(data) {
                    this.sprint = data
                }
            } catch(error) {
                errorHandler({error})
                this.visible = false
            } finally {
                this.infoLoading = false
            }
        },
        afterVisibleChange(vis) {
            if(!vis) {
                this.sprint = null
                this.inject = false
                this.selectSprint = null
            } else {
                if(this.$route.query?.viewProject || this.$route.query?.viewGroup)
                    this.inject = true
            }
        }
    },
    mounted() {
        eventBus.$on('end_sprint', item => {
            this.visible = true
            this.getSprint(item)
        })
    },
    beforeDestroy() {
        eventBus.$off('end_sprint')
    }
}
</script>

<style lang="scss" scoped>
.sprint_search{
    &:not(.selected){
        &:not(.search_active){
            &::v-deep{
                .ant-select-selection__placeholder{
                    display: block!important;
                }
            }
        }
    }
}
.sprint_end_drawer{
    &::v-deep{
        .ant-drawer-wrapper-body,
        .ant-drawer-content{
            overflow: hidden;
        }
        .drawer_title{
            color: #000;
            opacity: 0.6;
        }
        .ant-drawer-body{
            padding: 0px;
            display: flex;
            flex-direction: column;
            height: 100%;
        }
        .drawer_body{
            overflow-y: auto;
            height: 100%;
            padding: 20px 15px;
            @media (min-width: 768px) {
                padding: 30px 40px;
            }
        }
        .sprint_name{
            font-weight: 400;
            font-size: 24px;
            line-height: 24px;
            color: #000;
        }
        .sprint_stat{
            &__card{
                padding: 20px 30px;
                border-radius: 8px;
                color: #000;
                &.green{
                    background: #bff3d1;
                }
                &.red{
                    background: #f3c0c0;
                }
                .count{
                    font-weight: 400;
                    font-size: 24px;
                    line-height: 24px;
                    margin-bottom: 10px;
                }
                .label{
                    font-weight: 400;
                    font-size: 16px;
                    line-height: 16px;
                }
            }
        }
    }
}
</style>