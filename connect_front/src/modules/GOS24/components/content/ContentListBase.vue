<!-- components/content/ContentListBase.vue -->
<template>
    <div class="items-grid">
        <div class="toolbar">
            <a-input-search
                v-model="search"
                placeholder="Поиск..."
                allowClear
                size="large"
                @search="onSearchSubmit"
                @change="onSearchChange"/>
            <a-button v-if="createEvent" type="primary" @click="createItem">Создать</a-button>
        </div>

        <a-alert v-if="error" type="error" :message="error" show-icon class="mb-16" />

        <a-table
            :loading="loading"
            :columns="columns"
            :dataSource="items"
            :rowKey="rowKey"
            :pagination="paginationConfig"
            :locale="{ emptyText: loading ? 'Загрузка...' : 'Нет данных' }"
            class="content-table">
            <!-- thumb -->
            <template v-if="imageField" slot="thumb" slot-scope="text, record">
                <img
                    v-if="record[imageField]"
                    :src="record[imageField]"
                    :alt="getTitle(record)"
                    class="thumb"/>
            </template>

            <!-- title -->
            <template slot="titleCol" slot-scope="text, record">
                <div class="tbl-title">{{ getTitle(record) }}</div>
                <div v-if="subtitleField && record[subtitleField]" class="tbl-sub">{{ record[subtitleField] }}</div>
            </template>

            <!-- actions -->
            <template slot="actionsCol" slot-scope="text, record">
                <a @click="openItem(record)">Редактировать</a>
                <a-divider type="vertical" />
                <a-popconfirm :title="deleteConfirmTitle" okType="danger" @confirm="deleteItem(record)">
                    <a class="danger">Удалить</a>
                </a-popconfirm>
                <!-- Доп. действия потребителя -->
                <slot name="actions" :item="record" />
            </template>
        </a-table>
    </div>
</template>

<script>
import axios from '@/config/axios'
import eventBus from '@/utils/eventBus'

const headerStyle = {
    backgroundColor: '#f0f1f6',
    color: '#1D1F23',
    fontWeight: 400,
    fontSize: '14px'
}


