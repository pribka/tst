<template>
    <a-drawer
        :width="drawerWidth"
        class="sprint_show_drawer"
        :visible="visible"
        :closable="false"
        :zIndex="sprintDrawerZIndex"
        :afterVisibleChange="afterVisibleChange"
        @close="visible = false">
  
        <div  class="flex items-center justify-between -mt-2">
            <div
                v-if="sprint"
                class="text-base font-semibold truncate label">
                {{ $t('task.sprint_menu') }} {{sprint.name}}
            </div>
         
            <a-skeleton
                v-else
                active
                :paragraph="{ rows: 1 }" />
            <a-button
                type="link"
                class="ml-2 text-current"
                icon="close"
                @click="visible = false" />
         
        </div>  
        <a-divider class="mt-2 mb-2"></a-divider>
        <div 
            v-if="Object.keys(sprint).length && sprint.status !== 'completed'"
            class="flex h-full">
            <CardView  
                :sprint="sprint" 
                :allData="allData" 
                @change="changeS"/>
            <div 
                :key="kanbanKey" 
                class="kanban_container">
                <div 
                
                    class="kanban_wrapper" 
                    ref="kanbanWrapper">
                    <div  class="kanban-main" >
                        <span class="scroll_dummy"></span>
                        <div 
                            class="item-list mr-2 " 
                            :class="el.hide ? 'hide_item': ''" 
                            v-for="el in activeAllData" 
                            :key="el.name">
                            <div class="py-2 mx-2 px-3 flex justify-between items-center  item-title">
                                <div class="font-semibold flex items-center title-badge ">
                                    <div class="flex items-center">
                                        <a-badge :color="el.color" />
                                        <span> {{el.name2}}</span>
                                    </div>
                                    <span class="text-gray ml-2 count">
                                        <template v-if="el.loading">
                                            <a-spin size="small" />
                                        </template>
                                      
                                    </span>
                                </div>
                              
                            </div>

                            <div 
                                size="small" 
                                class="wrapper-item " 
                                :class="el.name ==='list' && 'list__filter'">
                             
                                <PageFilter 
                                    v-if="el.name === 'list'"
                                    :model="model" 
                                    width="800px"
                                    class="mb-2 ml-2"
                                    :zIndex="1300"
                                    :excludeFields="excludeFilters"
                                    :page_name ="pageName"/>
                                <div class="scroll_wrap">
                                    <div 
                                        class="p-2" 
                                        v-if="el.loading && el.page === 1">
                                        <a-skeleton 
                                            active 
                                            :paragraph="{ rows: 4 }" />
                                    </div>
                                    <draggable
                                        v-bind="dragOptions"
                                        class="list-group"
                                        :id="el.name"
                                        :list="el.list"
                                        group="tasks"
                                        @end="endDrag"
                                        draggable=".active_task"
                                        @change="changeItem">
                                    
                                        <KanbanItem
                                            v-for="(element) in el.list"
                                            :key="element.id"
                                            :active="activeItems"
                                            showStatus
                                            hideDeadline
                                            :myTaskEnabled="false"
                                            :item="element"
                                            @statusChanged="getTaskCount"/>
                                        <infinite-loading
                                            :distance="70"
                                            :identifier="el.name"
                                            :ref="`infinite_${el.name}`"
                                            @infinite="upScrollHandler(el.name, $event)">
                                            <div 
                                                slot="spinner" 
                                                class="pt-1">
                                                <a-spin v-if="el.list && el.list.length" />
                                            </div>
                                            <div slot="no-more"></div>
                                            <div slot="no-results"></div>
                                        </infinite-loading>
                                    </draggable>
                                </div>
                            </div>
                        </div>
                        <span class="scroll_dummy"></span>
                    </div>
                </div>
            </div>
        
        </div>

        <a-skeleton
            v-show="!!!report"
            active
            :paragraph="{ rows: 6 }" />
        <vueScroll :ops="opsScroll">
            <SprintReport v-if="report && sprint.status === 'completed'" :data="report" :sprint="sprint"/>
        </vueScroll>
    </a-drawer>
</template>

