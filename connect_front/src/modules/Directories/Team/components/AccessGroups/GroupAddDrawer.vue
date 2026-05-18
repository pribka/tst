<template>
    <DrawerTemplate
        class="drawer"
        :width="drawerWidth"
        destroyOnClose
        @afterVisibleChange="afterVisibleChange"
        :title="driwerTitle"
        v-model="visible"
        @close="close">
        <AccessGroupForm
            ref="accessGroupForm"
            :organization="organization" />
        <template #footer>
            <div class="flex items-center">
                <a-button
                    class="mr-2 px-6"
                    type="primary"
                    size="large"
                    :loading="loading"
                    @click="save">
                    {{ $t('Save') }}
                </a-button>
                <a-button
                    type="ui_ghost"
                    size="large"
                    @click="close">
                    {{ $t("Cancel") }}
                </a-button>
            </div>
        </template>
    </DrawerTemplate>
</template>


<script>
export default {
    components: {
        AccessGroupForm: () => import("./AccessGroupForm.vue"),
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue')
    },
    props: {
        organization: {
            type: Object,
            required: true,
        },
    },
    data() {
        return {
            loading: false,
            visible: false,
        };
    },
    computed: {
        driwerTitle() {
            return this.title || this.$t("New access group");
        },
        drawerWidth() {
            const baseWidth = 720;
            const offset = 40;
            return this.windowWidth > baseWidth + offset
                ? baseWidth
                : this.windowWidth;
        },
        windowWidth() {
            return this.$store.state.windowWidth;
        },
        isMobile() {
            return this.$store.state.isMobile;
        },
    },
    methods: {
        afterVisibleChange(visible) {
            if (!visible) {
                this.zIndex = 1200;
            }
        },
        close() {
            this.visible = false;
        },
        open() {
            this.visible = true;
        },
        save() {
            this.loading = true;
            this.$refs.accessGroupForm.submit()
                .then((id) => {
                    this.close();
                    this.$emit('update', id)
                })
                .finally(() => {
                    this.loading = false;
                })

        }
    },
};
</script>
