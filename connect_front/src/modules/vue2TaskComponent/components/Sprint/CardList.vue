<template>
    <div>
        <a-card
            v-for="item in listSprints"
            :key="item.id" 
            class="sprint_item">
            <div 
                class="sprint_row flex justify-between w-full"
                @click="openSprint(item.id)">
                <div class="sprint_name font-semibold">
                    {{ item.name }}
                </div>
                <div class="sprint_status">
                    <SprintStatus :sprint="item" />
                </div>
            </div>
            <div 
                class="sprint_row flex justify-between w-full"
                @click="openSprint(item.id)">
                <div class="sprint_status">
                    {{ item.target }}
                </div>
                <div class="sprint_tasks">
                    <TasksCount :record="item" />
                </div>
            </div>
            <div class="sprint_row flex justify-between w-full font-semibold mt-4">
                <div class="sprint_created_label">
                    {{ $t('task.sprint_created_date') }}
                </div>
                <div class="sprint_finished_label">
                    {{ $t('task.sprint_finished_date') }}
                </div>
            </div>
            <div class="sprint_row flex justify-between w-full">
                <div class="sprint_created flex">
                    <DateWidget :date="item.created_at" noColor/> 
                </div>
                <div class="sprint_finished">
                    <DateWidget :date="item.finished_date" /> 
                </div>
            </div>
            <div class="sprint_row flex justify-end w-full mt-4">
                <ActionsMobile 
                    class="w-full"
                    :record="item" 
                    @edit="startEdit" 
                    @delete="deleteSprint(item.id)" 
                    @updateStatus="updateStatus"/>
            </div>
        </a-card>
        <infinite-loading 
            ref="infiniteLoading"
            :identifier="infiniteId"
            @infinite="getSprints"
            :distance="10">
            <div 
                slot="spinner"
                class="flex items-center justify-center inf_spinner">
                <a-spin />
            </div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
        <div 
            v-if="showEmpty" 
            class="pt-8">
            <a-empty>
                <template #description>
                    {{ $t('task.sprint_empty') }}
                </template>
            </a-empty>
        </div>
    </div>
</template>

<script>
import InfiniteLoading from 'vue-infinite-loading'

import TasksCount from './components/TasksCount.vue'
import SprintStatus from './components/SprintStatus.vue'
import DateWidget from './components/DateWidget.vue'
import ActionsMobile from './components/ActionsMobile.vue'

export default {
    props: {
        listSprints: {
            type: Array,
            requered: true
        },
        openSprint: {
            type: Function,
            default: () => {}
        },
        deleteSprint: {
            type: Function,
            default: () => {}
        },
        updateStatus: {
            type: Function,
            default: () => {}
        },
        startEdit: {
            type: Function,
            default: () => {}
        },
        filters: {
            type: Object,
            default: null
        },
        pageName: {
            type: String,
            default: "sprint_list"
        }
    },
    components: {
        InfiniteLoading,
        DateWidget,
        ActionsMobile,
        TasksCount, 
        SprintStatus, 
    },
    data() {
        return {
            showEmpty: false,
            infiniteId: new Date(),
            listLoading: false,
            page: 1,
            pageSize: 15,
            next: true
        }
    },
    methods: {
        async getSprints($state){
            try{
                if(!this.listLoading && this.next) {
                    this.listLoading = true

                    const { data } = await this.$http(`tasks/sprint/list/`, { 
                        params: { 
                            page_size: this.pageSize,
                            page: this.page,
                            page_name: this.pageName,
                            filters: this.filters
                        }
                    })
                    
                    if(data.results.length)
                        this.listSprints.push(...data.results)

                    if(data.next) {
                        this.page++
                        $state.loaded()
                    } else {
                        this.checkAndSetShowEmpty()
                        $state.complete()
                    }
                }
            }
            catch(e){
                console.error(e)
            }
            finally{
                this.listLoading = false
            }
        },
        checkAndSetShowEmpty() {
            if(!this.listSprints.length) 
                this.showEmpty = true
            else 
                this.showEmpty = false
        }    
    },
}
</script>

<style lang="scss" scoped>
    .sprint_row {
        &:not(:last-child) {
            margin-bottom: 4px;
        }
    }
    .sprint_item {
        &:not(:last-child) {
            margin-bottom: 15px;
        }
    }
</style>