<script>
import { mapState } from 'vuex'
import vueScroll from 'vuescroll'
import actions from './actions'
import CardView from './CardView.vue'
import KanbanItem from '../Kanban/Item.vue'
import InfiniteLoading from 'vue-infinite-loading'
import draggable from "vuedraggable"
import PageFilter from '@/components/PageFilter'
import eventBus from '@/utils/eventBus'
import SprintReport from './SprintReport.vue'
export default {
    components: { CardView, KanbanItem, draggable, InfiniteLoading, PageFilter, SprintReport, vueScroll },
    mixins: [actions],
    data(){
        return {
            sprint: {},
            loading: false,
            loadingBtn: false,
            activeItems: true,
            pageSize: 10,
            report: null,
            opsScroll: {
                scrollPanel: {
                    scrollingX: false
                },
                vuescroll: {
                    mode: 'native',
                    locking: false
                },
                bar: {
                    background: "#ccc",
                    onlyShowBarOnScroll: false
                }
            },
            excludeFilters: ['sprint', 'status', 'dead_line'],
            model: "tasks.TaskModel",
            pageName: 'sprint_kanban_tasks.TaskMode',
            dragOptions: {
                animation: 200,
                ghostClass: "ghost"
            },
            kanbanKey: 2981,
            allData: [
                {
                    name: 'list',
                    name2: this.$t('task.backlog_menu'),
                    actionHidden: true,
                    next: false,
                    page: 1,
                    count: 0,
                    active: true,
                    hide: false,
                    loading: false,
                    color: 'blue',
                    list: []
                },
                {
                    name: 'sprint',
                    name2: this.$t('task.sprint_menu'),
                    color: 'purple',
                    next: false,
                    count: 0,
                    hide: false,
                    active: true,
                    page: 1,
                    loading: false,
                    list: []
                },
            ]
        }
    },
   
    computed: {
        ...mapState({
            user: state => state.user.user,
            windowWidth: state => state.windowWidth,
            sprintDrawerZIndex: state => state.task.sprintDrawerZIndex
        }),
        visible: {
            get() {
                return this.$store.state.task.sprintShow
            },
            set(val) {
                this.$store.commit('task/CHANGE_SPRINT_SHOW', val)
            }
        },
        drawerWidth() {
            if(this.windowWidth > 1300)
                return 1200
            else if(this.windowWidth < 1300 && this.windowWidth > 500)
                return this.windowWidth - 30
            else
                return this.windowWidth
        },
        id(){
            return this.$route.query.sprint
        },
        activeAllData(){
            return this.allData.filter(el=> el.active)
        },
       
        
    },
    watch: {
        '$route.name'() {
            this.visible = false
        },
        '$route.query'(val) {
            if(val.sprint) {
                if(this.sprint.id !== val.sprint)
                    this.openSprintDrawer()
            }
        },
        visible(val) {
            if(val) {
                this.getSprint()
               
            } else {
                this.close()
            }
        },
       
    },
    methods: {
        afterVisibleChange(vis) {
            if(!vis)
                this.$store.commit('task/SET_SPRINT_DRAWER_ZINDEX', 1000)
        },
        async getSprint() {
            try{ 
                this.loading = true
                this.kanbanKey ++
                const {data} = await this.$http(`tasks/sprint/${this.id}/`)
                this.sprint = JSON.parse(JSON.stringify(data))

                if(this.sprint.status !== 'new') {
                    let idx = this.allData.findIndex(el=> el.name === "list")
                    this.allData[idx].active = false
                }
                this.activeItems = data.status !== 'completed' ? true : false 
                if(data.status === 'completed') 
                    this.getReport()
            }
            catch(e){
                console.error(e)
            }
            finally{
                this.loading = false
            }
        },
        async getReport(){
            const {data} = await this.$http(`tasks/sprint/${this.id}/report/`)
            data['chartTasks'] = [data.completed_task_count, data.uncompleted_task_count, ]
            this.report = data
        },
        async getTasksList($state){
            try {
                const idx =  this.allData.findIndex(el=> el.name ==="list")
                this.allData[idx].loading = true              

                let params = {page_size: this.pageSize, page: this.allData[idx].page}

                params['page_name'] = this.pageName
                params['sprint'] = this.id
                
                const res =  await this.$http(`tasks/sprint/task/list/`, { params } )
                this.allData[idx].list = this.allData[idx].list.concat(res.data.results)
                this.allData[idx].count = res.data.count

                if(res.data.next) {
                    this.allData[idx].page += 1
                    this.allData[idx].next = true
                    if($state)
                        $state.loaded()
                    
                } else {
                    this.allData[idx].next = false
                    if($state)
                        $state.complete()
                }

                this.allData[idx].loading = false

            }
            catch(error){
                console.error(error)
                this.$message.error(this.$t('task.error') + error)
            }

        },
        async getTasksSprint($state){
            try {
                const idx = this.allData.findIndex(el=> el.name ==="sprint")
                this.allData[idx].loading = true              

                let params = {page_size: this.pageSize, page: this.allData[idx].page}

                const res =  await this.$http(`tasks/sprint/${this.id}/tasks_list/`, {params } )
                this.allData[idx].list = this.allData[idx].list.concat(res.data.results)
                this.allData[idx].count = res.data.count

                if(res.data.next) {
                    this.allData[idx].page += 1
                    this.allData[idx].next = true
                    if($state)
                        $state.loaded()
                    
                } else {
                    this.allData[idx].next = false
                    if($state)
                        $state.complete()
                }

                this.allData[idx].loading = false

            }
            catch(error){
                this.$message.error(this.$t('task.error') + error)
            }


        },
        upScrollHandler(status, $state){
            switch(status){
            case 'list':    this.getTasksList($state)
                break
            case 'sprint':  this.getTasksSprint($state)
                break
            }
        },
        close(){
            let query = Object.assign({}, this.$route.query)
            if(query.sprint) {
                delete query.sprint
                this.$router.push({query})
            }
            //this.sprint.id = null
            this.clear()
        },
        changeS(){
            if(this.sprint.status === "completed") this.getReport()
            const idx = this.allData.findIndex(el => el.name === 'list')
            this.allData[idx].active = false
         
        },
        async getTaskCount(){
            const {data} = await this.$http(`tasks/sprint/${this.sprint.id}/tasks_count/`)
            this.sprint = Object.assign(this.sprint, data)
            eventBus.$emit("sprint_update_table", JSON.parse(JSON.stringify(this.sprint)))
        },
       
        clear(){
            this.report = null
            this.allData = [
                {
                    name: 'list',
                    name2: this.$t('task.backlog_menu'),
                    actionHidden: true,
                    next: false,
                    page: 1,
                    count: 0,
                    active: true,
                    hide: false,
                    loading: false,
                    color: 'blue',
                    list: []
                },
                {
                    name: 'sprint',
                    name2: this.$t('task.sprint_menu'),
                    color: 'purple',
                    next: false,
                    count: 0,
                    active: true,
                    hide: false,
                    page: 1,
                    loading: false,
                    list: []
                },
            ]
        },
        openSprintDrawer() {
    
            this.clear()
            this.visible = true
            this.kanbanKey++
        
        },
        
        async changeItem(el){
            try{
                let element = null
                if(el.added) {
                    element = el.added.element
                    this.selectElement = element
                }
                if(el.moved) {
                    element = el.moved.element
                    this.selectElement = element
                }
            } catch(error) {
                console.log(error)
            }
        },
        async endDrag(el){
            try{
                setTimeout(async () => {
                    if(this.selectElement && (el.from.id !== el.to.id)){ 
                        const status = el.to.id === 'sprint' ? this.id : null,
                            current = this.selectElement.id
                           
                        await  this.$http.put(`/tasks/task/${current}/set_sprint/`,
                            { sprint: status })
                        await  this.getTaskCount()
                    }

                }, 100)
            }
            catch(error){
                this.$message.error(this.$t('task.error') + error)
            }
        }
    },
    created(){
        if(this.$route.query.sprint) {
            this.openSprintDrawer()
            this.getSprint()

        }
    },
    beforeDestroy(){
        eventBus.$off(`update_filter_${this.model}`)
    },  
    mounted(){
        eventBus.$on(`update_filter_${this.model}`, () => {
            this.clear()
            this.kanbanKey++
        })
    }
}
</script>

