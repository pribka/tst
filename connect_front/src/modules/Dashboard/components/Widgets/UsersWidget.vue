<template>
    <WidgetWrapper 
        :widget="widget"
        :class="isMobile && 'mobile_widget'">
        <template slot="actions">
            <a-dropdown :trigger="['click']">
                <span class="flex items-center cursor-pointer">
                    <template v-if="activeSort.order === orderAsc">
                        <i class="fi fi-rr-arrow-up"></i>
                    </template>
                    <template v-else>
                        <i class="fi fi-rr-arrow-down"></i>
                    </template>
                    <span class="ml-1">
                        {{ sortName }}
                    </span>
                </span>
                <a-menu slot="overlay">
                    <a-menu-item @click="changeSort(sortByName, orderAsc)">
                        <i class="fi fi-rr-arrow-up"></i>
                        <span class="ml-2">{{ $t('dashboard.full_name') }}</span>
                    </a-menu-item>
                    <a-menu-item @click="changeSort(sortByLastActivity, orderDesc)">
                        <i class="fi fi-rr-arrow-down"></i>
                        <span class="ml-2">{{ $t('dashboard.first_inactive') }}</span>
                    </a-menu-item>
                    <a-menu-item @click="changeSort(sortByLastActivity, orderAsc)">
                        <i class="fi fi-rr-arrow-up"></i>
                        <span class="ml-2">{{ $t('dashboard.first_active') }}</span>
                    </a-menu-item>
                </a-menu>
            </a-dropdown>
        </template>
        <div class="h-full user_list_wrap">
            <template v-if="!userListLoading">
                <RecycleScroller
                    :items="userList"
                    size-field="height"
                    :buffer="100"
                    emitUpdate
                    :item-size="53"
                    key-field="id">
                    <template #default="{ item }">
                        <UserCard 
                            :user="item" 
                            :fromNowDate="fromNowDate"
                            :userStatusColor="userStatusColor" />
                    </template>
                </RecycleScroller>
                <div 
                    v-if="isEmpty" 
                    class="flex justify-center">
                    <a-empty />
                </div>
                <div 
                    v-if="userListLoading" 
                    class="flex justify-center">
                    <a-spin size="small" />
                </div>
            </template>
            <template v-else>
                <div 
                    class="flex justify-center">
                    <a-spin size="small" />
                </div>
            </template>
        </div>
    </WidgetWrapper>
</template>

<script>
const ORDER_DESC = 'desc',
    ORDER_ASC = 'asc',
    FULLNAME = 'full_name',
    LAST_ACTIVITY = 'last_activity',
    TASK_COUNT = 'tasks_in_work';
