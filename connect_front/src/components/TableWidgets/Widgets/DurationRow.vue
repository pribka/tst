<template>
    <div>
        <i class="fi fi-rr-clock-three mr-1 text-xs"></i>
        {{ durationFormat(text) }}
    </div>
</template>

<script>
import { durationFormat } from '@apps/vue2MeetingComponent/utils/index'
export default {
    props: {
        text: {
            type: [Object, Boolean, String, Number]
        },
    },
    methods: {
        durationFormat,
        
        // dFormat(duration) {
        //     return durationFormat(duration)
        // },
    }
}
</script>