<template>
    <a-select
        v-model="selectValue"
        inputType="ghost"
        class="w-full"
        :placeholder="item.verbose_name"
        :getPopupContainer="triggerNode => triggerNode.parentNode"
        :options="optionList"/>
</template>

<script>
export default {
    props: {
        item: {
            type: Object,
            required: true,
        },
        changeItemValue: {
            type: Function,
            required: true,
        },
    },
    computed: {
        optionList() {
            return this.item.choices.map(choice => ({ 
                value: choice[0],
                label: choice[1], 
            }))
        },
        selectValue: {
            get() {
                return this.item.value
            },
            set(value) {
                this.changeItemValue(value)
            }
        }
    },
    // methods: {
    //     selectChange(value) {
    //         this.changeItemValue(value)
    //     }
    // }
}
</script>
