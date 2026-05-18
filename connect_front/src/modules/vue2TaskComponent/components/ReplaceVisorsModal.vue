<template>
    <a-modal 
        :visible="visible"
        :width="'550px'"
        @cancel="visible = false"
        :footer="null"
        class="modal">
        <template #title>
            <p class="text-center">
                <template v-if="hasVisors">
                    <p>{{ $t(`task.replace_visors_from_${reasonKey}`) }}</p>
                    <p class="text-muted text-sm font-normal">{{ $t(`task.replace_visors_change_text_${reasonKey}`)}}</p>
                </template>
                <template v-else>
                    <p class="font-semibold">
                        {{ $t('task.set_default_visors?') }}
                    </p>
                    <p class="mt-1 text-muted text-sm font-normal">
                        {{ $t(`task.set_default_visors_text_${reasonKey}`) }}
                    </p>
                </template>
            </p>
        </template>
        <div class="mt-[24px]">
            <div class="w-full flex flex-col sm:flex-row justify-center gap-3 ">
                <template v-if="hasVisors">
                    <a-button type="primary" @click="setDefaultVisors({ action: 'add'})">{{ buttonTextAdd }}</a-button>
                    <a-button type="primary" ghost @click="setDefaultVisors({ action: 'replace' })">{{ $t('task.replace_current_ones') }}</a-button>
                    <a-button type="primary" ghost @click="setDefaultVisors({ action: 'do_nothing' })">{{ $t('task.leave_as_it_is') }}</a-button>
                </template>
                <template v-else>
                    <a-button type="primary" block class="sm:max-w-[140px]" @click="setDefaultVisors({ action: 'add'})">{{ $t('Yes') }}</a-button>
                    <a-button type="primary" block class="sm:max-w-[140px]" ghost @click="setDefaultVisors({ action: 'do_nothing' })">{{ $t('No') }}</a-button>
                </template>
            </div>
        </div>
    </a-modal>
</template>

<script>
export default {
    props: {
        value: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            reason: null,
            visible: false,
            defaultVisors: [],
            hasVisors: this.form?.visors?.length > 0
        }
    },
    computed: {
        form: {
            get() {
                return this.value
            },
            set(value) {
                this.$emit('input', value)
            }
        },
        buttonTextAdd() {
            return this.$t(`task.add_visors_from_${this.reasonKey}`)
        },
        reasonKey() {
            return ['project', 'group'].includes(this.reason) ? this.reason : 'project'
        },
    },
    beforeDestroy() {
        this.defaultVisors = []
    },
    methods: {
        open({ reason, defaultVisors }) {
            this.visible = true
            this.reason = ['project', 'group'].includes(reason) ? reason : 'project'
            this.defaultVisors = defaultVisors
            this.syncHasVisors()
        },
        setDefaultVisors({ action }) {
            this.visible = false
            if (action === 'add') {
                const merged = [...this.form.visors, ...this.defaultVisors];
                const unique = Array.from(new Map(merged.map(item => [item.id, item])).values())
                this.form.visors = unique
                return
            } 
            if (action === 'replace') {
                this.form.visors = this.defaultVisors
                return
            } 
            if (action === 'do_nothing') { 
                return
            }
        },
        syncHasVisors() {
            this.hasVisors = this.form?.visors?.length > 0
        }
    }
}
</script>

<style lang="scss" scoped>
::v-deep {
    .ant-modal .ant-modal-header {
        padding-top: 24px;
    }
    .ant-modal .ant-modal-body {
        padding-top: 0;
        padding-bottom: 24px;
    }
}
</style>
