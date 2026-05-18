<template>
    <div class="list-view">
        <div class="search-and-add">
            <div class="search">
                <PageFilter
                    :model="model"
                    :key="page_name"
                    onlySearch
                    size="large"
                    :page_name="page_name"/>
            </div>
            <a-button
                class="add-button"
                size="large"
                @click="openAddEdit()">
                {{ $t('chat.add') }}
                <a-icon type="plus-circle" />
            </a-button>
        </div>
        <div class="template-list">
            <div v-for="template in templateList" :key="template.id" class="list-item">
                <div class="template-info">
                    <div class="template-title">
                        {{ template.title }}
                    </div>
                    <div class="template-text" @click="paste(template.text)">
                        {{ template.text }}
                    </div>
                </div>
                <div class="template-actions ml-auto">
                    <template v-if="template.update_available">
                        <a-popconfirm
                            :title="$t('chat.delete_template')"
                            :ok-text="$t('Yes')"
                            :cancel-text="$t('No')"
                            @confirm="deleteTemplate(template.id)">
                            <i class="fi fi-rr-trash red cursor-pointer"></i>
                        </a-popconfirm>
                        <i class="fi fi-rr-pencil cursor-pointer" @click="openAddEdit(edit=true, id=template.id)"></i>
                    </template>
                    <template v-else>
                        <i class="fi fi-rr-trash disabled"></i>
                        <i class="fi fi-rr-pencil disabled"></i>
                    </template>
                    <i v-if="!template.is_public" class="fi fi-rr-lock"></i>
                </div>
            </div>
            <infinite-loading
                ref="supportMessageTemplateInfiniteLoading"
                :identifier="infiniteId"
                @infinite="getList"
                :distance="10">
                <div 
                    slot="spinner"
                    class="mt-[30px]">
                    <a-spin />
                </div>
                <div slot="no-more"></div>
                <div slot="no-results"></div>
            </infinite-loading>
            <div 
                v-if="showEmpty" 
                class="pt-8">
                <a-empty :description="false" />
            </div>
        </div>
    </div>
</template>
<script>
import { mapState, mapMutations } from 'vuex'
import eventBus from '@/utils/eventBus'

export default {
    name: "ListView",
    components: {
        InfiniteLoading: () => import('vue-infinite-loading'),
        PageFilter: () => import('@/components/PageFilter')
    },
    props: {
        deleteTemplate: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            infiniteId: new Date(),
            loading: false,
            pageSize: 10,
            page_name: 'support_message_templates',
            showEmpty: false,
            model: 'chat.SupportMessageTemplateModel'
        }
    },
    computed: {
        ...mapState({
            templateList: state => state.chat.supportMessageTemplates,
            smt_page: state => state.chat.smt_page,
            smt_endOfList: state => state.chat.smt_endOfList,
        })
    },
    methods: {
        ...mapMutations({
            SET_SUPPORT_MESSAGE_TEMPLATES: 'chat/SET_SUPPORT_MESSAGE_TEMPLATES',
            RESET_SUPPORT_MESSAGE_TEMPLATES: 'chat/RESET_SUPPORT_MESSAGE_TEMPLATES',
            INCREMENT_SMT_PAGE: 'chat/INCREMENT_SMT_PAGE',
            RESET_SMT_PAGE: 'chat/RESET_SMT_PAGE',
            SET_SMT_END_OF_LIST: 'chat/SET_SMT_END_OF_LIST',
        }),
        paste(text) {
            eventBus.$emit('pasteText', text)
        },
        openAddEdit(edit=false, id='') {
            this.$emit('openAddEdit', edit, id)
        },
        checkAndSetShowEmpty() {
            if(this.templateList && !this.templateList.length) 
                this.showEmpty = true
            else 
                this.showEmpty = false
        },
        async getList($state) {
            if(this.loading)
                return
            if(this.smt_endOfList) {
                $state.complete()
                return
            }
            const url = 'chat/message_templates/'
            const params = {
                page: this.smt_page,
                page_size: this.pageSize,
                page_name: this.page_name
            }
            this.loading = true
            try {
                const { data } = await this.$http.get(url, {
                    params
                })
                if(data?.results?.length === 0) {
                    this.SET_SMT_END_OF_LIST(true)
                    $state.complete()
                }
                if(data?.results?.length) {
                    this.SET_SUPPORT_MESSAGE_TEMPLATES(data.results)
                    if(data.next) {
                        this.INCREMENT_SMT_PAGE()
                        $state.loaded()
                    } else {
                        $state.complete()
                        this.SET_SMT_END_OF_LIST(true)
                    }
                }
                this.checkAndSetShowEmpty()
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        },
        listReload() {
            this.RESET_SUPPORT_MESSAGE_TEMPLATES()
            this.RESET_SMT_PAGE()
            this.SET_SMT_END_OF_LIST(false)
            this.$nextTick(()=>{
                if(this.$refs['supportMessageTemplateInfiniteLoading']){
                    this.$refs['supportMessageTemplateInfiniteLoading'].stateChanger.reset()
                }
            })
        }
    },
    mounted() {
        eventBus.$on('reloadSMTList', () => {
            this.listReload()
        })
        eventBus.$on(`update_filter_${this.model}`, () => {
            this.listReload()
        })
    },
    beforeDestroy() {
        eventBus.$off('reloadSMTList')
        eventBus.$off(`update_filter_${this.model}`)
    }
}
</script>

<style>
.search{
    .filter_pop_wrapper{
        height: 100%;
        min-width: 0;
        max-width: none;
    }
}
</style>
<style lang="scss" scoped>
.list-view{
    height: 100%;
    width: 100%;
    display: grid;
    row-gap: 20px;
    @media (min-width: 768px) {
        grid-template-rows: 40px 1fr;
    }
    .search-and-add{
        display: grid;
        gap: 10px;
        grid-template-columns: 1fr;
        @media (min-width: 768px) {
            grid-template-columns: 408px 1fr;
        }
        .add-button{
            width: 100%;
            @media (min-width: 768px) {
                height: 100%;
            }

        }
    }
    .template-list{
        overflow-y: auto;
        @media (min-width: 768px) {
            height: 238px;
        }
        margin-right: -14px;
        padding-right: 14px;
        .list-item{
            padding-top: 8px;
            display: flex;
            @media (min-width: 768px) {
                display: grid;
                grid-template-columns: 1fr auto;
                grid-template-rows: 40px;
                column-gap: 15px;
            }
            .template-info {
                @media (min-width: 768px) {
                    display: grid;
                    grid-template-columns: 120px 1fr;
                    column-gap: 15px;
                }
            }
            
            .template-title{
                font-size: 14px;
                font-weight: 400;
                line-height: 19.6px;
                text-align: left;
            }
            .template-text{
                @media (min-width: 768px) {
                }
                height: 40px;
                overflow: hidden;
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
                text-overflow: ellipsis;
                font-size: 14px;
                font-weight: 400;
                line-height: 19.6px;
                text-align: left;
                opacity: 0.6;
                cursor: pointer;
            }
            .template-actions{
                margin-top: 2px;
                display: grid;
                grid-template-columns: repeat(3, 15px);
                grid-template-rows: 15px;
                column-gap:15px;
                direction: rtl;
                .cursor-pointer{
                    cursor: pointer;
                }
                .red{
                    color: rgb(220, 38, 38, 1);
                }
                .disabled {
                    color: rgb(209, 213, 219, 1);
                }
            }
            &:not(:last-child){
                border-bottom: 1px solid var(--borderColor);
                padding-bottom: 15px;
            }
        }
    }
}
</style>