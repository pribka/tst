<template>
    <div class="dashboard">
        <div class="flex items-center justify-between dashboard__header">
            <div class="title flex items-center w-full truncate">
                <div v-if="dLoading" class="mr-2 title_loader" style="min-width: 150px;" @click="visDashDrawer = true">
                    <a-skeleton active :paragraph="{ rows: 0 }" />
                </div>
                <template v-else>
                    <h1 v-if="activeDashboard" class="truncate cursor-pointer" @click="visDashDrawer = true">
                        {{ activeDashboard.name }}
                    </h1>
                </template>
                <i class="fi fi-rr-angle-small-down ml-1 text-sm gray"></i>
            </div>
            <div class="flex items-center pl-2 gap-2">
                <a-button 
                    icon="fi-rr-pencil" 
                    shape="circle"
                    type="ui"
                    ghost
                    flaticon
                    @click="editDashboard(activeDashboard)"/>
                <a-button 
                    v-if="dashboardList.length > 1"
                    icon="fi-rr-trash" 
                    shape="circle"
                    type="ui"
                    ghost
                    flaticon
                    @click="deleteDashboard(activeDashboard)"/>
                <HelpButton partCode="dashboard" type="button" />
            </div>
        </div>

        <a-spin :spinning="loading">
            <component :is="dashboardWidget" />
        </a-spin>

        <div class="float_dummy"></div>
        <div class="add_widget_float">
            <a-button 
                type="primary" 
                size="large"
                @click="selectWidget()">
                {{ $t('dashboard.addWidget') }}
            </a-button>
        </div>

        <WidgetsDrawer />
        <SettingDrawer />

        <a-modal 
            v-model="visible" 
            :footer="false"
            destroyOnClose
            :afterClose="afterClose"
            :title="edit ? $t('dashboard.editTitle') : $t('dashboard.addTitle')">
            <a-form-model
                ref="ruleForm"
                :model="form"
                :rules="rules">
                <a-form-model-item ref="name" :label="$t('dashboard.name')" prop="name">
                    <a-input v-model="form.name" size="large" />
                </a-form-model-item>
                <a-button type="primary" size="large" block :loading="formLoading" @click="formSubmit">
                    {{ $t('dashboard.save') }}
                </a-button>
            </a-form-model>
        </a-modal>
        <ActivityDrawer 
            v-model="visDashDrawer" 
            useVis
            :cDrawer="closeDashboardDrawer">
            <ActivityItem
                v-for="item in dashboardListFiltered" 
                :key="item.id"
                @click="selectDashboard(item)">
                <i class="fi fi-rr-share-square" />
                {{ item.name }}
            </ActivityItem>
            <ActivityItem v-if="dashboardList.length < 8"  @click="addDashboard()">
                <i class="fi fi-rr-plus" />
                {{ $t('dashboard.addNew') }}
            </ActivityItem>
        </ActivityDrawer>
    </div>
</template>

