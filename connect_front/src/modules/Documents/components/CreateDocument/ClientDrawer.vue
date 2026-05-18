<template>
    <div>
        <div class="ant-input ant-input-lg flex items-center w-full cursor-pointer truncate" @click="visible = true">
            <span v-if="value" class="truncate">{{ value.name }}</span>
            <a-button v-else type="link" class="px-0" icon="plus">
                Выбрать
            </a-button>
        </div>
        <a-drawer
            title="Выбрать контрагента"
            :visible="visible"
            @close="visible = false"
            class="sel_drawer"
            :zIndex="2000"
            destroyOnClose
            :afterVisibleChange="afterVisibleChange"
            :width="drawerWidth"
            placement="right">
            <div class="drawer_filter" ref="client_filter">
                <PageFilter
                    :model="model"
                    :key="pageName"
                    placement="bottomRight"
                    class="mb-3"
                    size="large"
                    :getPopupContainer="getPopupContainer"
                    :page_name="pageName"/>
            </div>
            <div class="drawer_body">
                <div 
                    v-if="empty && !loading" 
                    class="mt-5">
                    <a-empty description="Нет данных" />
                </div>
                <div class="list_items">
                    <div v-for="item in list.results" :key="item.id" class="list_items__card" @click="selectItem(item)">
                        <div class="flex items-center truncate">
                            <span class="truncate">{{ item.name }}</span>
                        </div>
                        <div class="pl-2">
                            <a-radio :checked="checkSelected(item)" />
                        </div>
                    </div>
                </div>
                <infinite-loading 
                    ref="org_sel_drawer"
                    @infinite="getList"
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
            <div class="drawer_footer">
                <a-button 
                    type="ui"
                    ghost
                    block
                    @click="visible = false">
                    Закрыть
                </a-button>
            </div>
        </a-drawer>
    </div>
</template>

<script>
import InfiniteLoading from 'vue-infinite-loading'
import PageFilter from '@/components/PageFilter'
import eventBus from '@/utils/eventBus'
export default {
    components: {
        InfiniteLoading,
        PageFilter
    },
    props: {
        value: { // v-model значение, если multiple false то передаем Object, если true то Array
            type: [Object, Array, String]
        },
        getTemplate: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        windowWidth() {
            return this.$store.state.windowWidth
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        drawerWidth() {
            if(this.windowWidth > 400)
                return 400
            else {
                return '100%'
            }
        }
    },
    data() {
        return {
            visible: false,
            loading: false,
            page: 0,
            empty: false,
            model: 'catalogs.ContractorModel',
            pageName: 'catalogs.ContractorModel_documents',
            list: {
                results: [],
                next: true,
                count: 0
            }
        }
    },
    methods: {
        getPopupContainer() {
            return this.$refs.client_filter
        },
        selectItem(item) {
            this.$emit('input', item)
            this.getTemplate()
            this.visible = false
        },
        checkSelected(item) {
            if(this.value) {
                if(item.id === this.value.id)
                    return true
                else
                    return false
            } else
                return false
        },
        afterVisibleChange(vis) {
            if(!vis) {
                this.page = 0
                this.empty = false
                this.list = {
                    results: [],
                    next: true,
                    count: 0
                }
                this.loading = false
            }
        },
        async getList($state) {
            if(!this.loading && this.list.next) {
                try {
                    this.loading = true
                    this.page += 1
                    const { data } = await this.$http.get('/catalogs/contractor_members/', {
                        params: {
                            page: this.page,
                            page_size: 15,
                            page_name: this.pageName
                        }
                    })

                    if(data) {
                        this.list.count = data.count
                        this.list.next = data.next
                    }

                    if(data?.results?.length)
                        this.list.results = this.list.results.concat(data.results)

                    if(this.page === 1 && !this.list.results.length) {
                        this.empty = true
                    }
                        
                    if(this.list.next)
                        $state.loaded()
                    else
                        $state.complete()
                } catch(e) {
                    console.log(e)
                } finally {
                    this.loading = false
                }
            }
        },
        reload() {
            this.page = 0
            this.empty = false
            this.list = {
                results: [],
                next: true,
                count: 0
            }
            this.loading = false

            this.$nextTick(() => {
                if(this.$refs.org_sel_drawer){
                    this.$refs.org_sel_drawer.stateChanger.reset()
                }
            })
        }
    },
    mounted () {
        eventBus.$on(`update_filter_${this.model}`, () => {
            this.reload()
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.model}`)
    }
}
</script>

<style lang="scss" scoped>
.sel_drawer{
    .list_items{
        &__card{
            padding: 12px;
            zoom: 1;
            color: #505050;
            font-size: 14px;
            font-variant: tabular-nums;
            line-height: 1.5;
            list-style: none;
            font-feature-settings: "tnum";
            background: #fff;
            border-radius: var(--borderRadius);
            border: 1px solid var(--border1);
            margin-bottom: 10px;
            -webkit-user-select: none;
            -moz-user-select: none;
            user-select: none;
            display: flex;
            align-items: center;
            justify-content: space-between;
            cursor: pointer;
        }
    }
    &::v-deep{
        .ant-drawer-wrapper-body,
        .ant-drawer-content{
            overflow: hidden;
            padding: 0px;
        }
        .ant-drawer-header{
            padding-left: 20px;
            padding-right: 20px;
        }
        .ant-drawer-body{
            height: calc(100% - 40px);
            padding: 0px;
        }
        .drawer_filter{
            height: 40px;
            .filter_pop_wrapper{
                min-width: 100%;
                max-width: 100%;
            }
            .filter_input{
                border-radius: 0px;
                border-top: 0px;
                border-left: 0px;
                border-right: 0px; 
            }
        }
        .drawer_body{
            height: calc(100% - 80px);
            overflow-y: auto;
            overflow-x: hidden;
            padding: 20px;
            .ck-content{
                height: 500px;
            }
        }
        .drawer_footer{
            display: flex;
            align-items: center;
            height: 40px;
            border-top: 1px solid #e8e8e8;
            padding-left: 20px;
            padding-right: 20px;
        }
    }
}
</style>