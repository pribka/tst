<template>
    <DrawerTemplate
        :width="drawerWidth"
        destroyOnClose
        @close="closeDrawer"
        v-model="visible">
        <template #title>
            <div class="flex w-full justify-between items-center">
                <span class="title">{{ titleText }}</span>
            </div>
        </template>

        <div class="d_body w-full">
            <div class="flex w-full justify-between items-center">
                <a-spin class="w-full" :spinning="formLoading">
                    <template>
                        <TagForm ref="tagForm" :visible="visible"/>
                    </template>
                </a-spin>
            </div>
        </div>

        <template #footer>
            <div class="d_footer">
                <a-button
                    type="primary"
                    :block="isMobile"
                    size="large"
                    class="mr-2 w-full md:w-auto lg:w-auto"
                    @click="save"
                    :loading="saving">
                    Сохранить
                </a-button>
            </div>
        </template>
    </DrawerTemplate>
</template>

<script>
import { mapState } from 'vuex'
import eventBus from '@/utils/eventBus'
import axios from '@/config/axios'

export default {
    name: 'TagDrawerActions',
    components: { 
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue'), 
        TagForm: () => import('./TagForm.vue')
    },
    props: { zIndex: { type: Number, default: 1010 } },
    data() {
        return {
            visible: false,
            mode: 'create',        // 'create' | 'edit'
            editingId: null,
            formLoading: false,
            saving: false,
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user,
            windowWidth: state => state.windowWidth,
            isMobile: state => state.isMobile,
        }),
        drawerWidth() { return this.windowWidth > 1100 ? 1100 : '100%' },
        titleText() { return this.mode === 'edit' ? 'Редактировать' : 'Создать' },
    },
    created() {
        eventBus.$on('create_tag_gos24', this.open)
        eventBus.$on('edit_tag_gos24', this.openEdit)
    },
    beforeDestroy() {
        eventBus.$off('create_tag_gos24', this.open)
        eventBus.$off('edit_tag_gos24', this.openEdit)
    },
    methods: {
        closeDrawer() {
            this.visible = false
            this.mode = 'create'
            this.editingId = null
        },
        open() {
            this.visible = true
            this.mode = 'create'
            this.$nextTick(() => { this.$refs.tagForm?.reset?.() })
        },
        async openEdit({ id }) {
            this.visible = true
            this.mode = 'edit'
            this.editingId = id
            this.formLoading = true
            try {
                const { data } = await axios.get(`/content_item_gos24/tag/${id}/`)
                this.$nextTick(() => { this.$refs.tagForm?.setData?.(data) })
            } catch (e) {
                const msg = (e?.response?.data?.detail || e?.response?.data?.message) || 'Ошибка загрузки'
                this.$message.error(msg)
            } finally {
                this.formLoading = false
            }
        },
        async save() {
            if (this.saving) return
            if (!this.$refs.tagForm?.submit) {
                this.$message.warning('Форма не инициализирована')
                return
            }

            const { valid, payload } = await this.$refs.tagForm.submit()
            if (!valid) return

            try {
                this.saving = true
                if (this.mode === 'edit' && this.editingId) {
                    await axios.patch(`/content_item_gos24/tag/${this.editingId}/`, payload)
                    this.$message.success('Изменения сохранены')
                } else {
                    await axios.post('/content_item_gos24/tag/', payload)
                    this.$message.success('Сохранено')
                }
                this.visible = false
                this.$nextTick(() => eventBus.$emit('tag:refresh'))
            } catch (e) {
                const msg = (e?.response?.data?.detail || e?.response?.data?.message) || 'Ошибка при сохранении'
                this.$message.error(msg)
                // eslint-disable-next-line no-console
                console.log('Create/Update tag error', e)
            } finally {
                this.saving = false
            }
        },
    },
}
</script>

<style lang="scss" scoped>
.custom_border { border: 1px solid var(--borderColor); }

.oc_drawer {
    &::v-deep {
        .ant-drawer-wrapper-body, .ant-drawer-content { overflow: hidden; padding: 0; }
        .ant-drawer-header { padding-left: 20px; padding-right: 20px; }
        .ant-drawer-body { height: calc(100% - 40px); padding: 0; }
        .drawer_body { height: calc(100% - 40px); overflow-y: auto; overflow-x: hidden; padding: 20px; }
        .drawer_footer { display: flex; align-items: center; height: 40px; border-top: 1px solid #e8e8e8; padding-left: 20px; padding-right: 20px; }
    }
}
</style>
