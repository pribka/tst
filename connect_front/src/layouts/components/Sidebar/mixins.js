import { mapState } from 'vuex'
export default {
    components: {
        draggable: () => import('vuedraggable')
    },
    data() {
        return {
            dragging: false,
            isTop: true,
            isBottom: false,
            ops: {
                scrollPanel: {
                    scrollingX: false
                },
                vuescroll: {
                    mode: 'native',
                    locking: false
                },
                bar: {
                    background: "#ccc",
                    onlyShowBarOnScroll: false
                }
            }
        }
    },
    computed: {
        ...mapState({
            routers: state => state.navigation.routerList,
            config: state => state.config.config,
            windowWidth: state => state.windowWidth
        }),
        isTablet() {
            const width = this.windowWidth || window.innerWidth
            const hasTouch = navigator.maxTouchPoints > 1 || 'ontouchstart' in window
            return width > 768 && width <= 1024 && hasTouch
        },
        frontPage() {
            if(this.routers?.length) {
                return this.routers[0].name
            } else
                return ''
        },
        routersList: {
            get() {
                return this.routers.filter(f => f.isShow).sort((a, b) => {
                    const aOrder = typeof a.descOrder === 'number' ? a.descOrder : 0
                    const bOrder = typeof b.descOrder === 'number' ? b.descOrder : 0
                    return aOrder - bOrder
                })
            },
            set(val) {
                const nextVisibleRoutes = val.map((route, index) => ({
                    ...route,
                    descOrder: index
                }))
                const hiddenRoutes = this.routers
                    .filter(route => !route.isShow)
                    .sort((a, b) => {
                        const aOrder = typeof a.descOrder === 'number' ? a.descOrder : 0
                        const bOrder = typeof b.descOrder === 'number' ? b.descOrder : 0
                        return aOrder - bOrder
                    })
                    .map((route, index) => ({
                        ...route,
                        descOrder: nextVisibleRoutes.length + index
                    }))

                this.$store.dispatch('navigation/changeRouterList', [...nextVisibleRoutes, ...hiddenRoutes])
            }
        }
    },
    methods: {
        openNewsFeed() {
            const query = {...this.$route.query, newList: 'true'}
            this.$router.push({ query })
        },
        onScroll(event) {
            this.isBottom = event.process >= 0.990
            this.isTop = event.scrollTop === 0 ? true : false
        },
        /*changeDraggable(e) {
            console.log(e, 'changeDraggable')
        },*/
        openSetting(params = null) {
            const query = {...this.$route.query}
            query.my_profile = 'open'

            if(params?.name) {
                query[params.name] = params.value
            }

            this.$router.push({query})
        }
    }
}
