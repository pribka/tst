<template>
    <Drawer 
        v-model="visible" 
        :title="edit ? $t('project.update_project') : $t('project.add_project')" 
        :width="500"
        :class="isMobile && 'mobile'" 
        class="project_create_drawer" 
        destroyOnClose
        :afterVisibleChange="afterVisibleChange"
        @close="visible = false">
        <div slot="body">
            <a-skeleton  active :paragraph="{ rows: 4 }" :loading="loading"/>
            <div v-show="!loading">
                <a-form-model-item :label="$t('project.avatar_project')">
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
                            <span>{{$t('project.logo_upload')}}</span>
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
                <a-form-model :model="form" ref="form"  :rules="rules">
                    <a-form-model-item  prop="name" :label="$t('project.title_project')">
                        <a-input v-model="form.name" size="large"  />
                    </a-form-model-item>
                    <a-form-model-item name="description" prop="description" :label="$t('project.description')">
                        <a-textarea
                            v-model="form.description"
                            :auto-size="{ minRows: 2, maxRows: 7 }" />
                    </a-form-model-item>
                    <a-form-model-item
                        :label="$t('project.organization')"
                        prop="organization"
                        labelAlign="left">
                        <OrganizationsDrawer
                            v-model="form.organization"
                            :title="$t('project.select_organization')"
                            inputSize="large" />
                    </a-form-model-item>


                    <a-form-model-item 
                        prop="date_start_plan" 
                        ref="date_start_plan" 
                        :label="$t('project.date_start_plan')">
                        <a-date-picker 
                            size="large"
                            :show-time="true"
                            :showTime="{
                                defaultValue: $moment('09:00:00', 'HH:mm:ss')
                            }"
                            @change="changeStartDate"
                            dropdownClassName="project_start"
                            :disabled-time="disabledDateTime"
                            :disabled-date="disabledDate"
                            format="DD.MM.YYYY HH:mm" 
                            v-model="form.date_start_plan"    />
                    </a-form-model-item>

                    <a-form-model-item 
                        prop="dead_line" 
                        ref="dead_line" 
                        :label="$t('project.deadline_project')">
                        <a-date-picker 
                            size="large" 
                            :show-time="true"
                            dropdownClassName="project_end"
                            :disabled-date="disabledDateFrom"
                            :showTime="{
                                defaultValue: $moment('18:00:00', 'HH:mm:ss')
                            }"
                            format="DD.MM.YYYY HH:mm" 
                            v-model="form.dead_line"    />
                    </a-form-model-item>
                    <a-form-model-item  prop="with_chat">
                        <a-checkbox v-model="form.control_dates" class="text-red-500">
                            {{$t('project.control_dates')}}
                        </a-checkbox>
                        <div class="text-gray-400 text-sm"> 
                            {{$t('project.project_control')}}
                        </div>
                    </a-form-model-item>
                    <a-form-model-item  prop="with_chat">
                        <a-checkbox v-model="form.with_chat">
                            {{$t('project.with_chat')}}
                        </a-checkbox>
                    </a-form-model-item>
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
                        {{$t('project.upload')}}
                    </a-button>
                    <a-button type="ui" ghost block size="large" @click="closeCropModal()">
                        {{$t('close')}}
                    </a-button>
                </div>
            </a-drawer>
        </div>
        <div slot="footer">
            <a-button  
                :loading="loadingBtn"  
                type="primary" 
                class="px-6"
                :block="isMobile"
                :size="isMobile ? 'large' : 'default'"
                @click="createProject()">
                {{  id === undefined ?  $t('project.create'):
                    $t('project.update')}}
            </a-button>
        </div>
    </Drawer>
</template>