<script>
import { ActivityItem, ActivityDrawer } from '@/components/ActivitySelect'
const updateKey = 'update_dashboard'
export default {
    components: {
        WidgetsDrawer: () => import('./WidgetsDrawer/index.vue'),
        SettingDrawer: () => import('./SettingDrawer/index.vue'),
        HelpButton: () => import('@apps/Support/components/HelpButton.vue'),
        ActivityItem,
        ActivityDrawer
    },
    computed: {
        dashboardList: {
            get() {
                return this.$store.state.dashboard.dashboardList
            },
            set(val) {
                this.$store.dispatch('dashboard/updateDashboardPosition', val)
            }
        },
        active: {
            get() {
                return this.$store.state.dashboard.active
            },
            set(val) {
                this.$store.commit('dashboard/SET_ACTIVE', val)
            }
        },
        dashboardListFiltered() {
            if(this.dashboardList.length) {
                return this.dashboardList.filter(f => f.id !== this.active)
            } else
                return []
        },
        activeDashboard() {
            if(this.dashboardList.length) {
                const find = this.dashboardList.find(f => f.id === this.active)
                return find || null
            } else
                return null
        },
        dashboardWidget() {
            return () => import('./MobileList.vue')
        }
    },
    data() {
        return {
            dragging: false,
            visDashDrawer: false,
            form: {
                name: '',
                desktop_template: null
            },
            rules: {
                name: [
                    { required: true, message: this.$t('dashboard.fieldRequired'), trigger: 'change' },
                    { max: 100, message: this.$t('dashboard.requiredSym', { sym: 100 }), trigger: 'change' }
                ]
            },
            edit: false,
            dLoading: false,
            loading: false,
            formLoading: false,
            visible: false,
            dashboardTemplate: [],
            dashboardTemplateLoader: false,
            ops: {
                scrollPanel: {
                    scrollingY: false
                },
                vuescroll: {
                    mode: 'native',
                    locking: false
                },
                bar: {
                    background: "#ccc",
                    onlyShowBarOnScroll: false
                }
            }
        }
    },
    created() {
        if(!this.dashboardList.length)
            this.getDashboardList()
        else
            this.updatedState()
    },
    methods: {
        closeDashboardDrawer() {
            this.visDashDrawer = false
        },
        async updatedState() {
            try {
                //this.$message.loading({ content: this.$t('dashboard.updating'), key: updateKey })
                await this.$store.dispatch('dashboard/updatedStateMobile')
                this.$message.success({ content: this.$t('dashboard.updated'), key: updateKey, duration: 0.5 })
            } catch(e) {
                console.log(e)
                //this.$message.error({ content: this.$t('dashboard.updateError'), key: updateKey, duration: 2 })
            }
        },
        selectTemplate(item) {
            if(this.form.desktop_template === item.id) {
                this.form.desktop_template = null
            } else {
                this.form.desktop_template = item.id
            }
        },
        addDashboard() {
            if(!this.dashboardTemplate.length)
                this.getDashboardTemplate()
            this.visible = true
        },
        async getDashboardTemplate() {
            try {
                this.dashboardTemplateLoader = true
                const { data } = await this.$http.get('/widgets/desktop_templates/')
                if(data?.length) {
                    this.dashboardTemplate = data
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.dashboardTemplateLoader = false
            }
        },
        selectDashboard(item) {
            if(this.active !== item.id) {
                this.active = item.id
                localStorage.setItem('active_dashboard', item.id)
                this.getWidgets()
            }
        },
        async getDashboardList() {
            try {
                this.loading = true
                this.dLoading = true 
                await this.$store.dispatch('dashboard/getDashboardList') 
                this.getWidgets()
            } catch(e) {
                console.log(e)
                this.loading = false
            } finally {
                this.dLoading = false
            }
        },
        async getWidgets() {
            try {
                if(!this.loading)
                    this.loading = true
                await this.$store.dispatch('dashboard/getActiveWidgetsMobile', {
                    id: this.active
                })
            } catch(error) {
                if(error?.detail && error.detail.includes(this.$t('dashboard.pageNotFound'))) {
                    localStorage.removeItem('active_dashboard')
                }
                console.log(error)
            } finally {
                this.loading = false
            }
        },
        editDashboard(item) {
            this.visible = true
            this.edit = true
            this.form = {...item}
        },
        reInit() {
            if(this.dashboardList.length) {
                this.active = this.dashboardList[0].id
                this.getWidgets()
            }
        },
        deleteDashboard(item) {
            this.$confirm({
                title: this.$t('dashboard.confirmDelete'),
                okText: this.$t('dashboard.delete'),
                okType: 'danger',
                cancelText: this.$t('dashboard.cancel'),
                maskClosable: true,
                mask: true,
                closable: true,
                onOk: async () => {
                    try { 
                        await this.$store.dispatch('dashboard/deleteDashboard', {
                            id: item.id
                        }) 
                        if(this.active === item.id)
                            this.reInit()
                    } catch(e) {
                        console.log(e)
                    }
                }
            })
        },
        afterClose() {
            this.form = {
                name: '',
                desktop_template: null
            }
            this.edit = false
        },
        formSubmit() {
            this.$refs.ruleForm.validate(async valid => {
                if (valid) {
                    try {
                        this.formLoading = true
                        if(this.edit) {
                            const data = await this.$store.dispatch('dashboard/updateDashboard', {
                                form: this.form
                            }) 
                            if(data) {
                                this.$message.success(this.$t('dashboard.updatedSuccessfully', { d_name: data.name }))
                                this.visible = false
                            }
                        } else {
                            const data = await this.$store.dispatch('dashboard/addDashboard', {
                                form: this.form
                            }) 
                            if(data) {
                                this.$message.success(this.$t('dashboard.createdSuccessfully', { d_name: data.name }))
                                this.visible = false
                                this.getWidgets()
                            }
                        }
                    } catch(e) {
                        console.log(e)
                    } finally {
                        this.formLoading = false
                    }
                } else {
                    return false;
                }
            })
        },
        selectWidget() {
            this.$store.commit('dashboard/SET_CATALOG_VISIBLE', true)
        }
    }
}
</script>

<style lang="scss" scoped>
.dashboard{
    padding: 15px;
    .float_dummy{
        height: 50px;
    }
    .title_loader{
        display: flex;
        align-items: center;
        &::v-deep{
            .ant-skeleton-content{
                display: flex;
                align-items: center;
            }
            .ant-skeleton{
                display: block;
            }
            .ant-skeleton-title{
                min-width: 100%;
                height: 20px;
                margin: 0px;
                border-radius: var(--borderRadius);
            }
        }
    }
    h1{
        font-size: 1.4rem;
        line-height: 1.5;
        font-weight: 300;
        margin-bottom: 0px;
        margin-top: 0px;
    }
    &__header{
        margin-bottom: 10px;
    }
    .add_widget_float{
        --safe-area-inset-bottom: env(safe-area-inset-bottom);
        position: fixed;
        bottom: calc(85px + var(--safe-area-inset-bottom));
        left: 50%;
        z-index: 50;
        display: flex;
        flex-direction: column;
        margin-left: -88px;
        &::v-deep{
            .ant-btn{
                border-radius: 30px;
                padding-left: 20px;
                padding-right: 20px;
                width: 176px;
            }
        }
    }
}
</style>