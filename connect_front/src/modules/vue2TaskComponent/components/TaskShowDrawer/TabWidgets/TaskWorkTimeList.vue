<template>
    <div class="time_list mobile_time_list" ref="timeMobileList">
        
        <div 
            v-for="item in timeList.results"
            :key="item.id"
            :style="`grid-template-columns: ${pageConfig.gridColumns};`"
            class="item">
            <div 
                v-for="col in pageConfig.tableInfo" 
                :key="col.field"
                :class="col.class ? col.class : ''"
                class="item_field">
                <template v-if="col.field === 'work_type'">
                    <template v-if="item.work_type">
                        <div class="item_field">
                            <span class="item_head">
                                {{ col.headerName }}:
                            </span>
                            <span>
                                {{ item.work_type.name }}
                            </span>
                        </div>
                    </template>
                </template>
                <template v-if="col.field === 'description'">
                    <div class="item_field">
                        <div v-if="item.description">
                            <span class="item_head">
                                {{ col.headerName }}:
                            </span>
                            <div class="mt-1">
                                <TextViewer 
                                    collapsible
                                    overlayColor="#fff"
                                    :body="item.description" />
                            </div>
                        </div>
                    </div>
                </template>
                <template v-if="col.field === 'is_result' && item.is_result">
                    <div class="item_field">
                        <div>
                            <span class="item_head">
                                {{ col.headerName }}:
                            </span>
                            <div class="mt-1">
                                <i class="fi fi-rr-check text-green-500" />
                            </div>
                        </div>
                    </div>
                </template>
                <template v-if="col.field === 'author'">
                    <div class="item_field flex items-center">
                        <span class="item_head mr-2">
                            {{ col.headerName }}:
                        </span>
                        <span>
                            <Profiler 
                                :user="item.author"
                                :avatarSize="18"
                                :getPopupContainer="() => $refs.timeMobileList"
                                hideSupportTag />
                        </span>
                    </div>
                    <template v-if="isModerator && item.user">
                        <div class="item_field flex items-center">
                            <span class="item_head mr-2">
                                {{ $t('task.user') }}:
                            </span>
                            <span>
                                <Profiler 
                                    :user="item.user"
                                    :avatarSize="18"
                                    :getPopupContainer="() => $refs.timeMobileList"
                                    hideSupportTag />
                            </span>
                        </div>
                    </template>
                </template>
                <template v-if="col.field === 'hours'" class="item_field">
                    <span class="item_head">
                        {{ col.headerName }}:
                    </span>
                    <span>
                        <template v-if="item.measure_unit">
                            {{ item.hours }} {{ item.measure_unit.name }}
                        </template>
                        <template v-else>
                            {{ item.hours }}
                        </template>
                    </span>
                </template>
                <template v-if="col.field === 'date'" class="item_field">
                    <template v-if="item.date">
                        <span class="item_head">
                            {{ col.headerName }}:
                        </span>
                        <span>
                            {{ $moment(item.date).format('DD.MM.YYYY') }}
                        </span>
                    </template>
                </template>
                <div v-if="col.field === 'actions'" class="item_field flex items-center gap-2 mt-4">
                    <template v-if="canAny(item)">
                        <a-button v-if="canEdit(item)" type="flat_primary" @click="$emit('editTime', item)" block>
                            {{ $t('task.edit') }}
                        </a-button>
                        <a-button v-if="canDelete(item)" type="flat_danger" @click="$emit('deleteTime', item)" block>
                            {{ $t('task.remove') }}
                        </a-button>
                    </template>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    components: {
        TextViewer: () => import('@apps/CKEditor/TextViewer.vue')
    },
    props: {
        pageConfig: {
            type: Object,
            required: true
        },
        timeList: {
            type: Object,
            required: true
        },
        task: {
            type: Object,
            required: true
        },
        isModerator: { type: Boolean, default: false }
    },
    computed: {
        user() {
            return this.$store.state.user.user
        },
    },
    methods: {
        getPopupContainer() {
            return document.querySelector('.work_time_form')
        },
        getPopupContainer2() {
            return document.querySelector('.task_body_wrap')
        },
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

<style lang="scss">
.mobile_time_list {
    .item {
        &:not(:last-child) {
            margin-bottom: 10px;
            padding-bottom: 10px;
            border-bottom: 1px solid var(--borderColor);
        }
    }
    .item_field {
        margin-bottom: 8px;
    }
    .item_head {
        margin-bottom: 0.3em;   
    }
}
</style>