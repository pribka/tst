<template>
    <component :is="tagWrapper" :class="[paragraph && 'hide_paragraph', titleFull && 'full_title']">
        <component :is="tagRow" v-for="(item, index) in skeletonRow" :key="index" :class="rowClass">
            <a-skeleton active :avatar="avatar" :paragraph="{ rows: paragraph }" />
        </component>
    </component>
</template>

<script>
export default {
    props: {
        paragraph: {
            type: Number,
            default: 1
        },
        avatar: {
            type: Boolean,
            default: false
        },
        hideParagraph: {
            type: Boolean,
            default: false
        },
        tagWrapper: {
            type: String,
            default: 'ul'
        },
        tagRow: {
            type: String,
            default: 'li'
        },
        rowClass: {
            type: String,
            default: ''
        },
        skeletonRow: {
            type: Number,
            default: 1
        },
        titleFull: {
            type: Boolean,
            default: false
        }
    }
}
</script>

<style lang="scss" scoped>
.hide_paragraph{
    &::v-deep{
        .ant-skeleton-paragraph{
            display: none;
        }
    }
}
.full_title{
    &::v-deep{
        .ant-skeleton-title{
            width: 100%!important;
        }
    }
}
</style>
