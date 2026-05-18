<template>
    <DrawerTemplate
        :title="drawerTitle"
        :width="drawerWidth"
        destroyOnClose
        @close="visible = false"
        @afterVisibleChange="afterVisibleChange"
        v-model="visible">
        <template #rightHeader>
            <HelpButton partCode="organization" />
        </template>
        <template>
            <template v-if="formLoading">
                <div class="w-full flex justify-center py-10">
                    <a-spin />
                </div>
            </template>
            <a-form-model
                v-else
                ref="orgForm"
                :model="form"
                :rules="rules">
                <template v-if="!isDepartment">
                    <a-form-model-item
                        ref="logo"
                        label=""
                        prop="logo">
                        <div class="relative flex items-center">
                            <div :key="logoUrl || visible">
                                <a-avatar
                                    :size="60"
                                    :src="logoUrl"
                                    icon="picture" />
                            </div>
                            <div class="ml-2">
                                <label for="or_logo_upload" class="ant-btn ant-btn-dashed flex items-center justify-center">
                                    <i class="fi fi-rr-cloud-upload-alt mr-2"></i> {{ logoUrl ? $t('team.replace_logo') : $t('team.upload_logo') }}
                                </label>
                                <input
                                    type="file"
                                    id="or_logo_upload"
                                    style="display:none;"
                                    ref="orLogoUpload"
                                    v-on:change="handleFileChange"
                                    accept=".jpg, .jpeg, .png, .gif" />
                            </div>
                        </div>
                    </a-form-model-item>
                </template>
                <a-form-model-item
                    ref="full_name_ru"
                    :label="formFullNameLabel"
                    prop="full_name_ru">
                    <a-input
                        :max-length="255"
                        v-model="form.full_name_ru"
                        @pressEnter="formSubmit()"
                        size="large" />
                </a-form-model-item>
                <!--<a-form-model-item
                    ref="full_name_kk"
                    :label="formFullNameLabel + ' (кз)'"
                    prop="full_name_kk">
                    <a-input
                        :max-length="255"
                        v-model="form.full_name_kk"
                        @pressEnter="formSubmit()"
                        size="large" />
                </a-form-model-item>-->
                <a-form-model-item
                    ref="name_ru"
                    :label="formShortNameLabel"
                    prop="name_ru">
                    <a-input
                        :max-length="255"
                        v-model="form.name_ru"
                        @pressEnter="formSubmit()"
                        size="large" />
                </a-form-model-item>
                <!--<a-form-model-item
                    ref="name_kk"
                    :label="formShortNameLabel + ' (кз)'"
                    prop="name_kk">
                    <a-input
                        :max-length="255"
                        v-model="form.name_kk"
                        @pressEnter="formSubmit()"
                        size="large" />
                </a-form-model-item>-->
                <template v-if="!isDepartment">
                    <a-form-model-item
                        ref="inn"
                        :label="taxIDLabel"
                        prop="inn">
                        <a-input
                            :max-length="12"
                            v-model="form.inn"
                            @input="onInnInput"
                            @pressEnter="formSubmit()"
                            type="text"
                            inputmode="numeric"
                            size="large" />
                    </a-form-model-item>
                </template>
                <template v-if="isDepartment || isStructure || edit">
                    <a-form-model-item
                        ref="director"
                        :label="$t('team.director')"
                        prop="director"
                        labelAlign="left">
                        <DrawerSelectUser
                            v-model="form.director"
                            inputSize="large"
                            class="w-full"
                            :isDepartment="isDepartment"
                            :parentId="organizationParent"
                            :organizationId="organizationParent"
                            isDirectorSelect
                            :title="$t('team.select_employee')" />
                    </a-form-model-item>
                </template>
                <template v-if="!isDepartment">
                    <a-form-model-item
                        ref="contractor_parent"
                        :label="$t('team.parent_organization')"
                        prop="inn">
                        <DrawerSelectOrganization
                            v-model="form.contractor_parent"
                            :disabled="isSelectOrganizationDisabled"
                            inputSize="large"
                            class="w-full"
                            :organizationId="organization && organization.id || null"
                            :title="$t('team.select_organization')" />
                    </a-form-model-item>
                </template>
                <a-form-model-item
                    ref="email"
                    :label="$t('team.email')"
                    prop="email">
                    <a-input
                        :max-length="255"
                        v-model="form.email"
                        @pressEnter="formSubmit()"
                        type="email"
                        size="large" />
                </a-form-model-item>
                <a-form-model-item
                    ref="phone"
                    :label="$t('team.phone')"
                    prop="phone">
                    <a-input
                        :max-length="255"
                        v-model="form.phone"
                        @pressEnter="formSubmit()"
                        type="tel"
                        size="large" />
                </a-form-model-item>
                <template v-if="!isDepartment">
                    <a-form-model-item
                        ref="doc_prefix"
                        :label="$t('team.prefix')"
                        prop="doc_prefix">
                        <a-input
                            :max-length="4"
                            v-model="form.doc_prefix"
                            @pressEnter="formSubmit()"
                            size="large" />
                    </a-form-model-item>
                    <a-alert
                        class="mb-4"
                        :message="$t('team.prefix_info')"
                        banner />
                </template>
            </a-form-model>
        </template>
        <template #footer>
            <a-button
                :loading="loading || formLoading"
                :disabled="formLoading"
                @click="formSubmit()"
                block
                size="large"
                type="primary">
                {{ $t('team.save') }}
            </a-button>
        </template>
        <a-modal
            class="cropper_modal"
            :closable="false"
            :visible="cropModal"
            :zIndex="99999">
            <div v-if="dataUrl" class="relative">
                <div class="action_btn absolute flex items-center">
                    <a-button icon="undo" @click="cropper.rotate(-45)" />
                    <a-button class="ml-1" @click="cropper.rotate(45)" icon="redo" />
                </div>
                <img
                    ref="avatarImg"
                    @load.stop="createCropper"
                    :src="dataUrl" />
            </div>
            <template slot="footer">
                <a-button @click="closeCropModal()">
                    {{$t('team.close')}}
                </a-button>
                <a-button type="primary" @click="uploadImage()" :loading="uploadLoading">
                    {{ $t('team.upload') }}
                </a-button>
            </template>
        </a-modal>
    </DrawerTemplate>
