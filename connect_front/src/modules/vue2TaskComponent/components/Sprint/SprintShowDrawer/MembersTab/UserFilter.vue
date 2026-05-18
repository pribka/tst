<template>
    <div class="flex">
        <Segmented 
            v-model="proxyValue" 
            bgInvert
            :options="userList">
            <template v-slot="{ option }">
                <template v-if="option?.key === 'all'">
                    {{ option.title }}
                    <a-badge
                        class="ml-2"
                        :count="option.count"
                        :number-style="{
                            backgroundColor: '#fff',
                            color: '#2D2D2D',
                        }"/>
                </template>
                <template v-else>
                    <a-avatar 
                        v-if="option?.avatar?.path" 
                        :src="option.avatar.path"
                        size="small"
                        class="!mr-2" />
                    {{ option.title }}
                </template>
            </template>
        </Segmented>
    </div>
</template>

<script>
import Segmented from '@apps/UIModules/Segmented'
export default {
    components: {
        Segmented
    },
    props: {
        userData: {
            type: Object,
            required: true
        },
        value: {
            type: [String, Number],
            required: true
        }
    },
    computed: {
        proxyValue: {
            get() {
                return this.value
            },
            set(value) {
                this.$emit('input', value)
                this.$emit('change', value)
            }
        },
        userList() {
            return [
                {
                    key: 'all',
                    title: this.$t('task.all'),
                    count: this.userData.count
                },
                ...this.userData.results.map((item) => ({
                    key: item.user.id,
                    title: item.user.first_name,
                    avatar: item.user.avatar
                }))
            ]
        }
    },
    data() {
        return {
            active: null
        }
    }
}
</script>
