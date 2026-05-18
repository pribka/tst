<template>
    <DrawerTemplate
        v-model="visible"
        :title="edit ? $t('support.editArticle') : $t('support.addArticle')"
        :width="isMobile ? '100%' : 1000"
        @afterVisibleChange="afterVisibleChange"
        @close="visible = false">
        <a-form-model ref="ruleForm" :model="form" :rules="rules">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-x-4">
                <a-form-model-item ref="name_ru" class="mb-2" :label="$t('support.nameRu')" prop="name_ru">
                    <a-input v-model="form.name_ru" size="large" />
                </a-form-model-item>
                <a-form-model-item ref="name_kk" class="mb-2" :label="$t('support.nameKk')" prop="name_kk">
                    <a-input v-model="form.name_kk" size="large" />
                </a-form-model-item>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-x-4">
                <a-form-model-item ref="contractor" :label="$t('support.organization')" prop="contractor" class="mb-2">
                    <WikiOrgSelect v-model="form.contractor" @change="handleContractorChange" />
                </a-form-model-item>
                <a-form-model-item ref="chapter" :label="$t('support.subsection')" prop="chapter" class="mb-2">
                    <a-spin class="w-full" size="small" :spinning="!selectedContractorId">
                        <WikiSubsectionSelect
                            v-model="form.chapter"
                            :selectItem="selectSections"
                            :contractorId="selectedContractorId"
                            :disabled="!selectedContractorId" />
                    </a-spin>
                </a-form-model-item>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-x-4">
                <a-form-model-item ref="sort" :label="$t('support.position')" prop="sort" class="mb-4">
                    <a-input-number v-model="form.sort" style="width: 100%;" size="large" :min="0" :max="100000" />
                </a-form-model-item>
            </div>
            <!--<a-form-model-item ref="code" :label="$t('support.code')" prop="code">
                <a-input v-model="form.code" size="large" />
            </a-form-model-item>-->
            <a-form-model-item ref="random_html_ru" prop="random_html_ru">
                <a-tabs>
                    <a-tab-pane :tab="$t('support.descriptionRuTab')" key="ru">
                        <div class="editor_wrap">
                            <component :is="ckEditor" :key="`ru_${editorRenderKey}`" v-model="form.random_html_ru" />
                        </div>
                    </a-tab-pane>
                    <a-tab-pane :tab="$t('support.descriptionKkTab')" key="kk">
                        <div class="editor_wrap">
                            <component :is="ckEditor" :key="`kk_${editorRenderKey}`" v-model="form.random_html_kk" />
                        </div>
                    </a-tab-pane>
                </a-tabs>
            </a-form-model-item>
        </a-form-model>
        <template #footer>
            <a-button type="primary" size="large" :block="isMobile" :loading="loading" @click="onSubmit()">
                {{ $t('save') }}
            </a-button>
            <!--<a-button v-if="edit && canDelete" :block="isMobile" type="flat_danger" size="large" class="ml-2" :loading="dangerLoading" @click="deleteHandler()">
                {{ $t('remove') }}
            </a-button>-->
        </template>
    </DrawerTemplate>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'

const getForm = () => ({
    name_ru: '',
    name_kk: '',
    random_html_ru: '',
    random_html_kk: '',
    contractor: null,
    use_in_wiki: true,
    sort: 500,
    code: '',
    chapter: null
})

export default {
    components: {
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue'),
        WikiSubsectionSelect: () => import('./WikiSubsectionSelect.vue'),
        WikiOrgSelect: () => import('./WikiOrgSelect.vue')
    },
    props: {
        fUpdChapterList: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        canDelete() {
            return this.$store.getters['supportWiki/canDelete']
        },
        ckEditor() {
            return this.visible ? () => import('@apps/CKEditor') : null
        },
        selectedContractorId() {
            return this.form?.contractor?.id || null
        }
    },
    data() {
        return {
            visible: false,
            loading: false,
            edit: false,
            editorRenderKey: 0,
            dangerLoading: false,
            form: getForm(),
            rules: {
                name_ru: [
                    { required: true, message: this.$t('field_required'), trigger: 'blur' }
                ],
                random_html: [
                    { required: true, message: this.$t('field_required'), trigger: 'blur' }
                ],
                chapter: [
                    { required: true, message: this.$t('field_required'), trigger: 'blur' }
                ],
                contractor: [
                    { required: true, message: this.$t('field_required'), trigger: 'blur' }
                ]
            }
        }
    },
    methods: {
        selectSections() {},
        handleContractorChange() {
            this.form.chapter = null
        },
        afterVisibleChange(vis) {
            if(!vis) {
                this.edit = false
                this.form = getForm()
                this.editorRenderKey += 1
            }
        },
        async deleteHandler() {
            this.$confirm({
                title: this.$t('support.removeArticleConfirm'),
                content: '',
                okText: this.$t('remove'),
                okType: 'danger',
                closable: true,
                maskClosable: true,
                cancelText: this.$t('cancel'),
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.dangerLoading = true
                        this.$http.post('/table_actions/update_is_active/', [{ id: this.form.id, is_active: false }])
                            .then(() => {
                                this.$message.success(this.$t('support.articleDeleted'))
                                this.visible = false
                                this.fUpdChapterList()
                                this.$router.push({ name: 'company-wiki', query: this.$route.query })
                                resolve()
                            })
                            .catch(error => {
                                errorHandler({ error })
                                reject(error)
                            })
                            .finally(() => {
                                this.dangerLoading = false
                            })
                    })
                }
            })
        },
        onSubmit() {
            this.$refs.ruleForm.validate(async valid => {
                if (!valid) return false

                const formData = {...this.form}
                if(formData.chapter?.id) {
                    formData.chapter = [formData.chapter.id]
                }
                if(formData.contractor)
                    delete formData.contractor
                if(formData.chapters?.length)
                    delete formData.chapters

                try {
                    this.loading = true
                    const { data } = this.edit
                        ? await this.$http.put(`/wiki/pages/${formData.id}/`, formData)
                        : await this.$http.post('/wiki/pages/', formData)

                    if(data) {
                        this.visible = false
                        this.fUpdChapterList()
                        this.$message.info(this.edit ? this.$t('support.articleUpdated') : this.$t('support.articleCreated'))
                    }
                } catch(error) {
                    errorHandler({ error })
                } finally {
                    this.loading = false
                }
            })
        },
        openDrawer(value = null) {
            if(value) {
                this.edit = true
                this.$http.get(`wiki/pages/${value.id}/form/`)
                    .then(({ data }) => {
                        const selectedChapter = Array.isArray(data.chapter) ? data.chapter[0] : data.chapter
                        data.chapter = selectedChapter || null
                        data.contractor = selectedChapter?.contractor || null
                        this.form = data
                        this.editorRenderKey += 1
                    })
                    .catch(error => errorHandler({ error, show: false }))
            } else {
                this.form = getForm()
                this.editorRenderKey += 1
            }
            this.visible = true
        }
    },
    mounted() {
        eventBus.$on('open_support_page_page_drawer', this.openDrawer)
    },
    beforeDestroy() {
        eventBus.$off('open_support_page_page_drawer', this.openDrawer)
    }
}
</script>

<style lang="scss" scoped>
.editor_wrap{
    &::v-deep{
        .ck-editor__editable_inline{
            min-height: 300px;
            @media (max-width: 767px) {
                min-height: 150px;
            }
        }
    }
}
</style>
