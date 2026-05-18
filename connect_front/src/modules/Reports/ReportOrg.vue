<template>
    <ReportCard>
        <template v-slot:h_title>
            Топ 5 отделов
        </template>
        <div v-if="statData" class="grid gap-4 grid-cols-1 lg:grid-cols-2">
            <div v-for="item in list" :key="item.id" class="stat_card">
                <div class="stat_card__header mb-3">
                    <div>
                        <div class="label" :title="item.title">{{ item.title }}</div>
                        <div class="user">{{ item.user }}</div>
                    </div>
                    <div class="rate">1 место</div>
                </div>
                <div class="grid gap-4 grid-cols-1 sm:grid-cols-2">
                    <div class="prg_stat flex items-center">
                        <a-progress 
                            type="circle" 
                            :strokeWidth="15"
                            strokeColor="#67dd9f"
                            stroke-linecap="square"
                            :format="percent => percent"
                            :percent="item.percent" 
                            :width="75" />
                        <div class="prg_stat__info pl-3">
                            <div class="count">{{ item.allTask }}</div>
                            <div class="c_label mb-3">Всего задач</div>
                            <div class="count">{{ item.percent }}%</div>
                            <div class="c_label">Выполнено</div>
                        </div>
                    </div>
                    <div class="prg_stat flex items-center">
                        <a-progress 
                            type="circle" 
                            :strokeWidth="15"
                            strokeColor="#67dd9f"
                            stroke-linecap="square"
                            :format="percent => percent"
                            :percent="item.percent2" 
                            :width="75" />
                        <div class="prg_stat__info pl-3">
                            <div class="count">{{ item.allProject }}</div>
                            <div class="c_label mb-3">Всего проектов</div>
                            <div class="count">{{ item.percent2 }}%</div>
                            <div class="c_label">Выполнено</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <CardLoader2 v-else />
    </ReportCard>
</template>

<script>
export default {
    components: {
        ReportCard: () => import('./ReportCard.vue'),
        CardLoader2: () => import('./CardLoader2.vue')
    },
    props: {
        statData: {
            type: Object,
            default: () => null
        }
    },
    data() {
        return {
            value: [],
            list: [
                {
                    id: 1,
                    title: 'Отдел ЖКХ',
                    user: 'Данилов Лев',
                    allTask: 74,
                    completedTask: 30,
                    percent: 32,
                    allProject: 123,
                    percent2: 12
                },
                {
                    id: 2,
                    title: 'Отдел ЖКХ',
                    user: 'Данилов Лев',
                    allTask: 74,
                    completedTask: 30,
                    percent: 11,
                    allProject: 123,
                    percent2: 55
                },
                {
                    id: 3,
                    title: 'Отдел ЖКХ',
                    user: 'Данилов Лев',
                    allTask: 74,
                    completedTask: 30,
                    percent: 54,
                    allProject: 123,
                    percent2: 65
                },
                {
                    id: 4,
                    title: 'Отдел ЖКХ',
                    user: 'Данилов Лев',
                    allTask: 74,
                    completedTask: 30,
                    percent: 11,
                    allProject: 123,
                    percent2: 32
                }
            ]
        }
    }
}
</script>

<style lang="scss" scoped>
@import "./card_org_style.scss";
</style>
