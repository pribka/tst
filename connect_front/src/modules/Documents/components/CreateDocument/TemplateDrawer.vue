<template>
    <div>
        <div class="ant-input ant-input-lg flex items-center w-full cursor-pointer truncate" @click="visible = true">
            <template v-if="value">{{ value.name }}</template>
            <a-button v-else type="link" class="px-0" icon="plus">
                Выбрать
            </a-button>
        </div>
        <a-drawer
            title="Выбрать организацию"
            :visible="visible"
            @close="visible = false"
            class="sel_drawer"
            :zIndex="2000"
            destroyOnClose
            :afterVisibleChange="afterVisibleChange"
            :width="drawerWidth"
            placement="right">
            <div class="drawer_body">
                <div 
                    v-if="empty && !loading" 
                    class="mt-5">
                    <a-empty description="Нет данных" />
                </div>
                <div class="list_items">
                    <div v-for="item in list.results" :key="item.id" class="list_items__card" @click="selectItem(item)">
                        <div>
                            <div class="mb-1">{{ item.name }}</div>
                            <div v-if="item.description" class="gray text-xs desc">
                                {{ item.description }}
                            </div>
                            <div v-if="item.doc_type">
                                <a-tag class="text-xs">
                                    {{ item.doc_type.name }}
                                </a-tag>
                            </div>
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
export default {
    components: {
        InfiniteLoading
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
            list: {
                results: [],
                next: true,
                count: 0
            }
        }
    },
    methods: {
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
                    const { data } = await this.$http.get('/contractor_docs/templates/', {
                        params: {
                            page: this.page,
                            page_size: 15
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
        }
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
            .desc{
                &:not(:last-child){
                    margin-bottom: 6px;
                }
            }
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
        .drawer_body{
            height: calc(100% - 40px);
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