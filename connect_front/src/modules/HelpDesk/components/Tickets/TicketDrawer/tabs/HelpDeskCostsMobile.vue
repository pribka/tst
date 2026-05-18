<template>
    <div class="h-full flex flex-col">
        <MobileInfiniteList
            :identifier="page_name"
            :reloadKey="ticket.id"
            :emptyDescription="$t('calendar.no_data')"
            :url="buildUrl">

            <!-- ✅ СЛОТ: как рендерить один item -->
            <template #item="{ item, index }">
                <div class="cost_card">
                    <div class="cost_row">
                        <div class="cost_label">#</div>
                        <div class="cost_value">
                            {{ index + 1 }}
                        </div>
                    </div>
                    <div class="cost_row">
                        <div class="cost_label">Наименование</div>
                        <div class="cost_value">
                            {{ item?.name || '-' }}
                        </div>
                    </div>

                    <div class="cost_row">
                        <div class="cost_label">Код товара</div>
                        <div class="cost_value">
                            {{ item?.article_number || '-' }}
                        </div>
                    </div>

                    <div class="cost_row">
                        <div class="cost_label">Количество</div>
                        <div class="cost_value">
                            {{ (item?.quantity ?? '-') }}
                        </div>
                    </div>

                    <!-- (опционально) действия, если надо -->
                    <!--
                    <div class="cost_actions" v-if="actions">
                        <a-button
                            v-if="actions?.edit?.availability"
                            size="small"
                            type="ui"
                            ghost
                            icon="fi-rr-edit"
                            flaticon
                            @click="$emit('edit', item)" />

                        <a-button
                            v-if="actions?.delete?.availability"
                            size="small"
                            type="ui"
                            ghost
                            class="text-red-500"
                            icon="fi-rr-trash"
                            flaticon
                            @click="$emit('delete', item)" />
                    </div>
                    -->
                </div>
            </template>

        </MobileInfiniteList>
    </div>
</template>

<script>
export default {
    name: 'HelpDeskCostsMobile',
    props: {
        ticket: { type: Object, required: true },
        actions: { type: Object, required: true }
    },
    components: {
        MobileInfiniteList: () => import('../../../../components/MobileInfiniteList.vue'),
    },
    data() {
        return {
            page_name: 'help_desk.HelpDeskCostModel_page'
        }
    },
    methods: {
        buildUrl() {
            // ✅ DRF пагинация сама вернёт next, тут только первая страница
            // Если надо page_size/ordering — добавь в query:
            // `?owner=${id}&page_size=15&ordering=...`
            return `/help_desk/costs/?owner=${this.ticket.id}`
        }
    }
}
</script>

<style scoped>
.cost_card {
    border: 1px solid rgba(0,0,0,0.06);
    border-radius: 12px;
    padding: 12px;
    margin: 10px 0;
    background: #fff;
}

.cost_row {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    padding: 6px 0;
}

.cost_label {
    flex: 0 0 auto;
    font-size: 12px;
    color: #8b8b8b;
}

.cost_value {
    flex: 1 1 auto;
    text-align: right;
    font-size: 14px;
    color: #222;
    word-break: break-word;
}

.cost_actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    margin-top: 8px;
}
.cost_head {
    display: flex;
    justify-content: flex-start;
    margin-bottom: 8px;
}

.cost_num {
    font-size: 12px;
    color: #8b8b8b;
}
</style>
