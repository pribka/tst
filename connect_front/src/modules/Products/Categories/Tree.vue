<template>
    <a-card>
        <div class="categories">
            <a-spin :spinning="loading">
                <div class="spin-content" >
                    <div class="mb-1">
                        <span 
                            class="text-sm cursor-pointer main_category"
                            :class="mainCategory && 'active'"
                            @click="returnAllCategory(true)">Все категории</span>
                    </div>
                    <a-tree 
                        @select="selectEl"
                        @expand="onExpand"
                        :tree-data="list"   
                        :defaultSelectedKeys="activeEl"
                        :default-expanded-keys="expandedKeys"
                        :selectedKeys="selectedKeys"
                        :expanded-keys="expandedKeys">
                        <template  
                            slot="title" 
                            slot-scope="item">
                            <span class="cat_title" >{{ item.title}}</span>
                            <span class="count">({{item.goods_count}})</span>
                        </template>
                    </a-tree>
                </div>
            </a-spin>   
        </div>
    </a-card>
</template>

<script>
export default {
    props: {
        list: {
            type: Array,
            default: () => []    
        },
        loading: {
            type: Boolean,
            default: false
        },
        expandedKeys: {
            type: Array,
            default: () => []
        },
        selectedKeys: {
            type: Array,
            default: () => []
        },
        activeEl: {
            type: Array,
            default: () => []
        },
        mainCategory: {
            type: Boolean,
            default: true
        },
        returnAllCategory: {
            type: Function,
            default: () => {}
        },
        selectEl: {
            type: Function,
            default: () => {}
        },
        onExpand: {
            type: Function,
            default: () => {}
        }
    }
}
</script>

<style lang="scss">
.categories{ 
    .cat_title{
        word-break: break-all;
        color: #1d65c0;
    }
    .ant-tree{
        .ant-tree-switcher{ 
            color: #1d65c0;
        }
        .ant-tree-title{
            white-space: normal;
            word-break: break-word;
            span{
                display: inline-block;
                white-space: normal;
                word-break: break-word;
                &.cat_title{
                    margin-right: 5px;
                }
                &.count{
                    color: #999;
                    font-size: 11px;
                }
            }
        }
        li{ 
            padding: 4px 0;
            span{
                &.ant-tree-switcher{
                    display: inline-block;
                    width: 16px;
                    height: 20px;
                    line-height: 14px;
                    text-align: left;
                }
            }
            .ant-tree-node-content-wrapper{ 
                height: auto;
                padding: 0px;
                line-height: 20px;
                &:hover{
                    background-color: transparent;
                    .title{
                        color: #000;
                    }
                }
            }
            .ant-tree-node-content-wrapper{ 
                &.ant-tree-node-selected{
                    background-color: transparent;
                    .cat_title{
                        color: #000;
                    }
                }
            }
            ul{
                padding: 0 0 0 8px;
            }
        }
    }
    .spin-content > ul > li > .ant-tree-switcher-noop{
        display: none;
    }
}
</style>