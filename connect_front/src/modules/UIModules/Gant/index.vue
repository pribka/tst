<template>
    <div class="gant_cont" :class="!inject && 'gant_page'">
        <div class="toolbar flex items-center justify-between pb-2">
            <div v-if="inject" class="flex items-center">
                <a-button 
                    type="primary" 
                    class="mr-2"
                    size="large" 
                    @click="addTaskDrawer()">
                    {{ $t('gantt.add_task') }}
                </a-button>
                <PageFilter
                    :model="pageModel"
                    :key="page_name"
                    size="large"
                    :page_name="page_name" />
            </div>
            <div v-else>
                <a-range-picker
                    v-model="dateRange"
                    class="range_ghost"
                    :mask="{ mask: '00.00.0000', lazy: true, autofix: true }"
                    allowClear
                    :ranges="{
                        [$t('gantt.today')]: [$moment(), $moment()], 
                        [$t('gantt.currentMonth')]: [$moment().startOf('month'), $moment().endOf('month')],
                        [$t('gantt.currentQuarters')]: [$moment().startOf('quarter'), $moment().endOf('quarter')],
                        [$t('gantt.currentYear')]: [$moment().startOf('year'), $moment().endOf('year')]
                    }"
                    :locale="locale"
                    format="DD.MM.YYYY"
                    @change="onDateChange">
                    <template slot="suffixIcon">
                        <i class="fi fi-rr-calendar blue_color" />
                    </template>
                </a-range-picker>
            </div>
            <div class="flex items-center">
                <div class="flex items-center">
                    <a-slider 
                        v-model="zoomLevel"
                        :marks="marks" 
                        class="zoom_steps"
                        style="min-width: 120px;"
                        :min="0"
                        :max="4"
                        :tooltipVisible="false"
                        :step="null"
                        @afterChange="afterChange" />
                    <span class="ml-4" style="min-width: 70px;color:#000;">{{ zoomLevelName }}</span>
                </div>
                <div class="flex items-center">
                    <a-button 
                        type="ui_ghost" 
                        flaticon
                        :disabled="leftActive"
                        class="mr-1"
                        shape="circle"
                        icon="fi-rr-arrow-small-left"
                        @mouseenter="scrollLeft"
                        @mouseleave="clear"
                        @click="gantSetScroll('left')" />
                    <a-button 
                        type="ui_ghost" 
                        flaticon
                        :disabled="rightActive"
                        shape="circle"
                        icon="fi-rr-arrow-small-right"
                        @mouseenter="scrollRight"
                        @mouseleave="clear"
                        @click="gantSetScroll('right')" />
                </div>
                <a-button 
                    type="ui_ghost" 
                    flaticon
                    class="ml-1"
                    shape="circle"
                    v-tippy="{ inertia : true, duration : '[600,300]'}"
                    :content="$t('gantt.toggleAside')"
                    icon="fi-rr-sidebar"
                    @click="toggleGrid()" />
                <TableSetting @change="changeColumns">
                    <template #button>
                        <a-button 
                            type="ui_ghost" 
                            flaticon
                            class="ml-1"
                            shape="circle"
                            v-tippy="{ inertia : true, duration : '[600,300]'}"
                            :content="$t('Table settings')"
                            icon="fi-rr-settings" />
                    </template>
                </TableSetting>
            </div>
        </div>
        <a-spin 
            class="gant_spin" 
            :spinning="loading">
            <div 
                class="gant_wrapper"
                ref="gant" 
                :class="`zoom_level_${zoomLevel}`"
                style="width: 100%;" />
        </a-spin>
        <div class="flex justify-end pt-1">
            <a-pagination 
                :value="page" 
                class="pager_wrapper"
                :total="count" 
                :defaultPageSize="page_size"
                show-less-items
                @change="pageChange" />
        </div>
    </div>
</template>

