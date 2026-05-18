<template>
    <a-modal 
        :zIndex="3100"
        :width="800"
        v-model="modalVisible"
        destroyOnClose
        centered>
        <Comments v-if="modalVisible"  class="w-full mt-6" :related_object="recordId" />
        <template #footer />
    </a-modal>
</template>
<script>
export default{
    props: {
        value: [Boolean],
        recordId: [String],
    },
    components: {
        Comments: () => import('@apps/vue2CommentsComponent')
    },
    computed:{
        modalVisible: {
            get() {
                return  this.value
            },
            set(value){  this.$emit('input', value)}
        }
    },
   
}
</script>