<template>
    <div class="points_list mt-4">
        <a-spin
            v-if="loading"
            class="flex justify-center" />
        <div v-if="noData">
            <a-empty :image="simpleImage" />
        </div>
        <a-list
            class="loadmore-list"
            item-layout="horizontal"
            v-for="(point, n) in contractorDeliveryPointsList"
            :key="n">
            <a-list-item>
                <a-button :class="isMobile && 'ant-btn-icon-only'" slot="actions" @click="showConfirm(point)">
                    <template v-if="isMobile">
                        <i class="fi fi-rr-trash"></i>
                    </template>
                    <template v-else>
                        Удалить
                    </template>
                </a-button>
                <a-list-item-meta :description="point.lat+', '+point.lon">
                    <div slot="title" class="list-item">
                        <h3>{{ point.name }}</h3>
                        <p>{{ point.address }}</p>
                    </div>
                </a-list-item-meta>
            </a-list-item>
        </a-list>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus.js'
import { Empty } from 'ant-design-vue';
export default {
    name: 'PointsList',
    components: {
    },
    data () {
        return {
        }
    },
    beforeCreate() {
        this.simpleImage = Empty.PRESENTED_IMAGE_SIMPLE
    },
    computed: {
        noData () {
            return this.contractorDeliveryPointsList.length === 0
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    props: {
        loading: {
            type: Boolean,
            default: false
        },
        contractorDeliveryPointsList: {
            type: Array,
            default: () => []
        }
    },
    methods: {
        showConfirm(point) {
            this.$confirm({
                title: 'Вы действительно хотите удалить точку доставки?',
                content: h => <div ><p><b>{point.name}</b></p><p>{point.address}</p><p>({point.lat}, {point.lon})</p></div>,
                okText: 'Да',
                okType: 'danger',
                cancelText: 'Нет',
                zIndex: 1100,
                onOk() {
                    eventBus.$emit('delet_delivery_points', point)
                },
                onCancel() {},
            });
        }
    }
}
</script>

<style scoped  lang="scss">
.list-item {
    h3 {
        font-weight: bold;
    }
}


</style>
