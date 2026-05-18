<template>
    <div class="wrg_dates whitespace-nowrap">
        <template v-if="listProject">
            <template v-if="item.date_start_plan">
                {{$moment(item.date_start_plan).format('DD.MM.YYYY HH:mm')}}
            </template>
            <span 
                v-if="checkAllDates" 
                class="l">
                -
            </span>
            <template v-if="item.dead_line">
                {{$moment(item.dead_line).format('DD.MM.YYYY HH:mm')}}
            </template>
        </template>
        <template v-else>
            {{$moment(item.created_at).format('DD.MM.YYYY HH:mm')}}
        </template>
    </div>
</template>

<script>
export default {
    props: {
        item: {
            type: Object,
            required: true
        },
        listProject: {
            type: Boolean,
            default: true
        }
    },
    computed: {
        checkAllDates() {
            return this.item.dead_line && this.item.date_start_plan ? true : false
        }
    }
}
</script>

<style lang="scss" scoped>
.wrg_dates{
    font-size: 13px;
    .l{
        margin-left: 0.06rem;
        margin-right: 0.06rem;
    }
}
</style>