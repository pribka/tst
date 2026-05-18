<template>
    <div
        class="sprint_card"
        ref="sprintCard"
        :class="[visible && 'active', inject && 'card_in']">
        <div class="sprint_card__header">
            <div
                class="flex items-center pr-2">
                <a-button
                    type="link"
                    flaticon
                    class="flex items-center justify-center card_arrow cursor-pointer"
                    style="font-size: 22px"
                    shape="circle"
                    :loading="actionsLoader"
                    @click="showSprintInfo()"
                    icon="fi-rr-angle-small-down"/>
                <div class="sprint_status ml-2" :style="`background: ${statusColor}`">
                    {{ $t(`task.${sprint.status}`) }}
                </div>
                <div class="card_info ml-3">
                    <div class="card_name cursor-pointer select-none" :title="sprint.name" @click="openSprint">
                        {{ sprint.name }}
                    </div>
                </div>
            </div>
            <div class="flex items-center justify-end">
                <div class="count_stat mr-2 cursor-pointer" @click="openSprint()">
                    <div
                        v-tippy="{ inertia: true, duration: '[600,300]' }"
                        :content="$t('task.new')"
                        class="count_stat__item new">
                        {{ sprint.new_task_count }}
                    </div>
                    <div
                        v-tippy="{ inertia: true, duration: '[600,300]' }"
                        :content="$t('task.in_work')"
                        class="count_stat__item process">
                        {{ sprint.in_work_task_count }}
                    </div>
                    <div
                        v-tippy="{ inertia: true, duration: '[600,300]' }"
                        :content="$t('task.completed')"
                        class="count_stat__item completed">
                        {{ sprint.completed_task_count }}
                    </div>
                </div>
                <a-button
                    v-if="windowWidth >= 1500"
                    type="primary"
                    ghost
                    size="large"
                    @click="openSprint()">
                    {{ $t('sprint.open') }}
                </a-button>
                <!--<a-button
                    v-if="
                        windowWidth >= 1200 && isAuthor && sprint.status !== 'completed'
                    "
                    type="primary"
                    class="ml-2"
                    size="large"
                    :loading="loading"
                    @click="actionHandler()">
                    <template v-if="sprint.status === 'new'"> Запустить спринт </template>
                    <template v-if="sprint.status === 'in_process'">
                        Завершить спринт
                    </template>
                </a-button>-->
                <a-dropdown
                    :trigger="['click']"
                    :getPopupContainer="getPopupContainer"
                    @visibleChange="visibleChange">
                    <a-button
                        type="primary"
                        ghost
                        flaticon
                        icon="fi-rr-angle-small-down"
                        class="flex items-center ml-1 lg:ml-2"
                        size="large">
                        <template v-if="windowWidth >= 992"> {{ $t('task.show_more') }} </template>
                    </a-button>
                    <a-menu slot="overlay">
                        <template v-if="actions">
                            <a-menu-item
                                v-if="
                                    actions &&
                                        actions.set_status &&
                                        actions.set_status.availability &&
                                        sprint.status !== 'completed'
                                "
                                key="change_status"
                                class="flex items-center"
                                @click="actionHandler()">
                                <template v-if="sprint.status === 'new'">
                                    <i class="fi fi-rr-play-circle mr-2" /> {{ $t('task.to_work') }}
                                </template>
                                <template v-if="sprint.status === 'in_process'">
                                    <i class="fi fi-rr-badge-check mr-2" /> {{ $t('task.to_completed') }}
                                </template>
                            </a-menu-item>
                            <a-menu-item
                                v-if="
                                    actions &&
                                        actions.set_task &&
                                        actions.set_task.availability &&
                                        sprint.status !== 'completed'
                                "
                                key="add_task"
                                class="flex items-center"
                                @click="addTask()">
                                <i class="fi fi-rr-plus mr-2" /> {{ $t('task.add_task') }}
                            </a-menu-item>
                            <a-menu-item
                                v-if="windowWidth < 1500"
                                key="open"
                                class="flex items-center"
                                @click="openSprint()">
                                <i class="fi fi-rr-zoom-in mr-2" /> {{ $t('sprint.open') }}
                            </a-menu-item>
                            <a-menu-item
                                key="share"
                                class="flex items-center"
                                @click="share()">
                                <i class="fi fi-rr-share mr-2" /> {{ $t("task.share_to_chat") }}
                            </a-menu-item>
                            <a-menu-item
                                key="analytics"
                                class="flex items-center"
                                @click="openAnalytics()">
                                <i class="fi fi-rr-chart-histogram mr-2" /> {{ $t('sprint.statistic') }}
                            </a-menu-item>
                            <a-menu-item
                                v-if="actions && actions.edit && actions.edit.availability"
                                key="edit"
                                class="flex items-center"
                                @click="edit()">
                                <i class="fi fi-rr-edit mr-2" /> {{ $t("task.edit") }}
                            </a-menu-item>
                            <template
                                v-if="actions && actions.delete && actions.delete.availability">
                                <a-menu-divider />
                                <a-menu-item
                                    class="text-red-500 flex items-center"
                                    key="delete"
                                    @click="deleteSprint()">
                                    <i class="fi fi-rr-trash mr-2" /> {{ $t("task.remove") }}
                                </a-menu-item>
                            </template>
                        </template>
                        <template v-else>
                            <a-menu-item class="flex justify-center" key="loader">
                                <a-spin size="small" />
                            </a-menu-item>
                        </template>
                    </a-menu>
                </a-dropdown>
            </div>
        </div>
        <div v-if="visible" class="sprint_card__body">
            <a-spin :spinning="actionsLoader" size="small" class="w-full">
                <div class="sprint_info_grid">
                    <div class="info_card">
                        <div class="info_card__head flex items-center justify-between">
                            <div class="h_label">{{ $t('task.dead_line') }}</div>
                            <a-button
                                v-if="
                                    actions &&
                                        actions.edit &&
                                        actions.edit.availability &&
                                        sprint.status !== 'completed'
                                "
                                type="link"
                                flaticon
                                v-tippy="{ inertia: true, duration: '[600,300]' }"
                                :content="$t('task.edit')"
                                icon="fi-rr-edit"
                                @click="edit()"/>
                        </div>
                        <div class="info_card__body">
                            <template v-if="sprint.begin_date && sprint.dead_line">
                                {{ $moment(sprint.begin_date).format("DD.MM.YY") }} -
                                {{ $moment(sprint.dead_line).format("DD.MM.YY") }}
                            </template>
                            <template v-else> {{ $t('task.no_time_limit') }} </template>
                        </div>
                    </div>
                    <div class="info_card">
                        <div class="info_card__head flex items-center justify-between">
                            <div class="h_label">{{ $t('task.task-list-page') }}</div>
                            <a-button
                                v-if="
                                    actions &&
                                        actions.set_task &&
                                        actions.set_task.availability &&
                                        sprint.status !== 'completed'
                                "
                                type="link"
                                flaticon
                                v-tippy="{ inertia: true, duration: '[600,300]' }"
                                :content="$t('task.add_task')"
                                icon="fi-rr-add"
                                @click="addTask()"/>
                        </div>
                        <div class="info_card__body">
                            {{ taskCount }}
                        </div>
                    </div>
                    <div v-if="sprintProjects" class="info_card">
                        <div class="info_card__head flex items-center justify-between">
                            <div class="h_label">{{ $t("Projects") }}</div>
                            <a-button
                                v-if="
                                    actions &&
                                        actions.edit &&
                                        actions.edit.availability &&
                                        sprint.status !== 'completed'
                                "
                                type="link"
                                flaticon
                                v-tippy="{ inertia: true, duration: '[600,300]' }"
                                :content="$t('task.edit')"
                                icon="fi-rr-edit"
                                @click="edit()"/>
                        </div>
                        <div class="info_card__body">
                            <span
                                v-for="project, index in sprintProjects"
                                :key="project.id">
                                <span 
                                    @click="openProjectById(project.id)"
                                    :class="project.id !== currentOpenedProject?.id && 'blue_color cursor-pointer'">
                                    {{ project.name }}</span><span v-if="index != (sprintProjects.length - 1)">,</span>
                            </span>
                        </div>
                    </div>

                    <div v-if="sprint.target" class="info_card">
                        <div class="info_card__head flex items-center justify-between">
                            <div class="h_label">{{ $t('sprint.spirnt_target') }}</div>
                            <a-button
                                v-if="
                                    actions &&
                                        actions.edit &&
                                        actions.edit.availability &&
                                        sprint.status !== 'completed'
                                "
                                type="link"
                                flaticon
                                v-tippy="{ inertia: true, duration: '[600,300]' }"
                                :content="$t('task.edit')"
                                icon="fi-rr-edit"
                                @click="edit()"/>
                        </div>
                        <div class="info_card__body">
                            {{ isExpanded ? sprint.target : truncatedText }}
                            <div v-if="sprint.target.length > expandLength">
                                <a-button
                                    type="link"
                                    size="small"
                                    style="font-size: 12px"
                                    class="px-0"
                                    @click="isExpanded = !isExpanded">
                                    {{ isExpanded ? $t('task.hide') : $t('task.show_more') }}
                                </a-button>
                            </div>
                        </div>
                    </div>
                    <div
                        v-if="sprint.expected_result && sprint.expected_result.length"
                        class="info_card">
                        <div class="info_card__head flex items-center justify-between">
                            <div class="h_label">{{ $t('task.expected_result') }}</div>
                            <a-button
                                v-if="
                                    actions &&
                                        actions.edit &&
                                        actions.edit.availability &&
                                        sprint.status !== 'completed'
                                "
                                type="link"
                                flaticon
                                v-tippy="{ inertia: true, duration: '[600,300]' }"
                                :content="$t('task.edit')"
                                icon="fi-rr-edit"
                                @click="edit()"/>
                        </div>
                        <div class="info_card__body">
                            {{ sprint.expected_result.join(", ") }}
                        </div>
                    </div>
                </div>
            </a-spin>
        </div>
    </div>
