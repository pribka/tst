<template>
    <div>
        <!-- :today="today" 
        :prev="prev" 
        :next="next" 
        :today="today" 
        :related_object="related_object"
        :relatedInfo="relatedInfo"
        :addCalendar="addCalendar"
        :todayCheck="todayCheck"
        :addEventCheck="addEventCheck" -->
        <Header
            class="mb-4"
            :prev="prev"
            :next="next"
            :today="today" 
            :activeType="activeType"
            :startDay="startDay"
            :downloadFile="downloadPDF"
            :shareFile="shareFile"
            
            :handleChangeType="handleChangeType"/>

        <PageFilter
            :model="model"
            :key="pageName"
            size="large"
            :page_name="pageName"/>


        <a-skeleton :loading="loading">
            <div class="calendar">
                <table>
                    <thead>
                        <tr>
                            <th>{{ $t('team.employees') }}</th>
                            <th v-for="(weekDay, index) in weekDaysWithDates" :key="index">
                                <span class="uppercase"> {{ weekDay.name }}, </span>
                                {{ weekDay.date }}
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="user in users.results" :key="user.id">
                            <td>
                                <div class="employee-inofo">
                                    <Profiler
                                        :avatarSize="22"
                                        nameClass="text-sm"
                                        :user="user"
                                        showUserName/>
                                </div>
                            </td>

                            <td
                                class="day-column"
                                v-for="(weekDay, index) in user.week"
                                :key="user.id + index">
                                <EventsPopover
                                    :user="user"
                                    :weekDay="weekDay" />
                               
                            </td>
                        </tr>
                    </tbody>
                </table>
                <!-- :show-size-changer="pageSizeOptions.length > 1" -->
                <!-- :pageSizeOptions="pageSizeOptions" -->
            </div>
            <div class="flex">
                <a-pagination
                    class="mt-4 ml-auto pager_wrapper"
                    :current="params.page"
                    :page-size.sync="params.page_size"
                    :defaultPageSize="Number(params.page_size)"
                    :total="users.count"
                    show-less-items
                    @change="changePage">
                    <template slot="buildOptionText" slot-scope="props">
                        {{ props.value }}
                    </template>
                </a-pagination>
            </div>
        </a-skeleton>
    </div>
</template>

