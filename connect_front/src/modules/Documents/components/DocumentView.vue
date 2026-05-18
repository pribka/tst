<template>
    <a-drawer
        title=""
        :visible="visible"
        class="dv_drawer"
        @close="visible = false"
        destroyOnClose
        :width="drawerWidth"
        :afterVisibleChange="afterVisibleChange"
        placement="right">
        <div ref="drawerHeader" class="drawer_header flex items-center justify-between truncate">
            <div v-if="document" class="text-base font-semibold truncate label">
                {{ document.name }}
            </div>
            <a-skeleton
                v-else
                active
                :paragraph="{ rows: 1 }" />
            <div class="flex items-center pl-4">
                <template v-if="actions && document">
                    <a-button 
                        v-if="actions.send && actions.send.availability" 
                        type="success" 
                        ghost 
                        class="mr-2"
                        :loading="signLoading"
                        @click="documentSign()">
                        Отправить на подпись
                    </a-button>
                    <a-tag v-if="document && document.locked" class="mr-3">
                        <i class="fi fi-rr-lock"></i>
                    </a-tag>
                    <a-dropdown 
                        :getPopupContainer="getPopupContainer" 
                        :trigger="['click']">
                        <a-button 
                            type="ui" 
                            ghost 
                            shape="circle"
                            :loading="actionLoading"
                            icon="fi-rr-menu-dots-vertical" 
                            flaticon />
                        <a-menu slot="overlay">
                            <a-menu-item 
                                v-if="!actionLoading"
                                key="copy"
                                class="flex items-center"
                                @click="copyDocument()">
                                <i class="fi fi-rr-copy-alt mr-2"></i>
                                Скопировать
                            </a-menu-item>
                            <a-menu-item 
                                v-if="actions.edit && actions.edit.availability && !document.locked" 
                                key="edit"
                                class="flex items-center"
                                @click="editHandler()">
                                <i class="fi fi-rr-edit mr-2"></i>
                                Редактировать
                            </a-menu-item>
                            <a-menu-item 
                                v-if="document.doc_file && document.doc_file.path" 
                                key="download"
                                class="flex items-center"
                                @click="documentDownload()">
                                <i class="fi fi-rr-file-upload mr-2"></i>
                                Скачать документ
                            </a-menu-item>
                            <template v-if="actions.delete && actions.delete.availability && !document.locked">
                                <a-menu-divider />
                                <a-menu-item 
                                    key="delete" 
                                    class="text-red-500 flex items-center" 
                                    @click="deleteHanlder()">
                                    <i class="fi fi-rr-trash mr-2"></i> Удалить
                                </a-menu-item>
                            </template>
                        </a-menu>
                    </a-dropdown>
                </template>
                <a-button
                    type="ui"
                    ghost
                    shape="circle"
                    class="ml-2 text-current"
                    icon="close"
                    @click="visible = false" />
            </div>
        </div>
        <div class="drawer_body doc_body">
            <div 
                class="grid" 
                :class="showAside ? 'md:grid-cols-[1fr,300px] lg:grid-cols-[1fr,400px]' : 'grid-cols-[1fr]'"
                style="min-height: 100%;">
                <div class="document_html" style="min-height: 100%;">

                    <div class="d_f_actions" :class="!showAside && 'hide_aside'">
                        <div class="d_f_actions__sticky">
                            <a-button 
                                :icon="showAside ? 'fi-rr-arrow-alt-to-right' : 'fi-rr-arrow-alt-to-left'" 
                                flaticon 
                                shape="circle"
                                @click="showAside = !showAside" />
                            <a-button 
                                v-if="document && document.doc_file && document.doc_file.path" 
                                icon="fi-rr-file-upload" 
                                v-tippy="{ inertia : true}"
                                content="Скачать документ"
                                flaticon 
                                shape="circle"
                                @click="documentDownload()" />
                        </div>
                    </div>
                    <!--<div v-if="actions && actions.edit" class="mb-2 flex items-center">
                        <a-switch 
                            :checked="editorVisible" 
                            @change="onChangeSwitch" />
                        <span 
                            class="ml-2 cursor-pointer" 
                            @click="onChangeSwitchLabel()">
                            Редактор
                        </span>
                    </div>-->
                    <template v-if="document">
                        <TextViewer
                            v-if="document.content"
                            class="body_text" 
                            :body="document.content" />
                        <div v-else class="body_text">
                            <a-empty class="mt-5">
                                <template slot="description">
                                    <p class="mb-4">Шаблон отсутствует</p>
                                    <a-button 
                                        v-if="document.doc_file && document.doc_file.path" 
                                        type="primary" 
                                        icon="fi-rr-file-upload"
                                        class="px-7" 
                                        flaticon
                                        @click="documentDownload()">
                                        Скачать файл
                                    </a-button>
                                </template>
                            </a-empty>
                        </div>
                    </template>
                    <div v-else class="body_text">
                        <a-skeleton
                            active
                            :paragraph="{ rows: 5 }" />
                    </div>
                </div>
                <div v-if="showAside" class="aside_info">
                    <template v-if="document">
                        <div>
                            <div class="item">
                                <div class="label">
                                    Статус:
                                </div>
                                <div class="value">
                                    <a-tag :color="document.approval_status.color || ''">
                                        {{ document.approval_status.name }}
                                    </a-tag>
                                </div>
                            </div>
                            <div class="item">
                                <div class="label">
                                    Статус отправки:
                                </div>
                                <div class="value">
                                    <a-tag :color="document.delivery_status.color || ''">
                                        {{ document.delivery_status.name }}
                                    </a-tag>
                                </div>
                            </div>
                            <div class="item">
                                <div class="value">
                                    <Profiler 
                                        :user="document.author" 
                                        initStatus
                                        :getPopupContainer="getPopupContainer"
                                        :subtitle="{ text: 'Автор', class: 'text-xs gray' }" />
                                </div>
                            </div>
                            <div v-if="document.members && document.members.length" class="item">
                                <div 
                                    v-for="us in document.members" 
                                    :key="us.id"
                                    class="item__mem">
                                    <Profiler 
                                        :user="us" 
                                        initStatus
                                        :getPopupContainer="getPopupContainer"
                                        :subtitle="{ text: 'Наблюдатель', class: 'text-xs gray' }" />
                                </div>
                            </div>
                            <div class="item">
                                <div class="label">
                                    Организация:
                                </div>
                                <div class="value">
                                    <div class="flex items-center truncate">
                                        <div :key="document.contractor.logo" class="pr-2">
                                            <a-avatar 
                                                :size="30"
                                                :src="document.contractor.logo"
                                                icon="fi-rr-users-alt" 
                                                flaticon />
                                        </div>
                                        <span class="truncate">{{ document.contractor.name }}</span>
                                    </div>
                                </div>
                            </div>
                            <div class="item">
                                <div class="label">
                                    Контрагент:
                                </div>
                                <div class="value">
                                    {{ document.customer.name }}
                                </div>
                            </div>
                            <div v-if="document.template" class="item">
                                <div class="label">
                                    Шаблон:
                                </div>
                                <div class="value">
                                    {{ document.template.name }}
                                </div>
                            </div>
                            <div v-if="document.template && document.template.doc_type" class="item">
                                <div class="label">
                                    Тип документа:
                                </div>
                                <div class="value">
                                    {{ document.template.doc_type.name }}
                                </div>
                            </div>
                            <div class="item">
                                <div class="label">
                                    Дата создания:
                                </div>
                                <div class="value">
                                    {{ $moment(document.created_at).format('DD.MM.YYYY') }}
                                </div>
                            </div>
                        </div>
                        <div class="mt-5">
                            <div class="mb-1 font-semibold">
                                Комментарии
                            </div>
                            <vue2CommentsComponent
                                bodySelector=".doc_body"
                                :related_object="document.id"
                                model="document" />
                        </div>
                    </template>
                    <a-skeleton
                        v-else
                        active
                        :paragraph="{ rows: 2 }" />
                </div>
            </div>
        </div>
    </a-drawer>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    components: {
        TextViewer: () => import('@apps/CKEditor/TextViewer.vue'),
        vue2CommentsComponent: () => import('@apps/vue2CommentsComponent')
    },
    computed: {
        windowWidth() {
            return this.$store.state.windowWidth
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        drawerWidth() {
            if(this.windowWidth > 1600)
                return 1600
            else {
                return '100%'
            }
        },
        ckEditor() {
            if(this.editorVisible)
                return () => import('@apps/CKEditor/DocumentEditor.vue')
            else
                return null
        }
    },
    data() {
        return {
            visible: false,
            document: null,
            loading: false,
            actionLoading: false,
            actions: null,
            editorVisible: false,
            showAside: true,
            signLoading: false
        }
    },
    watch: {
        '$route.query'(val) {
            if(val.document) {
                this.visible = true
            }
        },
    },
    created() {
        eventBus.$on('open_document', () => {
            this.visible = true
        })

        if(this.$route.query.document)
            this.visible = true
    },
    methods: {
        copyDocument() {
            this.visible = false
            eventBus.$emit('copy_document', this.document)
        },
        async documentSign() {
            try {
                this.signLoading = true
                const { data } = await this.$http.post(`/contractor_docs/${this.document.id}/send/ `)
                if(data) {
                    this.$message.success('Документ успешно отправлен на подпись')
                    //if(this.actions?.send?.availability)
                    // delete this.actions.send
                    this.$set(this.document, 'delivery_status', data.delivery_status)
                    this.$set(this.document, 'locked', data.locked)
                    eventBus.$emit('update_doc_list', data)
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.signLoading = false
            }
        },
        documentDownload() {
            window.open(this.document.doc_file.path, 'Download')
            /*this.$nextTick(() => {
                this.$refs.downloadModal.openModal(this.document)
            })*/
        },
        onChangeSwitch(e) {
            this.editorVisible = e
        },
        onChangeSwitchLabel() {
            this.editorVisible = !this.editorVisible
        },
        editHandler() {
            this.visible = false
            eventBus.$emit('edit_document', this.document, true)
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
                            id: this.document.id,
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
        getPopupContainer() {
            return this.$refs.drawerHeader
        },
        afterVisibleChange(vis) {
            if(vis) {
                this.getDocument()
                this.getActions()
            } else {
                const query = Object.assign({}, this.$route.query)
                if(query.document) {
                    delete query.document
                    this.$router.push({query})
                }
                this.document = null
                this.actions = null
            }
        },
        async getDocument() {
            try {
                this.loading = true
                const query = Object.assign({}, this.$route.query)
                const { data } = await this.$http.get(`/contractor_docs/${query.document}/`)
                if(data) {
                    this.document = data
                }
            } catch(error) {
                if(error && error.detail) {
                    if(error.detail === 'Не найдено.' || error.detail === 'Страница не найдена.' || error.detail === 'У вас недостаточно прав для выполнения данного действия.') {
                        this.$message.warning('Документ не найден или удален')
                    } else {
                        this.$message.error('Ошибка')
                    }
                } else {
                    this.$message.error('Ошибка')
                }
                console.log(error)
                this.visible = false
            } finally {
                this.loading = false
            }
        },
        async getActions() {
            try {
                this.actionLoading = true
                const query = Object.assign({}, this.$route.query)
                const { data } = await this.$http.get(`/contractor_docs/${query.document}/action_info/`)
                if(data?.actions) {
                    this.actions = data.actions
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.actionLoading = false
            }
        }
    },
    beforeDestroy() {
        eventBus.$off('open_document')
    }
}
</script>

<style lang="scss" scoped>
.dv_drawer{
    &::v-deep{
        .ant-drawer-header-no-title{
            display: none;
        }
        .ant-drawer-wrapper-body,
        .ant-drawer-content{
            overflow: hidden;
        }
        .ant-drawer-body{
            padding: 0px;
            height: 100%;
        }
    }
    .drawer_body{
        height: calc(100% - 40px);
        overflow-y: auto;
        &::v-deep{
            .ant-col{
                min-height: 100%;
            }
            .ant-row{
                min-height: 100%;
            }
        }
        .aside_info{
            padding: 20px;
            .item{
                &:not(:last-child){
                    border-bottom: 1px solid var(--borderColor);
                    padding-bottom: 15px;
                }
                &:not(:first-child){
                    padding-top: 15px;
                }
                .label{
                    margin-bottom: 0.25rem;
                    font-size: 0.875rem;
                    line-height: 1.25rem;
                    font-weight: 600;
                }
                &__mem{
                    &:not(:last-child){
                        margin-bottom: 6px;
                    }
                }
            }
        }
        .document_html{
            background: #e3e8ec;
            padding: 20px 30px;
            min-height: 100%;
            position: relative;
            .d_f_actions{
                position: absolute;
                top: 20px;
                right: 0;
                margin-right: -16px;
                z-index: 5;
                bottom: 0px;
                &.hide_aside{
                    margin-right: 16px;
                }
                &__sticky{
                    position: sticky;
                    top: 20px;
                    left: 0;
                    display: flex;
                    flex-direction: column;
                    &::v-deep{
                        .ant-btn{
                            margin-bottom: 10px;
                        }
                    }
                }
            }
            .body_text{
                background: #ffffff;
                padding: 20px;
                border: 1px hsl( 0,0%,82.7% ) solid;
                border-radius: var(--borderRadius);
                box-shadow: 0 0 5px hsla( 0,0%,0%,.1 );
                min-height: 100%;
                &::v-deep{
                    figure{
                        &.table{
                            margin: 0.9em auto;
                            display: table;
                        }
                    }
                }
            }
        }
    }
    .drawer_header{
        border-bottom: 1px solid var(--border2);
        height: 40px;
        padding: 0 15px;
        &::v-deep{
            .ant-skeleton-paragraph{
                display: none;
            }
            .ant-skeleton-content{
                .ant-skeleton-title{
                    width: 90%!important;
                    margin: 0px;
                    height: 20px;
                }
            }
        }
    }
}
</style>