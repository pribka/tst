<template>
    <div class="stat_card">
        <div class="stat_card__header mb-3">
            <div>
                <div class="label" :title="list[0].title">{{ title }}</div>
                <div class="user">{{ list[0].user }}</div>
            </div>
            <div class="rate">{{ $t('team.first_place') }}</div>
        </div>
        <div class="grid gap-4 grid-cols-1 sm:grid-cols-2">
            <div class="prg_stat flex list[0]s-center">
                <a-progress 
                    type="circle" 
                    :strokeWidth="15"
                    strokeColor="#67dd9f"
                    stroke-linecap="square"
                    :format="percent => percent"
                    :percent="list[0].percent" 
                    :width="75" />
                <div class="prg_stat__info pl-3">
                    <div class="count">{{ list[0].allTask }}</div>
                    <div class="c_label mb-3">{{ $t('team.total_tasks') }}</div>
                    <div class="count">{{ list[0].percent }}%</div>
                    <div class="c_label">{{ $t('team.completed') }}</div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    components: {
        // ReportCard,
        // CardLoader2
    },
    props: {
        statData: {
            type: Object,
            default: () => null
        },
        title: {
            type: String,
            default: ''
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
.stat_card{
    background: #fff;
    box-shadow: 0px 4px 8px 0px #0000000F;
    border-radius: 6px;
    padding: 15px;
    color: #000;
    .prg_stat{
        color: #000;
        &__info{
            .count{
                font-size: 16px;
                line-height: 16px;
                margin-bottom: 2px;
            }
            .c_label{
                font-size: 13px;
                line-height: 18px;
                word-break: break-word;
            }
        }
        &::v-deep{
            .ant-progress{
                .ant-progress-circle-trail{
                    stroke: #fc75a1!important;
                }
            }
        }
    }
    &__header{
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        .user{
            opacity: 0.6;
            font-size: 14px;
            word-break: break-word;
        }
        .label{
            font-size: 16px;
            line-height: 24px;
            word-wrap: break-word;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .rate{
            margin-left: 20px;
            font-size: 14px;
            line-height: 14px;
            opacity: 0.6;
        }
    }
}
</style>