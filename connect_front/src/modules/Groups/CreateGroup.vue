<template>
    <DrawerTemplate 
        v-model="visible" 
        :width="600" 
        :class="isMobile && 'mobile'"
        destroyOnClose
        @afterVisibleChange="afterVisibleChange"
        @close="clearAll()" >
        <template #title>
            <div class="drawer_title">
                {{ edit ? $t('wgr.update_group') : $t('wgr.create_group') }}
            </div>
        </template>
        <template #rightHeader>
            <HelpButton partCode="groups" />
        </template>
        <a-skeleton  active :paragraph="{ rows: 4 }" :loading="loading"/>
        <div v-show="!loading">
            <a-form-model 
                :model="form" 
                ref="form" 
                :rules="rules">
                <a-form-model-item 
                    class="mb-2"
                    :label="$t('wgr.avatar_group')">
                    <div class="flex items-center">
                        <label for="wrg_avatar" class="cursor-pointer">
                            <a-avatar 
                                :size="60" 
                                :src="form.workgroup_logo && form.workgroup_logo.path ? form.workgroup_logo.path : null"
                                :key="form.workgroup_logo && form.workgroup_logo.path ? form.workgroup_logo.path : null"
                                flaticon
                                icon="fi-rr-users-alt" />
                        </label>
                        <label for="wrg_avatar" class="cursor-pointer ml-2 ant-btn ant-btn-dashed flex items-center">
                            <i class="flaticon fi fi-rr-cloud-upload-alt"></i>
                            <span>{{ $t('wgr.logo_upload') }}</span>
                        </label>
                    </div>
                    <input
                        type="file"
                        id="wrg_avatar"
                        style="display:none;"
                        ref="wrg_avatar"
                        v-on:change="handleFileChange"
                        accept=".jpg, .jpeg, .png, .gif" />
                </a-form-model-item>
                <a-form-model-item 
                    prop="name" 
                    class="mb-2"
                    :label="$t('wgr.title_group')">
                    <a-input 
                        v-model="form.name" 
                        size="large"  />
                </a-form-model-item>
                <a-form-model-item 
                    prop="organization" 
                    class="mb-2"
                    :label="$t('Organization')">
                    <DSelect
                        v-model="form.organization"
                        apiUrl="/contractor_permissions/organizations/"
                        class="w-full"
                        oneSelect
                        size="large"
                        :params="{ permission_type: 'create_workgroup' }"
                        showPlaceholder
                        labelKey="name"
                        :placeholder="$t('Organization')"
                        :listObject="false"
                        :default-active-first-option="false"
                        :filter-option="false"
                        :not-found-content="null" />
                </a-form-model-item>
                <a-form-model-item v-if="!edit" :label="$t('wgr.participants')" prop="members" class="mb-2">
                    <UserDrawer
                        :id="defaultUserSelectId"
                        v-model="form.members.profile_id"
                        :metadata="{ key: 'profile_id', value: form.metadata }"
                        :changeMetadata="changeMetadata"
                        multiple
                        :buttonText="$t('wgr.participants')"
                        :title="$t('wgr.participants')"/>
                </a-form-model-item>
                <a-form-model-item 
                    class="mb-2"
                    name="description" 
                    prop="description" 
                    :label="$t('wgr.description')">
                    <a-textarea
                        v-model="form.description"
                        :auto-size="{ minRows: 2, maxRows: 7 }" />
                </a-form-model-item>
                <!--<div class="flex items-center gap-2">
                    <a-form-model-item  prop="public_or_private" class="mb-0" >
                        <a-checkbox v-model="form.public_or_private">
                            {{$t('wgr.closed')}}
                        </a-checkbox>
                    </a-form-model-item>
                    <a-form-model-item  prop="with_chat" class="mb-0" >
                        <a-checkbox v-model="form.with_chat">
                            {{$t('wgr.with_chat')}}
                        </a-checkbox>
                    </a-form-model-item>
                </div>-->
            </a-form-model>
        </div>
        <a-drawer
            title=""
            placement="right"
            :width="cropDrawerWidth"
            :zIndex="99999"
            destroyOnClose
            class="cropper_modal"
            :visible="cropModal"
            @close="closeCropModal()">
            <div class="cr_d_body">
                <div v-if="dataUrl" class="relative h-full">
                    <img
                        ref="avatarImg"
                        @load.stop="createCropper"
                        :src="dataUrl" />

                    <div class="action_btn flex items-center">
                        <a-button 
                            type="ui"
                            icon="fi-rr-rotate-left" 
                            flaticon
                            shape="circle"
                            @click="cropper.rotate(-45)" />
                        <a-button 
                            type="ui"
                            class="ml-1" 
                            flaticon
                            shape="circle"
                            icon="fi-rr-rotate-right"
                            @click="cropper.rotate(45)"  />
                    </div>
                </div>
            </div>
            <div class="cr_d_footer">
                <a-button type="primary" size="large" block @click="uploadImage()" class="mb-2" :loading="uploadLoading">
                    {{$t('wgr.upload')}}
                </a-button>
                <a-button type="ui" ghost block size="large" @click="closeCropModal()">
                    {{$t('close')}}
                </a-button>
            </div>
        </a-drawer>
        <template #footer>
            <a-button 
                :loading="loadingBtn" 
                type="primary"
                class="px-6"
                block
                size="large"
                @click="createGroup()">
                {{  edit ? $t('wgr.update') : $t('wgr.create')}} 
            </a-button>
        </template>
    </DrawerTemplate>
