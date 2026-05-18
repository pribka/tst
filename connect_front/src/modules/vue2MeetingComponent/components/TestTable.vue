<template>
    <div class="h-full flex">
        <UniversalTable
            :model="pageModel"
            :pageName="page_name"
            :tableType="tableType"
            :endpoint="endpoint"
            :openHandler="open" />
    </div>
</template>

<script>
import { mapState, mapActions } from 'vuex'
import eventBus from '../utils/eventBus'
import { durationFormat } from '../utils/index.js'
export default {
    name: 'MeetingTypeTable',
    components: {
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable')
    },
    props: {
        pageModel: {
            type: String,
            default: 'meetings.PlannedMeetingModel'
        },
        page_name: {
            type: String,
            default: 'page_list_meetings.PlannedMeetingModel'
        }
    },
    computed: {
        ...mapState({
            windowHeight: state => state.windowHeight,
            windowWidth: state => state.windowWidth,
            config: state => state.config.config,
        })
    },
    data() {
        return {
            endpoint: '/meetings/',
            loading: false,
            list: [],
            tableType: 'meetings'

        }
    },
    methods: {
        ...mapActions({
            getTableInfo: 'table/getTableInfo',
        }),
        dFormat(duration) {
            return durationFormat(duration)
        },
        open(record) {
            let query = Object.assign({}, this.$route.query)
            if(!query?.meeting) {
                query.meeting = record.id
                this.$router.push({query})
            }
        },
        endConference(id) {
            const index = this.list.findIndex(f => f.id === id)
            if(index !== -1)
                this.list[index].status = 'ended'
        },
        restartConference(id) {
            const index = this.list.findIndex(f => f.id === id)
            if(index !== -1)
                this.list[index].status = 'new'
        },
    },
    mounted() {
        eventBus.$on('END_CONFERENCE', id => {
            this.endConference(id)
        })
        eventBus.$on('RESTART_CONFERENCE', id => {
            this.restartConference(id)
        })
    },
    beforeDestroy() {
        eventBus.$off('END_CONFERENCE')
        eventBus.$off('RESTART_CONFERENCE')
    }
}
</script>

<style lang="scss" scoped>
.meeting_name{
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    transition: color 0.3s;
    word-break: break-word;
}
</style>