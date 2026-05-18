<template>
    <DrawerTemplate
        v-model="visible"
        :title="edit ? $t('support.editCategory') : $t('support.addCategory')"
        :width="isMobile ? '100%' : 1000"
        @afterVisibleChange="afterVisibleChange"
        @close="visible = false">
        <a-form-model
            ref="ruleForm"
            :model="form"
            :rules="rules">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-x-4">
                <a-form-model-item ref="name_ru" :label="$t('support.nameRu')" prop="name_ru" class="mb-2">
                    <a-input v-model="form.name_ru" size="large" />
                </a-form-model-item>
                <a-form-model-item ref="name_kk" :label="$t('support.nameKk')" prop="name_kk" class="mb-2">
                    <a-input v-model="form.name_kk" size="large" />
                </a-form-model-item>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-x-4">
                <a-form-model-item ref="contractor" :label="$t('support.organization')" prop="contractor" class="mb-2">
                    <WikiOrgSelect v-model="form.contractor" @change="handleContractorChange" />
                </a-form-model-item>
                <a-form-model-item ref="sort" :label="$t('support.position')" prop="sort" class="mb-2">
                    <a-input-number v-model="form.sort" style="width: 100%;" size="large" :min="0" :max="100000" />
                </a-form-model-item>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-x-4">
                <a-form-model-item ref="public" :label="$t('support.publicSection')" prop="public" class="mb-2">
                    <a-switch v-model="form.public" />
                </a-form-model-item>
                <!--<a-form-model-item ref="show_on_main_page" :label="$t('support.showOnMainPage')" prop="show_on_main_page" class="mb-2">
                    <a-switch v-model="form.show_on_main_page" />
                </a-form-model-item>-->
            </div>
            <div v-if="!form.public" class="access_block mb-4">
                <div class="access_block__head">
                    <div class="access_block__title">
                        {{ $t('support.accessUsers') }}
                    </div>
                    <WikiUserMiniSelect
                        v-model="selectedAccessUser"
                        :selectedItems="accessUsers"
                        :showRecent="false"
                        :showSearch="true"
                        :disabled="!selectedContractorId"
                        :apiUrl="accessUsersApiUrl"
                        pageName="support_page_section_access_users"
                        @change="handleAccessUserSelect" />
                </div>
                <a-spin :spinning="accessLoading">
                    <div v-if="accessUsers.length" class="access_users_list">
                        <div v-for="user in accessUsers" :key="user.id" class="access_user_item">
                            <Profiler
                                :user="user"
                                :avatarSize="26"
                                class="access_user_meta" />
                            <a-button
                                type="ui"
                                ghost
                                flaticon
                                shape="circle"
                                icon="fi-rr-trash"
                                :loading="removeUserLoadingIds.includes(user.id)"
                                @click="removeAccessUser(user)" />
                        </div>
                    </div>
                    <a-alert
                        v-else
                        banner
                        type="info"
                        :message="$t('support.noAccessUsers')" />
                </a-spin>
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
    public: true,
    use_in_wiki: true,
    show_on_main_page: true,
    sort: 500,
    code: ''
})

