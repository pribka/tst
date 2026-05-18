<template>
    <div>
        <a-button
            class="mb-5"
            type="primary"
            flaticon
            size="large"
            icon="fi-rr-plus"
            @click="addGroup">
            {{ $t('team.add_group') }}
        </a-button>
        <GroupAddDrawer 
            ref="addGroupDrawer"
            @update="reload"
            :organization="organization" />
        <GroupShowDrawer 
            ref="showGroupDrawer"
            @update="reload"
            :reloadAccessGroupList="reload"
            :organization="organization" />
        <div class="grid gap-2 md:grid-cols-3">
            <GroupCard :item="item" v-for="item in groups.results" :key="item.id" :openDetailById="openDetailById" />
        </div>
        <infinite-loading 
            ref="org_infinity"
            @infinite="infiniteHandler"
            :identifier="infiniteId"
            v-bind:distance="10">
            <div 
                slot="spinner"
                class="flex items-center justify-center inf_spinner">
                <a-spin />
            </div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
    </div>
</template>

<script>
export default {
    components: {
        GroupCard: () => import('./GroupCard.vue'),
        GroupAddDrawer: () => import('./GroupAddDrawer.vue'),
        GroupShowDrawer: () => import('./GroupShowDrawer.vue'),
        InfiniteLoading: () => import('vue-infinite-loading')
    },
    props: {
        organization: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            loading: false,
            groups: {
                results: []
            },
            params: {
                page: 1,
                page_size: 10,
                contractor: this.organization.id
            },
            infiniteId: new Date(),

        }
    },
    methods: {
        infiniteHandler($state) {
            const url = `/contractor_permissions/access_groups/`
            this.loading = true
            this.$http(url, { params: this.params })
                .then(({ data }) => {
                    data.results.unshift(...this.groups.results);
                    this.groups = data;
                    if (data?.next) {
                        this.params.page++;
                        $state.loaded();
                    } else {
                        $state.complete();
                    }
                })
                .catch(error => {
                    this.$message.error(this.$t('team.failed_to_get_data'))
                    console.error(error)
                    $state.complete();
                })
                .finally(() => {
                    this.loading = false
                })
        },
        addGroup() {
            this.$refs.addGroupDrawer.open()
        },
        openDetailById(id) {
            this.$refs.showGroupDrawer.openById(id)
        },
        reload(id=null) {
            if (id) {
                this.openDetailById(id)
            }

            this.infiniteId = new Date()
            this.params.page = 1
            this.groups.results = []
        }
    },
}
</script>