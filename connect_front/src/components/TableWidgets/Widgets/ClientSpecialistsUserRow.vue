<template>
    <div :class="isEdit && 'cursor-pointer'" @click="editSpec()">
        <Profiler 
            v-if="text"
            :avatarSize="22"
            nameClass="text-sm"
            :user="text" />
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
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
        tableType: {
            type: String
        },
        colParams: {
            type: Object,
            default: () => null
        }
    },
    computed: {
        canChange() {
            return this.colParams.actions?.edit_specialist?.availability
        },
        isEdit() {
            return this.colParams?.actions?.edit?.availability
        }
    },
    methods: {
        editSpec() {
            if(this.isEdit && this.canChange)
                eventBus.$emit('edit_specialist_modal', this.record)
        }
    }
}
</script>