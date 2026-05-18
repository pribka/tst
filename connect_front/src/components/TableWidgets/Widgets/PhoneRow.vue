<template>
    <div :class="text ? 'text-current' : 'text-gray-300'">
        <template v-if="text">
            <!-- {{ text }} -->
            <a :href="'tel:' + text">{{ text }}</a>
        </template>
        <template v-else>
            Не указан
        </template>
    </div>
</template>

<script>
export default {
    props: {
        text: {
            type: String,
            default: ""
        },
    },
    data() {
        return {
            textColor: 'text-gray-300',
        }
    },
    methods: {
        // getDisplayText() {
        //     if(this.text) {
        //         this.textColor = 'text-current'
        //         return this.text
        //     }
        //     return 'Не указан'
        // },
    }
}
</script>