<template>
    <div class="form">
        <a-radio-group
            v-if="item.radio && item.radio.length"
            v-model="form[item.key]"
            class="w-full"
            @change="onChange"
            :class="isMobile || 'flex'">
            <div
                v-for="radio in item.radio"
                :key="radio.key"
                class="radio_item"
                :class="isMobile && 'radio_item_mobile'">
                <a-radio :value="radio.value">
                    {{ radio.name }}
                </a-radio>
            </div>
        </a-radio-group>
        <template v-if="item.fields && item.fields.length">
            <template v-for="field in item.fields">
                <template v-if="checkRoles(field) && checkDepends(field)">
                    <div
                        v-if="form[item.key] === field.requireRadio"
                        :key="field.key ? `${field.key}_${field.widget}` : field.widget"
                        class="del_item mt-4">
                        <FieldsSwitch
                            :field="field"
                            :edit="edit"
                            :setOrderFormCalculated="setOrderFormCalculated"
                            :isOrderDrawer="isOrderDrawer"
                            :form="form" />
                    </div>
                    <div
                        v-if="typeof field.requireRadio === 'undefined'"
                        :key="field.key ? `${field.key}_${field.widget}` : field.widget"
                        class="del_item mt-4">
                        <FieldsSwitch
                            :field="field"
                            :edit="edit"
                            :setOrderFormCalculated="setOrderFormCalculated"
                            :isOrderDrawer="isOrderDrawer"
                            :form="form" />
                    </div>
                </template>
            </template>
        </template>
    </div>
</template>

<script>
import FieldsSwitch from './fields/FieldsSwitch.vue'
export default {
    components: {
        FieldsSwitch
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        user() {
            return this.$store.state.user.user
        }
    },
    props: {
        item: {
            type: Object,
            required: true
        },
        form: {
            type: Object,
            required: true
        },
        edit: {
            type: Boolean,
            default: false
        },
        setOrderFormCalculated: {
            type: Function,
            default: () => {}
        },
        isOrderDrawer: {
            type: Boolean,
            default: false
        }
    },
    methods: {
        checkRoles(field) {
            if(field.checkRoles?.length) {
                let check = []

                field.checkRoles.forEach(item => {
                    if(this.user && this.user[item])
                        check.push(true)
                })

                if(check?.length)
                    return true

                return false
            } else
                return true
        },
        checkDepends(field) {
            if(field?.depends?.length) {
                let depArr = []
                field.depends.forEach(key => {
                    if(this.form[key])
                        depArr.push(true)
                })

                if(field.depends.length === depArr.length)
                    return true
                else
                    return false
            } else
                return true
        },
        onChange(e) {
            // if(this.edit)
            //     this.setOrderFormCalculated(false)
        }
    }
}
</script>

<style lang="scss" scoped>
.radio_item{
    &:not(:last-child){
        margin-right: 20px;
    }
}
.radio_item_mobile {
    &:not(:last-child){
        margin: 0;
        margin-bottom: 8px;
    }
}
</style>