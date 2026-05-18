<template>
    <div class="sports_facilities_page">
        <div class="sports_facilities_row">
            <div class="aside_col">
                <Aside v-if="!isMobile" />
            </div>
            <div class="main_col">
                <div class="wrapper_header">
                    <div class="flex justify-between items-start">
                        <div class="mb-3 md:mb-0 md:flex items-center">
                            <a-button 
                                v-if="isMobile"
                                type="link" 
                                flaticon 
                                size="large" 
                                icon="fi-rr-arrow-small-left" 
                                class="back_button mr-2" 
                                @click="backProject()">
                                <template v-if="isMobile">
                                    <span style="color:#000;">{{ $t('sports.back_route') }}</span>
                                </template>
                            </a-button>
                            <a-button 
                                v-else
                                type="ui"
                                ghost
                                flaticon 
                                shape="circle" 
                                size="large" 
                                icon="fi-rr-arrow-small-left" 
                                class="back_button mr-2" 
                                @click="backProject()" />
                            <h2 v-if="project" class="break-words">{{ project.name }}</h2>
                            <a-skeleton v-else active :paragraph="{ rows: 0 }" />
                        </div>
                        <div v-if="!isMobile" class="lg:flex items-center justify-between head_panel">
                            <div v-if="project" class="lg:flex items-center">
                                <div class="doc_status mr-5" :class="isMobile && 'w-full flex justify-center mb-2'">
                                    <span class="opacity-60">
                                        {{ $t('sports.status') }}
                                    </span>
                                    <a-badge 
                                        class="doc_status__badge"
                                        :color="project.status.color" 
                                        :text="project.status.name" />
                                </div>
                                <template v-if="checkActions && actions.change_status && actions.change_status.availability">
                                    <a-button
                                        v-for="item in checkStatusList" 
                                        :key="item.id" 
                                        size="large"
                                        class="flex items-center mr-1"
                                        :style="`border-color: ${item.hex_color}; color: ${item.hex_color}`"
                                        @click="changeStatus(item.code)">
                                        {{ item.btn_title || item.name }}
                                    </a-button>
                                </template>
                                <a-dropdown
                                    v-if="checkActions" 
                                    :trigger="['click']">
                                    <a-button 
                                        type="ui" 
                                        ghost 
                                        shape="circle"
                                        icon="fi-rr-menu-dots-vertical"
                                        flaticon
                                        :loading="statusLoading" />
                                    <a-menu slot="overlay">
                                        <a-menu-item v-if="actions.edit && actions.edit.availability" class="flex items-center" @click="editHandler()">
                                            <i class="fi fi-rr-edit mr-2" />
                                            {{ $t('sports.edit') }}
                                        </a-menu-item>
                                        <a-menu-item 
                                            v-if="actions.delete && actions.delete.availability" 
                                            class="flex items-center text-red-500"
                                            @click="deleteProject()">
                                            <i class="fi fi-rr-trash mr-2" />
                                            {{ $t('sports.delete') }}
                                        </a-menu-item>
                                    </a-menu>
                                </a-dropdown>
                            </div>
                        </div>
                    </div>
                    <div v-if="isMobile" class="grid gap-2 grid-cols-2 mb-4">
                        <a-button 
                            type="primary" 
                            size="large" 
                            :ghost="$route.name === 'full_sports_facilities_pasport' ? false : true"
                            block
                            @click="$router.push({ name: 'full_sports_facilities_pasport' })">
                            {{ $t('sports.objectPassport') }}
                        </a-button>
                        <a-button 
                            type="primary" 
                            :ghost="$route.name === 'full_sports_facilities_pasport' ? true : false" 
                            size="large" 
                            block
                            @click="$router.push({ name: 'full_sports_facilities_repair' })">
                            {{ $t('sports.tabInformation') }}
                        </a-button>
                    </div>
                    <div v-if="!isMobile" class="tab_buttons mt-4">
                        <a-menu 
                            :selectedKeys="[$route.name]" 
                            ref="mainMenu"
                            class="top_menu w-full"
                            mode="horizontal">
                            <a-menu-item key="full_sports_facilities_gallery" @click="changeTab('full_sports_facilities_gallery')">
                                {{ $t('sports.gallery') }}
                            </a-menu-item>
                            <a-menu-item key="full_sports_facilities_section_information" @click="changeTab('full_sports_facilities_section_information')">
                                {{ $t('sports.sectionInfo') }}
                            </a-menu-item>
                            <a-menu-item key="full_sports_facilities_object_information" @click="changeTab('full_sports_facilities_object_information')">
                                {{ $t('sports.objectInformation') }}
                            </a-menu-item>
                            <a-menu-item key="full_sports_facilities_repair" @click="changeTab('full_sports_facilities_repair')">
                                {{ $t('sports.repair') }}
                            </a-menu-item>
                            <!--
                            <a-menu-item key="full_sports_facilities_sections" @click="changeTab('full_sports_facilities_sections')">
                                {{ $t('sports.sections') }}
                            </a-menu-item>
                            <a-menu-item key="full_sports_facilities_technical" @click="changeTab('full_sports_facilities_technical')">
                                {{ $t('sports.technical') }}
                            </a-menu-item>
                            <a-menu-item key="full_sports_facilities_characteristics" @click="changeTab('full_sports_facilities_characteristics')">
                                {{ $t('sports.characteristics') }}
                            </a-menu-item>-->
                        </a-menu>
                        <!--<a-button type="primary" size="large" :block="isMobile" :ghost="$route.name === 'full_sports_facilities_gallery' ? false : true" class="" @click="changeTab('full_sports_facilities_gallery')">
                            {{ $t('sports.gallery') }}
                        </a-button>
                        <a-button type="primary" size="large" :block="isMobile" :ghost="$route.name === 'full_sports_facilities_repair' ? false : true" class="" @click="changeTab('full_sports_facilities_repair')">
                            {{ $t('sports.repair') }}
                        </a-button>
                        <a-button type="primary" size="large" :block="isMobile" :ghost="$route.name === 'full_sports_facilities_characteristics' ? false : true" class="" @click="changeTab('full_sports_facilities_characteristics')">
                            {{ $t('sports.characteristics') }}
                        </a-button>
                        
                            <a-button type="primary" size="large" :block="isMobile" :ghost="$route.name === 'full_sports_facilities_sections' ? false : true" class="" @click="changeTab('full_sports_facilities_sections')">
                                {{ $t('sports.sections') }}
                            </a-button>
                            <a-button type="primary" size="large" :block="isMobile" :ghost="$route.name === 'full_sports_facilities_technical' ? false : true" @click="changeTab('full_sports_facilities_technical')">
                                {{ $t('sports.technical') }}
                            </a-button>
                        -->
                    </div>
                    <div v-if="isMobile" class="lg:flex items-center justify-between head_panel">
                        <div v-if="project" class="lg:flex items-center">
                            <div class="flex justify-between items-center">
                                <div class="doc_status mr-5" :class="isMobile && 'w-full flex justify-center mb-2'">
                                    <span class="opacity-60">
                                        {{ $t('sports.status') }}
                                    </span>
                                    <a-badge 
                                        class="doc_status__badge whitespace-nowrap"
                                        :color="project.status.color" 
                                        :text="project.status.name" />
                                </div>
                                <a-dropdown
                                    v-if="checkActions" 
                                    :trigger="['click']">
                                    <a-button 
                                        type="ui" 
                                        ghost 
                                        shape="circle"
                                        icon="fi-rr-menu-dots-vertical"
                                        flaticon
                                        :loading="statusLoading" />
                                    <a-menu slot="overlay">
                                        <a-menu-item v-if="actions.edit && actions.edit.availability" class="flex items-center" @click="editHandler()">
                                            <i class="fi fi-rr-edit mr-2" />
                                            {{ $t('sports.edit') }}
                                        </a-menu-item>
                                        <a-menu-item 
                                            v-if="actions.delete && actions.delete.availability" 
                                            class="flex items-center text-red-500"
                                            @click="deleteProject()">
                                            <i class="fi fi-rr-trash mr-2" />
                                            {{ $t('sports.delete') }}
                                        </a-menu-item>
                                    </a-menu>
                                </a-dropdown>
                            </div>
                            <template v-if="checkActions && actions.change_status && actions.change_status.availability">
                                <a-button
                                    v-for="item in checkStatusList" 
                                    :key="item.id" 
                                    size="large"
                                    class="mt-2"
                                    block
                                    :style="`border-color: ${item.hex_color}; color: ${item.hex_color}`"
                                    @click="changeStatus(item.code)">
                                    {{ item.btn_title || item.name }}
                                </a-button>
                            </template>
                            

                            
                            
                            
                            <!-- <div class="doc_status" :class="isMobile && 'w-full flex justify-center mb-2'">
                                {{ $t('sports.status') }}: {{ project.status.name }}
                            </div>



                            <a-button-group 
                                v-if="checkActions" 
                                class="lg:ml-2"
                                :class="isMobile && 'w-full'">
                                <a-button 
                                    v-if="nextStatus && actions.change_status && actions.change_status.availability"
                                    :loading="statusLoading"
                                    size="large"
                                    :block="isMobile"
                                    type="primary"
                                    @click="changeStatus(nextStatus.code)">
                                    {{ nextStatus.name }}
                                </a-button>
                                <a-dropdown :trigger="['click']">
                                    <a-button 
                                        block 
                                        class="act_btn flex items-center justify-center"
                                        size="large" 
                                        icon="fi-rr-menu-dots-vertical"
                                        flaticon
                                        :loading="statusLoading"
                                        type="primary" />
                                    <a-menu slot="overlay">
                                        <template v-if="actions.change_status && actions.change_status.availability">
                                            <a-menu-item 
                                                v-for="item in checkStatusList" 
                                                :key="item.id" 
                                                class="flex items-center"
                                                @click="changeStatus(item.code)">
                                                <a-badge :color="item.color" class="mr-2" />
                                                {{ item.name }}
                                            </a-menu-item>
                                        </template>
                                        <a-menu-item v-if="actions.edit && actions.edit.availability" class="flex items-center" @click="editHandler()">
                                            <i class="fi fi-rr-edit mr-2" />
                                            {{ $t('sports.edit') }}
                                        </a-menu-item>
                                        <a-menu-item 
                                            v-if="actions.delete && actions.delete.availability" 
                                            class="flex items-center text-red-500"
                                            @click="deleteProject()">
                                            <i class="fi fi-rr-trash mr-2" />
                                            {{ $t('sports.delete') }}
                                        </a-menu-item>
                                    </a-menu>
                                </a-dropdown>
                            </a-button-group> -->
                        </div>
                    </div>
                </div>
                <template v-if="project && actions">
                    <a-dropdown 
                        v-if="isMobile && $route.name !== 'full_sports_facilities_pasport'" 
                        :trigger="['click']" 
                        class="mb-4">
                        <a-button type="primary" size="large" block class="flex items-center justify-between">
                            <span>{{ $t(`sports.${$route.name}`) }}</span>
                            <i class="fi fi-rr-angle-small-down" />
                        </a-button>
                        <a-menu slot="overlay">
                            <a-menu-item @click="$router.push({ name: 'full_sports_facilities_gallery' })">
                                {{ $t('sports.gallery') }}
                            </a-menu-item>
                            <a-menu-item @click="$router.push({ name: 'full_sports_facilities_section_information' })">
                                {{ $t('sports.sectionInfo') }}
                            </a-menu-item>
                            <a-menu-item @click="$router.push({ name: 'full_sports_facilities_object_information' })">
                                {{ $t('sports.objectInformation') }}
                            </a-menu-item>
                            <a-menu-item @click="$router.push({ name: 'full_sports_facilities_repair' })">
                                {{ $t('sports.repair') }}
                            </a-menu-item>
                        </a-menu>
                    </a-dropdown>
                    <router-view :actionInfo="actions" />
                    <!--
                        <RepairRequest v-if="
                        $route.name !== 'full_sports_facilities_gallery' && 
                            $route.name !== 'full_sports_facilities_history' &&
                            $route.name !== 'full_sports_facilities_files' && 
                            $route.name !== 'full_sports_facilities_characteristics' &&
                            $route.name !== 'full_sports_facilities_technical' &&
                            $route.name !== 'full_sports_facilities_sections'" />
                    -->
                </template>
                <a-skeleton v-else active :paragraph="{ rows: 6 }" />
            </div>
        </div>
    </div>
