<template>
    <div class="h-full">
        <div 
            v-for="(time, index) in text" 
            :key="index" 
            class="time_block flex items-center">
            <Profiler
                :avatarSize="22"
                hideSupportTag
                nameWrapperClass="truncate"
                wrapperClass="truncate"
                nameClass="truncate"
                :user="time.user" />
        </div>
    </div>
</template>

<script>
export default {
    props: {
        text: {
            type: [Array]
        },
        record: {
            type: Object
        },
        column: {
            type: Object
        },
    },
    computed: {
    }

}
</script>


<style lang="scss" scoped>
.time_block{
    min-height: 45px;
    max-height: 45px;
    line-height: 15px;
    padding: 10px 0;
    &:not(:last-child){
        border-bottom: 1px solid #e8e8e8;
    }
    :deep span{
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
        word-break: break-word;
    }
}
</style>