</template>

<script>
import {checkImageWidthHeight, hashString, getFileExtension} from '@/utils/utils'
import eventBus from '@/utils/eventBus'
import 'cropperjs/dist/cropper.css'
import Cropper from 'cropperjs'
import { mapActions, mapState } from 'vuex'
import { errorHandler } from '@/utils/index.js'
export default {
    name: "OrganizationCreateDrawer",
    components: {
        DrawerSelectUser: () => import('./Drawers/DrawerSelectUser'),
        DrawerSelectOrganization: () => import('./Drawers/DrawerSelectOrganization'),
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue'),
        HelpButton: () => import('@apps/Support/components/HelpButton.vue')
    },
    props: {
        zIndex: {
            type: Number,
            default: 1010
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        taxIDLabel() {
            return this.$t('table.inn') // this.formInfo?.tax_ID_label ?? 
        },
        formShortNameLabel() {
            return this.$t('team.short_name')
        },
        
        formFullNameLabel() {
            if(this.isDepartment)
                return this.$t('team.full_name_label_department')
            if(this.isStructure)
                return this.$t('team.full_name_label_subdivision')
            return this.$t('team.full_name_label_organization')
        },
        drawerTitle() {
            if (this.edit) {
                if(this.isDepartment)
                    return this.$t('team.edit_department')
                if(this.isStructure)
                    return this.$t('team.edit_subdivision')
                return this.$t('team.edit_organization')
            } 
            if(this.isDepartment)
                return this.$t('team.add_department')
            if(this.isStructure)
                return this.$t('team.add_subdivision')
            return this.$t('team.add_organization')
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        drawerWidth() {
            if(this.windowWidth > 600)
                return 600
            else {
                return '100%'
            }
        },
        isStructure() {
            return this.organizationType === 'subdivision'
        },
        rules() {
            const rules = {
                name_ru: [
                    {
                        required: true,
                        message: this.$t('team.required_field'),
                        trigger: 'blur'
                    }
                ],
                full_name_ru: [
                    {
                        required: true,
                        message: this.$t('team.required_field'),
                        trigger: 'blur'
                    }
                ],
            }
            if(this.isDepartment || this.isStructure) {
                rules.director = [
                    {
                        required: true,
                        message: this.$t('team.required_field'),
                        trigger: 'blur'
                    }
                ]
            } 
            if(!this.isDepartment) {
                rules.doc_prefix = [
                    {
                        max: 4,
                        message: this.$t('team.max_4_chars'),
                        trigger: 'blur'
                    },
                    {
                        required: false,
                        message: this.$t('team.required_field'),
                        trigger: 'blur'
                    },

                ]
            }
            return rules
        }
    },
    async created() {
        eventBus.$on('create_organization', async ({
            organizationType,
            organizationParent=null,
            organization=null,
            isDepartment=false
        }) => {
            this.organizationType = organizationType
            this.organizationParent = organizationParent
            this.organization = organization
            this.isDepartment = isDepartment
            if(isDepartment) {
                this.form.director = ''
            }
            if((organization?.members_count === 1) && organization.director) {
                this.form.director = organization.director
            }
            if(organizationParent) {
                const { data } = await this.$http(`/users/my_organizations/${organizationParent}/detail/`)
                this.form.contractor_parent = data
                this.isSelectOrganizationDisabled = true
            }
            this.formLoading = false
            this.visible = true

        })
        eventBus.$on('edit_organization', async ({
            organization,
            organizationParent=null,
            organizationType=null,
            isDepartment=false
        }) => {
            this.edit = true
            this.organizationType = organizationType
            // TODO: рефакторинг
            this.organizationParent = organizationParent
            this.isDepartment = isDepartment
            this.visible = true
            this.formLoading = true
            this.organization = organization
            this.form = this.mapOrganizationToForm(organization)
            this.logoUrl = organization?.logo || null
            if(this.organizationParent && !isDepartment) {
                this.organizationType = 'subdivision'
            }

            // Для редактирования всегда берем свежие данные из detail.
            let actualOrganization = organization
            try {
                const detailUrl = isDepartment
                    ? `/users/my_organizations/departments/${organization.id}/detail/`
                    : `/users/my_organizations/${organization.id}/detail/`
                const { data } = await this.$http(detailUrl)
                if(data) {
                    actualOrganization = data
                }
            } catch(error) {
                errorHandler({ error, show: false })
            }

            this.organization = actualOrganization
            this.form = this.mapOrganizationToForm(actualOrganization)
            if(this.form.contractor_parent == null && organizationParent) {
                try {
                    const { data } = await this.$http(`/users/my_organizations/${organizationParent}/detail/`)
                    this.form.contractor_parent = data
                } catch(error) {
                    errorHandler({ error, show: false })
                }
            }
            this.logoUrl = actualOrganization.logo
            this.formLoading = false
        })
    },
    data() {
        return {
            pageModel: 'catalogs.ContractorModel',
            page_name: 'catalogs.ContractorModel_list',
            isDepartment: false,
            organization: null,
            organizationType: null,
            organizationParent: null,
            userDrawer: false,
            edit: false,
            formLoading: false,
            visible: false,
            minSize: 150,
            file: null,
            cropModal: false,
            uploadLoading: false,
            logoUrl: null,
            dataUrl: null,
            formInfo: null,
            form: {
                name_ru: '',
                name_kk: '',
                full_name_ru: '',
                full_name_kk: '',
                inn: '',
                email: '',
                phone: '',
                logo: null,
                director: '',
                doc_prefix: ''
            },
            cropperOptions: {
                aspectRatio: 1 / 1
            },
            loading: false,
            isSelectOrganizationDisabled: false
        }
    },
    methods: {
        ...mapActions({
            addDepartment: 'organization/addDepartment',
            addOrganization: 'organization/addOrganization',
            addStructure: 'organization/addStructure',
            updateDepartment: 'organization/updateDepartment',
            getOrganizationActionInfo: 'organization/getOrganizationActionInfo',
        }),
        async getFormInfo() {
            await this.$http.get('catalogs/contractors/create_form_info/')
                .then(({ data }) => {
                    this.formInfo = data
                })
                .catch(error => {
                    errorHandler({error, show: false})
                })
        },
        afterVisibleChange(vis) {
            if(!vis) {
                this.form = {
                    name_ru: '',
                    name_kk: '',
                    full_name_ru: '',
                    full_name_kk: '',
                    inn: '',
                    email: '',
                    phone: '',
                    logo: null,
                    director: '',
                    doc_prefix: ''
                }
                this.organizationType = null
                this.organizationParent = null
                this.isDepartment = false
                this.edit = false
                this.isSelectOrganizationDisabled = false
                this.logoUrl = null
                this.formLoading = false
                this.closeCropModal()
            } else {
                this.getFormInfo()
            }
        },
        closeCropModal() {
            this.cropModal = false
            this.dataUrl = null
            this.file = null
        },
        uploadImage() {
            this.cropper.getCroppedCanvas().toBlob(async (avatar) => {
                try {
                    const exc = getFileExtension(this.file.name),
                        filename = `${hashString(this.file.name)}.${exc}`

                    this.uploadLoading = true
                    const data = await this.$uploadFile({
                        file: avatar,
                        url: '/common/upload/',
                        fieldName: 'upload',
                        fileName: filename
                    })
                    if(data?.length) {
                        if(this.edit) {
                            const aData = await this.$http.post(`/users/my_organizations/${this.form.id}/logo/`, {
                                logo: data[0].id
                            })
                            if(aData?.data?.id) {
                                eventBus.$emit('updateTableOrg', aData.data)
                                this.logoUrl = aData.data.logo
                            }
                        } else {
                            this.logoUrl = data[0].path
                            this.form.logo = data[0].id
                        }

                        this.closeCropModal()
                    }
                } catch(error) {
                    errorHandler({error})
                } finally {
                    this.uploadLoading = false
                }
            })
        },
        createCropper() {
            this.cropper = new Cropper(this.$refs.avatarImg, this.cropperOptions)
        },
        async handleFileChange(event) {
            const file = Object.values(event.target.files)[0]
            if(file) {
                const fileSize = await checkImageWidthHeight(file)
                if(fileSize.width > this.minSize && fileSize.height > this.minSize) {
                    let reader = new FileReader()
                    reader.onload = e => {
                        this.dataUrl = e.target.result
                    }
                    reader.readAsDataURL(file)
                    this.file = file
                    this.cropModal = true
                } else
                    this.$message.error(this.$t('team.max_file_h_w', {size: this.minSize}))
            }
        },
        onInnInput(event) {
            const rawValue = event && event.target ? event.target.value : event
            const normalized = String(rawValue || '').replace(/\D/g, '').slice(0, 12)
            if (normalized !== this.form.inn) {
                this.form.inn = normalized
            }
        },
        mapOrganizationToForm(organization) {
            const fallbackForm = {
                name_ru: '',
                name_kk: '',
                full_name_ru: '',
                full_name_kk: '',
                inn: '',
                email: '',
                phone: '',
                logo: null,
                director: '',
                doc_prefix: '',
                contractor_parent: null
            }

            const source = JSON.parse(JSON.stringify(organization || {}))
            const mapped = {
                ...fallbackForm,
                ...source
            }

            mapped.name_ru = mapped.name_ru || source.name || ''
            mapped.full_name_ru = mapped.full_name_ru || source.full_name || ''
            mapped.name_kk = mapped.name_kk || source.name_kk || ''
            mapped.full_name_kk = mapped.full_name_kk || source.full_name_kk || ''

            delete mapped.members_count
            return mapped
        },
        formSubmit() {
            this.$refs.orgForm.validate(async valid => {
                if (valid) {
                    try {
                        this.loading = true
                        const formData = JSON.parse(JSON.stringify(this.form))
                        if(formData.director) {
                            formData.director = formData.director.id
                        }
                        let data
                        if(this.edit)
                            data = await this.editOrganization(formData)
                        else
                            data = await this.createOrganization(formData)
                        if(data)
                            eventBus.$emit(`update_filter_${this.pageModel}_${this.page_name}`);
                        if(data?.contractor?.id)
                            await this.getOrganizationActionInfo({ organizationId: data.contractor.id })
                    } catch(error) {
                        errorHandler({error})
                    } finally {
                        this.loading = false
                    }
                } else
                    return false
            })
        },
        async editOrganization(formData) {
            delete formData.logo

            const payload = formData
            let updatedData = null
            if(this.isDepartment) {
                updatedData = await this.updateDepartment({
                    payload: payload,
                    departmentId: this.organization.id,
                    parentId: this.organizationParent
                })
                if(updatedData) {
                    this.visible = false
                    eventBus.$emit('updateTableOrg', {
                        ...updatedData,
                        showChildren: formData.showChildren
                    })
                    this.$message.success(this.$t('team.department_updated'))
                }

            } else {
                if(formData.contractor_parent) {
                    formData.contractor_parent = formData.contractor_parent.id
                }
                const { data } = await this.$http.put(`/users/my_organizations/${formData.id}/update/`, formData)
                if(data) {
                    updatedData = data
                    if(formData.contractor_parent) {
                        //
                        // this.$store.commit('organization/MOVE_ORGANIZATION', {
                        //     data: data,
                        //     parentId: this.organizationParent,
                        //     organizationId: this.organization.id,
                        //     fosterParentId: formData.contractor_parent.contractor_parent
                        // })
                    }
                    this.visible = false
                    eventBus.$emit('updateTableOrg', {
                        ...updatedData,
                        showChildren: formData.showChildren
                    })
                    if(!this.isDepartment) {
                        this.$store.commit('organization/UPDATE_ORGANIZATION', {
                            updatedOrganization: data,
                            organizationParentId: this.organizationParent
                        })
                        this.$message.success(this.$t('team.organization_updated'))
                    } else {
                        this.$message.success(this.$t('team.departament_updated'))
                    }
                    
                }
            }
            return updatedData

        },
        async createOrganization(formData) {
            let data
            if(this.organizationType === 'subdivision') {
                const payload = {
                    ...formData,
                    director: formData.director,
                    contractor_parent: this.organizationParent
                }
                data = this.addStructure({
                    payload: payload,
                    parentId: this.organizationParent,
                })
                if(data) {
                    this.$message.success(this.$t('team.structure_departament_created'))
                }

            } else if(this.isDepartment) {
                const payload = {
                    director: formData.director,
                    email: formData.email,
                    full_name_ru: formData.full_name_ru,
                    full_name_kk: formData.full_name_kk,
                    name_ru: formData.name_ru,
                    name_kk: formData.name_kk,
                    phone: formData.phone,
                    contractor_parent: {
                        contractor_parent: this.organizationParent,
                        relation_type: 'department'
                    }
                }
                data = this.addDepartment({
                    payload: payload,
                    key: this.organizationParent,
                })
                if(data) {
                    this.$message.success(this.$t('team.departament_created'))
                }
            } else {
                const parentId = formData?.contractor_parent?.id || null
                const payload = {
                    ...formData,
                }
                if(parentId) {
                    payload.contractor_parent = parentId
                }
                data = this.addOrganization({
                    payload,
                    parentId: parentId,
                    relationType: 'structural_division'
                })
                if(data) {
                    this.$message.success(this.$t('team.organization_created'))
                }
            }
            if(data) {
                this.visible = false
                eventBus.$emit('orgTableReload')
            }
            return data
        }
    },
    beforeDestroy() {
        eventBus.$off('create_organization')
        eventBus.$off('edit_organization')
    }
}
</script>

<style lang="scss" scoped>
.custom_border {
    border: 1px solid var(--borderColor);

}
.oc_drawer{
    &::v-deep{
        .ant-drawer-wrapper-body,
        .ant-drawer-content{
            overflow: hidden;
            padding: 0px;
        }
        .ant-drawer-header{
            padding-left: 20px;
            padding-right: 20px;
        }
        .ant-drawer-body{
            height: calc(100% - 40px);
            padding: 0px;
        }
        .drawer_body{
            height: calc(100% - 40px);
            overflow-y: auto;
            overflow-x: hidden;
            padding: 20px;
        }
        .drawer_footer{
            display: flex;
            align-items: center;
            height: 40px;
            border-top: 1px solid #e8e8e8;
            padding-left: 20px;
            padding-right: 20px;
        }
    }
}
</style>
