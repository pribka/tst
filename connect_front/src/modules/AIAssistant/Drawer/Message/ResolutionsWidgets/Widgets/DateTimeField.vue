<template>
    <div>
        <a-date-picker 
            v-if="isEdit"
            v-model="value"
            class="w-full wdg_input"
            :format="format"
            :show-time="{ format: 'HH:mm' }"
            :getCalendarContainer="fieldContainer"
            inputType="ghost"
            @change="dateChange">
            <template #renderExtraFooter>
                <div class="dp-shortcuts mt-1" style="display:flex;flex-wrap:wrap;gap:6px;">
                    <a-button
                        v-for="item in quickShortcuts"
                        :key="item.key"
                        size="small"
                        type="ui"
                        :title="item.title"
                        @click="applyShortcut(item.key)">
                        {{ item.label }}
                    </a-button>
                </div>
            </template>
        </a-date-picker>
        <div v-else>
            <div v-if="value">
                {{ $moment(value).format('DD.MM.YYYY HH:mm') }}
            </div>
            <div v-else class="field_empty">
                {{ $t('ai_assistant.date_not_specified') }}
            </div>
        </div>
    </div>
</template>

<script>
import props from '../props.js'
import mixins from './mixins.js'
export default {
    props: {...props},
    mixins: [mixins],
    computed: {
        quickShortcuts() {
            const items = [
                { key: 'today', label: this.$t('ai_assistant.shortcut_today'), make: () => this.$moment() },
                { key: 'tomorrow', label: this.$t('ai_assistant.shortcut_tomorrow'), make: () => this.$moment().add(1, 'day') },
                { key: 'end_week', label: this.$t('ai_assistant.shortcut_end_week'), make: () => this.$moment().endOf('isoWeek') },
                { key: 'plus_week', label: this.$t('ai_assistant.shortcut_plus_week'), make: () => this.$moment().add(1, 'week') },
                { key: 'end_month', label: this.$t('ai_assistant.shortcut_end_month'), make: () => this.$moment().endOf('month') }
            ]
            return items.map(it => {
                const m = this.applyDefaultTime(it.make())
                const title = this.tooltipFormat(m)
                const disabled = this.checkDisabledDate(m)
                return { ...it, moment: m, title, disabled }
            })
        }
    },
    data() {
        return {
            value: null,
            format: "DD.MM.YYYY HH:mm",
            disabledBefore: null,
            disabledAfter: null
        }
    },
    created() {
        if(this.intents.resolutions?.[this.widgetKey]?.value) {
            this.value = this.$moment(this.intents.resolutions[this.widgetKey].value)
        }
    },
    methods: {
        checkDisabledDate(current) {
            const before = this.$moment(this.disabledBefore)
            const after = this.$moment(this.disabledAfter)
            if (before.isValid() && after.isValid()) {
                return !current.isBetween(before, after, 'day', '[]')
            }
            if (before.isValid()) {
                const endOfCurrentDay = this.$moment(current).endOf('day')
                return endOfCurrentDay.isBefore(before)
            }
            if (after.isValid()) {
                const startOfCurrentDay = this.$moment(current).startOf('day')
                return startOfCurrentDay.isAfter(after)
            }
            return false
        },
        applyShortcut(key) {
            const item = this.quickShortcuts.find(i => i.key === key)
            if (!item) return
            const m = item.moment
            const payload = this.normalizeForEmit(m)
            this.value = m
            this.dateChange(payload)
        },
        applyDefaultTime(baseMoment) {
            const m = this.$moment(baseMoment).clone()
            if (!this.showTime) {
                return m.startOf('day')
            }
            const def = this.showTimeOptions?.defaultValue || this.$moment('00:00:00', 'HH:mm:ss')
            return m.hour(def.hour()).minute(def.minute()).second(def.second())
        },
        tooltipFormat(m) {
            const fmt = this.showTime ? (this.dateFormat || 'DD.MM.YYYY HH:mm') : 'DD.MM.YYYY'
            return this.$moment(m).format(fmt)
        },
        normalizeForEmit(m) {
            if (typeof this.valueFormat === 'string' && this.valueFormat) {
                return m ? this.$moment(m).format(this.valueFormat) : null
            }
            return m
        }
    }
}
</script>

<style lang="scss" scoped>
.wdg_input{
    &::v-deep{
        .ant-input{
            height: initial;
            padding: 0px
        }
    }
}
</style>
