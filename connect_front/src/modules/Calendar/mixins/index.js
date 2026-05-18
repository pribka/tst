import FullCalendar from '@fullcalendar/vue'
import CalendarEvent from '../components/CalendarEvent.vue'
//import CalendarEventYear from '../components/CalendarEventYear.vue'
import CalendarEventList from '../components/CalendarEventList.vue'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import listPlugin from '@fullcalendar/list'
import momentPlugin from '@fullcalendar/moment'
import axios from 'axios'
import { setData, getById } from '../utils/indexedDb.js'
import eventBus from '@/utils/eventBus'
import { calendarConfig } from '../utils/index.js'
import { errorHandler } from '@/utils/index.js'

export default {
    components: {
        FullCalendar,
        CalendarEvent,
        CalendarEventList,
        //CalendarEventYear
    },
    props: {
        uKey: {
            type: [String, Number],
            default: 'default'
        },
        related_object: {
            type: [String, Number],
            default: null
        },
        addEventCheck: {
            type: Boolean,
            default: true
        },
        defaultType: {
            type: String,
            default: ''
        },
        page_name: {
            type: String,
            default: ''
        },
        startDate: {
            type: String,
            default: null
        },
        endDate: {
            type: String,
            default: null
        }
    },
    computed: {
        activeType() {
            if(this.defaultType.length)
                return this.defaultType
            else
                return this.$store.state.calendar.activeType
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        dayDrawerContainer() {
            if(this.related_object) {
                return () => document.body
            } else {
                return false
            }
        }
    },
    data() {
        return {
            calendarReady: false,
            events: [],
            showAside: true,
            todayCheck: true,
            calendarRequest: null,
            loading: false,
            configInit: true,
            configLoader: false,
            viewCache: '',
            relatedInfo: null,
            selectedDay: '',
            selectedDayRange: null,
            dayVisible: false,
            dayEvents: [],
            dyEventsEmpty: false,
            dayLoading: false,
            calendarOptions: {
                listDayFormat: 'dddd',
                listDaySideFormat: 'D MMMM YYYY',
                timeFormat: calendarConfig.timeFormat,
                events: [],
                plugins: [
                    momentPlugin,
                    dayGridPlugin,
                    timeGridPlugin,
                    interactionPlugin,
                    listPlugin
                ],
                selectAllow: select => {
                    const start = select.start;
                    const end = select.end;
                    if (this.$moment(start).format('Hms') === '000' && this.$moment(end).format('Hms') === '000') {
                        return true;
                    }
                    return this.$moment(start).format('Y-MM-DD') === this.$moment(end).format('Y-MM-DD');
                },
                views: {
                    listDay: {
                        dayHeaderContent: null,
                        listDayFormat: 'dddd',
                        listDaySideFormat: 'D MMMM YYYY'
                    },
                    listWeek: {
                        dayHeaderContent: null,
                        listDayFormat: 'dddd',
                        listDaySideFormat: 'D MMMM YYYY'
                    },
                    listMonth: {
                        dayHeaderContent: null,
                        listDayFormat: 'dddd',
                        listDaySideFormat: 'D MMMM YYYY'
                    },
                    timeGridWeek: {
                        dayHeaderFormat: { weekday: 'short', day: '2-digit', month: '2-digit' }
                    },
                    timeGridDay: {
                        dayHeaderFormat: { weekday: 'long' }
                    },
                    dayGridMonth: {
                        dayHeaderFormat: { weekday: 'short' }
                    },
                    day: {
                        dayHeaderFormat: { weekday: 'long', month: 'numeric', day: 'numeric', omitCommas: true }
                    }
                },
                nowIndicator: true,
                headerToolbar: false,
                dropAccept: '.drop-act',
                dayHeaderContent: this.fcDayHeader,
                titleFormat: this.fcTitle,
                minTime: calendarConfig.minTime,
                handleWindowResize: true,
                expandRows: true,
                eventLimit: true,
                maxTime: calendarConfig.maxTime,
                aspectRatio: 1.5,
                slotLabelFormat: {hour: 'numeric', minute: '2-digit', hour12: false},
                locale: null,
                locales: [],
                initialView: this.initView(),
                initialEvents: [],
                editable: true,
                selectable: true,
                resizable: true,
                droppable: true,
                selectMirror: true,
                height: '100%',
                dayMaxEvents: true,
                weekends: true,
                datesSet: this.datesSet,
                select: this.handleDateSelect,
                dateClick: this.dateClick,
                eventClick: this.handleEventClick,
                eventsSet: this.handleEvents,
                eventChange: this.eventChange,
                eventDrop: this.eventDrop,
                eventResize: this.eventResize
            }
        }
    },
    created() {
        this.loadLocale()
        this.getConfig()
    },
    methods: {
        removeFromLocalEvents(id) {
            const idStr = String(id)

            if (this.events?.length) {
                const idx = this.events.findIndex(e => String(e.id) === idStr)
                if (idx !== -1) this.events.splice(idx, 1)
            }

            if (this.dayEvents?.length) {
                const idx2 = this.dayEvents.findIndex(e => String(e.id) === idStr)
                if (idx2 !== -1) this.dayEvents.splice(idx2, 1)
                if (!this.dayEvents.length && this.dayVisible) this.dyEventsEmpty = true
            }

            this.calendarOptions.events = this.eventReplace(this.events)
        },
        initView() {
            if(this.defaultType?.length)
                return this.defaultType

            const localType = localStorage.getItem('cType')
            if(this.isMobile) {
                if(localType === 'multiMonthYear')
                    return 'timeGridDay'
                if(localType === 'dayGridMonth')
                    return 'timeGridDay'
                return localType || 'timeGridDay'
            } else
                return localType || 'dayGridMonth'
        },
        fcCap(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : s },
        fcDayHeader(arg) {
            const lang = this.$i18n?.locale || 'ru'
            const v = arg.view?.type || this.activeType
            const m = this.$moment(arg.date).locale(lang)

            if (v && v.startsWith('list')) return this.fcCap(m.format('dddd YYYY'))
            if (v === 'timeGridDay' || v === 'dayGridDay') return this.fcCap(m.format('dddd'))
            if (v === 'timeGridWeek' || v === 'dayGridWeek') return `${this.fcCap(m.format('dd'))} ${m.format('DD.MM')}`
            return this.fcCap(m.format('dd'))
        },
        fcTitle(rangeArg) {
            const lang = this.$i18n?.locale || 'ru'
            const v = this.$refs.fullCalendar?.getApi()?.view?.type || this.activeType
            const m = this.$moment
            if (v === 'dayGridMonth') return this.fcCap(m(rangeArg.start).locale(lang).format('MMMM YYYY'))
            if (v && v.includes('Week')) {
                const s = m(rangeArg.start).locale(lang)
                const e = m(rangeArg.end).add(-1, 'day').locale(lang)
                return `${s.format('D MMM')} — ${e.format('D MMM YYYY')}`
            }
            if (v === 'timeGridDay' || v === 'dayGridDay') return this.fcCap(m(rangeArg.start).locale(lang).format('dddd, D MMMM YYYY'))
            return this.fcCap(m(rangeArg.start).locale(lang).format('D MMMM YYYY'))
        },
        normLang(v) {
            const l = (v || 'ru').toLowerCase()
            if (l === 'kz' || l.startsWith('kk')) return 'kk'
            if (l.startsWith('ru')) return 'ru'
            return l
        },
        async loadLocale() {
            const raw = this.$i18n && this.$i18n.locale ? this.$i18n.locale : 'ru'
            const lang = this.normLang(raw)
            this.$moment.locale(lang)
            let mod
            try {
                mod = await import(`../lang/locales/${lang}`)
            } catch {
                mod = await import(`../lang/locales/ru`)
            }
            const fcLocale = mod.default || mod
            this.calendarOptions.locales = [fcLocale]
            this.calendarOptions.locale = lang
            await this.$nextTick()
            const api = this.$refs.fullCalendar && this.$refs.fullCalendar.getApi ? this.$refs.fullCalendar.getApi() : null
            if (api) {
                try {
                    api.setOption('locales', [fcLocale])
                    api.setOption('locale', lang)
                    api.setOption('listDayFormat', 'dddd')
                    api.setOption('listDaySideFormat', 'D MMMM YYYY')
                    api.updateSize()
                } catch (e) {
                    console.log(e)
                }
            }
            this.configInit = false
        },
        floatAddEvent() {
            eventBus.$emit('open_event_form', 
                null, 
                null, 
                null, 
                this.relatedInfo, 
                this.uKey,
                false,
                this.related_object)
        },
        afterVisibleChange(vis) {
            if(!vis) {
                this.selectedDay = ''
                this.selectedDayRange = null
                this.dayEvents = []
                this.dyEventsEmpty = false
            }
        },
        checkDayVisible() {
            if(this.dayVisible)
                this.dayVisible = false
        },
        changeAsideShow() {
            this.showAside = !this.showAside
            setTimeout(() => {
                this.$refs.fullCalendar.getApi().updateSize()
            }, 100)
        },
        async getCalendarId() {
            try {
                const { data } = await this.$http.get(`calendars/related/${this.related_object}/`)
                if(data) {
                    this.relatedInfo = data
                }
            } catch(error) {
                errorHandler({error, show: false})
            }
        },
        async getConfig() {
            try {
                this.configLoader = true
                const getByIdTimeout = (opts, ms = 3000) => Promise.race([
                    getById(opts),
                    new Promise((_, rej) => setTimeout(() => rej(new Error('getById timeout')), ms))
                ])
                let dbData
                try {
                    dbData = await getByIdTimeout({ id: 'calendar', databaseName: 'config' }, 3000)
                } catch (err) {
                    dbData = null
                }
                if (dbData?.value) {
                    this.calendarOptions.timeFormat = dbData.value.timeFormat || calendarConfig.timeFormat
                    this.calendarOptions.minTime = dbData.value.minTime || calendarConfig.minTime
                    this.calendarOptions.maxTime = dbData.value.maxTime || calendarConfig.maxTime
                    if (this.isMobile) {
                        this.calendarOptions.height = 'auto'
                        if (!this.defaultType || !this.defaultType.length)
                            this.calendarOptions.initialView = this.initView()
                    }
                    if (this.related_object)
                        await this.getCalendarId()
                    return
                }
                const { data } = await this.$http.get('/calendars/info/')
                await setData({
                    data: {
                        id: 'calendar',
                        value: data
                    },
                    databaseName: 'config'
                })
                this.calendarOptions.timeFormat = data.timeFormat || calendarConfig.timeFormat
                this.calendarOptions.minTime = data.minTime || calendarConfig.minTime
                this.calendarOptions.maxTime = data.maxTime || calendarConfig.maxTime
                if (this.isMobile) {
                    this.calendarOptions.height = 'auto'
                    if (!this.defaultType || !this.defaultType.length)
                        this.calendarOptions.initialView = this.initView()
                }
                if (this.related_object)
                    await this.getCalendarId()
            } catch (error) {
                errorHandler({error, show: false})
            } finally {
                this.configLoader = false
                if(this.isMobile && !this.defaultType?.length)
                    this.$refs.fullCalendar.getApi().changeView(this.initView())
            }
        },
        selectOneDay(date) {
            this.$refs.fullCalendar.getApi().gotoDate(date.toISOString())
            this.$store.commit('calendar/SET_ACTIVE_TYPE', 'timeGridDay')
            this.$refs.fullCalendar.getApi().changeView('timeGridDay')
        },
        async eventResize(event) {
            const key = `update_${event.event.id}`
            try {
                this.$message.loading({ content: this.$t('calendar.updating_event'), key })
                await this.$store.dispatch('calendar/changeEventDate', event)
            } catch(error) {
                errorHandler({error})
                event.revert()
            } finally {
                this.$message.success({ content: this.$t('calendar.event_updated'), key })
            }
        },
        datesSet(e) {
            const endStr = e.endStr
            const startStr = e.startStr

            this.todayCheck = this.$moment().isBetween(startStr, endStr)
            if (!this.calendarReady) {
                this.calendarReady = true
                this.viewCache = e.view.type
                this.getEventsType()
                return
            }

            if (this.viewCache !== e.view.type) {
                this.viewCache = e.view.type
                this.getEventsType()
            }
        },
        async eventDrop(event) {
            const key = `update_${event.event.id}`
            try {
                this.$message.loading({ content: this.$t('calendar.updating_event'), key })
                await this.$store.dispatch('calendar/changeEventDate', event)
                this.$message.success({ content: this.$t('calendar.event_updated'), key })
            } catch(error) {
                errorHandler({error})
                event.revert()
            }
        },
        eventChange(event) {
            // console.log(event, 'eventChange')
        },
        clearEvents() {
            this.events = []
            this.calendarOptions.events = []
        },
        async getEventsType(clear = true) {
            if(this.activeType !== 'multiMonthYear') {
                await this.getEvents(clear)
            } else {
                await this.getYearEvents()
            }
        },
        async getYearEvents() {
            try {
                this.loading = true
                const {start, end} = this.$refs.fullCalendar.getApi().currentData.dateProfile.activeRange,
                    startDate = this.$moment(start).add(-1, 'days').toISOString(),
                    endDate = this.$moment(end).toISOString()
                
                const params = {
                    start: startDate,
                    end: endDate,
                    ranges: true
                }

                if(this.related_object) {
                    params.related_object = this.related_object
                }

                const { data } = await this.$http.get('/calendars/events/', {
                    params
                })
                if(data) {
                    const eArray = data.map((item, index) => {
                        return {
                            ...item,
                            id: index,
                            start: this.$moment(item.start_at).format('YYYY-MM-DD'),
                            end: this.$moment(item.end_at).format('YYYY-MM-DD'),
                            diff: this.$moment(this.$moment(item.end_at).format('YYYY-MM-DD')).diff(this.$moment(item.start_at).format('YYYY-MM-DD'), 'days'),
                            color: '#000000',
                            editable: false,
                            allDay: true,
                            selectable: false,
                            resizable: false,
                            droppable: false
                        }
                    })

                    eArray.forEach((item, index) => {
                        const diff = this.$moment(item.end).diff(item.start, 'days')
                        if(diff > 1) {
                            let start = item.start,
                                end = item.end
                            for (let i = 0; i < diff; i++) {
                                eArray.push({
                                    ...item,
                                    id: `s_${i}_${index}`,
                                    start: start,
                                    end: this.$moment(start).format('YYYY-MM-DD'),
                                    color: '#000000',
                                    editable: false,
                                    allDay: true,
                                    added: true,
                                    selectable: false,
                                    resizable: false,
                                    droppable: false
                                })

                                start = this.$moment(start).add(1, 'days').format('YYYY-MM-DD')
                                end = this.$moment(start).add(1, 'days').format('YYYY-MM-DD')
                            }
                        }
                    })

                    eArray.forEach(item => {
                        const index = eArray.findIndex(f => this.$moment(f.start).isSame(item.start , 'day') && !f.added && f.id !== item.id)
                        if(index !== -1) {
                            eArray.splice(index, 1)
                        }
                    })

                    this.calendarOptions.events = eArray
                    this.events = eArray
                } else {
                    this.calendarOptions.events = []
                    this.events = []
                }
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                this.loading = false
            }
        },
        async getEvents(clear = true) {
            try {
                this.loading = true
                if(this.calendarRequest) {
                    this.calendarRequest.cancel()
                }

                const axiosSource = axios.CancelToken.source()
                this.calendarRequest = { cancel: axiosSource.cancel }

                let startDate, endDate
                
                if(this.startDate && this.endDate) {
                    startDate = this.startDate
                    endDate = this.endDate
                } else {
                    const {start, end} = this.$refs.fullCalendar.getApi().currentData.dateProfile.activeRange
                    startDate = this.$moment(start).add(-1, 'days').toISOString()
                    endDate = this.$moment(end).toISOString()
                }
                
                const params = {
                    start: startDate,
                    end: endDate
                }

                if(this.page_name)
                    params.page_name = this.page_name

                if(this.related_object) {
                    params.related_object = this.related_object
                }

                if(clear)
                    this.clearEvents()

                const { data } = await this.$http.get('/calendars/events/', {
                    cancelToken: axiosSource.token,
                    params
                })
                if(data) {
                    this.calendarOptions.events = this.eventReplace(data)
                    this.events = this.eventReplace(data)
                }
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                this.loading = false
            }
        },
        addCalendar() {
            this.$refs['aside'].addCalendarHandler()
        },
        changeDate(date) {
            this.$refs.fullCalendar.getApi().gotoDate(date.toISOString())
            this.getEventsType()
            this.checkDayVisible()
        },
        handleChangeType(event) {
            this.$nextTick(() => {
                const value = event.target.value
                this.$store.commit('calendar/SET_ACTIVE_TYPE', value)
                if(this.$refs?.fullCalendar)
                    this.$refs.fullCalendar.getApi().changeView(value)
                this.checkDayVisible()
            })
        },
        today(){
            if(!this.isMobile)
                this.$refs.aside.calendarDefault()

            this.$refs.fullCalendar.getApi().today()
            this.getEventsType()
            this.checkDayVisible()
        },
        antCalendarHeader() {
            return (
                <div></div>
            )
        },
        prev() {
            this.$refs.fullCalendar.getApi().prev()
            if(!this.isMobile) {
                this.$refs.aside.calendarDefault(this.$refs.fullCalendar.getApi().currentData.currentDate)
            }
            this.getEventsType()
            this.checkDayVisible()
        },
        next() {
            this.$refs.fullCalendar.getApi().next()
            if(!this.isMobile) {
                this.$refs.aside.calendarDefault(this.$refs.fullCalendar.getApi().currentData.currentDate)
            }
            this.getEventsType()
            this.checkDayVisible()
        },
        changeView(name) {
            this.activeType = name
            this.$refs.fullCalendar.getApi().changeView(name)
            this.checkDayVisible()
        },
        dateClick(selectInfo) {
            if(this.activeType === 'multiMonthYear' && this.isMobile) {
                this.selectedDayRange = {
                    start: this.$moment(selectInfo.dateStr).set('hour', 0).set('minute', 0).set('second', 0).set('millisecond', 0).toISOString(true),
                    end: this.$moment(selectInfo.dateStr).set('hour', 23).set('minute', 59).set('second', 59).set('millisecond', 59).toISOString(true)
                }

                this.selectedDay = this.$t('calendar.events_for_date', { date: this.$moment(selectInfo.dateStr).format('DD.MM.YYYY') })
                if(!this.dayVisible)
                    this.dayVisible = true
                
                this.getDayEvents()
            }
        },
        handleDateSelect(selectInfo) {
            if(this.activeType === 'multiMonthYear') {
                this.selectedDayRange = {
                    start: selectInfo.start,
                    end: selectInfo.end
                }
                this.selectedDay = this.$t('calendar.events_for_date', { date: this.$moment(selectInfo.startStr).format('DD.MM.YYYY') })
                if(!this.dayVisible)
                    this.dayVisible = true
                
                this.getDayEvents()
            } else {
                if(this.addEventCheck) {
                    eventBus.$emit('open_event_form', 
                        selectInfo.startStr, 
                        selectInfo.endStr, 
                        null, 
                        this.relatedInfo,
                        this.uKey,
                        false,
                        this.related_object)
                }
            }
        },
        async getDayEvents() {
            try {
                this.dayLoading = true
                this.dyEventsEmpty = false
                this.dayEvents = []
                const startDate = this.$moment(this.selectedDayRange.start).set('hour', 0).set('minute', 0).set('second', 0).set('millisecond', 0).toISOString(true),
                    endDate = this.$moment(this.selectedDayRange.start).set('hour', 23).set('minute', 59).set('second', 59).set('millisecond', 59).toISOString(true)

                const params = {
                    start: startDate,
                    end: endDate
                }
                if(this.related_object) {
                    params.related_object = this.related_object
                }

                const { data } = await this.$http.get('/calendars/events/', {params})
                if(data?.length) {
                    this.dayEvents = this.eventReplace(data)
                } else {
                    this.dyEventsEmpty = true
                }
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                this.dayLoading = false
            }
        },
        handleEventClick(clickInfo) {
            if(this.activeType === 'multiMonthYear') {
                const { event } = clickInfo
                const start = event.startStr

                this.selectedDayRange = {
                    start: this.$moment(start).set('hour', 0).set('minute', 0).set('second', 0),
                    end: this.$moment(start).set('hour', 23).set('minute', 59).set('second', 59)
                }

                this.selectedDay = this.$t('calendar.events_for_date', { date: this.$moment(start).format('DD.MM.YYYY') })
                if(!this.dayVisible)
                    this.dayVisible = true
                
                this.getDayEvents()
            } else {
                const { id } = clickInfo.event
                const query = JSON.parse(JSON.stringify(this.$route.query))
                if(query.event && Number(query.event) !== id || !query.event) {
                    query.event = id
                    this.$router.push({query})
                }
            }
        },
        handleEvents(events) {
            // console.log('change event')
            // console.log(events)
        },
        eventReplace(events) {
            return events.map(item => {
                return {
                    ...item,
                    title: item.name,
                    start: item.all_day ? this.$moment(item.start_at).format('YYYY-MM-DD') : item.start_at,
                    end: item.all_day ? this.$moment(item.end_at).add(1, 'day').format('YYYY-MM-DD') : item.end_at,
                    allDay: item.all_day,
                    extendedProps: {
                        ...item
                    }
                }
            })
        }
    },
    mounted() {
        eventBus.$on('events_reload', () => {
            this.getEventsType()
        })
        eventBus.$on('delete_event', id => {
            const api = this.$refs.fullCalendar.getApi()
            const event = api.getEventById(id)
            if (event) event.remove()
            this.removeFromLocalEvents(id)
        })
        eventBus.$on('edit_event', value => {
            if(this.events.length) {
                const index = this.events.findIndex(f => f.id === value.id)
                if(index !== -1) {
                    const event = this.$refs.fullCalendar.getApi().getEventById(value.id)
                    if(event) {
                        event.remove()
                    }
                    this.$set(this.events, index, value)
                    this.calendarOptions.events = this.eventReplace(this.events)
                }
            }
            if(this.dayEvents.length) {
                const index = this.dayEvents.findIndex(f => f.id === value.id)
                if(index !== -1) {
                    const rData = this.eventReplace([value])
                    this.$set(this.dayEvents, index, rData[0])
                }
            }
        })
        eventBus.$on(`add_event_${this.uKey}`, value => {
            this.$refs.fullCalendar.getApi().addEvent({
                ...value,
                allDay: value.all_day,
                title: value.name,
                start: value.all_day ? this.$moment(value.start_at).format('YYYY-MM-DD') : value.start_at,
                end: value.all_day ? this.$moment(value.end_at).add(1, 'day').format('YYYY-MM-DD') : value.end_at,
                extendedProps: {
                    ...value
                }
            })
            this.events.push({
                ...value,
                allDay: value.all_day,
                title: value.name,
                start: value.all_day ? this.$moment(value.start_at).format('YYYY-MM-DD') : value.start_at,
                end: value.all_day ? this.$moment(value.end_at).add(1, 'day').format('YYYY-MM-DD') : value.end_at,
                extendedProps: {
                    ...value
                }
            })
        })
    },
    beforeDestroy() {
        eventBus.$off(`add_event_${this.uKey}`)
        eventBus.$off('edit_event')
        eventBus.$off('delete_event')
        eventBus.$off('events_reload')
    }
}