</template>

<script>
import eventBus from "@/utils/eventBus";
import { declOfNum } from "@/utils/utils.js";
import { errorHandler } from '@/utils/index.js'
export default {
    props: {
        sprint: {
            type: Object,
            required: true,
        },
        inject: {
            type: Boolean,
            default: false,
        },
    },
    data() {
        return {
            visible: false,
            sprintDetail: null,
            loading: false,
            taskList: [],
            count: 0,
            pageSize: 10,
            taskLoading: false,
            page: 1,
            empty: false,
            takeLoader: false,
            page_name: `sprint_tasks_${this.sprint.id}`,
            actions: null,
            actionsLoader: false,
            isExpanded: false,
            expandLength: 60,
        };
    },
    computed: {
        currentOpenedProject() {
            return this.$store.getters['projects/info'] || null
        },
        sprintProjects() {
            if (this.sprint?.projects?.length) {
                return this.sprint.projects;
            }
            return "";
        },
        truncatedText() {
            return this.sprint.target.length > this.expandLength
                ? this.sprint.target.slice(0, this.expandLength) + "..."
                : this.sprint.target;
        },
        isInject() {
            return this.inject ? `_inject` : "";
        },
        windowWidth() {
            return this.$store.state.windowWidth;
        },
        taskCount() {
            return `${this.sprint.task_count} ${declOfNum(this.sprint.task_count, [
                this.$t('task.task_singular'),
                this.$t('task.task_plural_2_4'),
                this.$t('task.task_plural_5_plus'),
            ])}`;
        },
        user() {
            return this.$store.state.user.user;
        },
        isAuthor() {
            if (this.$store.state.user.user?.id === this.sprint.author.id)
                return true;
            else return false;
        },
        statusColor() {
            switch (this.sprint.status) {
            case "new":
                return "#1D65C0";
                break;
            case "in_process":
                return "#722ed1";
                break;
            case "completed":
                return "#52c41a";
                break;
            default:
                return "#1D65C0";
            }
        },
    },
    methods: {
        openProjectById(id) {
            const query = { ...this.$route.query }
            if (query.viewProject !== id) {
                query.viewProject = id
                this.$router.replace({ query }) 
                return 
                delete query.viewProject
                this.$router.replace({ query })
                    .then(() => {
                        query.viewProject = id
                        this.$router.replace({ query })
                    })
            }
        },
        getPopupContainer() {
            return this.$refs.sprintCard;
        },
        addTask() {
            eventBus.$emit("sprint_add_task", this.sprint.id);
        },
        visibleChange(vis) {
            if (vis && !this.actions) {
                this.getSprintActions();
            }
        },
        async getSprintActions(open = false) {
            try {
                this.actionsLoader = true;
                const { data } = await this.$http.get(
          `/tasks/sprint/${this.sprint.id}/action_info/`
                );
                if (data) {
                    this.actions = data;
                    if (open) this.visible = true;
                }
            } catch (error) {
                errorHandler({error, show: false})
            } finally {
                this.actionsLoader = false;
            }
        },
        openSprint() {
            const query = Object.assign({}, this.$route.query);
            if (query.sprint === this.sprint.id) {
                delete query.sprint;
                this.$router.replace({ query });
            }
            if (
                (query.sprint && Number(query.sprint) !== this.sprint.id) ||
        !query.sprint
            ) {
                query.sprint = this.sprint.id;
                this.$router.push({ query });
            }
        },
        openAnalytics() {
            const query = Object.assign({}, this.$route.query);
            if (
                (query.sprint && Number(query.sprint) !== this.sprint.id) ||
        !query.sprint
            ) {
                query.sprint = this.sprint.id;
                query.sptab = "analytics";
                this.$router.push({ query });
            }
        },
        showSprintInfo() {
            if (!this.actions) {
                this.getSprintActions(true);
            } else this.visible = !this.visible;
        },
        share() {
            this.$store.commit("share/SET_SHARE_PARAMS", {
                model: "tasks.TaskModel",
                shareId: this.sprint.id,
                object: { ...this.sprint, isSprint: true },
                shareUrl: `${window.location.origin}/ru/dashboard?sprint=${this.sprint.id}`,
                shareTitle: `${this.$t('task.sprint_menu')} - ${this.sprint.name}`,
            });
        },
        async actionHandler() {
            if (this.sprint.status === "new") {
                try {
                    this.loading = true;
                    await this.$http.put(
            `tasks/sprint/${this.sprint.id}/update_status/`,
            { status: "in_process" }
                    );
                    this.$message.success(this.$t('task.to_work'));
                    eventBus.$emit(`update_sprints_list${this.isInject}`);
                } catch (error) {
                    errorHandler({error})
                } finally {
                    this.loading = false;
                }
            }
            if (this.sprint.status === "in_process") {
                eventBus.$emit("end_sprint", this.sprint);
                /*try {
                    this.loading = true
                    await this.$http.put(`tasks/sprint/${this.sprint.id}/update_status/`, {status: 'completed'})
                    this.$message.success("Спринт завершен")
                    eventBus.$emit(`update_sprints_list${this.isInject}`)
                } catch(e) {
                    this.$message.error(this.$t('error'))
                } finally {
                    this.loading = false
                }*/
            }
        },
        edit() {
            eventBus.$emit("edit_sprint", {
                ...this.sprint,
                inject: this.inject,
            });
        },
        deleteSprint() {
            this.$confirm({
                title: this.$t('task.delete_message'),
                closable: true,
                maskClosable: true,
                cancelText: this.$t('task.no'),
                okText: this.$t('task.remove'),
                okType: "danger",
                zIndex: 99999,
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http
                            .post("/table_actions/update_is_active/", [
                                { id: this.sprint.id, is_active: false },
                            ])
                            .then(() => {
                                this.$message.success(this.$t('task.remove'));
                                eventBus.$emit(`update_sprints_list${this.isInject}`);
                                resolve();
                            })
                            .catch((error) => {
                                errorHandler({error})
                                reject();
                            });
                    });
                },
            });
        },
    },
};
</script>

