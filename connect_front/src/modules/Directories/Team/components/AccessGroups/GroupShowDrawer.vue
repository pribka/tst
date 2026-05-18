<template>
    <DrawerTemplate
        class="drawer"
        :width="drawerWidth"
        destroyOnClose
        @afterVisibleChange="afterVisibleChange"
        v-model="visible"
        @close="close">
        <template #title>
            <div v-if="!item" class="custom_header_skeleton"></div>
            <template v-else>
                {{ item?.name }}
            </template>
        </template>
        <template #tabs>
            <a-tabs 
                default-active-key="" 
                v-model="activeTab"
                :showContent="false"
                class="header_tab"
                @change="changeActiveTab">
                <a-tab-pane 
                    key="employees" 
                    :tab="$t('Employees')" />
                <a-tab-pane 
                    key="settings" 
                    :tab="$t('Access group settings')" />
            </a-tabs>
        </template>
        <a-skeleton :loading="!item">
            <component 
                ref="dynamicWidget"
                :is="widget"
                edit
                :reloadAccessGroupList="reloadAccessGroupList"
                :accessGroup="item"
                :organization="organization" />
        </a-skeleton>
        <template #footer>
            <div class="flex items-center">
                <template v-if="showFooterButtons">
                    <a-button
                        class="mr-2 w-full"
                        type="primary"
                        size="large"
                        :loading="loading"
                        @click="save">
                        {{ $t('Save') }}
                    </a-button>
                    <a-button
                        type="primary"
                        ghost
                        class="w-full"
                        size="large"
                        @click="close">
                        {{ $t("Cancel") }}
                    </a-button>
                </template>
            </div>
        </template>
    </DrawerTemplate>
</template>


<script>
export default {
    components: {
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue')
    },
    props: {
        organization: {
            type: Object,
            required: true,
        },
        reloadAccessGroupList: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            activeTab: 'employees',
            loading: false,
            id: null,
            item: null,
            visible: false,
        };
    },
    computed: {
        showFooterButtons() {
            return this.activeTab === 'settings' && !this.item?.is_predefined
        },
        driwerTitle() {
            return this.item?.name || ''
        },
        drawerWidth() {
            const baseWidth = 1000;
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
        widget() {
            const components = {
                employees: () => import('./Employees.vue'),
                settings: () => import('./AccessGroupForm.vue'),
            }
            return components[this.activeTab]
        },
    },
    methods: {
        getData() {
            const url = `/contractor_permissions/access_groups/${this.id}/`;
            return this.$http(url).then(({ data }) => {
                this.item = data
            });
        },
        openById(id) {
            this.id = id
            this.open()
            this.getData()
        },

        afterVisibleChange(visible) {
            if (!visible) {
                this.zIndex = 1200;
            }
        },
        close() {
            this.visible = false;
            this.item = null
        },
        open() {
            this.visible = true;
        },

        save() {
            this.loading = true;
            this.$refs.dynamicWidget.submit('update')
                .then((id) => {
                    this.close();
                    this.$emit('update')
                })
                .finally(() => {
                    this.loading = false;
                })

        },


        async changeActiveTab(tab) {
            // const query = JSON.parse(JSON.stringify(this.$route.query))
            // query.tab = tab
            // await this.$router.replace({ query })
        },  
    },
};
</script>

<style lang="scss" scoped>
.form-panel {
  padding: 20px;
  border: 1px solid #d9d9d9;
  border-radius: 8px;

  & + & {
    margin-top: 10px;
  }
}

.module-row {
  display: grid;
  align-items: center;
  grid-template-columns: 1fr 3fr;
  column-gap: 20px;
  &:not(:last-child) {
    margin-bottom: 15px;
  }
}
.custom_header_skeleton {
    height: 1rem;
    background-color: #f2f2f2;
    width: 38%;
}
</style>
