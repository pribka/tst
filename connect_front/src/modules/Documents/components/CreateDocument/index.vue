<template>
    <a-drawer
        :title="edit ? 'Редактировать документ' : 'Добавить документ'"
        :visible="visible"
        class="de_drawer"
        @close="visible = false"
        destroyOnClose
        :zIndex="zIndex"
        :width="drawerWidth"
        :afterVisibleChange="afterVisibleChange"
        placement="right">
        <div class="drawer_body" ref="docAddBody">
            <a-spin :spinning="docLoading">
                <a-form-model
                    ref="docForm"
                    :model="form"
                    :rules="rules">
                    <a-form-model-item ref="name" label="Название" prop="name" class="w-full">
                        <a-input v-model="form.name" size="large" />
                    </a-form-model-item>
                    <div class="grid gap-2 grid-cols-3">
                        <a-form-model-item ref="contractor" label="Организация" prop="contractor" class="w-full">
                            <OrganizationDrawer v-model="form.contractor" :getTemplate="getTemplate" />
                        </a-form-model-item>
                        <a-form-model-item ref="customer" label="Контрагент" prop="customer" class="w-full">
                            <ClientDrawer v-model="form.customer" :getTemplate="getTemplate" />
                        </a-form-model-item>

                        <a-form-model-item v-if="!customFile" ref="template" label="Шаблон" prop="template" class="w-full">
                            <TemplateDrawer v-model="form.template" :getTemplate="getTemplate" />
                        </a-form-model-item>
                        <a-form-model-item v-else ref="template" label="Шаблон" prop="template" class="w-full">
                            <div class="flex items-center ant-input ant-input-lg truncate ant-input-disabled" disabled="disabled">
                                <a-icon type="plus" /> <span class="ml-2">Выбрать</span>
                            </div>
                        </a-form-model-item>
                    </div>
                    <a-form-model-item ref="doc_file" label="Загрузить документ" prop="doc_file" class="w-full">
                        <div class="flex items-center">
                            <label for="doc_file_upload" class="ant-input ant-input-lg flex items-center truncate cursor-pointer">
                                <template v-if="form.doc_file && customFile">
                                    {{ form.doc_file.name }}.{{ form.doc_file.extension }}
                                </template>
                                <template v-else>
                                    <a-spin :spinning="fileLoading" size="small">
                                        <div class="flex items-center blue_color">
                                            <i class="fi fi-rr-cloud-upload-alt"></i>
                                            <span class="ml-2">Выбрать файл</span>
                                        </div>
                                    </a-spin>
                                </template>
                            </label>
                            <a-button v-if="form.doc_file" type="ui" size="large" class="ml-1" ghost flaticon icon="fi-rr-trash" @click="clearFile()" />
                        </div>
                        <input
                            type="file"
                            id="doc_file_upload"
                            style="display:none;"
                            ref="doc_file_upload"
                            v-on:change="handleFileChange"
                            accept=".docx, .odt, .doc, .pdf, .xml" />
                    </a-form-model-item>
                    <a-form-model-item ref="members" label="Наблюдатели" prop="members" class="w-full">
                        <UserDrawer
                            v-model="form.members"
                            inputSize="large"
                            multiple
                            class="w-full"
                            title="Выбрать участников" />
                    </a-form-model-item>
                    <a-form-model-item v-if="!customFile" ref="content" label="Редактор шаблона" prop="content">
                        <a-spin :spinning="loadingCKTemplate">
                            <component
                                :is="ckEditor"
                                :key="edit || visible"
                                v-model="form.content" />
                        </a-spin>
                    </a-form-model-item>
                </a-form-model>
            </a-spin>
        </div>
        <div class="drawer_footer">
            <a-spin :spinning="docLoading">
                <a-button 
                    type="primary"
                    :loading="loading"
                    @click="formSubmit()">
                    Сохранить
                </a-button>
                <a-button 
                    v-if="edit && actions && actions.delete && actions.delete.availability"
                    type="ui"
                    class="ml-2"
                    :loading="delLoading"
                    @click="deleteHanlder()">
                    Удалить
                </a-button>
            </a-spin>
        </div>
    </a-drawer>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    components: {
        OrganizationDrawer: () => import('./OrganizationDrawer.vue'),
        ClientDrawer: () => import('./ClientDrawer.vue'),
        TemplateDrawer: () => import('./TemplateDrawer.vue'),
        UserDrawer: () => import('./UserDrawer')
    },
    props: {
        zIndex: {
            type: Number,
            default: 1000
        }
    },
    computed: {
        windowWidth() {
            return this.$store.state.windowWidth
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        drawerWidth() {
            if(this.windowWidth > 1200)
                return 1200
            else {
                return '100%'
            }
        },
        ckEditor() {
            if(this.visible)
                return () => import('@apps/CKEditor/DocumentEditor.vue')
            else
                return null
        }
    },
    data() {
        return {
            edit: false,
            visible: false,
            customFile: false,
            fileLoading: false,
            docLoading: false,
            delLoading: false,
            loading: false,
            viewEdit: false,
            templateLoading: false,
            loadingCKTemplate: false,
            actions: null,
            templates: [],
            form: {
                name: '',
                contractor: null,
                customer: null,
                content: "",
                template: null,
                members: [],
                doc_file: null
            },
            rules: {
                name: [
                    { required: true, message: 'Обязательно для заполнения', trigger: 'blur' },
                    { max: 255, message: 'Максимум 255 символов', trigger: 'blur' }
                ],
                contractor: [
                    { required: true, message: 'Обязательно для заполнения', trigger: 'blur' }
                ],
                customer: [
                    { required: true, message: 'Обязательно для заполнения', trigger: 'blur' }
                ],
                template: [
                    { required: true, message: 'Обязательно для заполнения', trigger: 'blur' }
                ],
                content: [
                    { required: true, message: 'Обязательно для заполнения', trigger: 'blur' }
                ]
            }
        }
    },
    created() {
        eventBus.$on('create_document', () => {
            this.visible = true
        })
        eventBus.$on('edit_document', (document, view = false) => {
            this.edit = true
            this.viewEdit = view
            this.getDocument(document.id)
            this.visible = true
        })
        eventBus.$on('copy_document', (document) => {
            const cDocument = JSON.parse(JSON.stringify(document))
            delete cDocument.customer
            delete cDocument.contractor
            delete cDocument.members
            delete cDocument.author
            delete cDocument.created_at
            delete cDocument.approval_status
            delete cDocument.delivery_status
            delete cDocument.doc_file
            cDocument.content = ''
            this.copyDocument(cDocument)
            this.visible = true
        })
    },
    methods: {
        clearFile() {
            this.form.doc_file = null
            this.customFile = false
            this.rules.template = [
                { required: true, message: 'Обязательно для заполнения', trigger: 'blur' }
            ]
            this.rules.content = [
                { required: true, message: 'Обязательно для заполнения', trigger: 'blur' }
            ]
        },
        async handleFileChange(event) {
            const file = Object.values(event.target.files)[0]
            if(file) {
                try {
                    this.fileLoading = true
                    const data = await this.$uploadFile({
                        file,
                        url: '/common/upload/',
                        fieldName: 'upload',
                        fileName: file.name
                    })
                    if(data?.length) {
                        this.form.doc_file = data[0]
                        this.customFile = true
                        delete this.rules.template
                        delete this.rules.content
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.fileLoading = false
                }
            }
        },
        deleteHanlder() {
            this.$confirm({
                title: 'Вы действительно хотите удалить документ?',
                content: '',
                okText: 'Удалить',
                okType: 'danger',
                zIndex: 2000,
                closable: true,
                maskClosable: true,
                cancelText: 'Закрыть',
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post('/table_actions/update_is_active/', {
                            id: this.form.id,
                            is_active: false
                        })
                            .then(() => {
                                this.$message.success('Документ удален')
                                eventBus.$emit('docTableReload')
                                this.visible = false
                                resolve()
                            })
                            .catch(e => {
                                console.log(e)
                                reject(e)
                            })
                    })
                }
            })
        },
        copyDocument(document) {
            this.form = {
                ...this.form,
                ...document
            }
        },
        async getDocument(id) {
            try {
                this.docLoading = true
                const { data } = await this.$http.get(`/contractor_docs/${id}/`)
                if(data) {
                    const formData = data
                    this.form = formData
                    this.getActions(id)
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.docLoading = false
            }
        },
        async getActions(id) {
            try {
                const { data } = await this.$http.get(`/contractor_docs/${id}/action_info/`)
                if(data?.actions) {
                    this.actions = data.actions
                }
            } catch(e) {
                console.log(e)
            }
        },
        async getTemplate() {
            if(this.form.contractor && this.form.customer && this.form.template) {
                try {
                    this.loadingCKTemplate = true
                    const { data } = await this.$http.post('/contractor_docs/content/', {
                        template: this.form.template.id,
                        contractor: this.form.contractor.id,
                        customer: this.form.customer.id
                    })
                    if(data?.content) {
                        this.form.content = data.content
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.loadingCKTemplate = false
                }
            }
        },
        getPopupContainer() {
            return this.$refs.docAddBody
        },
        afterVisibleChange(vis) {
            if(!vis) {
                if(this.viewEdit) {
                    const { id } = this.form
                    let query = Object.assign({}, this.$route.query)
                    if(query.document && Number(query.document) !== id || !query.document) {
                        query.document = id
                        this.$router.push({query})
                    }
                }

                this.actions = null
                this.form = {
                    name: '',
                    contractor: null,
                    customer: null,
                    content: "",
                    template: null,
                    members: [],
                    doc_file: null
                }
                this.edit = false
                this.customFile = false
                this.viewEdit = false
            }
        },
        formSubmit() {
            this.$refs.docForm.validate(async valid => {
                if (valid) {
                    try {
                        this.loading = true
                        const formData = JSON.parse(JSON.stringify(this.form))

                        if(formData.contractor) {
                            formData.contractor = formData.contractor.id
                        }
                        if(formData.customer) {
                            formData.customer = formData.customer.id
                        }
                        if(formData.template) {
                            formData.template = formData.template.id
                        }
                        if(formData.created_at) {
                            delete formData.created_at
                        }
                        if(formData.author) {
                            delete formData.author
                        }

                        if(formData.members.length) {
                            formData.members = formData.members.map(us => {
                                return us.id
                            })
                        }

                        if(this.customFile && formData.doc_file?.id) {
                            formData.doc_file = formData.doc_file.id
                            formData.template = null
                            formData.content = ''
                        }

                        if(this.edit) {
                            const { data } = await this.$http.put(`/contractor_docs/${formData.id}/`, formData)
                            if(data) {
                                this.visible = false
                                eventBus.$emit('docTableReload')
                                this.$message.info('Документ обновлен')

                                let query = Object.assign({}, this.$route.query)
                                if(query.document && Number(query.document) !== id || !query.document) {
                                    query.document = this.form.id
                                    this.$router.push({query})
                                }
                            }
                        } else {
                            const { data } = await this.$http.post('/contractor_docs/', formData)
                            if(data) {
                                this.visible = false
                                eventBus.$emit('docTableReload')
                                this.$message.info('Документ создан')
                            }
                        }
                    } catch(e) {
                        console.log(e)
                        this.$message.error('Ошибка')
                    } finally {
                        this.loading = false
                    }
                } else
                    return false
            })
        }
    },
    beforeDestroy() {
        eventBus.$off('create_document')
        eventBus.$off('edit_document')
        eventBus.$off('copy_document')
    }
}
</script>

<style lang="scss" scoped>
.de_drawer{
    &::v-deep{
        .temp_sel{
            .ant-select-dropdown-menu-item{
                white-space: initial;
                overflow: initial;
                text-overflow: initial;
            }
        }
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
            .ck-editor{
                &.ck-rounded-corners{
                    .ck{
                        &.ck-editor__top{
                            position: sticky;
                            top: 0px;
                            left: 0;
                            z-index: 10;
                            .ck-sticky-panel{
                                .ck-sticky-panel__placeholder{
                                    display: none!important;
                                }
                                .ck-sticky-panel__content_sticky{
                                    position: initial!important;
                                    width: 100%!important;
                                    box-shadow: initial;
                                }
                                .ck-toolbar{
                                    border-radius: var(--ck-border-radius);
                                    border-bottom-left-radius: var(--ck-border-radius);
                                    border-bottom-right-radius: var(--ck-border-radius);
                                    border-bottom-width: 1px;
                                    background: #ffffff;
                                }
                            }
                        }
                    }
                }
            }
            .ck-content{
                min-height: 400px;
                &.ck-editor__editable{
                    border: 0px;
                    box-shadow: initial;
                    padding-left: 0px;
                    padding-right: 0px;
                }
            }
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