export default {
    name: 'ContentListBase',
    props: {
        // API & data
        apiUrl: { type: String, required: true }, // например: 'content_item_gos24/article/' (со слэшем в конце)
        deleteUrlBase: { type: String, default: '' }, // по умолчанию используется apiUrl
        idField: { type: String, default: 'id' },

        // отображение
        titleKeys: { type: Array, default: () => ['title', 'name'] },
        subtitleField: { type: String, default: '' }, // например: 'code'
        imageField: { type: String, default: '' }, // например: 'image'

        // сортировка и запрос
        ordering: { type: String, default: '-id' },
        pageSizeDefault: { type: Number, default: 12 },
        searchParam: { type: String, default: 'search' },

        // события шины
        refreshEvent: { type: String, default: '' }, // например: 'articles:refresh'
        createEvent: { type: String, default: '' },  // например: 'create_article_gos24'
        editEvent: { type: String, default: '' },    // например: 'edit_article_gos24'
        editPayloadType: { type: String, default: '' },

        // UI тексты
        deleteConfirmTitle: { type: String, default: 'Удалить запись?' },

        // (для совместимости — не используется в таблице)
        grid: {
            type: Object,
            default: () => ({ gutter: 16, xs: 1, sm: 2, md: 3, lg: 4, xl: 4, xxl: 6 })
        }
    },
    data () {
        return {
            items: [],
            total: 0,
            current: 1,
            pageSize: this.pageSizeDefault,
            loading: false,
            error: null,
            search: '',
            debounceTimer: null,
            lastRequestId: 0
        }
    },
    computed: {
        columns () {
            const cols = []
            if (this.imageField) {
                cols.push({
                    title: '',
                    dataIndex: this.imageField,
                    key: 'thumb',
                    width: 172,
                    align: 'center',
                    scopedSlots: { customRender: 'thumb' },
                    customHeaderCell: () => ({ style: headerStyle })
                })
            }
            cols.push({
                title: 'Название',
                key: 'title',
                scopedSlots: { customRender: 'titleCol' },
                customHeaderCell: () => ({ style: headerStyle })
            })
            // Если хотите отдельную колонку «Подзаголовок» (вместо второй строки) — раскомментируйте:
            // if (this.subtitleField) {
            //   cols.push({
            //     title: 'Подзаголовок',
            //     dataIndex: this.subtitleField,
            //     key: 'subtitle',
            //     ellipsis: true
            //   })
            // }
            cols.push({
                title: 'Действия',
                key: 'actions',
                width: 220,
                align: 'left',
                scopedSlots: { customRender: 'actionsCol' },
                customHeaderCell: () => ({ style: headerStyle })
            })
            return cols
        },
        paginationConfig () {
            return {
                total: this.total,
                current: this.current,
                pageSize: this.pageSize,
                showSizeChanger: true,
                pageSizeOptions: ['8', '12', '24', '48'],
                showTotal: (total) => `Всего: ${total}`,
                onChange: this.onPageChange,
                onShowSizeChange: this.onPageSizeChange,
                customHeaderCell: () => ({ style: headerStyle })
            }
        }
    },
    mounted () {
        this.fetchData()
        if (this.refreshEvent) eventBus.$on(this.refreshEvent, this.onExternalRefresh)
    },
    beforeDestroy () {
        if (this.refreshEvent) eventBus.$off(this.refreshEvent, this.onExternalRefresh)
        if (this.debounceTimer) clearTimeout(this.debounceTimer)
    },
    methods: {
        rowKey (record) {
            return record?.[this.idField]
        },
        // helpers
        getTitle (item) {
            for (const k of this.titleKeys) {
                if (item && item[k]) return item[k]
            }
            return 'Без названия'
        },

        // events
        createItem () {
            if (!this.createEvent) return
            eventBus.$emit(this.createEvent)
        },
        openItem (item) {
            if (!this.editEvent) return
            const id = item?.[this.idField]
            eventBus.$emit(this.editEvent, { id, type: this.editPayloadType || undefined })
        },

        // pagination / search
        onExternalRefresh () { this.fetchData() },
        onPageChange (page) { this.current = page; this.fetchData() },
        onPageSizeChange (current, size) { this.pageSize = size; this.current = 1; this.fetchData() },
        onSearchSubmit () {
            if (this.debounceTimer) clearTimeout(this.debounceTimer)
            this.current = 1
            this.fetchData()
        },
        onSearchChange () {
            if (this.debounceTimer) clearTimeout(this.debounceTimer)
            this.debounceTimer = setTimeout(() => { this.current = 1; this.fetchData() }, 400)
        },

        // server
        normalizeResponse (data) {
            if (Array.isArray(data)) return { results: data, count: data.length }
            if (data && Array.isArray(data.results)) return { results: data.results, count: data.count || data.total || 0 }
            if (data && Array.isArray(data.items)) return { results: data.items, count: data.total || data.items.length }
            return { results: data ? [data] : [], count: data ? 1 : 0 }
        },
        async deleteItem (item) {
            this.loading = true
            this.error = null
            try {
                const id = item?.[this.idField]
                const base = this.deleteUrlBase || this.apiUrl
                await axios.delete(`${base}${id}/`)
                this.$message.success('Удалено')
                if (this.items.length === 1 && this.current > 1) this.current -= 1
                this.fetchData()
            } catch (e) {
                const msg = (e?.response?.data?.detail || e?.response?.data?.message) || 'Ошибка удаления'
                this.$message.error(msg)
            } finally { this.loading = false }
        },
        async fetchData () {
            this.error = null
            this.loading = true
            const requestId = ++this.lastRequestId
            try {
                const params = {
                    page: this.current,
                    page_size: this.pageSize,
                    ordering: this.ordering
                }
                if (this.search) params[this.searchParam] = this.search

                const { data } = await axios.get(this.apiUrl, { params })
                if (requestId !== this.lastRequestId) return
                const normalized = this.normalizeResponse(data)
                this.items = normalized.results
                this.total = normalized.count
            } catch (err) {
                if (requestId !== this.lastRequestId) return
                this.error = 'Ошибка загрузки списка'
                // eslint-disable-next-line no-console
                console.log('err', err)
            } finally {
                if (requestId === this.lastRequestId) this.loading = false
            }
        }
    }
}
</script>

<style scoped>
.mb-16 { margin-bottom: 16px; }
.toolbar { display: flex; gap: 12px; align-items: center; margin-bottom: 12px; }
.danger { color: #ff4d4f; }

/* Таблица */

/* Колонки */
.thumb { width: 48px; height: 48px; object-fit: cover; border-radius: 4px; display: inline-block; }
.tbl-title { word-break: break-word; }
.tbl-sub { color: #888; font-size: 12px; margin-top: 2px; }

/* На всякий */
.items-grid { width: 100%; }

.ant-table-wrapper {
    border: 1px solid #E2E4E9;
    border-radius: 8px;
    overflow: hidden;
}
</style>
