<template>
    <a-popover
        v-model="visible"
        trigger="click"
        @click="getDayEvents"
        @visibleChange="visibleChange($event, weekDay)">
        <template #content>
            <template v-if="eventsLoading || plansLoading">
                <a-spin />
            </template>
            <template v-else>
                <div class="mb-4 flex items-center justify-between pt-2">
                    <Profiler
                        :avatarSize="22"
                        nameClass="text-sm"
                        :user="user"
                        showUserName/>
                    <a-button
                        size="small"
                        @click="visible = false"
                        type="ui"
                        shape="circle"
                        ghost
                        icon="fi-rr-cross"
                        flaticon/>
                </div>
                <div
                    v-if="plans?.length"
                    class="text-[#000000D9] bg-[#C5E6F6] rounded p-4">
                    <p class="mb-3">{{ $t("Tasks") }}</p>
                    <ul>
                        <li
                            v-for="plan in plans"
                            :key="plan.id"
                            class="list__item truncate">
                            <span class="cursor-pointer" @click="openTask(plan)">
                                <span  class="blue_color mr-1">
                                    {{ plan?.task?.counter }}
                                </span>
                                {{ plan?.task?.name }}
                            </span>
                        </li>
                    </ul>
                </div>

                <div
                    v-if="events?.length"
                    class="mt-2.5 text-[#000000D9] bg-[#FFEFC9] rounded p-4">
                    <p class="mb-3">{{ $t("Events") }}</p>
                    <ul>
                        <li v-for="event in events" :key="event.id" class="list__item truncate">
                            <span class="cursor-pointer" @click="openEvent(event)">
                                <i class="fi fi-rr-clock mr-2"></i>
                                <span class="mr-2">{{ getEventDate(event) }}</span>
                                {{ event.name }}
                            </span>
                        </li>
                    </ul>
                </div>
            </template>
        </template>
        <div
            class="event-tag event-tag_plan"
            v-for="plan in weekDay.plans"
            :key="plan.id">
            {{ $t("Tasks") }}: {{ plan.count }}
        </div>
        <div class="event-tag" v-for="event in weekDay.events" :key="event.id">
            {{ $t("Events") }}: {{ event.count }}
        </div>
    </a-popover>
</template>

<script>
export default {
    props: {
        weekDay: {
            type: Object,
            required: true,
        },
        user: {
            type: Object,
            required: true,
        },
    },
    data() {
        return {
            plansLoading: false,
            eventsLoading: false,
            events: {
                results: [],
            },
            plans: {
                results: [],
            },
            visible: false,
        };
    },
    methods: {
        getDayEvents() {
            this.eventsLoading = true;
            const params = {
                user: this.user.id,
                start: this.weekDay.date.startOf("day").format("YYYY-MM-DDTHH:mm:ssZ"),
                end: this.weekDay.date.endOf("day").format("YYYY-MM-DDTHH:mm:ssZ"),
            };
            const url = "calendars/events/events_by_user";
            this.$http(url, { params })
                .then(({ data }) => {
                    this.events = data;
                })
                .finally(() => {
                    this.eventsLoading = false;
                });
        },
        getDayPlans() {
            this.plansLoading = true;
            const params = {
                user: this.user.id,
                plane_date: this.weekDay.date.startOf("day").format("YYYY-MM-DD"),
            };
            const url = "personal_planes/plan_by_user";
            this.$http(url, { params })
                .then(({ data }) => {
                    this.plans = data.plane_items;
                })
                .finally(() => {
                    this.plansLoading = false;
                });
        },

        visibleChange(event, user) {
            if (!event) {
                return;
            }

            this.getDayEvents();
            this.getDayPlans();
        },
        openTask(plan) {
            this.visible = false;
            this.$router.replace({ query: { task: plan?.task?.id } });
        },
        openEvent(event) {
            this.visible = false;
            this.$router.replace({ query: { event: event?.id } });
        },
        getEventDate(event) {
            const start = this.$moment(event.start_at)
            const end = this.$moment(event.end_at)
            const isNotToday = !start.isSame(this.$moment(), 'day') || !end.isSame(this.$moment(), 'day')
            if (isNotToday) {
                return `${start.format('DD.MM.YY')} - ${end.format('DD.MM.YY')}`
            }
            return `${start.format('HH:MM')} - ${end.format('HH:MM')}`
        }
    },
};
</script>

<style lang="scss" scoped>
.list__item:not(:last-child) {
  margin-bottom: 15px;
}
.list__item {
  line-height: 1;
  max-width: 400px;
}

.event {
  background-color: #f0f0f0;
  padding: 5px;
  margin-top: 5px;
  border-radius: 5px;
}

.event-tag {
  min-width: 90px;
  max-width: 110px;
  padding: 5px 10px;
  background-color: #ffefc9;
  border-radius: 6px;
  line-height: 1;
  cursor: pointer;
  user-select: none;
  &:not(:last-child) {
    margin-bottom: 5px;
  }
}

.event-tag_plan {
  background-color: #c5e6f6;
}
</style>