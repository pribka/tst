<template>
    <div class="org-tree">
        <OrgNode
            v-for="node in roots"
            :key="node.key"
            :node="node"
            :load-children="loadChildren"
            :selectedOrgID="selectedOrgID"
            @select="onSelect"
            @expand="onExpand" />
        <infinite-loading ref="rootInfinite" @infinite="getRoot" :distance="10">
            <div slot="spinner"><a-spin size="small" /></div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
export default {
    name: 'OrgTree',
    components: {
        InfiniteLoading: () => import('vue-infinite-loading'),
        OrgNode: () => import('./OrgNode.vue')
    },
    props: {
        selectedOrgID: {
            type: [String, null],
            default: null
        }
    },
    data() {
        return {
            page: 0,
            loading: false,
            pageSize: 10,
            roots: []
        }
    },
    methods: {
        async getRoot($state = null) {
            if(!this.loading) {
                try {
                    this.loading = true
                    this.page = this.page + 1
                    let params = {
                        page_size: this.pageSize,
                        page: this.page,
                        display: 'root'
                    }
                    const { data } = await this.$http.get('users/my_organizations_short/', { params })
                    if(data && data.results && data.results.length)
                        this.roots.push(...data.results.map(org => {
                            return {
                                title: org.name,
                                key: org.id,
                                logo: org.logo,
                                isLeaf: org.structural_division_count ? false : true,
                                children: []
                            }
                        }))
                    if(data.next) {
                        if($state) 
                            $state.loaded()
                    } else {
                        if($state) 
                            $state.complete()
                    }
                } catch (error) {
                    errorHandler({error})
                } finally {
                    this.loading = false
                }
            } else {
                if($state) 
                    $state.complete()
            }
        },
        loadChildren(orgID, page, page_size) {
            let params = {
                page: page,
                page_size: page_size,
                display: 'tree',
                filters: {
                    contractor_relations__relation_type_id: "structural_division",
                    contractor_relations__contractor_parent_id: orgID
                }
            }
            return new Promise((resolve, reject) => {
                this.$http
                    .get('users/my_organizations_short/', { params })
                    .then(({ data }) => {
                        const result = {
                            children: data.results.map(org => ({
                                title: org.name,
                                key: org.id,
                                logo: org.logo,
                                isLeaf: org.structural_division_count ? false : true,
                                children: []
                            })),
                            hasMore: Boolean(data.next),
                            isLeaf: data.results.length === 0
                        }
                        resolve(result)
                    })
                    .catch(error => {
                        errorHandler({error})
                        reject(error)
                    })
            })
        },
        onExpand({ expanded, key }) {
            if (expanded) {
                this.loadChildren(key)
            }
        },
        onSelect({ selected, key }) {
            this.$emit('select', key)
        }
    }
}
</script>