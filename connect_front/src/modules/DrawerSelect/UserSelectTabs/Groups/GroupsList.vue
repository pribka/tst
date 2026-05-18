<template>
    <div class="groups-list">
        <GroupItem
            v-for="group in list"
            :key="group.id"
            :group="group"
            :selectedGroupID="selectedGroupID"
            @select="onSelect" />
        <infinite-loading ref="groupsInfinite" @infinite="getList" :distance="10">
            <div slot="spinner"><a-spin size="small" /></div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
export default {
    name: 'GroupsList',
    components: {
        InfiniteLoading: () => import('vue-infinite-loading'),
        GroupItem: () => import('./GroupItem.vue')
    },
    props: {
        selectedGroupID: {
            type: [String, null],
            default: null
        }
    },
    data() {
        return {
            page: 0,
            loading: false,
            list: [],
            pageSize: 10
        }
    },
    methods: {
        async getList($state = null) {
            if(!this.loading) {
                try {
                    this.loading = true
                    this.page = this.page + 1
                    let params = {
                        page_size: this.pageSize,
                        page: this.page,
                        is_project: 0
                    }
                    const { data } = await this.$http.get('work_groups/workgroups/list_short/', { params })
                    if(data && data.results && data.results.length)
                        this.list.push(...data.results)
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
        onSelect({ selected, key }) {
            this.$emit('select', key)
        }
    }
}
</script>