<template>
    <div>
        <template v-if="record.sla">
            <div v-if="record.sla.from" class="text-xs" style="color: #888888;">
                Источник: {{ record.sla.from }}
            </div>
            <div class="flex items-center">
                <a-badge :color="record.sla.color" />
                {{ record.sla.name }}
            </div>
        </template>
    </div>
</template>

<script>
export default {
    props: {
        text: {
            type: [String, Number, Boolean, Object, Array]
        },
        record: {
            type: Object
        },
        model: {
            type: String
        },
        tableType: {
            type: String
        },
        column: {
            type: Object
        },
        openHandler: {
            type: Function,
            default: () => {}
        }    
    }
}
</script>