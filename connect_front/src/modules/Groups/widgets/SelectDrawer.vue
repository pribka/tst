<template>
    <div>
        <div  
            class="ant-input flex items-center justify-between relative ant-input-lg truncate">
            <a-button 
                v-if="!value"
                type="link"
                @click="visible = true"
                class="px-0"
                icon="plus">
                {{ $t('wgr.select') }}
            </a-button>
            <template v-else>
                <div>
                    <span class="mr-2 truncate">
                        {{ value.name }}
                    </span>
                    <a-button 
                        type="link"
                        @click="visible = true"
                        class="px-0">
                        {{ $t('wgr.change') }}
                    </a-button>
                </div>
                <a-button
                    icon="close-circle"
                    type="link"
                    @click="clearValue()"
                    class="text_current" />
            </template>
        </div>
        <a-drawer
            :title="drawerLabel"
            placement="right"
            :zIndex="1200"
            class="drawer_slct"
            :width="400"
            :visible="visible"
            @close="closeDrawer">
            <div 
                v-if="visible" 
                class="body_list">
                <div class="select_list">
                    <div 
                        v-for="item in list.results" 
                        class="item"
                        :key="item.id"
                        @click="select(item)">
                        <span>{{ item.name }}</span>
                        <a-radio :checked="checkSelected(item)" />
                    </div>
                </div>
                <infinite-loading
                    v-if="list.next"
                    :identifier="apiUrl"
                    @infinite="getList" 
                    v-bind:distance="10">
                    <div slot="spinner"><a-spin /></div>
                    <div slot="no-more"></div>
                    <div slot="no-results"></div>
                </infinite-loading>
            </div>
        </a-drawer>
    </div>
</template>

<script>
import InfiniteLoading from 'vue-infinite-loading'
export default {
    props: {
        value: [Object, String],
        apiUrl: {
            type: String,
            default: '/program/list/'
        },
        drawerLabel: {
            type: String,
            default: 'Выбрать'
        }
    },
    components: {
        InfiniteLoading
    },
    data() {
        return {
            visible: false,
            list: {
                results: [],
                next: true,
                count: 0
            },
            page: 0,
            loading: false
        }
    },
    watch: {
        visible(val) {
            if(!val) {
                this.list = {
                    results: [],
                    next: true,
                    count: 0
                }
                this.page = 0
            }
        }
    },
    methods: {
        clearValue() {
            this.$emit('input', null)
        },
        checkSelected(item) {
            if(this.value && this.value.id === item.id)
                return true
            else
                return false
        },
        select(item) {
            this.$emit('input', item)
            this.closeDrawer()
        },
        closeDrawer() {
            this.visible = false
        },
        async getList($state) {
            if(!this.loading && this.list.next) {
                try {
                    this.loading = true
                    this.page += 1
                    const { data } = await this.$http.get(this.apiUrl, {
                        params: {
                            page_size: 20,
                            page: this.page
                        }
                    })

                    this.list.results = this.list.results.concat(data.results)
                    this.list.next = data.next
                    this.list.count = data.count

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

<style lang="scss">
.drawer_slct{
    .ant-drawer-content,
    .ant-drawer-wrapper-body{
        overflow: hidden;
    }
    .body_list{
        overflow-y: auto;
        height: 100%;
    }
    .ant-drawer-body{
        padding: 0px;
        height: calc(100% - 40px);
        overflow: hidden;
    }
    .select_list{
        .item{
            cursor: pointer;
            padding: 12px 15px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            &:not(:last-child){
                border-bottom: 1px solid var(--border2);
            }
        }
    }
}
</style>