<template>
    <div class="card" @click="openDetailById(item.id)">
        <div class="mb-1 flex items-center">
            <p class="group_name">{{ item.name }}</p>
            <template v-if="!item.is_predefined">
                <a-button 
                    class="ml-2"
                    size="small"
                    type="ui"
                    
                    flaticon icon="fi-rr-edit" />
            </template>
        </div>
        <p v-if="item.description" class="mb-2">{{ item.description }}</p>
        <Members :item="item" :visibleCount="3" />
    </div>
</template>

<script>
export default {
    components: {
        Members: () => import('@/components/TableWidgets/components/Members.vue')
    },
    props: {
        item: {
            type: Object,
            required: true
        },
        openDetailById: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
        }
    }
}
</script>

<style lang="scss" scoped>
.group_name{
    font-weight: 600;
}
.card {
    padding: 15px;
    padding-top: 20px;
    border-radius: 6px;
    background-color: #EFF2F5;
    cursor: pointer;
}
</style>