<template>
    <div>
        <a-popover v-if="text.length" :title="$t('directories.comment')" destroyTooltipOnHide :getPopupContainer="getPopupContainer">
            <template slot="content">
                <div class="comment_wrapper">
                    <div v-html="text" />
                </div>
            </template>
            <a-button 
                type="ui" 
                ghost
                shape="circle"
                size="small"
                icon="fi-rr-comment-alt"
                flaticon />
        </a-popover>
        <div v-else style="color: #888;">
            {{ $t('directories.no_comment') }}
        </div>
    </div>
</template>

<script>
export default {
    props: {
        main: { // Если вставляем этот компонент куда то помимо страницы задач, тут надо ставить false
            type: Boolean,
            default: false
        },
        record: {
            type: Object,
            required: true
        },
        text: {
            type: [Object, Number, String],
        },
        colParams: {
            type: Object,
            default: () => null
        }
    },
    methods: {
        getPopupContainer() {
            return this.colParams.getPopupContainer()
        }
    }
}
</script>
