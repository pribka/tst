<template>
    <div class="pj_padding">
        <div v-if="!isMobile" class="page_header flex items-center pb-4">
            <a-button 
                type="primary" 
                icon="plus"
                class="mr-2"
                size="large"
                @click="createDocument()">
                Добавить документ
            </a-button>
            <PageFilter 
                :model="model"
                :key="page_name"
                size="large"
                :page_name="page_name" />
        </div> 
        <div class="list">
            <keep-alive>
                <component 
                    :is="listComponent" 
                    :model="model"
                    :page_name="page_name" />
            </keep-alive>
        </div>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    components: {
        PageFilter: () => import('@/components/PageFilter')
    },
    data() {
        return {
            page_name: 'contractor_docs',
            model: 'contractor_docs.ContractorDocModel'
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        listComponent() {
            if(this.isMobile)
                return () => import(/* webpackMode: "lazy" */'./components/List.vue')
            else
                return () => import(/* webpackMode: "lazy" */'./components/Table.vue')
        }
    },
    methods: {
        createDocument() {
            eventBus.$emit('create_document')
        }
    }
}
</script>