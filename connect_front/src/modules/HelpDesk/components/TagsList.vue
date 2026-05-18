<template>
    <div class="tags_list">
        <template v-if="tags && tags.length">
            <a-tag 
                v-for="tag in tags" 
                :key="tag.id" 
                :useTextColor="false"
                :color="tag.color === 'default' ? '' : tag.color">
                {{ tag.name }}
            </a-tag>
        </template>
        <a-tag v-else>
            {{ $t('helpdesk.tags_not_specified') }}
        </a-tag>
    </div>
</template>

<script>
export default {
    props: {
        tags: {
            type: Array,
            default: () => []
        }
    }
}
</script>

<style lang="scss" scoped>
.tags_list{
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    &::v-deep{
        .ant-tag{
            display: flex;
            align-items: center;
            margin-bottom: 0px;
            margin-right: 0px;
        }
    }
}
</style>