<style scoped lang="scss">

.sprint_drawer_body{
 
    .kanban_button{
        padding-left: 30px;
        padding-right: 30px;
        padding-top: 20px;
    }
    .flip-list-move {
        transition: transform 0.5s;
    }
    .no-move {
        transition: transform 0s;
    }
    .ghost{
        opacity: 0.5;
        background: #c8ebfb;
        &:not(:last-child){
            margin-bottom: 15px;
        }
    }
}
.scroll_wrap{
    padding-left: 7px;
    padding-right: 7px;
    height: 100%;
    margin-bottom: 50px;
    overflow-y: auto;
    overflow-x: hidden;
}
.kanban_wrapper{
    position: relative;
    padding-bottom: 5px;
    overflow-x: auto;
    overflow-y: hidden;
    display: flex;
    -webkit-overflow-scrolling: touch;
    overscroll-behavior-x: contain;
    flex-direction: column;
    --safe-area-inset-bottom: env(safe-area-inset-bottom);
    height: 100%;
    &::-webkit-scrollbar{
        height: 7px;
    }
    @media(min-width: 981px){
        scroll-padding: 40px;
    }
    @media(max-width: 980px){
        scroll-padding: 20px;
        scroll-snap-type: x mandatory;
    }
}
.kanban_container{
    flex-grow: 1;
    height: calc(100% - 36px);
}
.kanban-main{
    display: flex;
    flex-grow: 1;
    flex-direction: row;
    height: 100%;


.scroll_dummy{
    @media(min-width: 981px){
        min-width: 10px;
    }
    @media(max-width: 980px){
        min-width: 15px;
    }
}
.list-group{
    height: 100%;
    .scroll_wrap{
        padding-left: 7px;
        padding-right: 7px;
        padding-top: 7px;
        padding-bottom: 10px;
    }
}

.wrapper-item{
    height: calc(100% - 40px);
}

.item-list{
    min-width: 350px;
    max-width: 350px;
    height: 100%;
    scroll-snap-align: start;
    flex-grow: 0;
    background-color: #eff2f5;
    border-radius: var(--borderRadius);
    flex-shrink: 0;
    padding-bottom: 5px;
    overflow: hidden;
    .list__filter{
        height: calc(100% - 80px)
    }
    .block_btn{
        margin-right: -7px;
    }
}
}
</style>

<style lang="scss">
.sprint_show_drawer{ 
    .__bar-is-vertical{
        left: 8px !important;
    }
    .filter_clear{
        right: 16% !important;
        top: 0 !important;
    }
.filter_input{
    width: 84% !important;
    
}
}
.ant-drawer-body{
       overflow: hidden;
      
        height: 100%;
        padding-bottom: 40px;
   }

</style>