import { orderBy } from 'lodash'
import eventBus from '@/utils/eventBus.js';
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css';
import { RecycleScroller } from 'vue-virtual-scroller';
import { errorHandler } from '@/utils/index.js'
export default {
    props: {
        widget: {
            type: Object,
            required: true
        }
    },
    components: {
        RecycleScroller,
        UserCard: () => import('../WidgetComponents/UserCard.vue'),
        WidgetWrapper: () => import('../WidgetWrapper.vue')
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile;
        },
        sortName() {
            if (this.activeSort.key === FULLNAME)
                return this.$t('dashboard.full_name');
            if (this.activeSort.key === LAST_ACTIVITY)
                return this.$t('dashboard.activity');
            if (this.activeSort.key === TASK_COUNT)
                return this.$t('dashboard.tasks');
            return this.$t('dashboard.full_name');
        },
        pageName() {
            return this.widget.page_name || this.widget.id;
        }
    },
    data() {
        return {
            userList: [],
            userDropper: [],
            userListLoading: false,
            activeSort: {
                key: FULLNAME,
                order: ORDER_ASC
            },
            sortByName: FULLNAME,
            sortByLastActivity: LAST_ACTIVITY,
            sortByTaskCount: TASK_COUNT,
            orderAsc: ORDER_ASC,
            orderDesc: ORDER_DESC,
            model: 'users.ProfileModel',
            isEmpty: false,
        };
    },
    sockets: {
        chat_online_user(data) {
            const userId = data.user;
            const foundUserIndex = this.userList.findIndex(user => user.id === userId);

            if (foundUserIndex > -1) {
                this.userList[foundUserIndex].online = true;
                this.userList[foundUserIndex].status_for_order = 'c';

                if (this.activeSort.key === 'last_activity')
                    this.changeSort(this.activeSort.key, this.activeSort.order);
            }
        },

        system_notify(data) {
            const userId = data.data.user;
            const foundUser = this.userList.find(user => user.id === userId);
            if (foundUser)
                foundUser.tasks_in_work = data.data.count;
        },

        chat_status_user(data) {
            const sockerUser = data.members;
            const foundUser = this.userList.find(user => user.id === sockerUser.user_uid);
            if (foundUser)
                this.setUserState(foundUser, sockerUser);

            let fi = this.userDropper.findIndex(user => user === sockerUser.user_uid);
            if (fi > -1) this.userDropper.splice(fi, 1);

            if (this.userDropper.length === 0 && this.activeSort.key === 'last_activity')
                this.changeSort(this.activeSort.key, this.activeSort.order);
        },
        
        chat_offline_user(data) {
            const userId = data.user;
            const foundUser = this.userList.find(user => user.id === userId);
            if (foundUser) {
                foundUser.online = false;
                foundUser.status_for_order = 'b';
                foundUser.last_activity = data.last_activity;
            }
            if (this.activeSort.key === 'last_activity')
                this.changeSort(this.activeSort.key, this.activeSort.order);
        }
    },
    async created() {
        eventBus.$on(`update_filter_${this.model}_${this.widget.page_name || this.widget.id}`, () => {
            this.reloadUserList();
        });
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.model}_${this.widget.page_name || this.widget.id}`);
    },
    mounted() {
        this.getUserList();
    },
    methods: {
        reloadUserList() {
            this.userList = [];
            this.getUserList();
        },
        
        async getUserList() {
            this.userListLoading = true;
            
            try {
                let params = {
                    page_size: 1000,
                    page: 1,
                    page_name: this.pageName
                };

                const { data } = await this.$http.get('/user/list_by_task/', { params });

                if (data?.results?.length) {
                    this.isEmpty = false;
                    for (const user of data.results) {
                        this.setUserState(user, user); // Обрисуем цветами
                    }
                    this.userList.push(...data.results);
    
                    this.initSort();
                    this.changeSort(this.activeSort.key, this.activeSort.order);
                } else {
                    this.isEmpty = true;
                }

            } catch (error) {
                errorHandler({error, show: false})
            } finally {
                this.userListLoading = false;
            }
        },
        
        changeSort(sortKey, order) {
            this.activeSort.key = sortKey;
            this.activeSort.order = order;

            let sortedUserList = [];
            if (sortKey === LAST_ACTIVITY) {
                let sortedUserDict = _.groupBy(this.userList, 'status_for_order'); // порвём массив на 3 участка
                if (order === 'desc') {
                    if (sortedUserDict.a)
                        sortedUserList = sortedUserList.concat(orderBy(sortedUserDict.a, 'full_name', 'asc'));
                    if (sortedUserDict.b)
                        sortedUserList = sortedUserList.concat(orderBy(sortedUserDict.b, 'last_activity', 'asc'));
                    if (sortedUserDict.c)
                        sortedUserList = sortedUserList.concat(orderBy(sortedUserDict.c, 'full_name', 'asc'));
                } else {
                    if (sortedUserDict.c)
                        sortedUserList = sortedUserList.concat(orderBy(sortedUserDict.c, 'full_name', 'asc'));
                    if (sortedUserDict.b)
                        sortedUserList = sortedUserList.concat(orderBy(sortedUserDict.b, 'last_activity', 'desc'));
                    if (sortedUserDict.a)
                        sortedUserList = sortedUserList.concat(orderBy(sortedUserDict.a, 'full_name', 'asc'));
                }
            } else {
                sortedUserList = orderBy(this.userList, sortKey, 'asc');
            }

            this.userList.splice(0);
            this.userList.push(...sortedUserList);

            this.saveSortToLocalstorage(sortKey, order);
            this.userListLoading = false;
        },
        
        saveSortToLocalstorage(sortKey, order) {
            localStorage.setItem('ourTeamSortKey', sortKey);
            localStorage.setItem('ourTeamSortOrder', order);
        },
        
        initSort() {
            const defaultSortKey = FULLNAME;
            const defaultSortOrder = ORDER_ASC;

            const localstorageSorKey = localStorage.getItem('ourTeamSortKey');
            const localstorageSortOrder = localStorage.getItem('ourTeamSortOrder');

            this.activeSort.key = localstorageSorKey || defaultSortKey;
            this.activeSort.order = localstorageSortOrder || defaultSortOrder;
        },
        
        userStatusColor(online, last_activity) {
            if (online)
                return 'green';
            else if (last_activity)
                return 'red';
            else 
                return 'gray';
        },
        
        setUserState(user, newState) {
            user.online = newState.online;
            if (user.online)
                user.status_for_order = 'c'; // онлайн
            else
                user.status_for_order = 'b'; // оффлайн
            user.last_activity = newState.last_activity;
            if (user.online) user.last_activity = this.$moment(new Date()); // today's date
            if (!user.last_activity) {
                user.last_activity = 0;
                user.status_for_order = 'a'; // никогда не был
            }
        },
        
        fromNowDate() {
            let now = this.$moment(new Date()); // today's date
            let end = this.$moment(this.statusUser.last_activity); // another date
            let duration = this.$moment.duration(now.diff(end));
            let hours = duration.asHours();

            return hours > 23 ? true : false;
        },
    },
}
</script>

<style scoped lang="scss">
.user_list_wrap {
    &::v-deep{
        .vue-recycle-scroller{
            overflow-y: scroll;
            height: 100%;
        }
    }
}

.chart_card {
    padding: 0 !important;
    border-radius: 10px;
    border: 1px solid var(--border2);
    .user_list_header {
        padding: 15px;
        padding-bottom: 0;
    }
}
.mobile_widget{
    &::v-deep{
        .vue-recycle-scroller{
            height: 350px;
        }
    }
}
</style>