<script>
import { Gantt } from "@dhx/trial-gantt"
import "@dhx/trial-gantt/codebase/dhtmlxgantt.css"
import props from './props.js'
import filters from './filters.js'
import { durationFormat, shortDurationFormat, marks, injectData } from './utils.js'
import eventBus from "@/utils/eventBus"
import { mapState } from 'vuex'
import { errorHandler } from '@/utils/index.js'
let stepTimer;
let widthTimer;
let dragTimer;
export default {
    mixins: [props, filters],
    components: {
        PageFilter: () => import('@/components/PageFilter'),
        TableSetting: () => import('./TableSetting')
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        zoomLevelName() {
            switch (this.zoomLevel) {
            /*case 0:
                return this.$t('gantt.hours')*/
            case 0:
                return this.$t('gantt.days')
            case 1:
                return this.$t('gantt.weeks')
            case 2:
                return this.$t('gantt.months')
            case 3:
                return this.$t('gantt.quarters')
            case 4:
                return this.$t('gantt.years')
            default:
                return this.$t('gantt.hours')
            }
        },
        isInject() {
            return this.inject ? '_INJECT' : ''
        }
    },
    data() {
        return {
            isDragging: false,
            saveScroll: null,
            page: 1,
            count: 0,
            kkLocale: null,
            leftActive: false,
            rightActive: false,
            gantList: {
                data: []
            },
            gantRef: null,
            gantt: null,
            loading: false,
            zoomLevel: 0,
            isGridVisible: true,
            gridWidth: 500,
            page_size: 20,
            scrollTimer: null,
            task_type: 'task,stage,milestone',
            marks,
            columns: [
                {
                    name:"text",
                    label: this.useProjects ? this.$t('gantt.projectTask') : this.$t('gantt.task'),
                    width:300,
                    tree: true,
                    sortable: false,
                    resize: true,
                    template: obj => {
                        if(obj.type === 'project')
                            return `<div class="wght_b">${obj.text}</div>`
                        else {
                            if(obj.type === 'stage')
                                return `<div class="wght_b">${obj.text}</div>`
                            return `${obj.text}`
                        }
                    }
                },
                {
                    name:"start_date",
                    label: `${this.$t('gantt.startDate')} - ${this.$t('gantt.endDate')}`,
                    align:"center",
                    resize: true,
                    sortable: false,
                    template: obj => {
                        return this.$moment(obj.start_date).format('DD.MM') + ' - ' + this.$moment(obj.end_date).format('DD.MM')
                    }
                },
                {
                    name:"duration",
                    label: this.$t('gantt.duration'),
                    align:"center",
                    sortable: false,
                    resize: true,
                    template: obj => {
                        if(obj.type === 'milestone')
                            return ''
                        return shortDurationFormat(obj.duration)
                        // return durationFormat(obj.duration)
                    
                    }
                },
                {
                    name:"progress",
                    label: this.$t('gantt.progress'),
                    align:"center",
                    sortable: false,
                    resize: true,
                    template: obj => {
                        if(obj.type === 'milestone' || obj.type === 'task')
                            return ''
                        return `${obj.progress || 0}%`
                    }
                },
                {
                    name:"result",
                    label: this.$t('Result'),
                    align:"center",
                    resize: true,
                    sortable: false,
                    template: obj => {
                        return obj.result || '-'
                    }
                }
            ]
        }
    },
    methods: {
        async applyGanttLocale(loc) {
            const lang = loc || this.$i18n?.locale || 'ru'
            if (lang === 'kk') {
                if (!this.kkLocale) {
                    const m = await import(/* webpackChunkName: "gantt-locale-kk" */ './lang/gantt.locale.kk.js')
                    this.kkLocale = m.default || m
                }
                this.gantt.i18n.setLocale(this.kkLocale)
            } else {
                this.gantt.i18n.setLocale('ru')
            }
            this.gantt.render()
        },
        statusUpdate({task, status}) {
            try {
                const gantTask = this.gantt.getTask(task.id)
                if(gantTask) {
                    const taskUpdate = {
                        status
                    }
                    Object.assign(gantTask, taskUpdate)
                    this.gantt.updateTask(gantTask.id)
                }
            } catch(error) {
                errorHandler({error, show: false})
            }
        },
        addTask(data) {
            try {
                if(!this.onlyTask && data.project) {
                    const task = this.gantt.getTask(data.project.id)
                    if(task) {
                        const projectUpdate = {
                            $has_child: true
                        }
                        Object.assign(task, projectUpdate)
                        this.gantt.updateTask(task.id)
                    }
                }
                if(data.parent) {
                    const task = this.gantt.getTask(data.parent.id)
                    if(task) {
                        const taskUpdate = {
                            $has_child: true
                        }
                        Object.assign(task, taskUpdate)
                        this.gantt.updateTask(task.id)
                    }
                }
                if(data.date_start_plan && data.dead_line) {
                    let taskAdd = false
                    const taskData = {
                        id: data.id,
                        text: data.counter ? `${data.name} - ${data.counter}` : data.name,
                        status: data.status,
                        operator: data.operator,
                        owner: data.owner,
                        project: data.project,
                        duration: data.duration,
                        start_date: this.$moment(data.date_start_plan).toDate(),
                        end_date: this.$moment(data.dead_line).toDate(),
                        type: data.task_type || 'task'
                    }
                    if(!this.inject) {
                        if(data.project)
                            taskData.parent = data.project.id
                    }
                    if(data.parent)
                        taskData.parent = data.parent.id
                    if(taskData.parent) {
                        const parentTask = this.gantt.getTask(taskData.parent)
                        if(parentTask?.$open || parentTask.loaded) {
                            taskAdd = true
                        }
                    } else 
                        taskAdd = true
                    if(taskAdd) {
                        this.gantt.clearAll()
                        this.gantList.data.push(taskData)
                        this.gantList.data.forEach(item => {
                            this.gantt.addTask(item)
                        })
                        this.calculateGanttRange()
                        this.markersInit()
                    }
                }
            } catch(error) {
                errorHandler({error})
            }
        },
        updateTask(data) {
            try {
                const task = this.gantt.getTask(data.id)
                if(task) {
                    const taskUpdate = {
                        text: `${data.name} - ${data.counter}`,
                        status: data.status,
                        operator: data.operator,
                        owner: data.owner,
                        duration: data.duration,
                        start_date: this.$moment(data.date_start_plan).toDate(),
                        end_date: this.$moment(data.dead_line).toDate(),
                    }
                    if(this.inject) {
                        taskUpdate.parent = data.parent?.id ? data.parent.id : 0
                        if(!data.project || data.project?.id !== this.related_object)
                            this.deleteTask(task)
                    }
                    const checkTask = this.gantt.getTask(data.id)
                    if(checkTask) {
                        Object.assign(task, taskUpdate)
                        this.gantt.updateTask(task.id)
                    }
                }
            } catch(error) {
                errorHandler({error})
            }
        },
        deleteTask(task) {
            try {
                const gantTask = this.gantt.getTask(task.id)
                if(gantTask) {
                    this.gantt.deleteTask(gantTask.id)
                    this.$nextTick(() => {
                        const index = this.gantList.data.findIndex(f => f.id === gantTask.id)
                        if(index !== -1)
                            this.gantList.data.splice(index, 1)
                        if(gantTask.parent) {
                            const parentTask = this.gantt.getTask(gantTask.parent)
                            if(parentTask) {
                                const childTask = this.gantList.data.filter(f => f.parent === parentTask.id)
                                if(!childTask.length) {
                                    const taskUpdate = {
                                        $has_child: false
                                    }
                                    Object.assign(parentTask, taskUpdate)
                                    this.gantt.updateTask(parentTask.id)
                                }
                            }
                        }
                    })
                }
            } catch(error) {
                errorHandler({error})
            }
        },
        markersInit() {
            if(this.showTodayMarker) {
                this.gantt.addMarker({
                    start_date: new Date(),
                    text: this.$t('gantt.today'),
                    css: "today-marker"
                })
            }
            if(this.useForceDatesMarks && this.forceStartDate && this.forceEndDate) {
                this.gantt.addMarker({
                    start_date: this.$moment(this.forceStartDate).toDate(),
                    text: this.$t('gantt.project_start'),
                    css: "start-marker deadline-marker"
                })
                this.gantt.addMarker({
                    start_date: this.$moment(this.forceEndDate).toDate(),
                    text: this.$t('gantt.project_end'),
                    css: "end-marker deadline-marker"
                })
            }
        },
        async changeTask(task) {
            try {
                const taskData = {
                    date_start_plan: this.$moment(task.start_date).format(),
                    dead_line: this.$moment(task.end_date).format()
                }
                const { data } = await this.$http.put(`/tasks/task/${task.id}/update/`, taskData)
                if(data) {
                    const uTask = this.gantt.getTask(data.id)
                    if(uTask) {
                        const taskUpdate = {
                            duration: data.duration
                        }
                        Object.assign(uTask, taskUpdate)
                        this.gantt.updateTask(uTask.id)
                    }
                }
            } catch(error) {
                const taskData = this.gantt.getTask(task.id)
                if(taskData) {
                    const taskUpdate = {
                        start_date: taskData.original_start_date,
                        end_date: taskData.original_end_date,
                        duration: taskData.original_duration
                    }
                    Object.assign(taskData, taskUpdate)
                    this.gantt.updateTask(taskData.id)
                }
                errorHandler({error})
            }
        },
        gantSetScroll(type) {
            const scrollState = this.gantt.getScrollState()
            if(type === 'left') {
                this.gantt.scrollTo(0, scrollState.y)
            }
            if(type === 'right') {
                const ganttContainer = this.gantt.$task
                this.gantt.scrollTo(ganttContainer.scrollWidth, scrollState.y)
            }
        },
        scrollLeft() {
            this.scrollTimer = setInterval(() => {
                const scrollState = this.gantt.getScrollState()
                const scrollSpeed = this.zoomLevel === 0 || this.zoomLevel === 1 ? 20 : 10
                this.gantt.scrollTo(scrollState.x-scrollSpeed, scrollState.y)
            }, 10)
        },
        scrollRight() {
            this.scrollTimer = setInterval(() => {
                const scrollState = this.gantt.getScrollState()
                const scrollSpeed = this.zoomLevel === 0 || this.zoomLevel === 1 ? 20 : 10
                this.gantt.scrollTo(scrollState.x+scrollSpeed, scrollState.y)
            }, 10)
        },
        clear() {
            clearInterval(this.scrollTimer)
        },
        addTaskDrawer() {
            //this.$store.commit('task/SET_TASK_DRAWER_ZINDEX', 1010)
            /*this.$store.dispatch('task/sidebarOpen', {
                ...this.formParams,
                task_type: 'task'
            })*/
            this.$store.commit('task/SET_PAGE_NAME', {
                pageName: this.page_name
            })
            eventBus.$emit('add_task_modal_watch', {type: 'add_task', data: this.formParams })
        },
        calculateGanttRange() {
            if (this.gantList.data?.length) {
                const minDate = this.$moment.min(
                    this.gantList.data.map(task => this.$moment(task.start_date))
                )
                const maxDate = this.$moment.max(
                    this.gantList.data.map(task => this.$moment(task.end_date))
                )
                this.gantt.config.start_date = minDate.add(-1, 'month').toDate()
                this.gantt.config.end_date = maxDate.add(2, 'month').toDate()
            }
            this.gantt.render()
        },
        pageChange(page) {
            this.page = page
            this.gantReload()
        },
        gantReload() {
            this.gantList = {
                data: []
            }
            this.gantt.clearAll()
            if(this.useProjects)
                this.getProjects()
            else
                this.getTasks()
        },
        setCurrentScroll() {
            if(this.saveScroll) {
                this.gantt.scrollTo(this.saveScroll.x, this.saveScroll.y)
                this.saveScroll = null
            }
        },
        async getChildTask(parent) {
            try {
                this.saveScroll = this.gantt.getScrollState()
                this.loading = true
                const params = {
                    page: 1,
                    page_size: 'all',
                    task_type: this.task_type
                }
                if(parent.type === 'project') {
                    params.parent = 'null'
                    params.filters = JSON.stringify({project: parent.id})
                } else
                    params.parent = parent.id
                if(this.related_object)
                    params.filters = JSON.stringify({project: this.related_object})
                const { data } = await this.$http.get('/tasks/tasks_chart_gantt_v2/list/', { params })
                if(data) {
                    this.gantList.data = this.gantList.data.concat(data.results.map(item => {
                        const taskItem = {
                            ...item,
                            ...injectData,
                            $has_child: item.has_child,
                            parent: parent.id,
                            text: item.counter ? `${item.text} - ${item.counter}` : item.text,
                            loaded: false,
                            progress: Number(item.progress) || 0,
                            duration: item.type === 'milestone' ? 0 : item.duration
                        }
                        if(item.type === 'milestone') {
                            delete taskItem.end_date
                            taskItem.$no_end = true
                        }
                        return taskItem
                    }))
                    this.gantt.clearAll()
                    this.gantList.data.forEach(item => {
                        this.gantt.addTask(item)
                    })
                    this.calculateGanttRange()
                    this.setCurrentScroll()
                    this.markersInit()
                }
                this.setInitStateScrollBtn()
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                this.loading = false
            }
        },
        async getTasks() {
            try {
                this.loading = true
                const params = {
                    page_name: this.page_name,
                    page: this.page,
                    page_size: this.page_size,
                    parent: 'all',
                    task_type: this.task_type
                }
                if(this.related_object)
                    params.filters = JSON.stringify({project: this.related_object})
                const { data } = await this.$http.get('/tasks/tasks_chart_gantt_v2/list/', { params })
                if(data) {
                    this.count = data.count
                    this.gantList.data = data.results.map(item => {
                        const taskItem = {
                            ...item,
                            ...injectData,
                            $has_child: item.has_child,
                            text: item.counter ? `${item.text} - ${item.counter}` : item.text,
                            loaded: false,
                            progress: Number(item.progress) || 0,
                            duration: item.type === 'milestone' ? 0 : item.duration
                        }
                        if(item.type === 'milestone') {
                            taskItem.$no_end = true
                            delete taskItem.end_date
                        }
                        return taskItem
                    })
                    //this.gantt.parse({...this.gantList})
                    this.gantList.data.forEach(item => {
                        this.gantt.addTask(item)
                    })
                    this.calculateGanttRange()
                    this.setGanttScale(this.zoomLevel)
                } else {
                    this.count = 0
                    this.gantList.data = []
                }
                this.setInitStateScrollBtn()
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                this.loading = false
            }
        },
        async getProjects() {
            try {
                this.loading = true
                const params = {
                    page_name: this.page_name,
                    is_project: 1,
                    page: this.page,
                    page_size: this.page_size,
                    task_type: this.task_type
                }
                const { data } = await this.$http.get('/work_groups/workgroups/gantt_chart/', { params })
                if(data) {
                    this.count = data.count
                    this.gantList.data = data.results.map(item => {
                        const taskItem = {
                            ...item,
                            ...injectData,
                            $has_child: item.has_child,
                            loaded: false,
                            progress: Number(item.progress) || 0,
                            duration: item.type === 'milestone' ? 0 : item.duration
                        }
                        if(item.type === 'milestone') {
                            taskItem.$no_end = true
                            delete taskItem.end_date
                        }
                        return taskItem
                    })
                    //this.gantt.parse({...this.gantList})
                    this.gantList.data.forEach(item => {
                        this.gantt.addTask(item)
                    })
                    this.calculateGanttRange()
                    this.setGanttScale(this.zoomLevel)
                } else {
                    this.count = 0
                    this.gantList.data = []
                }
                this.setInitStateScrollBtn()
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                this.loading = false
            }
        },
        saveLocalStorage() {
            const localConfig = JSON.parse(localStorage.getItem('gant_conf'))
            localStorage.setItem('gant_conf', JSON.stringify({
                ...localConfig,
                zoomLevel: this.zoomLevel,
                isGridVisible: this.isGridVisible,
                gridWidth: this.gridWidth
            }))
        },
        toggleGrid(init = false) {
            if(!init)
                this.isGridVisible = !this.isGridVisible

            if (this.isGridVisible)
                this.gantt.config.grid_width = 500
            else
                this.gantt.config.grid_width = 0

            this.gantt.render()
            this.saveLocalStorage()
        },
        afterChange(value) {
            clearTimeout(stepTimer)
            stepTimer = setTimeout(() => {
                this.setGanttScale(value)
            }, 500)
        },
        setGanttScale(level) {
            switch (level) {
            /*case 0: // Часы
                this.gantt.config.scale_unit = "day"
                this.gantt.config.date_scale = "%d %M"
                this.gantt.config.subscales = [
                    { unit: "hour", step: 1, date: "%H:%i" }
                ]
                break;*/
            case 0: // Дни
                this.gantt.config.scale_unit = "month"
                this.gantt.config.date_scale = "%F %Y"
                this.gantt.config.subscales = [
                    { unit: "day", step: 1, date: "%d" }
                ]
                break;
            case 1: // Недели
                this.gantt.config.scale_unit = "month"
                this.gantt.config.date_scale = "%F %Y"
                this.gantt.config.subscales = [
                    {
                        unit: "week", 
                        step: 1, 
                        date: (date) => {
                            const start = this.gantt.date.date_to_str("%d")(date)
                            const end = this.gantt.date.date_to_str("%d")(
                                this.gantt.date.add(date, 6, "day")
                            );
                            return `${start}-${end}`
                        }
                    }
                ];
                break;
            case 2: // Месяцы
                this.gantt.config.scale_unit = "year"
                this.gantt.config.date_scale = "%Y"
                this.gantt.config.subscales = [
                    { unit: "month", step: 1, date: "%M" }
                ]
                break;
            case 3: // Кварталы
                this.gantt.date.quarter_str = function (date) {
                    const quarter = Math.floor(date.getMonth() / 3) + 1
                    return `${quarter} квартал`
                }
                this.gantt.config.scale_unit = "year"
                this.gantt.config.date_scale = "%Y"
                this.gantt.config.subscales = [
                    { unit: "quarter", step: 1, date: this.gantt.date.quarter_str }
                ]
                this.gantt.render()
                break;
            case 4: // Годы
                this.gantt.config.scale_unit = "year"
                this.gantt.config.date_scale = "%Y"
                this.gantt.config.subscales = []
                break;
            }
            this.gantt.render()
            this.saveLocalStorage()
            this.setInitStateScrollBtn()
        },
        setInitStateScrollBtn() {
            this.$nextTick(() => {
                const scrollState = this.gantt.getScrollState()
                if(scrollState.x === 0)
                    this.leftActive = true
                const ganttContainer = this.gantt.$task
                const ganttWidth = ganttContainer.offsetWidth
                const totalWidth = ganttContainer.scrollWidth 
                if (scrollState.x + ganttWidth >= totalWidth)
                    this.rightActive = true
                else
                    this.rightActive = false
            })
        },
        // Получение видимого диапазона
        fetchVisibleData() {
            const state = this.gantt.getState()
            const visibleStartDate = state.min_date
            const visibleEndDate = state.max_date
            console.log(visibleStartDate, visibleEndDate)
        },
        hideGanttTooltip() {
            try {
      // 1) штатно закрываем тултип через API
      this.gantt?.ext?.tooltips?.tooltip?.hide?.()
            } catch (_) {}

            // 2) fallback: если узел «завис» — удалим его из DOM
            const el = document.querySelector('.gantt_tooltip')
            if (el && el.parentNode) el.parentNode.removeChild(el)
        },
        clickGridButton(taskId, action) {
            this.hideGanttTooltip()
            const gantgTask = this.gantt.getTask(taskId)
            //this.$store.commit('task/SET_TASK_DRAWER_ZINDEX', 1010)
            if(action === 'add') {
                if(gantgTask) {
                    if(gantgTask.type === 'project') {
                        /*this.$store.dispatch('task/sidebarOpen', {
                            project: {
                                name: gantgTask.text, 
                                id: gantgTask.id,
                                workgroup_logo: null,
                                date_start_plan: this.$moment(gantgTask.start_date).format(),
                                dead_line: this.$moment(gantgTask.end_date).format(),
                                workgroup_logo: gantgTask.workgroup_logo?.is_image ? gantgTask.workgroup_logo : null
                            },
                            task_type: 'task'
                        })*/
                        const taskObject = {
                            project: {
                                name: gantgTask.text, 
                                id: gantgTask.id,
                                date_start_plan: this.$moment(gantgTask.start_date).format(),
                                dead_line: this.$moment(gantgTask.end_date).format(),
                                workgroup_logo: gantgTask.workgroup_logo?.is_image ? gantgTask.workgroup_logo : null
                            }
                        }

                        this.$store.commit('task/SET_PAGE_NAME', {
                            pageName: this.page_name
                        })
                        eventBus.$emit('add_task_modal_watch', {type: 'add_task', data: taskObject })
                    } else {
                        const taskObject = {
                            parent: {
                                ...gantgTask,
                                name: gantgTask.text
                            },
                            dead_line: this.$moment(gantgTask.end_date).format(),
                            date_start_plan: this.$moment(gantgTask.start_date).format(),
                            task_type: 'task'
                        }
                        //eventBus.$emit('ADD_WATCH', {type: 'subtask', data: taskObject})
                        this.$store.commit('task/SET_PAGE_NAME', {
                            pageName: this.page_name
                        })
                        eventBus.$emit('add_task_modal_watch', {type: 'add_task', data: taskObject })
                    }
                }
            }
        },
        getTooltipTemplate(start,end,task){
            const getTaskType = type => {
                if(type === 'stage')
                    return this.$t('Stage')
                if(type === 'milestone')
                    return this.$t('Milestone')
                return this.$t('Task')
            }

            const textArray = [
                `<b>${getTaskType(task.type)}:</b><span class="break-words whitespace-normal">${task.text}</span>`,
                `<b>${this.$t('Start date')}:</b>${this.$moment(start).format('DD.MM')}`,
                `<b>${this.$t('Finish date')}:</b>${this.$moment(end).format('DD.MM')}`,
            ]
            if (task.task_type !== 'milestone') {
                const duration = durationFormat(task.duration)
                const textString = `<b>${this.$t('Duration')}:</b>${duration}`
                textArray.push(textString)
            }
            if (task.result) {
                const textString = `<b>${this.$t('Result')}:</b>${task.result}`
                textArray.splice(1, 0, textString)
            }
            return textArray.join('<br>')
        },
        changeColumns(selectedColumns) {
            const customizedFields = [
                'start_date',
                'duration',
                'progress',
                'result',
            ]
            this.gantt.config.columns = this.columns.reduce((columnList, column) => {
                if (!customizedFields.includes(column.name) 
                    || selectedColumns.includes(column.name)) {
                    return [...columnList, column]
                }
                return [...columnList]
            }, [])
            
            this.gantt.render()       
        },
        initColumns() {
            const localConfig = JSON.parse(localStorage.getItem('gant_conf'))
            if (localConfig?.selectedColumns) {
                this.changeColumns(localConfig.selectedColumns)
            }
        },
    },
    mounted() {
        this.gantRef = this.$refs.gant
        let clickTimeout = null

        let gantt = Gantt.getGanttInstance()
        gantt.i18n.setLocale(this.$i18n.locale || "ru")
        gantt.plugins({ 
            marker: true,		
            tooltip: true,
            drag_timeline: true
        })

        const config = JSON.parse(localStorage.getItem('gant_conf'))
        if(config) {
            this.zoomLevel = config.zoomLevel
            this.isGridVisible = config.isGridVisible
        }
        gantt.config.show_progress = this.useProgress
        gantt.config.show_links = this.useLinks
        gantt.config.drag_move = this.useEdit
        gantt.config.drag_resize = this.useEdit
        gantt.config.drag_progress = false
        gantt.config.drag_links = this.useEdit
        gantt.config.grid_resize = this.useGridResize
        gantt.config.grid_resizable_columns = true
        gantt.config.grid_drag_columns = true 
        gantt.config.scroll_size = this.scrollSize
        gantt.config.select_task = this.selectTask
        gantt.config.date_format = this.dateFormat
        gantt.config.xml_date = this.dateFormat
        gantt.config.date_grid = this.dateGrid
        gantt.config.task_date = this.taskDate
        gantt.config.time_picker = this.timePicker
        gantt.config.resize_rows = this.resizeRows
        gantt.config.show_date = true
        gantt.config.current_time = true
        gantt.config.scale_height = this.scaleHeight
        gantt.config.order_branch = false //this.orderBranch
        gantt.config.order_branch_free = this.orderBranch
        gantt.config.branch_loading = true
        gantt.config.sort = true
        gantt.config.duration_unit = this.durationUnit
        gantt.config.duration_step = this.durationStep
        gantt.config.autocalculate_duration = false
        gantt.config.autoset_dates = false
        gantt.config.fit_tasks = true
        gantt.assert = function () {}
        gantt.config.drag_mode.order = false
        gantt.config.show_tasks_outside_timescale = true
        gantt.config.smart_rendering = true
        //gantt.config.server_utc = true

        gantt.config.drag_timeline = {
            ignore:".gantt_task_line, .gantt_task_link",
            useKey: false
        }

        gantt.templates.tooltip_text = this.getTooltipTemplate
        gantt.attachEvent("onGanttReady", function(){
            const tooltips = gantt.ext.tooltips;
            tooltips.tooltip.setViewport(gantt.$task_data);
        });

        gantt.attachEvent("onTaskDblClick", id => {
            if(this.isDragging)
                this.isDragging = false
            const task = gantt.getTask(id)
            if(task) {
                const query = Object.assign({}, this.$route.query)
                if(task.type === 'project') {
                    query.viewProject = task.id
                    this.$router.push({query})
                } else {
                    if(query.task && Number(query.task) !== task.id || !query.task) {
                        query.task = task.id
                        this.$router.push({query})
                    }
                }
            }
            return true
        })

        gantt.attachEvent('onBeforeTaskDrag', (id, mode, e) => {
            if (mode === gantt.config.drag_mode.order) {
                return false
            }
            const task = gantt.getTask(id)
            if(task) {
                const taskUpdate = {
                    original_start_date: task.start_date,
                    original_end_date: task.end_date,
                    original_duration: task.duration
                }
                Object.assign(task, taskUpdate)
                gantt.updateTask(task.id)
            }
            if (task?.type === "project" || task?.type === "stage")
                return false
            if(task.operator.id !== this.user.id || task.owner.id !== this.user.id || task.project?.author?.id !== this.user.id)
                return false
            return !clickTimeout
        })
        gantt.attachEvent('onTaskDrag', (id, mode, task, original) => {
            this.isDragging = true

            if (mode === "resize") {
                const durationInMinutes = gantt.calculateDuration(task.start_date, task.end_date) * 60
                if (durationInMinutes < 10) {
                    task.start_date = original.start_date
                    task.end_date = gantt.addMinutes(original.start_date, 10)
                }
            }
            return true
        })

        gantt.addMinutes = (date, minutes) => {
            return new Date(date.getTime() + minutes * 60 * 1000)
        }

        gantt.attachEvent('onTaskDragEnd', () => {
            this.isDragging = false
        })

        gantt.attachEvent("onBeforeTaskChanged", function (id, mode, task) {
            if (mode === "resize") {
                const minDuration = 10 / 60 / 24;
                const newDuration = gantt.calculateDuration(task.start_date, task.end_date);

                if (newDuration < minDuration) {
                    gantt.message({ text: this.$t('gantt.taskMinTime'), type: "error" });
                    return false;
                }
            }
            return true;
        });

        gantt.attachEvent("onTaskOpened", id => {
            const task = gantt.getTask(id);
            if (task.$has_child && !task.loaded) {
                this.getChildTask(task)
                const index = this.gantList.data.findIndex(f => f.id === id)
                if(index !== -1)
                    this.$set(this.gantList.data[index], 'loaded', true)
            }
            return true
        })

        gantt.attachEvent("onBeforeTaskDisplay", function (id, task) {
            task.$calculate_duration = false
            task.$no_start = false
            task.$no_end = false
            return true
        });
        
        gantt.templates.scale_cell_class = (date) => {
            if (date.getDay() === 0 || date.getDay() === 6) {
                return "gantt-weekend"
            }
        }
        gantt.templates.timeline_cell_class = (item, date) => {
            if (date.getDay() === 0 || date.getDay() === 6) {
                return "gantt-weekend"
            }
        }
        gantt.templates.grid_header_class = function (columnName, column) {
            if (columnName === "add") {
                return "hide-add-button"
            }
            return ""
        }

        if(this.useEdit) {
            this.columns.push({
                name: "buttons",
                label: ``,
                align:"center",
                sortable: false,
                width: 40,
                template: () => {
                    return `
                        <i class="fi fi-rr-plus gantt_button_grid gantt_grid_add cursor-pointer" />
                    `
                }
            })
        }
        gantt.config.columns = this.columns

        gantt.config.row_height = 36;
        gantt.templates.task_text = function (start, end, task) {
            return task.text
        }

        gantt.templates.task_class = (start, end, task) => {
            if (task.type === 'task')
                return 'gantt-task-task'
            if (task.type === 'stage')
                return 'gantt-task-stage'
            return ''
        }

        gantt.templates.task_row_class = (start, end, task) => {
            if (task.type === "project" || task.type === "stage")
                return "gantt-row-bold"
            return ""
        }

        gantt.attachEvent("onGridHeaderClick", function() {
            return true
        })

        gantt.attachEvent("onTaskClick", (id, e) => {
            const target = e.target

            if (
                target.classList.contains("gantt_grid_edit") ||
                target.classList.contains("gantt_grid_add") ||
                target.classList.contains("gantt_grid_delete")
            ) {
                if (e.target.classList.contains("gantt_grid_add")) {
                    this.clickGridButton(id, "add")
                }
                e.preventDefault()
                return false
            }

            if (target?.classList.contains('gantt_tree_icon'))
                return true
            if (this.isDragging)
                return false

            if (clickTimeout) {
                clearTimeout(clickTimeout)
                clickTimeout = null
                return false
            }

            clickTimeout = setTimeout(() => {
                clickTimeout = null
            }, 300)

            return true
        })

        gantt.attachEvent("onBeforeRowDragMove", function(id, parent, tindex){
            console.log(id, parent, tindex, 'onBeforeRowDragMove')
            return true
        })

        gantt.attachEvent("onGridResize", (old_width, new_width) => {
            clearTimeout(widthTimer)
            widthTimer = setTimeout(() => {
                this.gridWidth = new_width
                this.saveLocalStorage()
            }, 400)
        })

        gantt.attachEvent("onAfterTaskMove", function(id, parent, tindex){
            clearTimeout(dragTimer)
            dragTimer = setTimeout(() => {
                // console.log("Task order to:", gantt.getTask(id))
            }, 800)
            return false
        })

        gantt.attachEvent("onAfterTaskDrag", (id, mode, e) => {
            const task = gantt.getTask(id)
            if(task) {
                if(mode === 'move' || mode === 'resize')
                    this.changeTask(task)
            }
        })

        gantt.attachEvent("onGanttScroll", (left, top) => {
            if(left === 0)
                this.leftActive = true
            else
                this.leftActive = false

            const ganttContainer = this.gantt.$task
            const ganttWidth = ganttContainer.offsetWidth
            const totalWidth = ganttContainer.scrollWidth 
            if (left + ganttWidth >= totalWidth)
                this.rightActive = true
            else
                this.rightActive = false
        })

        /*
        gantt.templates.timeline_cell_class = (task, date) => {
            if(this.forceStartDate && this.forceEndDate) {
                const startDate = this.$moment(this.forceStartDate)
                const endDate = this.$moment(this.forceEndDate)
                const currentDate = this.$moment(date)
                if (currentDate.isBetween(startDate, endDate, "minute", "[]"))
                    return "highlighted-range"
                return ""
            }
        }*/

        gantt.attachEvent("onBeforeLightbox", () => false)
        gantt.init(this.$refs.gant)
        this.gantt = gantt
        this.applyGanttLocale(this.$i18n?.locale)
        this.toggleGrid(true)
        this.setGanttScale(this.zoomLevel)
        this.markersInit()

        if(this.useProjects)
            this.getProjects()
        else
            this.getTasks()

        this.initColumns()

        eventBus.$on(`update_filter_${this.pageModel}_${this.page_name}`, () => {
            this.gantReload()
        })
        eventBus.$on('update_list_project', () => {
            this.gantReload()
        })
        eventBus.$on(`ADD_TASK_H${this.isInject}`, data => {
            this.addTask(data)
        })
        eventBus.$on(`UPDATE_TASK_H${this.isInject}`, data => {
            this.updateTask(data)
        })
        eventBus.$on(`STATUS_TASK_H${this.isInject}`, ({task, status}) => {
            this.statusUpdate({task, status})
        })
        eventBus.$on(`DELETE_TASK_H${this.isInject}`, task => {
            this.deleteTask(task)
        })
        eventBus.$on('project_deleted', id => {
            try {
                const task = this.gantt.getTask(id)
                if(task) {
                    this.gantt.deleteTask(task.id)
                    this.$nextTick(() => {
                        const index = this.gantList.data.findIndex(f => f.id === task.id)
                        if(index !== -1)
                            this.gantList.data.splice(index, 1)
                    })
                }
            } catch(e) {
                console.log(e)
            }
        })
    },
    beforeDestroy() {
        if (this.gantt) this.gantt.destructor()
        this.gantRef.innerHTML = ""
        this.gantRef = null
        this.gantt = null
        eventBus.$off(`update_filter_${this.pageModel}_${this.page_name}`)
        eventBus.$off('update_list_project')
        eventBus.$off(`UPDATE_TASK_H${this.isInject}`)
        eventBus.$off(`ADD_TASK_H${this.isInject}`)
        eventBus.$off(`STATUS_TASK_H${this.isInject}`)
        eventBus.$off(`DELETE_TASK_H${this.isInject}`)
        eventBus.$off('project_deleted')
    }
}
</script>