export default {
    components: {
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue'),
        WikiOrgSelect: () => import('./WikiOrgSelect.vue'),
        WikiUserMiniSelect: () => import('./WikiUserMiniSelect.vue')
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
        selectedContractorId() {
            return this.form?.contractor?.id || null
        },
        accessUsersApiUrl() {
            if(!this.selectedContractorId) return ''
            return `/users/my_organizations/${this.selectedContractorId}/users_short/?display=my_organizations_only`
        },
        ckEditor() {
            return this.visible ? () => import('@apps/CKEditor') : null
        }
    },
    data() {
        return {
            visible: false,
            loading: false,
            edit: false,
            editorRenderKey: 0,
            dangerLoading: false,
            accessLoading: false,
            removeUserLoadingIds: [],
            form: getForm(),
            selectedAccessUser: null,
            accessUsers: [],
            initialAccessUserIds: [],
            rules: {
                name_ru: [
                    { required: true, message: this.$t('field_required'), trigger: 'blur' }
                ],
                random_html: [
                    { required: true, message: this.$t('field_required'), trigger: 'blur' }
                ],
                contractor: [
                    { required: true, message: this.$t('field_required'), trigger: 'blur' }
                ]
            }
        }
    },
    methods: {
        afterVisibleChange(vis) {
            if(!vis) {
                this.edit = false
                this.form = getForm()
                this.editorRenderKey += 1
                this.selectedAccessUser = null
                this.accessUsers = []
                this.initialAccessUserIds = []
                this.removeUserLoadingIds = []
            }
        },
        handleContractorChange() {
            this.selectedAccessUser = null
            this.accessUsers = []
            this.initialAccessUserIds = []
        },
        normalizeUser(user) {
            return user?.user || user?.profile || user || null
        },
        normalizeUsersList(data) {
            const users = Array.isArray(data)
                ? data
                : data?.results || data?.users || []

            return users
                .map(item => this.normalizeUser(item))
                .filter(item => item?.id)
                .reduce((acc, item) => {
                    if(!acc.find(user => user.id === item.id)) {
                        acc.push(item)
                    }

                    return acc
                }, [])
        },
        handleAccessUsersInput(users = []) {
            this.accessUsers = this.normalizeUsersList(users)
        },
        handleAccessUserSelect(user) {
            const normalizedUser = this.normalizeUser(user)
            if(!normalizedUser?.id) {
                this.selectedAccessUser = null
                return
            }

            if(!this.accessUsers.find(item => item.id === normalizedUser.id)) {
                this.accessUsers = [...this.accessUsers, normalizedUser]
            }

            this.selectedAccessUser = null
        },
        async loadAccessUsers(sectionId) {
            if(!sectionId) return

            try {
                this.accessLoading = true
                const { data } = await this.$http.get(`/wiki/${sectionId}/access/`)
                const users = this.normalizeUsersList(data)
                this.accessUsers = users
                this.initialAccessUserIds = users.map(user => user.id)
            } catch(error) {
                errorHandler({ error, show: false })
                this.accessUsers = []
                this.initialAccessUserIds = []
            } finally {
                this.accessLoading = false
            }
        },
        async syncAccessUsers(sectionId) {
            if(!sectionId || this.form.public) return

            const userIds = this.accessUsers
                .map(user => user.id)
                .filter(Boolean)

            if(!userIds.length) return

            try {
                await this.$http.post(`/wiki/${sectionId}/access/`, {
                    users: userIds
                })

                this.initialAccessUserIds = [...new Set(userIds)]
            } catch(error) {
                errorHandler({ error })
                throw error
            }
        },
        async removeAccessUser(user) {
            if(!user?.id) return

            const hasPersistedAccess = this.edit && this.form.id && this.initialAccessUserIds.includes(user.id)

            if(!hasPersistedAccess) {
                this.accessUsers = this.accessUsers.filter(item => item.id !== user.id)
                return
            }

            try {
                this.removeUserLoadingIds.push(user.id)
                await this.$http.post(`/wiki/${this.form.id}/access/remove/`, {
                    user: user.id
                })
                this.accessUsers = this.accessUsers.filter(item => item.id !== user.id)
                this.initialAccessUserIds = this.initialAccessUserIds.filter(id => id !== user.id)
            } catch(error) {
                errorHandler({ error })
            } finally {
                this.removeUserLoadingIds = this.removeUserLoadingIds.filter(id => id !== user.id)
            }
        },
        async deleteHandler() {
            this.$confirm({
                title: this.$t('support.removeCategoryConfirm'),
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
                                this.$message.success(this.$t('support.categoryDeleted'))
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
                if(formData.contractor?.id) {
                    formData.contractor = formData.contractor.id
                }

                try {
                    this.loading = true
                    const { data } = this.edit
                        ? await this.$http.put(`/wiki/sections/${formData.id}/`, formData)
                        : await this.$http.post('/wiki/sections/', formData)

                    const sectionId = data?.id || formData.id

                    if(data) {
                        await this.syncAccessUsers(sectionId)
                        this.visible = false
                        this.fUpdChapterList()
                        this.$message.info(this.edit ? this.$t('support.categoryUpdated') : this.$t('support.categoryCreated'))
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
                this.$http.get(`wiki/sections/${value.id}/form/`)
                    .then(async ({ data }) => {
                        this.form = data
                        this.editorRenderKey += 1
                        if(!this.form.public) {
                            await this.loadAccessUsers(value.id)
                        } else {
                            this.accessUsers = []
                            this.initialAccessUserIds = []
                        }
                    })
                    .catch(error => errorHandler({ error, show: false }))
            } else {
                this.form = getForm()
                this.editorRenderKey += 1
                this.accessUsers = []
                this.initialAccessUserIds = []
            }
            this.visible = true
        }
    },
    mounted() {
        eventBus.$on('open_support_page_section_drawer', this.openDrawer)
    },
    beforeDestroy() {
        eventBus.$off('open_support_page_section_drawer', this.openDrawer)
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

.access_block {
    margin-bottom: 16px;
    &__head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        margin-bottom: 14px;
    }
    &__title {
        font-size: 14px;
        font-weight: 600;
        color: #1f1f1f;
        line-height: 1.4;
    }
}

.access_users_list {
    display: flex;
    flex-direction: column;
}

.access_user_item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 14px 0;
    &:not(:last-child) {
        border-bottom: 1px solid var(--border2);
    }
}

.access_user_meta {
    display: flex;
    align-items: center;
    min-width: 0;
    flex: 1;
}

@media (max-width: 767px) {
    .access_block__head {
        flex-direction: column;
        align-items: stretch;
    }
    .access_user_item {
        padding: 12px 0;
    }
}
</style>
