<template>
    <div class="invest_card">
        <div class="card_header">
            <div class="card_header__left truncate">
                <div class="date cursor-pointer" @click="openProject()">{{ $t('invest.plannedDeadline') }}: {{ $moment(item.dead_line).format('DD MMMM YYYY') }}г.</div>
                <h2 class="cursor-pointer truncate" @click="openProject()">{{ item.project_name }}</h2>
            </div>
            <div v-if="!isMobile" class="card_header__right">
                <a-button type="link" size="large" class="flex items-center" @click="openProject()">
                    {{ $t('invest.open') }}
                    <i class="fi fi-rr-arrow-up-right ml-3 text-xs"></i>
                </a-button>
            </div>
        </div>
        <div class="card_body">
            <div class="left">
                <div class="card_list">
                    <div v-if="item.date_start" class="card_list__item">
                        <div class="name">{{ $t('invest.startDate') }}:</div>
                        <div class="value">{{ $moment(item.date_start).format('DD MMMM YYYY') }}</div>
                    </div>
                    <div v-if="item.category" class="card_list__item">
                        <div class="name">{{ $t('invest.category') }}:</div>
                        <div class="value">{{ item.category.name }}</div>
                    </div>
                    <div v-if="item.subcategory" class="card_list__item">
                        <div class="name">{{ $t('invest.subcategory') }}:</div>
                        <div class="value">{{ item.subcategory.name }}</div>
                    </div>
                    <div class="card_list__item">
                        <div class="name">{{ $t('invest.cadasterNumber') }}:</div>
                        <div class="value">{{ item.cadaster }}</div>
                    </div>
                    <div v-if="item.company_director_name" class="card_list__item">
                        <div class="name">{{ $t('invest.director') }}:</div>
                        <div class="value">{{ item.company_director_name }}</div>
                    </div>
                    <div v-if="item.company_phone" class="card_list__item">
                        <div class="name">{{ $t('invest.phone') }}:</div>
                        <div class="value"><a :href="`tel:${item.company_phone}`">{{ item.company_phone }}</a></div>
                    </div>
                    <div v-if="item.location" class="card_list__item">
                        <div class="name">{{ $t('invest.location') }}:</div>
                        <div class="value">{{ item.location.full_name }}</div>
                    </div>
                </div>
            </div>
            <div v-if="!isMobile" class="right">
                <transition name="component-fade" mode="out-in">
                    <component :is="chartComponent" :item="item" />
                </transition>
            </div>
        </div>
        <div class="card_footer">
            <div class="card_footer__status" :style="`background-color: ${item.status.hex_color}`">
                {{ $t('invest.status') }}: {{ item.status.name }}
            </div>
            <div class="card_footer__info">
                <div v-if="item.stage && item.stage.name" class="stage blue">
                    {{ item.stage.name }}
                </div>
                <div class="psd" :class="item.has_documentation ? 'green' : 'blue'">
                    {{ item.has_documentation ? $t('invest.psdDeveloped') : $t('invest.psdNotDeveloped') }}
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        item: {
            type: Object,
            required: true
        }
    },
    computed: {
        chartComponent() {
            if(this.tab === 1)
                return () => import('./PriceChart.vue')
            if(this.tab === 2)
                return () => import('./PeopleChart.vue')

            return () => import('./PriceChart.vue')
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return {
            tab: 1
        }
    },
    methods: {
        openProject() {
            this.$router.push({ name: 'full_invest_project_info', params: { id: this.item.id } })
        }
    }
}
</script>

<style lang="scss" scoped>
.invest_card{
    padding: 15px;
    border: 1px solid var(--border2);
    border-radius: var(--borderRadius);
    display: flex;
    flex-direction: column;
    background: #ffffff;
    @media (min-width: 768px) {
        padding: 20px 20px 5px 20px;
    }
    .component-fade-enter-active, .component-fade-leave-active {
        transition: opacity .4s ease, transform .3s ease;
    }
    .component-fade-enter, .component-fade-leave-to {
        opacity: 0;
        transform: translateX(30px);
    }
    .card_footer{
        border-top: 1px solid var(--border2);
        padding-top: 25px;
        margin-top: 15px;
        margin-bottom: 25px;
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        &__status{
            height: 36px;
            font-size: 13px;
            font-weight: 400;
            line-height: 13px;
            text-align: center;
            color: rgba(255, 255, 255, 1);
            width: max-content;
            padding-left: 20px;
            padding-right: 20px;
            border-radius: 4px;
            display: flex;
            align-items: center;
        }
        &__info{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            .stage, .psd {
                height: 36px;
                font-size: 13px;
                font-weight: 400;
                line-height: 13px;
                text-align: center;
                padding-left: 20px;
                padding-right: 20px;
                border: 1px solid;
                border-radius: 4px;
                display: flex;
                align-items: center;
            }
            .blue{
                border-color: rgba(29, 101, 192, 1);
                color: rgba(29, 101, 192, 1);
            }
            .green{
                border-color: rgba(77, 174, 0, 1);
                color: rgba(77, 174, 0, 1);
            }
        }
        @media (min-width: 768px) {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-top: 25px;
            margin-top: 55px;
        }
    }
    .tab_button{
        display: flex;
        align-items: center;
        margin-bottom: 20px;
    }
    .card_list{
        font-size: 14px;
        &__item{
            display: flex;
            &:not(:last-child){
                margin-bottom: 8px;
                @media (min-width: 1700px) {
                    margin-bottom: 14px;
                }
            }
            .name{
                min-width: 180px;
                max-width: 180px;
                color: #000000;
                opacity: 0.6;
                padding-right: 20px;
                word-break: break-word;
            }
            .value{
                color: #000000;
                word-break: break-word;
            }
        }
    }
    .card_body{
        @media (min-width: 768px) {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 20px;
            flex-grow: 1;
        }
        @media (min-width: 1700px) {
            gap: 40px;
        }
    }
    .card_header{
        display: flex;
        justify-content: space-between;
        padding-bottom: 15px;
        @media (min-width: 768px) {
            padding-bottom: 25px;
        }
        .date{
            font-size: 13px;
            margin-bottom: 8px;
            opacity: 0.6;
            color: #000000;
        }
        h2{
            font-size: 20px;
            margin: 0px;
        }
    }
}
</style>