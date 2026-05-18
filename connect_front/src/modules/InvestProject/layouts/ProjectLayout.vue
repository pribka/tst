<template>
    <div class="invest_project_wrapper">
        <div class="wrapper_header grid page_grid gap-5 2xl:gap-8">
            <div class="w-full flex flex-col place-content-between">
                <div class="flex items-baseline">
                    <a-button type="ui" ghost flaticon shape="circle" size="large" icon="fi-rr-arrow-small-left" class="back_button mr-2" @click="backProject()" />
                    <h2 v-if="project" class="project-name" :title="project.project_name">
                        {{ project.project_name }}
                    </h2>
                    <a-skeleton v-else active :paragraph="{ rows: 0 }" />
                </div>
                <div class="tab_buttons">
                    <a-button type="primary" size="large" :block="isMobile" :ghost="$route.name === 'full_invest_project_info' ? false : true" class="" @click="changeTab('full_invest_project_info')">
                        {{ $t('invest.projectInfo') }}
                    </a-button>
                    <a-button type="primary" size="large" :block="isMobile" :ghost="$route.name === 'full_invest_project_documents' ? false : true" class="" @click="changeTab('full_invest_project_documents')">
                        {{ $t('invest.documents') }}
                    </a-button>
                    <a-button type="primary" size="large" :block="isMobile" :ghost="$route.name === 'full_invest_project_timeline' ? false : true" @click="changeTab('full_invest_project_timeline')">
                        {{ $t('invest.changeHistory') }}
                    </a-button>
                </div>
            </div>
            <div>
                <div class="header_block">
                    <template v-if="project">
                        <div class="header_block__header">
                            <div class="label">{{ $t('invest.projectInfo') }}</div>
                            <div v-if="project.project" class="tasks-button">
                                <a-button size="large" type="primary" @click="openProjectTasks">
                                    {{ $t('invest.projectTasks') }}
                                </a-button>
                            </div>
                            <div v-else-if="showCreateProject" class="create-button">
                                <a-button size="large" @click="createProject">
                                    {{ $t('invest.createProject') }}
                                </a-button>
                            </div>
                        </div>
                        <div class="block_list">
                            <div v-if="project.organization" class="block_list__item">
                                <div class="name">{{ $t('invest.organization') }}: </div>
                                <div class="value">{{ project.organization.name }}</div>
                            </div>
                            <div v-if="project.author" class="block_list__item">
                                <div class="name">{{ $t('invest.projectAuthor') }}: </div>
                                <div class="value">
                                    <Profiler :user="project.author" :avatarSize="18" />
                                </div>
                            </div>
                        </div>
                    </template>
                </div>
            </div>
        </div>
        <router-view 
            :loading="loading" 
            :actionInfo="actionInfo"
            :actions="actions"
            :statusList="statusList"
            :viewMode="viewMode"
            :project="project" />
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { useTitle } from '@vueuse/core'
export default {
    data() {
        return {
            actionInfo: null,
            actions: null,
            viewMode: false,
            loading: false,
            project: null,
            showCreateProject: false,
            statusList: []
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    methods: {
        openProjectTasks() {
            this.$router.replace({
                query: { viewGroup: this.project.project }
            })
        },
        createProject() {
            this.$confirm({
                title: this.$t('invest.createProjectConfirmation'),
                content: '',
                okText: this.$t('invest.create'),
                cancelText: this.$t('invest.cancel'),
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post(`/invest_projects_info/${this.$route.params.id}/add_project/`)
                            .then((response) => {
                                this.$set(this.project, 'project', response.data)
                                this.$message.success(this.$t('invest.projectCreated'))
                                resolve()
                            })
                            .catch(e => {
                                this.$message.error(this.$t('invest.projectCreationError'))
                                console.log(e)
                                reject(e)
                            })
                    })
                },
                onCancel() {},
            })
        },
        backProject() {
            this.$router.push({ name: 'invest-project' })
        },
        changeTab(name) {
            if(this.$route.name !== name)
                this.$router.push({ name })
        },
        async getInvestActions() {
            try{
                const { data } = await this.$http.get(`/invest_projects_info/${this.$route.params.id}/action_info/`)
                if(data?.edit && data.edit.length) {
                    const object = {}
                    data.edit.forEach(item => {
                        object[item] = true
                    })
                    this.actionInfo = object
                }
                if(data?.actions) {
                    this.actions = data.actions
                    this.showCreateProject = ('add_project' in data.actions) && data.actions.add_project.availability
                }
                if(!('edit' in data) && data.actions.view.availability) {
                    this.viewMode = true
                }
            } catch(e) {
                console.log(e)
            }
        },
        async getStatusList() {
            try{
                const { data } = await this.$http.get(`/invest_projects_info/${this.$route.params.id}/status/`)
                if(data) {
                    this.statusList = data
                }
            } catch(e) {
                console.log(e)
            }
        },
        async getProject() {
            try {
                this.loading = true
                const { data } = await this.$http.get(`/invest_projects_info/${this.$route.params.id}/`)
                if(data) {
                    this.project = data
                    useTitle(data.project_name)
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        },
        reloadData() {
            this.actionInfo = null
            this.actions = null
            this.project = null
            this.statusList = []
            this.viewMode = false
            this.showCreateProject = false
            this.getData()
        },
        getData() {
            this.getProject()
            this.getInvestActions()
            this.getStatusList()
        }
    },
    created() {
        this.getData()
    },
    mounted() {
        eventBus.$on('update_invest_full_project', (data) => {
            this.project = data
        })
        eventBus.$on('reload_invest_full_project', () => {
            this.reloadData()
        })
        eventBus.$on('project_deleted', (id) => {
            if(this.project.project === id) {
                this.$set(this.project, 'project', null)
            }
            this.getInvestActions()
        })
    },
    beforeDestroy() {
        eventBus.$off('update_invest_full_project')
        eventBus.$off('reload_invest_full_project')
        eventBus.$off('project_deleted')
    }
}
</script>

<style lang="scss" scoped>
.header_block{
    background: #fff;
    padding: 15px;
    border-radius: var(--borderRadius);
    @media (min-width: 768px) {
        background: #eff2f5;
        padding: 10px 20px;
    }
    @media (min-width: 1700px){
        padding: 15px 30px;
    }
    .header_block__header{
        display: flex;
        justify-content: space-between;
        .label{
            font-size: 16px;
            color: #000000;
            margin-bottom: 10px;
        }
    }
    .block_list{
        font-size: 14px;
        &__item{
            @media (min-width: 768px) {
                display: flex;
            }
            &:not(:last-child){
                margin-bottom: 10px;
            }
            .name{
                color: #000000;
                opacity: 0.6;
                word-break: break-word;
                @media (min-width: 768px) {
                    min-width: 150px;
                    max-width: 150px;
                    padding-right: 20px;
                }
                @media (min-width: 1200px) {
                    min-width: 150px;
                    max-width: 150px;
                }
            }
            .value{
                color: #000000;
                word-break: break-word;
            }
        }
    }
}
.invest_project_wrapper{
    padding: 20px;
    .back_button{
        font-size: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .wrapper_header{
        margin-bottom: 15px;
        grid-template-columns: 1fr;
        min-height: 171px;
        @media (min-width: 768px) {
            margin-bottom: 30px;
        }
        @media (min-width: 1100px) {
            grid-template-columns: 420px 1fr;
        }
        @media (min-width: 1200px) {
            grid-template-columns: 520px 1fr;
        }
        @media (min-width: 1400px) {
            grid-template-columns: 620px 1fr;
        }
        @media (min-width: 1600px) {
            grid-template-columns: 720px 1fr;
        }
    }
    h2{
        color: #000;
        margin: 0px;
        font-size: 20px;
        font-weight: 400;
        line-height: 26px;
    }
    .tab_buttons{
        margin-top: 15px;
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        @media (max-width: 767px) {
            flex-direction: column;
        }
        @media (min-width: 768px) {
            display: flex;
            align-items: center;
            margin-top: 20px;
        }
        &::v-deep{
            .ant-btn{
                @media (max-width: 768px) {
                    &:not(:last-child){
                        margin-bottom: 8px;
                    }
                }
            }
        }
    }
}
</style>