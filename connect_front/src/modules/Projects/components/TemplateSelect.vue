<template>
    <a-popover
        placement="bottomLeft"
        trigger="click"
        v-model="visible"
        transitionName=""
        :destroyTooltipOnHide="true"
        overlayClassName="project_popover"
        :getPopupContainer="getPopupContainer"
        @visibleChange="visibleChange">
        <a-button
            type="flat"
            class="sel_p_btn"
            :title="value ? `${$t('project.template')} : ${value.name}` : $t('project.template')">
            <div v-if="value" class="flex items-center gap-2 truncate">
                {{ $t('project.template') }}:
                <div class="flex items-center truncate">
                    <span class="truncate">{{ value.name }}</span>
                </div>
            </div>
            <div v-else class="flex items-center">
                <i class="fi fi-rr-clip mr-2" />
                {{ $t('project.template') }}
            </div>
        </a-button>

        <template #content>
            <a-input-search
                class="mb-2 search_input"
                v-model="search"
                ref="searchInput"
                :placeholder="$t('project.template_name')"/>
            <div class="popover_list">
                <div
                    v-for="(work, index) in filteredWorkList"
                    :key="work.id || index"
                    :title="work.name"
                    :class="checkSelected(work)"
                    class="cursor-pointer project_item p-2 flex items-center truncate"
                    @click="selectWork(work)">
                    {{ work.name }}
                </div>

                <div v-if="!loading && filteredWorkList.length === 0" class="p-2 text-center text-gray-500">
                    {{ $t('no_data') }}
                </div>

                <div v-if="loading" class="flex justify-center">
                    <a-spin size="small" />
                </div>
            </div>
        </template>
    </a-popover>
</template>

<script>
export default {
    props: {
        value: {
            type: [Object, Array, String]
        },
        selectItem: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            scrollStatus: true,
            page: 0,
            visible: false,
            loading: false,
            workList: [],
            search: ""
        }
    },
    computed: {
        filteredWorkList() {
            const q = this.normalizeText(this.search)
            if (!q) return this.workList
            return this.workList.filter(w =>
                this.normalizeText(w?.name || "").includes(q)
            )
        }
    },
    methods: {
    // Нормализация строки: приводим к lowerCase и убираем диакритику/лишние пробелы
        normalizeText(s) {
            return (s || "")
                .toString()
                .trim()
                .toLowerCase()
                .normalize("NFD")
                .replace(/[\u0300-\u036f]/g, "")
        },
        getPopupContainer(trigger) {
            return trigger.parentNode
        },
        async visibleChange(vis) {
            this.visible = vis
            if (vis) {
                if (this.workList.length === 0) {
                    await this.getWorkList()
                }
                this.$nextTick(() => {
                    requestAnimationFrame(() => {
                        const el =
              this.$refs.searchInput &&
              this.$refs.searchInput.$refs &&
              this.$refs.searchInput.$refs.input
                        if (el) el.focus()
                    })
                })
            } else {
                // Не чистим workList, чтобы при повторном открытии не дергать бэк
                this.search = ""
            }
        },
        checkSelected(work) {
            return this.value?.id === work.id ? "active" : ""
        },
        selectWork(work) {
            if (work.id === this.value?.id) {
                this.$emit("input", null)
                this.selectItem(null)
                this.$emit("change", null)
                if(this.search?.length) {
                    this.$nextTick(() => {
                        const el =
                        this.$refs.searchInput &&
                        this.$refs.searchInput.$refs &&
                        this.$refs.searchInput.$refs.input
                        if (el) el.focus()
                    })
                    this.search = ""
                } else {
                    this.visible = false
                }
            } else {
                this.$emit("input", work)
                this.selectItem(work)
                this.$emit("change", work)
                this.visible = false
            }
        },
        async getWorkList() {
            try {
                this.loading = true
                const { data } = await this.$http.get(
                    "/work_groups/templates/available_temlates/"
                )
                if (Array.isArray(data) && data.length) {
                    this.workList = data // сразу присваиваем, без push, чтобы избежать дублей
                }
            } catch (e) {
                // можно добавить нотификацию при ошибке
            } finally {
                this.loading = false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.search_input{
    &::v-deep{
        .ant-input{
            background: #f7f9fc;
            border-color: #f7f9fc;
            box-shadow: initial!important;
            min-height: 36px;
            color: var(--text);
            &::placeholder{
                color: #888888;
            }
            .ant-input-suffix{
                color: var(--text);
            }
        }
    }
}
.popover_list{
    max-height: 200px;
    overflow-y: auto;
    max-width: 250px;
    min-width: 250px;
}
.project_item{
    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    border-radius: 8px;
    margin-bottom: 3px;
    &:hover,
    &.active{
        background: #f7f9fc;
    }
}
.sel_p_btn{
    max-width: 250px;
}
</style>

<style lang="scss">
.project_popover{
    .ant-popover-arrow{
        display: none;
    }
    &.ant-popover-placement-bottom, 
    &.ant-popover-placement-bottomLeft, 
    &.ant-popover-placement-bottomRight{
        padding-top: 10px;
    }
}
</style>