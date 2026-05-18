<template>
    <div>
        <div class="w-full max-w-[340px] mr-6">
            <TemplateListItem
                v-for="item in templates.results"
                :activeItem="activeItem"
                :selectHandler="selectHandler"
                :key="item.id"
                :item="item" />
          
            <infinite-loading 
                ref="infiniteLoading" 
                @infinite="infiniteHandler" 
                :identifier="infiniteId"
                :distance="10">
                <div slot="spinner" class="flex items-center justify-center inf_spinner">
                    <a-spin />
                </div>
                <div slot="no-more"></div>
                <div slot="no-results"></div>
            </infinite-loading>
            <a-empty 
                v-if="templates.count === 0" 
                :description="$t('no_data')"
                class="mb-4" />

           
        </div>
    </div>
</template>

<script>
import InfiniteLoading from 'vue-infinite-loading'
import eventBus from "@/utils/eventBus"
export default {
    components: {
        InfiniteLoading,
        TemplateListItem: () => import('./TemplateListItem.vue')
    },
    props: {
        activeItem: {
            type: String,
            default: ''
        },
        selectHandler: {
            type: Function,
            default: () => {}
        },
    },
    data() { 
        return {
            infiniteId: new Date(),
            templates: {
                results: []
            },
            params: {
                page_size: 10,
                page: 1
            }
        }
    },
    mounted() {
        eventBus.$on('reload_template_list', () => {
            this.resetList()
        })
    },
    beforeDestroy() {
        eventBus.$off('reload_template_list')
    },
    methods: {
        async infiniteHandler($state) {
            this.getTemplates()
                .then(data => {
                    data.results.unshift(...this.templates.results);
                    this.templates = data;

                    if (data?.next) {
                        this.params.page++;
                        $state.loaded();
                    } else {
                        $state.complete();
                    }
                })
                .catch((error) => {
                    console.error(error)
                    this.$notification.error({
                        message: this.$t("project.could_not_load_templates"),
                    })
                    $state.complete();
                });
        },
        getTemplates() {
            const url = "/work_groups/templates/"
            return this.$http.get(url, { params: this.param })
                .then(({ data }) => data)
                .catch(error => { throw error })
        },
        resetList() {
            this.infiniteId = new Date()
            this.templates = { results: [] }
        },
    }

}
</script>