<script>
import Drawer from './widgets/DrawerTemplate'
import OrganizationsDrawer from './components/OrganizationsDrawer.vue'
import createdMethods from './mixins/createdMethods'
import eventBus from "@/utils/eventBus"
import 'cropperjs/dist/cropper.css'
export default {
    name: "GroupsAndProjectCreateProject",
    mixins: [createdMethods],
    components: {
        Drawer,
        OrganizationsDrawer
    },
    props: {
        pageName: {
            type: String,
            default: 'page_list_project_workgroups.WorkgroupModel'
        },
    },
    data() {
        return {
            dateFormat: 'YYYY-MM-DD HH:mm',
            form: {
                name: "",
                description: "",
                workgroup_logo: null,
                social_links: [],
                is_project: true,
                with_chat: false,
                dead_line: null,
                program: null,
                counterparty: null,
                costing_object: null,
                date_start_plan: null,
                control_dates: false,
                organization: null
            },

            visible: false,
            loading: false,
            previewFile: null,
            edit: false,
            rules: {
                name: [
                    { required: true, message: this.$t('project.field_require'), trigger: 'blur' },
                ],
                description: [{ required: true, message: this.$t('project.field_require'), trigger: 'blur' },],
                dead_line: [{ required: true, message: this.$t('project.field_require'), trigger: 'change' },],
            },
            groupTypes: [],
            sLinks: [],
            listLinks: [],

            loadingBtn: false
        }
    },
    async created() {
        this.getParamsQuerySet()
    },
    watch: {
        async '$route.query' () {
            this.getParamsQuerySet()

        },
    },
    computed:{
        id() {
            return this.$route.query.updateProject
        },
        isMobile() {
            return this.$store.state.isMobile
        }
        // showCreateRelations() {
        //     if(this.$store.state.config.config?.groups_and_projects?.hideCreateRelations)
        //         return false
        //     return true
        // }
    },
    
    mounted(){
        eventBus.$on('open_create_project_drawer', ({ 
            organization=null 
        }) => {  
            this.$router.replace({
                query: { createProject: true }
            })

            this.form.organization = organization
            this.getParamsQuerySet()
        })
    },
    beforeDestroy(){
        eventBus.$off('open_create_project_drawer')
    },
    methods: {
        afterVisibleChange(vis) {
            if(!vis) {
                this.clearAll()
            }
        },
        changeStartDate(date) {
            if(this.form.dead_line && this.$moment(this.form.dead_line).isSameOrBefore(date)) {
                this.form.date_start_plan = this.$moment(date).subtract({hours:1})
            }
        },
        disabledDateTime() {
            if(this.form.dead_line) {
                return {
                    disabledHours: () => this.range(this.$moment(this.form.dead_line).subtract({hours:1}).format('HH'), 24)
                }
            } else
                return null
        },
        range(start, end) {
            const result = []
            for (let i = start; i < end; i++) {
                result.push(i)
            }
            return result
        },
        disabledDate(current) {
            if(this.form.dead_line)
                return current && current > this.$moment(this.form.dead_line).endOf('day')
            else
                return null
        },
        disabledDateFrom(current) {
            if(this.form.date_start_plan) {
                if(this.$moment(this.form.date_start_plan).isSame(current.format(), 'day')) {
                    return false
                } else
                    return current && current < this.$moment(this.form.date_start_plan).endOf('day')
            } else
                return null
        },
        getParamsQuerySet() {
            const query =  Object.assign({}, this.$route.query)

            if(query.hasOwnProperty('createProject')){
                this.init()
            }
            if(query.updateProject){
                this.init()
                this.initUpdate()
            }
        },
        clearAll() {
            this.form = {
                name: "",
                description: "",
                workgroup_logo: null,
                social_links: [],
                is_project: true,
                with_chat: false,
                dead_line: null,
                program: null,
                counterparty: null,
                costing_object: null,
                date_start_plan: null,
                control_dates: false,
                organization: null
            }
            this.close()
        },
        close() {
            const query =  Object.assign({}, this.$route.query)
            delete query['createProject']
            if(query.updateProject) {
                const viewGroup = query.updateProject
                delete query['updateProject']
                query.viewGroup = viewGroup
            }
            this.edit = false
            this.$router.replace({query})
        },
        async createProject() {
            this.$refs.form.validate(async v=>{
                if(v){
                    try{
                        this.loadingBtn = true
                        await this.uploadSocLink();
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
                        if(form.organization?.id)
                            form['organization'] = form.organization.id
                        else
                            form['organization'] = null

                        if(this.id !== undefined){
                            form.name_ru = form.name
                            res =   await   this.updateGroupS({data: form, id: this.id})
                            this.$message.success(this.$t('project.information_edited'))
                        } else {
                            res =   await   this.createGroupS(form)
                            this.$message.success(this.$t('project.project_created'))
                        }


                        this.$refs.form.resetFields()
                        this.sLinks = []
                        eventBus.$emit(`update_filter_workgroups.WorkgroupModel`)
                        eventBus.$emit(`table_row_${this.pageName}`, {
                            action: this.id !== undefined ? 'update' : 'create',
                            row: res
                        })
                        this.visible = false
                        this.$router.replace({
                            query: {viewProject: res.id}
                        })
                    }
                    catch(error){
                        console.log(error)
                        if(error?.length)
                            this.$message.error(error.join(', '))
                        else
                            this.$message.error(this.$t('project.error') + error)
                    }
                    finally{
                        this.loadingBtn = false
                    }
                } else {
                    this.$message.error(this.$t('project.fill_all_fields'))
                }
            })
        }
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
.project_create_drawer{
    &::v-deep{
        .ant-drawer-wrapper-body,
        .ant-drawer-content{
            overflow: hidden;
        }
        .ant-drawer-body{
            padding: 0px;
            height: calc(100% - 40px);
        }
        .drawer_body{
            padding: 15px;
            height: calc(100% - 40px);
            overflow-y: auto;
        }
        .drawer_footer{
            display: flex;
            align-items: center;
            padding-left: 15px;
            padding-right: 15px;
            border-top: 1px solid var(--border2);
            height: 40px;
        }
    }
    &.mobile{
        &::v-deep{
            .drawer_body{
                height: calc(100% - 50px);
            }
            .drawer_footer{
                height: 50px;
                & > div{
                    width: 100%;
                }
            }
        }
    }
}
</style>