<script>
import EventsPopover from "./EventsPopover.vue";
import Header from "./Header";
import PageFilter from '@/components/PageFilter'
import eventBus from '@/utils/eventBus';
export default {
    components: {
        Header,
        EventsPopover,
        PageFilter
    },
    props: {
        organization: {
            type: Object,
            required: true,
        },
    },
    data() {
        return {
            users: {
                results: [],
                count: 0
            },
            activeType: "day",
            loading: false,
            startDay: this.$moment(),
            params: {
                page: 1,
                page_size: 10,
            },
            pageName: 'workplan_calendar',
            model: 'users.ProfileModel'
        };
    },
    computed: {
        weekDaysWithDates() {
            const startOfWeek = this.startDay.clone().startOf("day");
            return Array.from({ length: this.daysCount }).map((_, index) => ({
                name: startOfWeek.clone().add(index, "days").format("dd"),
                date: startOfWeek.clone().add(index, "days").format("DD"),
            }));
        },
        daysCount() {
            const daysCount = {
                day: 1,
                threeDays: 3,
                week: 7,
            };
            return daysCount[this.activeType];
        },
        startOfDay() {
            return this.$moment().startOf("day");
        },
        endOfDay() {
            return this.$moment().endOf("day");
        },
        startOfWeek() {
            return this.$moment().startOf("week");
        },
        endOfWeek() {
            return this.$moment().endOf("week");
        },
        queryParams() {
            const activeTypes = {
                day: {
                    start: () => this.startDay.clone().startOf("day"),
                    end: () => this.startDay.clone().endOf("day"),
                },
                threeDays: {
                    start: () => this.startDay.clone().startOf("day"),
                    end: () => this.startDay.clone().add(2, "days").endOf("day"),
                },
                week: {
                    start: () => this.startDay.clone().startOf("day"),
                    end: () => this.startDay.clone().add(6, "days").endOf("day"),
                },
            };

            return {
                page_size: this.params.page_size,
                page: this.params.page,
                start: activeTypes[this.activeType]
                    .start()
                    .format("YYYY-MM-DDTHH:mm:ssZ"),
                end: activeTypes[this.activeType].end().format("YYYY-MM-DDTHH:mm:ssZ"),
                organization: this.organization.id,
                page_name: this.pageName
            };
        },
    },
    created() {
        this.getActivities();
    },
    mounted() {
        eventBus.$on(`update_filter_${this.model}`, () => {
            this.changePage(1)
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.model}`)
    },
    methods: {
        changePage(newPage) {
            this.params.page = newPage
            this.getActivities()
        },
        getActivities() {
            this.loading = true;
            const params = {
                ...this.queryParams,
                start: this.queryParams.start,
                end: this.queryParams.end,
            };
            const url = `/users/activities/`;
            this.$http(url, { params })
                .then(({ data }) => {
                    data.results.forEach((user) => {
                        user.week = this.groupItemsByWeekday(user.events, user.plans);
                    });
                    this.users = data;
                })
                .finally(() => {
                    this.loading = false;
                });
        },
       
        groupItemsByWeekday(events, plans) {
            const startOfToday = this.startDay.clone();
            const dayCount = this.activeType === "week" ? 7 : this.activeType === "day" ? 1 : 3;
            const days = Array.from({ length: dayCount }, (_, index) => ({
                events: [],
                plans: [],
                date: this.startDay.clone().add(index, 'days')
            }));

            const filteredEvents = events.filter((event) => event.count);

            [...filteredEvents, ...plans].forEach((item) => {
                const eventDate = this.$moment(item.date, "YYYY-MM-DDTHH:mm:ss").startOf("day");
                const index = this.activeType === "week" ? eventDate.weekday() : eventDate.diff(startOfToday, "days");

                if (index >= 0 && index < dayCount) {
                    days[index][events.includes(item) ? "events" : "plans"].push(item);
                }
            });

            return days;
        },
        async downloadPDF(dateRange=null) {
            const params = {
                start: this.queryParams.start,
                end: this.queryParams.end,
                file_type: "xlsx",
                organization: this.organization.id,
                page_name: this.pageName
            };
            if (dateRange) {
                params.start = dateRange.start
                params.end = dateRange.end
            }

            const endpoint = "personal_planes/report/file/";

            try {
                const response = await this.$http(endpoint, {
                    params,
                    responseType: "blob",
                });
                const url = window.URL.createObjectURL(response.data);
                const link = document.createElement("a");
                link.href = url;
                link.setAttribute("download", `file.xlsx`);
                document.body.appendChild(link);
                link.click();
                link.remove();
            } catch (error) {
                console.error(this.$t('team.file_download_error'), error);
                this.$message.error(this.$t('team.file_download_error'));
            }
        },
        prev() {
            const deltaTimes = {
                week: () => this.startDay.subtract(1, "week"),
                day: () => this.startDay.subtract(1, "days"),
                threeDays: () => this.startDay.subtract(3, "days"),
            };
            this.startDay = deltaTimes[this.activeType]().clone();
            this.getActivities();
        },
        next() {
            const deltaTimes = {
                week: () => this.startDay.add(1, "week"),
                day: () => this.startDay.add(1, "day"),
                threeDays: () => this.startDay.add(3, "days"),
            };
            this.startDay = deltaTimes[this.activeType]().clone();
            this.getActivities();
        },
        today() {
            this.startDay = this.$moment().startOf("day");
            if (this.activeType === 'week') {
                this.startDay = this.startDay.clone().startOf("week")
            }
        },
        handleChangeType(type) {
            this.activeType = type;
            if (this.activeType === 'week') {
                this.startDay = this.startDay.clone().startOf("week")
            }
            this.getActivities();
        },
        async shareFile() {
            const params = {
                start: this.queryParams.start,
                end: this.queryParams.end,
                file_type: "pdf",
                organization: this.organization.id,
            };
            const endpoint = "personal_planes/report/file/";

            try {
                const response = await this.$http(endpoint, {
                    params,
                    responseType: "blob",
                });
                const url = window.URL.createObjectURL(response.data);
                const link = document.createElement("a");
                link.href = url;
                link.setAttribute("download", `file.pdf`);
                document.body.appendChild(link);
                link.click();
                link.remove();
            } catch (error) {
                console.error(this.$t('team.file_download_error'), error);
                this.$message.error(this.$t('team.file_download_error'));
            }
        },
    },
};
</script>

<style scoped lang="scss">
.calendar {
  position: relative;
  overflow-x: auto;
  max-width: 100%;

  margin-top: 20px;
  font-family: Arial, sans-serif;
}

table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  border-radius: 10px;
}

th,
td {
  padding: 12px;
  border-bottom: 1px solid #f0f2ff;
  border-right: 1px solid #f0f2ff;
  font-weight: 400;
}

table tr td:first-child,
table tr th:first-child {
  border-left: 1px solid #f0f2ff;
}

table tr th {
  border-top: 1px solid #f0f2ff;
}

table tr:first-child th:first-child {
  border-top-left-radius: 12px;
}

table tr:first-child th:last-child {
  border-top-right-radius: 12px;
}

table tr:last-child td:first-child {
  border-bottom-left-radius: 12px;
}

table tr:last-child td:last-child {
  border-bottom-right-radius: 12px;
}

th:first-child,
td:first-child {
  min-width: 220px;
  width: 300px;
  background-color: #fbfbfb;

  @media (min-width: 640px) {
    position: sticky;
    left: 0;
  }
}

.employee-info {
  display: flex;
  align-items: center;
}

.employee-info .avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  margin-right: 10px;
}

.day-column {
  min-width: 130px;
}

</style>