<!-- components/HolidayCalendarAdmin.vue -->
<template>
    <a-card>
        <div class="mb-3 legends">
            <span class="legend"><i class="dot dot--holiday"></i> Праздничный/выходной</span>
            <span class="legend"><i class="dot dot--workday"></i> Рабочий (перенос)</span>
            <span class="legend"><i class="dot dot--none"></i> Обычный день</span>
        </div>

        <a-calendar
            :value="calendarValue"
            :fullscreen="false"
            @panelChange="onPanelChange">
            <!-- Полная перерисовка ячейки -->
            <template slot="dateFullCellRender" slot-scope="current">
                <div
                    class="cell"
                    :class="cellClass(current)"
                    @click="openModal(current)"
                    :title="tooltipTitle(current)">
                    <div class="cell__num">{{ current.date() }}</div>
                    <div class="cell__mark" />
                </div>
            </template>
        </a-calendar>

        <a-modal
            :visible="modalVisible"
            :confirmLoading="saving"
            :title="modalTitle"
            @ok="applyKind"
            @cancel="closeModal"
            okText="Сохранить"
            cancelText="Отмена"
            :maskClosable="false">
            <a-radio-group v-model="dayType" class="w-full">
                <a-radio value="holiday">Праздничный/выходной</a-radio>
                <a-radio value="workday">Рабочий (перенос)</a-radio>
            </a-radio-group>

            <a-input v-model="form.title" class="mt-3" placeholder="Название (необязательно)" />
            <a-textarea v-model="form.description" class="mt-3" :rows="3" placeholder="Заметка (необязательно)" />

            <div class="mt-4">
                <a-button type="danger" :disabled="!hasMark(selectedISO)" :loading="saving" @click="clearDate">
                    Очистить метку
                </a-button>
            </div>
        </a-modal>
    </a-card>
</template>

<script>
import axios from '@/config/axios'
import moment from 'moment'
import 'moment/locale/ru'

moment.locale('ru')

export default {
    name: 'HolidayCalendarAdmin',
    data () {
        return {
            API: '/content_item_gos24',
            calendarValue: moment(),          // текущий месяц
            modalVisible: false,
            saving: false,
            picked: null,                     // moment выбранной даты

            // 'holiday' | 'workday'
            dayType: 'holiday',

            // Метаданные по датам
            // marks[iso] = 'holiday' | 'workday'
            marks: Object.create(null),
            // meta[iso] = { title, description }
            meta: Object.create(null),

            form: {
                title: '',
                description: ''
            }
        }
    },
    computed: {
        selectedISO () {
            return this.picked ? this.picked.format('YYYY-MM-DD') : ''
        },
        modalTitle () {
            return this.picked ? `Метка на ${this.picked.format('DD.MM.YYYY')}` : 'Метка'
        }
    },
    methods: {
        async loadMonth (d) {
            const start = d.clone().startOf('month').format('YYYY-MM-DD')
            const end   = d.clone().endOf('month').format('YYYY-MM-DD')

            const { data } = await axios.get(`${this.API}/calendar-finance-items/`, {
                params: { start, end },
                withCredentials: true
            })

            // Сброс
            this.marks = Object.create(null)
            this.meta  = Object.create(null)

            ;(data || []).forEach(it => {
                const iso = it.common_date
                if (iso && (it.content_type === 'holiday' || it.content_type === 'workday')) {
                    this.$set(this.marks, iso, it.content_type)
                    this.$set(this.meta, iso, { title: it.title || '', description: it.description || '' })
                }
            })
        },

        onPanelChange (value /* moment */, mode) {
            this.calendarValue = value
            this.loadMonth(value)
        },

        hasMark (iso) {
            return !!this.marks[iso]
        },

        cellClass (m /* moment */) {
            const iso = m.format('YYYY-MM-DD')
            const kind = this.marks[iso]
            if (kind === 'holiday') return 'cell--holiday'
            if (kind === 'workday') return 'cell--workday'
            return 'cell--none'
        },

        tooltipTitle (m) {
            const iso = m.format('YYYY-MM-DD')
            const kind = this.marks[iso]
            if (kind === 'holiday') return (this.meta[iso] && this.meta[iso].title) || 'Праздничный/выходной'
            if (kind === 'workday') return (this.meta[iso] && this.meta[iso].title) || 'Рабочий (перенос)'
            return 'Обычный день'
        },

        openModal (m /* moment */) {
            this.picked = m
            const iso = m.format('YYYY-MM-DD')
            this.dayType = this.marks[iso] || 'holiday'
            this.form.title = (this.meta[iso] && this.meta[iso].title) || ''
            this.form.description = (this.meta[iso] && this.meta[iso].description) || ''
            this.modalVisible = true
        },

        closeModal () {
            this.modalVisible = false
            this.picked = null
        },

        async applyKind () {
            if (!this.picked) return
            this.saving = true
            try {
                const iso = this.picked.format('YYYY-MM-DD')
                await axios.post(
                    `${this.API}/calendar-finance-items/upsert/`,
                    {
                        date: iso,
                        content_type: this.dayType,         // 'holiday' | 'workday'
                        title: this.form.title,
                        description: this.form.description
                    },
                    { withCredentials: true }
                )
                // локально обновим кэш
                this.$set(this.marks, iso, this.dayType)
                this.$set(this.meta, iso, { title: this.form.title, description: this.form.description })
            } finally {
                this.saving = false
                this.closeModal()
            }
        },

        async clearDate () {
            if (!this.picked) return
            this.saving = true
            try {
                const iso = this.picked.format('YYYY-MM-DD')
                await axios.delete(`${this.API}/calendar-finance-items/by_date/`, {
                    params: { date: iso },
                    withCredentials: true
                })
                this.$delete(this.marks, iso)
                this.$delete(this.meta, iso)
            } finally {
                this.saving = false
                this.closeModal()
            }
        }
    },
    mounted () {
        this.loadMonth(this.calendarValue)
    }
}
</script>

<style scoped>
.legends { display: flex; gap: 12px; flex-wrap: wrap; }
.legend { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; color: var(--placeholder-color, #666); }
.dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.dot--holiday { background: #ff4d4f; }
.dot--workday { background: #52c41a; }
.dot--none { background: #d9d9d9; }

.cell {
    position: relative;
    width: 100%;
    height: 46px;
    border-radius: 6px;
    cursor: pointer;
    padding: 4px 6px;
    transition: box-shadow .15s ease;
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
}
.cell:hover { box-shadow: 0 0 0 2px rgba(0,0,0,.06) inset; }

.cell__num { font-size: 13px; font-weight: 600; }
.cell__mark { width: 8px; height: 8px; border-radius: 50%; align-self: flex-end; margin-bottom: 2px; opacity: .9; }

.cell--holiday { background: rgba(255, 77, 79, .08); }
.cell--holiday .cell__mark { background: #ff4d4f; }

.cell--workday { background: rgba(82, 196, 26, .08); }
.cell--workday .cell__mark { background: #52c41a; }

.cell--none { background: transparent; }
.cell--none .cell__mark { background: transparent; }

.mt-3 { margin-top: 12px; }
.mt-4 { margin-top: 16px; }
.w-full { width: 100%; }
</style>
