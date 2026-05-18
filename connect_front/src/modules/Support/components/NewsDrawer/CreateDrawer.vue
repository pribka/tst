<template>
    <DrawerTemplate
        :title="edit ? $t('support.editNews') : $t('support.addNews')"
        :width="isMobile ? '100%' : 700"
        class="news_drawer"
        v-model="visible"
        :zIndex="9999"
        @afterVisibleChange="afterVisibleChange"
        @close="visible = false">
        <a-form-model
            ref="ruleForm"
            :model="form"
            :rules="rules">
            <a-form-model-item 
                ref="title" 
                :label="$t('name')" 
                prop="title">
                <a-input v-model="form.title" size="large" />
            </a-form-model-item>
            <a-form-model-item 
                ref="content" 
                :label="$t('text')" 
                prop="content">
                <component
                    :is="ckEditor"
                    :key="edit || visible"
                    v-model="form.content" />
            </a-form-model-item>
            <a-form-model-item 
                ref="is_important" 
                :label="$t('support.importantNews')" 
                prop="is_important">
                <a-switch v-model="form.is_important" />
            </a-form-model-item>
            <a-form-model-item
                ref="is_banner"
                :label="$t('support.showAsBanner')"
                prop="is_banner">
                <a-switch v-model="form.is_banner" />
            </a-form-model-item>
        </a-form-model>
        <template #footer>
            <a-button type="primary" size="large" :loading="loading" @click="onSubmit()">
                {{ $t('save') }}
            </a-button>
        </template>
    </DrawerTemplate>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'
export default {
    components: {
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue')
    },
    props: {
        resetList: {
            type: Function,
            default: () => {}
        },
        afterSubmit: {
            type: Function,
            default: () => {}
        }
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
            edit: false,
            loading: false,
            form: {
                id: null,
                title: '',
                content: '',
                is_important: false,
                is_banner: false,
                related_object: null,
                image: null,
                files: []
            },
            rules: {
                title: [
                    { required: true, message: this.$t('field_required'), trigger: 'blur' }
                ],
                content: [
                    { required: true, message: this.$t('field_required'), trigger: 'blur' }
                ]
            }
        }
    },
    methods: {
        afterVisibleChange(vis) {
            if(!vis) {
                this.edit = false
                this.form = this.defaultForm()
            }
        },
        defaultForm() {
            return {
                id: null,
                title: '',
                content: '',
                is_important: false,
                is_banner: false,
                related_object: null,
                image: null,
                files: []
            }
        },
        openDrawer(news = null) {
            if(news?.id) {
                this.edit = true
                this.form = {
                    ...this.defaultForm(),
                    id: news.id,
                    title: news.title || '',
                    content: news.content || '',
                    is_important: !!news.is_important,
                    is_banner: !!news.is_banner
                }
            }
            this.visible = true
        },
        onSubmit() {
            this.$refs.ruleForm.validate(async valid => {
                if (valid) {
                    const formData = {...this.form}
                    if(this.edit) {
                        try {
                            this.loading = true
                            const { data } = await this.$http.put(`/news/news/${formData.id}/update/`, formData)
                            if(data) {
                                await this.$store.dispatch('config/clearHiddenBannerNews', {
                                    userId: this.$store.state.user.user?.id
                                })
                                await this.$store.dispatch('config/fetchBannerNews', { force: true })
                                this.resetList()
                                eventBus.$emit('support_news_list_reload')
                                this.afterSubmit(data)
                                this.visible = false
                                this.$message.info(this.$t('support.newsUpdated'))
                            }
                        } catch(error) {
                            errorHandler({ error })
                        } finally {
                            this.loading = false
                        }
                    } else {
                        try {
                            this.loading = true
                            const { data } = await this.$http.post('/news/news/create/', formData)
                            if(data) {
                                await this.$store.dispatch('config/fetchBannerNews', { force: true })
                                this.resetList()
                                eventBus.$emit('support_news_list_reload')
                                this.afterSubmit(data)
                                this.visible = false
                                this.$message.info(this.$t('support.newsCreated'))
                            }
                        } catch(error) {
                            errorHandler({ error })
                        } finally {
                            this.loading = false
                        }
                    }
                } else {
                    return false
                }
            })
        },
    }
}
</script>
