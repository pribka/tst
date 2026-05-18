import { isArray } from 'lodash'
import { formatsInMoments } from '@/utils/dateSettings'
import eventBus from '@/utils/eventBus'
let timeout;
export default {
    methods: {
        keydownSearchInput(e) {
            if(e.keyCode !== 8 && this.visible)
                this.visible = false

            clearTimeout(timeout)
            timeout = setTimeout(() => {
                this.setFilter(false)
            }, 700)
        },
        changeSearchInput(e) {
            const value = e.target.value
            this.$store.commit('filter/SET_FILTERS_SEARCH', {
                name: this.name,
                value
            })
        },
        // Выбор таба
        selectTab(tab) {
            this.activeTab = tab
        },
        // Скрол к элементу
        scrollTop() {
            if (this.scrollElements.length) {
                this.scrollElements.forEach(elem => {
                    let scrollElements = document.querySelectorAll(elem)
                    if (scrollElements.length)
                        scrollElements.forEach(scrollElem => scrollElem.scrollTop = 0)
                })
            } else
                document.body.scrollIntoView({ behavior: 'smooth', block: 'start' })
        },

        // Сбросить фильтры к исходному состоянию
        resetFilters() {
            this.filterIncludeData = null
            this.$store.commit('filter/RESET_ACTIVE_FILTER', this.name)
            this.tagGenerate()
            if (this.buttonsActive)
                this.setFilter()
        },

        // Очистить фильтры
        clearFilters() {
            if(this.isMobile) {
                this.$store.commit('filter/SET_FILTERS_SEARCH', {
                    name: this.name, 
                    value: ""
                })
            }
            this.filterIncludeData = null
            this.$store.commit('filter/CLEAR_ACTIVE_FILTER', this.name)
            this.tags = []
            if (this.buttonsActive)
                this.setFilter()
        },

        // Очистить фильтры и обновить таблицу
        removeFilters() {
            this.$store.commit('filter/SET_FILTERS_SEARCH', {
                name: this.name,
                value: ""
            })
            this.clearFilters()
            this.setFilter()
        },

        // Установка струтуры
        setFilterData() {
            this.filterInclude =
                this.$store.state.filter.filter[this.name]?.include ?
                    this.$store.state.filter.filter[this.name]?.include : []
            this.filterExclude = this.$store.state.filter.filter[this.name]?.exclude ?
                this.$store.state.filter.filter[this.name]?.exclude : []
        },


        // Генрация тегов
        async tagGenerate() {
            let tags = []
            let filtersTagsData = {...this.filterTags}
            if(this.filterIncludeData?.filterTags?.structure && Object.keys(this.filterIncludeData.filterTags.structure).length) {
                filtersTagsData = {
                    ...this.filterTags,
                    ...this.filterIncludeData.filterTags.structure
                }
            }
            if (filtersTagsData) {
                const filter = JSON.parse(JSON.stringify(filtersTagsData))
                //  Идем по тегам
                for (let prop in filter) {
                    // проверяем активен ли фильтр
                    if (this.activeFilters[prop]) {

                        let findFilter = this.filterInclude.find(f => f.name === prop)
                        if (findFilter === undefined) findFilter = this.filterExclude.find(f => f.name === prop)


                        if (['DateField', 'DateTimeField'].includes(findFilter.type)) {
                            if (filter[prop] && filter[prop].length) {
                                const start = filter[prop][0]
                                const end = filter[prop][1]
                                let val = ''

                                if (start && end) {
                                    val = this.prettyDate(start) + ' - ' + this.prettyDate(end)
                                } else if (start) {
                                    val = this.prettyDate(start)
                                } else if (end) {
                                    val = this.prettyDate(end)
                                }

                                tags.push({
                                    name: prop,
                                    field: 'date',
                                    value: val || 'null',
                                    verbose_name: findFilter.verbose_name
                                })
                            }
                        }

                        else if (['Integer', 'Decimal'].includes(findFilter.widget.type)) {
                            if (filter[prop]) {

                                let val = ''
                                if (filter[prop].length > 1 && filter[prop][0] && filter[prop][1])
                                    val = 'от ' + filter[prop][0] + ' до ' + filter[prop][1]
                                else if (filter[prop][0])
                                    val = '' + filter[prop][0]


                                if (val.length > 0)
                                    tags.push({
                                        name: prop,
                                        field: 'date',
                                        value: val,
                                        verbose_name: findFilter.verbose_name
                                    })
                            }

                        }



                        else if (['Input', "IsActiveField"].includes(findFilter.widget.type)) {

                            tags.push({
                                name: prop,
                                field: 'input',
                                value: '' + filter[prop],
                                verbose_name: findFilter.verbose_name
                            })

                        }

                        else {
                            if (isArray(filter[prop])) {

                                if (filter[prop].length) {
                                    tags.push({
                                        name: prop,
                                        field: 'array',
                                        value: filter[prop],
                                        verbose_name: findFilter.verbose_name
                                    })
                                } else {
                                    tags.push({
                                        name: prop,
                                        field: 'input',
                                        value: 'null',
                                        verbose_name: findFilter.verbose_name
                                    })
                                }


                            }
                        }

                    }
                }
                this.tags = tags
                if(this.filterIncludeData)
                    this.filterIncludeData = null
            }
        },
        prettyDate(date) {
            if(this.notCurrentYear(date))
                return this.$moment(date).format('lll')
            return this.$moment(date).format('D MMM HH:mm')
        },
        notCurrentYear(date) {
            const currentDate = this.$moment()
            const targetDate = this.$moment(date)
            const yearsDifference = targetDate.diff(currentDate, 'years')
            return Boolean(yearsDifference)
        },

        // Установить фильтры 
        setFilter(changeVisible = true) {
            eventBus.$emit('filter_is_set')
            try {
                this.searchLoading = true
                eventBus.$emit(`filter_start_${this.page_name}`)

                let sendData = {
                    key: this.model,
                    fields: {},
                    filterTags: {
                        structure: {},
                        data: []
                    }
                }

                Object.keys(this.selected).forEach(el => {
                    let findFilter = this.filterInclude.find(f => f.name === el)

                    if (findFilter === undefined) findFilter = this.filterExclude.find(f => f.name === el)


                    // Отключаем фильтры в которых нет значений
                    if (this.selected[el] === null || (isArray(this.selected[el]) && this.selected[el].length === 0)) {
                        this.$store.commit("filter/SET_ACTIVE_FILTERS", { name: this.name, filterName: el, value: false })
                    }


                    // Для полей с макс и мин
                    if (this.selected[el]?.start || this.selected[el]?.end) {
                        sendData.fields[el] = { values: {} }
                        sendData.fields[el].values = this.selected[el]
                        sendData.fields[el].active = this.$store.state.filter.filterActive[this.name][el]
                    }
                    else if (
                        this.selected[el] !== "Invalid date" ||
                        this.selected[el] === true ||
                        this.selected[el] === false
                    ) {
                        sendData.fields[el] = { values: {} }
                        let active = this.$store.state.filter.filterActive[this.name][el]
                        let value = this.selected[el]
                        if (isArray(this.selected[el]) && this.selected[el].length === 0 && active === true) {
                            value = [null]
                        }
                        sendData.fields[el].values = { value }
                        sendData.fields[el].active = active

                    }
                })
                this.mergeFilterIncludeData(sendData)
                this.tagGenerate()
                sendData.filterTags = {
                    structure: this.$store.state.filter.filterTags[this.name],
                    data: this.tags
                }
                sendData['page_name'] = this.page_name
                this.$store.dispatch('filter/sendFilters', sendData)

                if(changeVisible)
                    this.visible = false
            }
            catch (e) {
                console.error('Ошибка скорей всего что то с данными с бэка! Проверьте совпадают ли данные в activeFilters и include' + e)
            } finally {
                this.searchLoading = false
            }
        },

        mergeFilterIncludeData(sendData) {
            try {
                if (!this.filterIncludeData) return
                if (this.filterIncludeData.fields && Object.keys(this.filterIncludeData.fields).length)
                    sendData.fields = { ...sendData.fields, ...this.filterIncludeData.fields }

                if (this.filterIncludeData.others && Object.keys(this.filterIncludeData.others).length) {
                    sendData.others = sendData.others 
                        ? { ...sendData.others, ...this.filterIncludeData.others } 
                        : this.filterIncludeData.others
                }
                if (this.filterIncludeData.filterTags?.structure && 
                Object.keys(this.filterIncludeData.filterTags.structure).length) {
                    sendData.filterTags.structure = {
                        ...sendData.filterTags.structure,
                        ...this.filterIncludeData.filterTags.structure
                    }
                    for (const filterName in this.filterIncludeData.fields) {
                        const field = this.filterIncludeData.fields[filterName],
                            structure = this.filterIncludeData.filterTags.structure[filterName]
                        this.$store.commit("filter/SET_ACTIVE_FILTERS", {
                            name: this.page_name,
                            filterName,
                            value: field.active
                        })
                        this.$store.commit("filter/SET_SELECTED_FILTER", {
                            name: this.page_name,
                            filterName,
                            value: field.values.value
                        })
                        if (Array.isArray(structure)) {
                            this.$store.commit('filter/CLEAR_FILTER_TAG', {
                                name: this.page_name,
                                filterName
                            })

                            if (field.active) {
                                structure.forEach(value => {
                                    this.$store.commit('filter/INCLUDE_FILTER_TAG', {
                                        value,
                                        name: this.page_name,
                                        filterName
                                    })
                                })
                            }
                        } else {
                            this.$store.commit('filter/SET_FILTER_TAG', {
                                name: this.page_name,
                                filterName,
                                value: field.active ? structure : Array.isArray(structure) ? [] : ''
                            })
                        }
                    }
                }
            } catch(e) {
                console.log(e, 'mergeFilterIncludeData')
            }
        },
        // Генерация кол-во выбранных фильтров
        generateLength(is_exclude) {
            let filterProp
            if (is_exclude)
                filterProp = this.filterExclude
            else filterProp = this.filterInclude

            let length = 0

            filterProp.forEach(el => {
                if (this.$store.state.filter.filterActive[this.name][el.name] === true)
                    length++
            })

            return length

        },

        // Принудительная проверка исключения фильтров
        // checkExclude(excludeFilters) {
        //     this.$store.commit('filter/forceExclude', excludeFilters)
        // }


    },
}
