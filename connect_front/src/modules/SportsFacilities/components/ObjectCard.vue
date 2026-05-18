<template>
    <div class="object_card">
        <div class="object_card__head" @click="open = !open">
            <div class="card_row">
                <div class="card_row__label">
                    {{ $t('sports.objectName') }}
                </div>
                <div class="card_row__value">
                    {{ item.name }}
                </div>
            </div>
            <div class="card_row">
                <div class="card_row__label">
                    {{ $t('sports.purpose') }}
                </div>
                <div class="card_row__value">
                    {{ item.purpose_type.purpose.name }}
                </div>
            </div>
            <div v-if="item.purpose_type && item.purpose_type.building_type" class="card_row">
                <div class="card_row__label">
                    {{ $t('sports.roomType') }}
                </div>
                <div class="card_row__value">
                    {{ item.purpose_type && item.purpose_type.building_type ? item.purpose_type.building_type.name : '-' }}
                </div>
            </div>
            <div class="expand_btn" :class="open && 'expanded'">
                <i class="fi fi-rr-angle-small-down mr-2" />{{ open ? $t('sports.collapse') : $t('sports.expand') }}
            </div>
        </div>
        <div v-if="open" class="object_card__body">
            <div class="expand_list">
                <div v-for="info in getListData(item)" :key="info.id" class="expand_list__item">
                    <div class="item_row">
                        <div class="item_name">{{ info.name }}</div>
                        <div class="item_value">{{ info.value }}</div>
                    </div>
                </div>
            </div>
            <a-button 
                v-if="actions && actions.buildings_edit && actions.buildings_edit.availability"
                type="primary" 
                flaticon
                ghost
                block
                size="large"
                class="mr-1"
                icon="fi-rr-edit"
                @click="editHandler(item)">
                {{ $t('sports.edit') }}
            </a-button>
            <a-button 
                v-if="actions && actions.buildings_delete && actions.buildings_delete.availability"
                type="danger" 
                flaticon
                class="mt-2"
                ghost
                block
                size="large"
                icon="fi-rr-trash"
                @click="deleteHandler(item)">
                {{ $t('sports.delete') }}
            </a-button>
        </div>
    </div>
</template>

<script>
import { mapState } from 'vuex'
export default {
    props: {
        item: {
            type: Object,
            required: true
        },
        editHandler: {
            type: Function,
            default: () => {}
        },
        deleteHandler: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        ...mapState({
            actions: state => state.facilities.projectActions
        })
    },
    data() {
        return {
            open: false
        }
    },
    methods: {
        getListData(record) {
            const values = []
            for(const key in record) {
                if(key.includes("x_")) {
                    values.push({
                        ...record[key],
                        name: record[key].name || "-",
                        value: this.widgetValueData(record[key])
                    })
                }
            }
            return values
        },
        widgetValueData(record) {
            if(record.widgetType === 'Checkbox')
                return record.value ? this.$t('sports.yes') : this.$t('sports.no')
            if(!record.value)
                return '-'
            if(record.widgetType === 'ForeignKey') {
                if(Array.isArray(record.value)) {
                    if(!record.value?.length)
                        return '-'
                    return record.value.map(item => item.name).join(', ')
                } else {
                    return record.value.name
                }
            }
            return record.value
        }
    }
}
</script>

<style lang="scss" scoped>
.object_card{
    border: 1px solid #EBEBEB;
    border-radius: 8px;
    color: #000;
    &:not(:last-child){
        margin-bottom: 10px;
    }
    &__head{
        padding: 15px;
    }
    &__body{
        border-top: 1px solid #EBEBEB;
        padding: 15px;
        background: #f0f2f6;
    }
    .expand_btn{
        display: flex;
        align-items: center;
        margin-top: 5px;
        color: var(--blue);
        .fi{
            transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
        }
        &.expanded{
            .fi{
                transform: rotate(180deg);
            }
        }
    }
}
.card_row{
    &:not(:last-child){
        margin-bottom: 10px;
    }
    &__label{
        opacity: 0.6;
    }
}
.expand_list{
    &:not(:last-child){
        margin-bottom: 10px;
    }
    &__item{
        line-height: 18px;
        width: 100%;
        .item_name{
            opacity: 0.6;
        }
        .item_value{
            padding-top: 5px;
        }
        .item_row{
            padding: 10px 0;
            width: 100%;
        }
        &:not(:last-child){
            .item_row{
                border-bottom: 1px solid #c0c2c4;
            }
        }
    }
}
</style>