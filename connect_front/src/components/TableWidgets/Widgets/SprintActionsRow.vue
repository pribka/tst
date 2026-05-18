<template>
    <a-dropdown
        :trigger="['click']"
        :getPopupContainer="getContainer"
        @visibleChange="visibleChange">
        <a-button 
            :loading="loading" 
            icon="fi-rr-menu-dots-vertical" 
            flaticon
            shape="circle"
            style="color: var(--text);"
            ghost
            type="ui" />
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
</template>

<script>
import eventBus from "@/utils/eventBus"
import { errorHandler } from '@/utils/index.js'
export default {
    props: {
        record: {
            type: Object,
            required: true
        },
        colParams: {
            type: Object,
            default: () => null
        }
    },
    computed: {
        sprint() {
            return this.record
        },
        isInject() {
            return this.colParams?.isInject || ''
        },
        inject() {
            return this.colParams?.inject || false
        }
    },
    data() {
        return {
            loading: false,
            actions: null,
            actionsLoader: false
        }
    },
    methods: {
        getContainer() {
            return this.colParams.getContainer()
        },
        addTask() {
            eventBus.$emit("sprint_add_task", this.sprint.id);
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
        edit() {
            eventBus.$emit("edit_sprint", {
                ...this.sprint,
                inject: this.inject,
            });
        },
        deleteSprint() {
            this.$confirm({
                title: this.$t('task.confirm_delete_sprint'),
                closable: true,
                maskClosable: true,
                cancelText: this.$t('task.no'),
                okText: this.$t('task.remove'),
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
                            .catch(error => {
                                errorHandler({error})
                                reject();
                            });
                    });
                },
            });
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
        visibleChange(vis) {
            if (vis && !this.actions) {
                this.getSprintActions();
            }
        },
        async getSprintActions() {
            try {
                this.actionsLoader = true;
                const { data } = await this.$http.get(
          `/tasks/sprint/${this.sprint.id}/action_info/`
                );
                if (data) {
                    this.actions = data
                }
            } catch (error) {
                errorHandler({error, show: false})
            } finally {
                this.actionsLoader = false;
            }
        },
    }
}
</script>