</template>

<script>
import createdMethods from './mixins/createdMethods'
import eventBus from "@/utils/eventBus"
import { formModel } from './utils.js'
import 'cropperjs/dist/cropper.css'
import { mapState } from 'vuex'
import { errorHandler } from '@/utils/index.js'
export default {
    name: "GroupsAndProjectsCreateGroup",
    mixins: [createdMethods],
    props: {
        buttonSize: {
            type: String,
            default: 'default'
        },
        pageName: {
            type: String,
            default: 'page_list_workgroup_workgroups.WorkgroupModel'
        },
    },
    components: {
        HelpButton: () => import('@apps/Support/components/HelpButton.vue'),
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue'),
        UserDrawer: () => import("@apps/DrawerSelect/index.vue"),
        DSelect: () => import('@apps/DrawerSelect/Select.vue')
    },
    data(){
        return{
            form: {...formModel},
            visible: false,
            loading: false,
            previewFile: null,
            defaultUserSelectId: 'workgroups',
            edit: false,
            rules: {
                organization: [
                    {
                        required: true,
                        message: this.$t("project.field_require"),
                        trigger: "blur",
                    },
                ],
                name: [
                    { required: true, message: this.$t('wgr.field_require'), trigger: 'blur' },
                ],
                workgroup_type: [{ required: true, message: this.$t('wgr.field_require'), trigger: 'blur' },]
            },
            groupTypes: [],
            sLinks: [],
            listLinks: [],

            loadingBtn: false
        }
    },
    created(){
        this.getParamsQuerySet()
    },
    watch: {
        '$route.query'() {
            this.getParamsQuerySet()
        }
    },
    computed:{
        ...mapState({
            user: state => state.user.user,
            formInject: state => state.workgroups.formInject
        }),
        id(){
            return   this.$route.query.updateGroup
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        isEditFromList() {
            return this.$route.query.updateGroupFromList === '1'
        },
        // showCreateRelations() {
        //     if(this.$store.state.config.config?.groups_and_projects?.hideCreateRelations)
        //         return false
        //     return true
        // }

    },
    methods: {
        changeMetadata({ key, value }) {
            this.$set(this.form.metadata, key, value);
        },
        getParamsQuerySet() {
            if(this.$route.query?.createGroup){
                this.init()

            }
            if(this.$route.query?.updateGroup){
                this.init()
                this.initUpdate()
            }
        },
        afterVisibleChange(vis) {
            if(!vis) {
                this.edit = false
                this.$store.commit('workgroups/SET_FORM_INJECT', null)
            } else {
                if(this.formInject) {
                    this.form = {...this.formInject}
                    this.$store.commit('workgroups/SET_FORM_INJECT', null)
                }
            }
        },
        clearAll(){
            this.visible = false
            this.form = JSON.parse(JSON.stringify(formModel))
            this.form.members.profile_id = []
            this.form.metadata.profile_id = []
            this.close()
        },
        close(){
            const query = {...this.$route.query}
            if(query.createGroup) {
                delete query.createGroup
            }
            if(query.updateGroup) {
                const viewGroup = query.updateGroup
                delete query.updateGroup
                if(!query.updateGroupFromList) {
                    query.viewGroup = viewGroup
                }
            }
            delete query.updateGroupFromList
            this.file = null
            this.dataUrl = null
            this.previewFile = null
            this.groupTypes = []
            this.sLinks = []
            this.listLinks = []
            this.$router.replace({query})
        },
        async createGroup(){
            this.$refs.form.validate(async v=>{
                if(v){
                    try{
                        this.loadingBtn = true
                        await this.uploadSocLink();
                        await new Promise(resolve => setTimeout(resolve, 1000))
                        let res;

                        let form = {
                            ...this.form
                        }

                        if(form?.program?.id)
                            form['program'] = form.program.id
                        if(form?.counterparty?.id)
                            form['counterparty'] = form.counterparty.id
                        if(form?.costing_object?.id)
                            form['costing_object'] = form.costing_object.id
                        if(form.workgroup_logo?.id)
                            form['workgroup_logo'] = form.workgroup_logo.id
                        else
                            form['workgroup_logo'] = null

                        delete form.funds_currency

                        if(this.id !== undefined){
                            form.name_ru = form.name
                            delete form.members
                            res =   await   this.updateGroupS({data: form, id: this.id})
                            this.$message.success(this.$t('wgr.information_edited'))
                        } else {
                            if (form.members.profile_id?.length)
                                form.members.profile_id = form.members.profile_id
                                    .map(item => item.id)
                                    .filter(id => id !== this.user.id)

                            res =   await   this.createGroupS(form)
                            this.$message.success(this.$t('wgr.group_created'))
                        }

                        if(res) {
                            if(this.$refs?.form)
                                this.$refs.form.resetFields();
                            this.sLinks = [];
                            this.visible = false
                            eventBus.$emit('update_list_group')
                            eventBus.$emit(`table_row_${this.pageName}`, {
                                action: this.id !== undefined ? 'update' : 'create',
                                row: res
                            })
                            const query = {...this.$route.query}
                            delete query.updateGroup
                            delete query.updateGroupFromList
                            delete query.createGroup
                            if(!this.isEditFromList) {
                                query.viewGroup = res.id
                            }
                            this.$router.replace({query})
                        }
                    }
                    catch(error){
                        errorHandler({error})
                    }
                    finally{
                        setTimeout(() => {
                            this.loadingBtn = false
                        }, 1000);

                    }
                } else {
                    this.$message.error(this.$t('wgr.fill_all_fields'))
                }
            })

        },

    }
}
</script>

<style lang="scss" scoped>
.cropper_modal{
    &::v-deep{
        .ant-drawer-wrapper-body,
        .ant-drawer-content{
            overflow: hidden;
        }
        .cropper-face{
            border-radius: 50%;
        }
        .cropper-view-box {
            border-radius: 50%;
        }
        .ant-drawer-header-no-title{
            display: none;
        }
        .ant-drawer-body{
            height: 100%;
            padding: 0px;
        }
        .cr_d_body{
            height: calc(100% - 100px);
        }
        .action_btn{
            position: absolute;
            bottom: 10px;
            right: 15px;
        }
        .cr_d_footer{
            height: 100px;
            border-top: 1px solid var(--border1);
            padding: 5px 15px;
        }
    }
}
</style>
