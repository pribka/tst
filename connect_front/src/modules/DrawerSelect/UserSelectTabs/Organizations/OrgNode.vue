<template>
    <div class="org-node">
        <div class="node-panel" :class="selectedOrgID === node.key && 'selected'">
            <a-spin v-if="loading" class="arrow" size="small"></a-spin>
            <div
                v-else
                class="arrow"
                :class="{ expanded }"
                @click.stop="toggleOpen">
                <i v-if="!isLeaf" class="fi fi-rr-angle-right" style="color: #888888;" />
            </div>
            <div class="logo">
                <a-avatar
                    icon="team"
                    :size="24"
                    :src="node.logo" />
            </div>
            <div
                class="node-title"
                @click.stop="toggleSelect">
                <span>{{ node.title || $t('Not specified') }}</span>
            </div>
        </div>
  
        <div class="children" v-show="expanded">
            <OrgNode
                v-for="child in children"
                :key="child.key"
                :node="child"
                :load-children="loadChildren"
                :selectedOrgID="selectedOrgID"
                @select="$emit('select', $event)"
                @open="$emit('open', $event)"/>
            <infinite-loading v-if="expanded" ref="infinite" :identifier="infiniteId" @infinite="loadMoreChildren">
                <div slot="spinner"><a-spin v-if="page !== 1" size="small" /></div>
                <div slot="no-more"></div>
                <div slot="no-results"></div>
            </infinite-loading>
        </div>
    </div>
</template>
  
<script>
import { errorHandler } from '@/utils/index.js'
export default {
    name: 'OrgNode',
    components: { 
        InfiniteLoading: () => import('vue-infinite-loading')
    },
    props: {
        node: { type: Object, required: true },
        loadChildren: { type: Function, required: true },
        pageSize: { type: Number, default: 20 },
        selectedOrgID: { type: [String, null], default: null }
    },
    data() {
        return {
            expanded: false,
            selected: false,
            loading: false,
            children: [],
            isLeaf: this.node.isLeaf,
            page: 1,
            hasMore: true,
            loadedOnce: false,
            infiniteId: 'node-' + Math.random().toString(36).substr(2, 9)
        }
    },
    methods: {
        toggleSelect() {
            this.selected = !this.selected
            this.$emit('select', { key: this.node.key, selected: this.selected })
        },
        toggleOpen() {
            this.expanded = !this.expanded
            if (this.expanded && !this.loadedOnce) {
                this.loading = true
                this.$nextTick(() => {
                    if (this.$refs.infinite) {
                        this.$refs.infinite.$emit('$InfiniteLoading:reset')
                    }
                })
            }
        },
        loadMoreChildren($state) {
            if (!this.expanded) {
                $state.complete()
                return
            }
            if (!this.hasMore) {
                $state.complete()
                return
            }
            this.loadChildren(this.node.key, this.page, this.pageSize)
                .then(res => {
                    this.children.push(...res.children)
                    this.hasMore = res.hasMore
                    this.isLeaf = res.isLeaf
                    this.page++
                    this.loadedOnce = true
                    this.loading = false
                    res.hasMore ? $state.loaded() : $state.complete()
                })
                .catch(error => {
                    errorHandler({error})
                    this.loading = false
                    $state.complete()
                })
        }
    }
}
</script>
  
<style lang="scss" scoped>
.org-node {
    margin: 6px 0;
}
.node-panel {
    display: flex;
    align-items: center;
    padding: 8px;
    border-radius: 8px;
    gap: 8px;
    &:hover{
        background: rgb(240, 241, 247, 1);
    }
    &:not(:last-child){
        margin-bottom: 4px;
    }
}
.arrow {
    width: 20px;
    font-size: 12px;
    text-align: center;
    cursor: pointer;
    transition: transform 0.15s;
}
.arrow.expanded {
    transform: rotate(90deg);
}
  .node-title {
    flex: 1;
    cursor: pointer;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 1.5;
    max-height: calc(2 * 1.5em);
    word-break: break-word;
}
.node-panel.selected {
    background: rgba(240, 241, 247, 1);
}
.children {
    margin-left: 28px;
    margin-top: 4px;
    transition: height 0.15s;
}
</style>
  