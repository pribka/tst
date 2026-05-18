<template>
    <div class="float_add">
        <div class="filter_slot">
            <PageFilter
                :model="pageModel"
                :key="pageName"
                size="large"
                :popoverMaxWidth="popoverMaxWidth"
                :page_name="pageName" />
        </div>
        <a-button
            shape="circle"
            size="large"
            class="mb-2"
            type="ui"
            icon="fi-rr-menu-burger"
            flaticon
            ghost
            @click="$emit('open-menu')" />
        <a-button
            v-if="showAdd"
            flaticon
            shape="circle"
            size="large"
            type="primary"
            :icon="addIcon"
            @click="$emit('create')" />
    </div>
</template>

<script>
export default {
    name: 'DirectoriesMobileFloatActions',
    components: {
        PageFilter: () => import('@/components/PageFilter')
    },
    props: {
        pageModel: {
            type: String,
            default: ''
        },
        pageName: {
            type: String,
            default: ''
        },
        showAdd: {
            type: Boolean,
            default: false
        },
        addIcon: {
            type: String,
            default: 'fi-rr-plus'
        },
        popoverMaxWidth: {
            type: Number,
            default: 400
        }
    }
}
</script>
