<template>
    <component 
        :is="wrapperModule" 
        :class="inject || !showHead && 'flex-grow flex flex-col'"
        :pageTitle="pageTitle">
        <div v-if="inject" class="flex mb-4">
            <a-button 
                v-if="showCreateButton"
                icon="fi-rr-plus" 
                flaticon
                size="large" 
                type="primary"
                class="mr-2"
                @click="addSprint()">
                {{ $t('task.create_sprint') }}
            </a-button>
            <PageFilter 
                :model="model"
                :key="pageName"
                size="large"
                :excludeFields="excludeFields"
                :page_name="pageName"/>
        </div>
        <template v-if="!inject && showHead" v-slot:h_left>
            <PageFilter 
                :model="model"
                :key="pageName"
                size="large"
                :excludeFields="excludeFields"
                :page_name="pageName"/>
        </template>
        <template v-if="!inject && showHead" v-slot:h_right>
            <a-button 
                v-if="showCreateButton"
                icon="fi-rr-plus" 
                flaticon
                size="large" 
                type="primary"
                @click="addSprint()">
                {{ $t('task.create_sprint') }}
            </a-button>
            <HelpButton partCode="sprints" type="button" class="ml-2" />
            <component
                :is="settingsButtonWidget"   
                :pageName="pageName"
                size="default"
                class="ml-2" />
        </template>
        <div ref="wrapperRef" class="h-full flex flex-col">
            <UniversalTable 
                :model="model"
                :pageName="pageName"
                tableType="sprint_page"
                :params="queryParams"
                isSprint
                :excludeCol="excludeCol"
                :sprintInject="inject"
                :colParams="{
                    pageName: pageName,
                    model: model,
                    inject: inject,
                    isInject: isInject,
                    getContainer: getContainer
                }"
                :endpoint="`tasks/sprint/list/`" />
        </div>
    </component>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    name: "SprintList",
    components: { 
        PageFilter: () => import('@/components/PageFilter'),
        ModuleWrapper: () => import('@/components/ModuleWrapper/index.vue'),
        HelpButton: () => import('@apps/Support/components/HelpButton.vue'),
        //SprintCard: () => import('./SprintCard.vue'),
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable')
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
        },
        excludeCol: {
            type: Array,
            default: () => []
        }
    },
    data(){
        return {
            wrapperModule: null,
            sprintList: [],
            count: 0,
            listLoading: false,
            page: 1,
            pageSize: 15,
            pageSizeOptions: ['15', '30', '50']
        }
    },
    computed: {
        settingsButtonWidget() {
            return () => import(/* webpackMode: "lazy" */'@/components/TableWidgets/SettingsButton')
        },
        queryParams() {
            if(this.filters)
                return {filters: this.filters}
            return {}
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
        }
    },
    created() {
        this.wrapperModule = this.inject || !this.showHead
            ? 'div'
            : () => import('@/components/ModuleWrapper/index.vue')
    },
    methods: {
        getContainer() {
            return this.$refs.wrapperRef
        },
        addSprint() {
            eventBus.$emit('add_sprint', this.injectForm)
        }
    }
}
</script>