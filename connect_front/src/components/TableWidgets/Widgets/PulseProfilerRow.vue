<template>
    <div class="h-full flex items-center cursor-pointer" @click="openHandler(record)">
        <Profiler 
            v-if="text"
            :avatarSize="22"
            nameClass="text-sm"
            hideSupportTag
            :user="text"
            :showUserName="showUserName" />
    </div>
</template>

<script>
export default {
    props: {
        text: {
            type: [Object, String]
        },
        record: {
            type: Object
        },
        column: {
            type: Object
        },
        openHandler: {
            type: Function,
            default: () => {}
        }  
    },
    computed: {
        showUserName() {
            return true
        }
    }

}
</script>