<template>
    <div class="time_list" ref="timeList">
        <div 
            v-if="columns.length" 
            class="grid_row grid_head" 
            :style="gridTemplate">
            <div 
                v-for="key in columns" 
                :key="`head_${key}`" 
                class="grid_cell head_cell">
                {{ key === 'actions' ? '' : itemCol[key] }}
            </div>
        </div>

        <div 
            v-for="item in timeList.results" 
            :key="item.id" 
            class="grid_row grid_body" 
            :style="gridTemplate">
            <div v-for="key in columns" :key="`cell_${item.id}_${key}`" class="grid_cell">
                <template v-if="key === 'work_type'">
                    <span v-if="item.work_type" :title="item.work_type.name">{{ item.work_type.name }}</span>
                    <span v-else>-</span>
                </template>

                <template v-else-if="key === 'description'">
                    <a-popover 
                        v-if="descLength(item.description)"
                        transitionName=""
                        :getPopupContainer="() => $refs.timeList">
                        <template slot="content">
                            <div style="max-width: 400px;">
                                {{ item.description }}
                            </div>
                        </template>
                        <span>{{ descSubstr(item.description) }}</span>
                    </a-popover>
                    <span v-else>{{ descSubstr(item.description) }}</span>
                </template>

                <template v-else-if="key === 'author'">
                    <Profiler hideSupportTag :avatarSize="23" :user="item.author" :getPopupContainer="() => $refs.timeList" />
                </template>

                <template v-else-if="key === 'user'">
                    <Profiler v-if="item.user" hideSupportTag :avatarSize="23" :user="item.user" :getPopupContainer="() => $refs.timeList" />
                </template>

                <template v-else-if="key === 'hours'">
                    <span v-if="item.measure_unit" :title="`${item.hours} ${item.measure_unit.name}`">
                        {{ item.hours }} {{ item.measure_unit.name }}
                    </span>
                    <span v-else :title="item.hours">
                        {{ item.hours }}
                    </span>
                </template>

                <template v-else-if="key === 'date'">
                    <span v-if="item.date" :title="$moment(item.date).format('DD.MM.YYYY')">{{ $moment(item.date).format('DD.MM.YYYY') }}</span>
                    <span v-else>-</span>
                </template>

                <template v-else-if="key === 'actions'">
                    <div class="grid_cell actions_wrap">
                        <div class="actions_cell">
                            <i 
                                v-if="item.is_result" 
                                class="fi fi-rr-checkbox text-green-500" 
                                v-tippy="{ inertia : true, duration : '[600,300]'}"
                                :content="$t('task.is_results')"
                                style="font-size: 16px;" />
                            <div v-else class="dummy_ico"></div>
                            <a-dropdown v-if="canAny(item)" :trigger="['click']" :getPopupContainer="() => $refs.timeList">
                                <a-button type="ui_ghost" flaticon shape="circle" icon="fi-rr-menu-dots-vertical" />
                                <a-menu slot="overlay">
                                    <a-menu-item v-if="canEdit(item)" class="flex items-center" @click="$emit('editTime', item)">
                                        <i class="fi fi-rr-edit mr-2" />
                                        {{ $t('task.edit') }}
                                    </a-menu-item>
                                    <template v-if="canDelete(item)">
                                        <a-menu-divider v-if="canEdit(item)" />
                                        <a-menu-item class="text_red flex items-center" @click="$emit('deleteTime', item)">
                                            <i class="fi fi-rr-trash mr-2" />
                                            {{ $t('task.remove') }}
                                        </a-menu-item>
                                    </template>
                                </a-menu>
                            </a-dropdown>
                        </div>
                    </div>
                </template>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        pageConfig: { type: Object, required: true },
        timeList: { type: Object, required: true },
        task: { type: Object, required: true },
        actions: { type: Object, default: () => null },
        isModerator: { type: Boolean, default: false }
    },
    computed: {
        user() {
            return this.$store.state.user.user
        },
        checkActions() {
            return this.actions?.delete_accounting?.availability || this.actions?.edit_accounting?.availability
        },
        itemCol() {
            const { tableInfo } = this.pageConfig || {}
            if (Array.isArray(tableInfo)) {
                const cols = Object.fromEntries(tableInfo.map(i => [i.field, i.headerName || i.field]))
                if (this.isModerator) {
                    const result = {}
                    for (const [k, v] of Object.entries(cols)) {
                        result[k] = v
                        if (k === 'author') result.user = this.$t('task.user')
                    }
                    return result
                }
                return cols
            }
            return {}
        },
        columns() {
            const supported = ['work_type','description','author','user','hours','date']
            const base = Object.keys(this.itemCol).filter(k => supported.includes(k))
            base.push('actions')
            return base
        },
        gridTemplate() {
            const weights = { description: 2, author: 1.2, user: 1.2, hours: 1, date: 1 }
            const parts = this.columns.map(k => {
                if (k === 'actions') return '104px'
                const w = weights[k] || 1
                return `minmax(0, ${w}fr)`
            })
            return `grid-template-columns: ${parts.join(' ')}`
        }
    },
    methods: {
        descSubstr(text) {
            if (text && text.length > 60) return text.substr(0, 60) + '...'
            return text
        },
        descLength(text) {
            return text && text.length > 60
        },
        isAuthor(item) {
            const u = this.$store.state.user.user
            return !!(u && item && item.author && u.id === item.author.id)
        },
        canEdit(item) {
            return this.isAuthor(item) || !!(this.actions?.edit_accounting?.availability)
        },
        canDelete(item) {
            return this.isAuthor(item) || !!(this.actions?.delete_accounting?.availability)
        },
        canAny(item) {
            return this.canEdit(item) || this.canDelete(item)
        }
    }
}
</script>

<style lang="scss" scoped>
.time_list {
  display: grid;
  grid-row-gap: 10px;
  width: 100%;
}

.grid_row {
  display: grid;
  align-items: center;
  column-gap: 16px;
  width: 100%;
  overflow: hidden; /* не даём содержимому вылезать за плашку */
}

.grid_head {
  padding: 0 8px;
  font-size: 13px;
  color: #8c8c8c;
}

.grid_body {
  position: relative;
}

.grid_body::before {
  content: '';
  position: absolute;
  inset: 0;
  background: #fafafa;
  border-radius: 8px;
}

.grid_head .grid_cell {
  padding: 8px 12px;
  font-weight: 500;
}

.grid_cell {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding: 5px 12px;
  position: relative;
  z-index: 1;
}

.actions_wrap {
  overflow: visible;
}

.actions_cell {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
}
.dummy_ico{
    min-width: 16px;
}
/* лёгкая адаптация: на узких экранах уменьшаем долю description,
   чтобы actions точно оставалась в видимой области */
@media (max-width: 900px) {
  .grid_row {
    column-gap: 12px;
  }
}
@media (max-width: 700px) {
  :root {
    --desc-fr: 1.5;
  }
}
</style>