<style lang="scss" scoped>
.range_ghost{
    &::v-deep{
        .ant-input{
            border-color: #fff;
            .ant-calendar-range-picker-input{
                color: var(--text);
                &::placeholder{
                    color: #888888;
                }
            }
        }
    }
}
.gant_cont{
    display: flex;
    flex-direction: column;
    height: 100%;
    &.gant_page{
        padding: 20px;
    }
}
.gant_spin{
    min-height: 0;
    height: calc(100% - 68px);
    &::v-deep{
        .ant-spin-container{
            height: 100%;
        }
    }
}
.zoom_steps{
    margin: 0px;
    &::v-deep{
        .ant-slider-handle{
            border-color: var(--blue);
            background: var(--blue);
        }
        .ant-slider-rail{
            background-color: #ccc;
        }
        .ant-slider-step{
            .ant-slider-dot{
                border-color: #ccc;
            }
        }
        .ant-slider-track{
            display: none;
        }
    }
}
.gant_wrapper{
    height: 100%;
    &::v-deep{
        .wght_b{
            font-weight: 600;
        }
        .gantt_task_row,
        .gantt_row{
            &.gantt_selected{
                background-color: rgba(228, 230, 234, 0.3);
            }
        }
        .gantt_row{
            &:hover{
                background-color: rgba(228, 230, 234, 0.6);
            }
        }
        .gantt_layout_root{
            border-radius: 8px;
        }
        .hide-add-button {
            display: none !important;
        }
        .gantt_grid_head_cell{
            background: #f0f2f5;
        }
        .gantt_task_scale{
            .gantt_scale_cell{
                background: #f0f2f5;
            }
        }
        .highlighted-range {
            background-color: #f8fafc;
        }
        .gantt_task_line{
            &.gantt-task-task{
                border-radius: 30px;
                background: var(--blue);
            }
            &.gantt-task-stage{
                background: #7f86ab;
            }
        }
        .gantt_tree_icon.gantt_open:before, .gantt_tree_icon.gantt_close:before{
            font-family: 'icomoon' !important;
            speak: never;
            font-style: normal;
            font-weight: normal;
            font-variant: normal;
            text-transform: none;
            line-height: 1;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            font-size: 14px!important;
            height: 100%;
            display: flex;
            align-items: center;
        }
        .gantt_tree_icon.gantt_close:before{
            content: "\ee58";
        }
        .gantt_tree_icon.gantt_open:before{
            content: "\ee5a";
        }
        .gantt_task_drag{
            height: 27px;
            width: 12px;
            transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
            &::after{
                content: "";
                background: #fff;
                position: absolute;
                top: 6px;
                bottom: 5px;
                width: 3px;
                border-radius: 10px;
                opacity: 0.6;
                transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
            }
            &.task_left{
                left: 0px;
                &::after{
                    right: 2px;
                }
            }
            &.task_right{
                right: 0px;
                &::after{
                    left: 2px;
                }
            }
            &:hover{
                &::after{
                    opacity: 0.9;
                }
            }
        }
        .gantt-task-stage,
        .gantt_bar_project{
            .gantt_task_drag{
                display: none;
            }
            &.gantt_drag_move,
            &.gantt_selected{
                .gantt_task_content{
                    cursor: pointer;
                }
            }
        }
        .deadline-marker{
            background-color: #7e5ab8;
        }
        .gantt_marker{
            .gantt_marker_content{
                border-radius: 0 4px 4px 0;
            }
        }
        .deadline-marker{
            width: 0px;
            .gantt_marker_content{
                border-radius: 4px;
            }
        }
    }
    &.zoom_level_0{
        &::v-deep{
            .gantt-weekend {
                background-color: #f4f7fa;
            }
        }
    }
}
::v-deep {
    .gant_divider {
        width: 60%;
        margin: 4px auto;
        border-top: 1px solid #e6e6e6;
    }

    .gantt_grid_head_cell {
        align-content: center;
        line-height: 1;
    }
}
</style>

<style lang="scss">
.gantt_tooltip {
    z-index: 1000;
    max-width: 400px;
    text-wrap: auto;
}
</style>