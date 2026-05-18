<template>
    <DrawerTemplate
        v-model="visible"
        :title="edit ? $t('support.editSubsection') : $t('support.addSubsection')"
        :width="isMobile ? '100%' : 1000"
        @afterVisibleChange="afterVisibleChange"
        @close="visible = false">
        <a-form-model
            ref="ruleForm"
            :model="form"
            :rules="rules">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-x-4">
                <a-form-model-item
                    ref="name_ru"
                    :label="$t('support.nameRu')"
                    prop="name_ru"
                    class="mb-2">
                    <a-input v-model="form.name_ru" size="large" />
                </a-form-model-item>
                <a-form-model-item
                    ref="name_kk"
                    :label="$t('support.nameKk')"
                    prop="name_kk"
                    class="mb-2">
                    <a-input v-model="form.name_kk" size="large" />
                </a-form-model-item>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-x-4">
                <a-form-model-item
                    ref="section"
                    :label="$t('support.category')"
                    prop="section"
                    class="mb-2">
                    <div class="ant-input ant-input-lg cursor-pointer" @click="showSection = true">
                        <a-tag v-if="form.section && form.section.name" color="blue">
                            {{ form.section.name }}
                        </a-tag>
                    </div>
                    <SectionSelectDrawer
                        v-model="form.section"
                        :taskDrawer="showSection"
                        :selectParentTask="selectSections"
                        :closeHandler="closeSections" />
                </a-form-model-item>
                <a-form-model-item
                    ref="sort"
                    :label="$t('support.position')"
                    prop="sort"
                    class="mb-2">
                    <a-input-number v-model="form.sort" style="width: 100%;" size="large" :min="0" :max="100000" />
                </a-form-model-item>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-x-4 mb-2">
                <a-form-model-item
                    ref="show_on_main_page"
                    :label="$t('support.showOnMainPage')"
                    prop="show_on_main_page"
                    class="mb-2">
                    <a-switch v-model="form.show_on_main_page" />
                </a-form-model-item>
            </div>
            <a-form-model-item 
                ref="code" 
                label="Код" 
                prop="code">
                <a-input v-model="form.code" size="large" />
            </a-form-model-item>
            <a-form-model-item
                ref="random_html_ru"
                prop="random_html_ru">
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
            <template v-if="edit">
                <a-button type="danger" size="large" class="ml-2" :block="isMobile" :loading="dangerLoading" @click="deleteHandler()">
                    {{ $t('remove') }}
                </a-button>
            </template>
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
    use_in_wiki: true,
    show_on_main_page: true,
    sort: 500,
    code: '',
    section: null
})

export default {
    props: {
        fUpdChapterList: {
            type: Function,
            default: () => {}
        }
    },
    components: {
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue'),
        SectionSelectDrawer: () => import('./SectionSelectDrawer.vue')
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        ckEditor() {
            if(this.visible)
                return () => import('@apps/CKEditor')
            else
                return null
        }
    },
    data() {
        return {
            visible: false,
            loading: false,
            edit: false,
            editorRenderKey: 0,
            showSection: false,
            dangerLoading: false,
            form: getForm(),
            rules: {
                name: [
                    { required: true, message: this.$t('field_required'), trigger: 'blur' }
                ],
                random_html: [
                    { required: true, message: this.$t('field_required'), trigger: 'blur' }
                ],
                section: [
                    { required: true, message: this.$t('field_required'), trigger: 'blur' }
                ]
            }
        }
    },
    methods: {
        selectSections() {

        },
        closeSections() {
            this.showSection = false
        },
        afterVisibleChange(vis) {
            if(!vis) {
                this.edit = false
                this.form = getForm()
                this.editorRenderKey += 1
            }
        },
        async deleteHandler() {
            try {
                this.dangerLoading = true
                await this.$http.delete(`/wiki/chapters/${this.form.id}/`)
                this.visible = false
                this.fUpdChapterList()
                this.$message.info('Глава удалена')
            } catch(error) {
                errorHandler({ error })
            } finally {
                this.dangerLoading = false
            }
        },
        onSubmit() {
            this.$refs.ruleForm.validate(async valid => {
                if (valid) {
                    const formData = {...this.form}
                    if(formData.section?.id) {
                        formData.section = [formData.section.id]
                    }
                    if(formData.sections?.length)
                        delete formData.sections

                    if(this.edit) {
                        try {
                            this.loading = true
                            const { data } = await this.$http.put(`/wiki/chapters/${formData.id}/`, formData)
                            if(data) {
                                this.visible = false
                                this.fUpdChapterList()
                                this.$message.info('Глава обновлена')
                            }
                        } catch(error) {
                            errorHandler({ error })
                        } finally {
                            this.loading = false
                        }
                    } else {
                        try {
                            this.loading = true
                            const { data } = await this.$http.post('/wiki/chapters/', formData)
                            if(data) {
                                this.visible = false
                                this.fUpdChapterList()
                                this.$message.info('Глава создана')
                            }
                        } catch(error) {
                            errorHandler({ error })
                        } finally {
                            this.loading = false
                        }
                    }
                } else {
                    return false;
                }
            });
        },
    },
    mounted() {
        eventBus.$on('open_chapter_drawer', (value = null) => {
            if(value) {
                this.edit = true
                const url = `wiki/chapters/${value.id}/form/`
                this.$http.get(url)
                    .then(({ data }) => {
                        if(data.sections?.length) {
                            data.section = data.sections[0]
                        }
                        this.form = data
                        this.editorRenderKey += 1
                    })
                    .catch(error => errorHandler({ error, show: false }))
            } else {
                this.form = getForm()
                this.editorRenderKey += 1
            }

            this.visible = true
        })
    },
    beforeDestroy() {
        eventBus.$off('open_chapter_drawer')
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