</template>

<script>
import Aside from '../components/Aside.vue'
//import RepairRequest from '../components/RepairRequest.vue'
import { mapState } from 'vuex'
import store from "../store/index"
import eventBus from '@/utils/eventBus'

export default {
    components: {
        Aside,
        //RepairRequest
    },
    computed: {
        ...mapState({
            project: state => state.facilities.project,
            actions: state => state.facilities.projectActions
        }),
        isMobile() {
            return this.$store.state.isMobile
        },
        checkActions() {
            if(this.actions) {
                if(this.actions.change_status?.availability || this.actions.delete?.availability || this.actions.edit?.availability)
                    return true
            }
            return false
        },
        checkStatusList() {
            if(this.statusList.length && this.project)
                return this.statusList.filter(f => f.code !== this.project.status.code)
            return []
        },
        nextStatus() {
            if(this.checkStatusList.length) {
                return this.checkStatusList[0]
            }
            return null
        }
    },
    data() {
        return {
            loading: false,
            statusLoading: false,
            statusList: []
        }
    },
    metaInfo() {
        return {
            htmlAttrs: {
                class: 'bg_white'
            }
        }
    },
    created() {
        if(!this.$store.hasModule('facilities')) {
            this.$store.registerModule("facilities", store)
        }
        this.getProject()
    },
    methods: {
        deleteProject() {
            this.$confirm({
                title: this.$t('sports.delete_message'),
                okText: this.$t('sports.delete'),
                okType: 'danger',
                cancelText: this.$t('sports.cancel'),
                onOk: () => {
                    this.statusLoading = true
                    return new Promise((resolve, reject) => {
                        this.$http.put('/sports_facilities/delete/', {
                            id: this.$route.params.id
                        })
                            .then(() => {
                                this.statusLoading = false
                                this.$message.success(this.$t('sports.delete_success'))
                                this.backProject()
                                resolve()
                            })
                            .catch((error) => { reject(error) })
                    })
                }
            })
        },
        editHandler() {
            eventBus.$emit('edit_sports_facilities', {...this.project})
        },
        async changeStatus(code) {
            try {
                this.statusLoading = true
                await this.$store.dispatch('facilities/changeStatus', { id: this.$route.params.id, code })
                await this.$store.dispatch('facilities/getProjectActions', { id: this.$route.params.id })
                if(this.actions.change_status?.availability)
                    await this.getProjectStatus()
            } catch(e) {
                console.log(e)
            } finally {
                this.statusLoading = false
            }
        },
        async getProject(reload = false) {
            try {
                this.loading = true
                await this.$store.dispatch('facilities/getProject', { id: this.$route.params.id, reload })
                if(!reload && this.actions.change_status?.availability)
                    await this.getProjectStatus()
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        },
        async getProjectStatus() {
            try {
                this.statusLoading = true
                const { data } = await this.$http.get(`/sports_facilities/${this.$route.params.id}/status/`)
                if(data) {
                    this.statusList = data
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.statusLoading = false
            }
        },
        backProject() {
            this.$router.push({ name: 'sports-facilities' })
        },
        changeTab(name) {
            if(this.$route.name !== name)
                this.$router.push({ name })
        },
    },
    beforeDestroy() {
        this.$store.commit('facilities/SET_PROJECT', null)
    }
}
</script>

<style lang="scss" scoped>
.top_menu{
    border: 0px;
    user-select: none;
    background: #f7f9fc;
    &.ant-menu-horizontal{
        line-height: 38px;
    }
    &::v-deep{
        .ant-menu-submenu{
            &.ant-menu-submenu-horizontal{
                border: 1px solid #1890ff;
                top: initial;
                border-radius: 8px;
                height: 40px;
                width: 40px;
                font-size: 24px;
                .ant-menu-submenu-title{
                    padding: 0px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #000;
                }
            }
        }
        .ant-menu-item{
            top: initial;
            border: 1px solid #1890ff;
            border-radius: 8px;
            padding: 0 15px;
            color: #1890ff;
            height: 40px;
            &:not(:last-child){
                margin-right: 10px;
            }
            &:hover{
                border-bottom: 1px solid #1890ff;
            }
            &.ant-menu-item-selected{
                background: #1890ff;
                color: #fff;
                &:hover{
                    color: #fff;
                }
            }
        }
    }
}
.sports_facilities_page{
    padding: 20px;
    .sports_facilities_row{
        margin-left: -15px;
        margin-right: -15px;
        @media (min-width: 992px) {
            display: flex;
            flex-wrap: wrap;
        }
    }
    .main_col,
    .aside_col{
        padding-left: 15px;
        padding-right: 15px;
        flex: 0 0 auto;
    }
    .aside_col{
        @media (min-width: 992px) {
            width: 35%;
        }
        @media (min-width: 1100px) {
            width: 30%;
        }
        @media (min-width: 1500px) {
            width: 25%;
        }
        
    }
    .main_col{
        @media (min-width: 992px) {
            width: 65%;
        }
        @media (min-width: 1100px) {
            width: 70%;
        }
        @media (min-width: 1500px) {
            width: 75%;
        }
    }
    .wrapper_header{
        margin-bottom: 20px;
        @media (min-width: 768px) {
            margin-bottom: 30px;
        }
    }
    .doc_status{
        display: flex;
        flex-direction: column;
        // background: #FFA940;
        color: #000;
        // border-radius: 8px;
        // height: 40px;
        // padding: 0 15px;
        // font-size: 13px;
        // line-height: 40px;
        // white-space: nowrap;
        // @media (min-width: 1024px) {
        //     display: inline-block;
        // }
    }

    .doc_status__badge::v-deep {
        .ant-badge-status-dot {
            width: 10px;
            height: 10px;
        }
        .ant-badge-status-text {
            margin-left: 5px;
            color: #000;
        }
    }

    .back_button{
        font-size: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        @media (max-width: 767px) {
            padding-left: 0px;
        }
        @media (min-width: 768px) {
            font-size: 32px;
        }
    }
    h2{
        color: #000;
        margin: 0px;
        font-size: 20px;
        font-weight: 400;
        line-height: 26px;
    }
    &::v-deep{
        .page_block{
            @media (min-width: 768px) {
                border-top: 1px solid #EBEBEB;
                padding-top: 30px;
            }
        }
    }
}
</style>