<style lang="scss" scoped>
.info_card {
  background: #eef2f4;
  padding: 15px;
  border-radius: 8px;
  color: #000;

  &__head {
    padding-bottom: 5px;
    min-height: 40px;
  }

  &__body {
    word-break: break-word;
  }

  .h_label {
    opacity: 0.6;
  }
}

.task_table_name {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: color 0.3s;
  word-break: break-word;
}

.sprint_table {
  &::v-deep {
    .table_status {
      height: 30px;
      line-height: 30px;
      padding-left: 15px;
      padding-right: 15px;
      border-radius: 30px;
    }

    .ant-table-row {
      td {
        border-color: #ced3fb;
      }
    }
  }
}

.sprint_card {
  background: #ffffff;
  border-radius: 8px;
  padding: 20px 15px;
  margin-bottom: 15px;
  color: #000;

  &.card_in {
    background: #fafafa;

    .info_card {
      background: #fff;
    }
  }

  @media (min-width: 1200px) {
    padding: 20px;
  }

  &.active {
    .card_arrow {
      transform: rotate(180deg);
    }
  }

  .sprint_target {
    &__item {
      opacity: 0.6;

      &:not(:last-child) {
        margin-bottom: 5px;
      }
    }
  }

  &__body {
    border-top: 1px solid #e8e8e8;
    margin-top: 20px;
    padding-top: 20px;

    .sprint_info_grid {
      display: grid;
      gap: 15px;
      grid-template-columns: repeat(2, minmax(0, 1fr));

      @media (min-width: 1350px) {
        grid-template-columns: repeat(5, minmax(0, 1fr));
      }

      @media (min-width: 1400px) {
        grid-template-columns: 190px 190px 1fr 1fr 1fr;
      }
    }
  }

  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .count_stat {
    display: flex;
    align-items: center;

    &__item {
      height: 40px;
      width: 40px;
      color: #000;
      font-size: 14px;
      line-height: 40px;
      text-align: center;
      border-radius: 6px;

      &:not(:last-child) {
        margin-right: 5px;
      }

      &.new {
        background: #ced3fb;
      }

      &.process {
        background: #efbdbd;
      }

      &.completed {
        background: #bdf0cc;
      }
    }
  }

  .sprint_status {
    background: #1d65c0;
    border-radius: 30px;
    height: 35px;
    padding-left: 20px;
    padding-right: 20px;
    color: #fff;
    line-height: 35px;
    text-align: center;
    min-width: 112px;
  }
  .card_name {
    font-size: 18px;
    line-height: 22px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    word-break: break-word;
    transition: color 0.2s, opacity 0.2s;
    &:hover {
        color: var(--primaryColor);
    }
    &:active {
        opacity: 0.7;
    }

  }

  .card_dates {
    opacity: 0.6;
    font-size: 14px;
  }
}
</style>
