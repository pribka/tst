export default {
    computed: {
        meetingsCreate() {
            if(this.$store.state?.meeting?.showEdit?.show)
                return this.$store.state.meeting.showEdit.show
            else
                return false
        },
        taskCreate() {
            if(this.$store.state?.task?.editDrawer)
                return this.$store.state.task.editDrawer
            else
                return false
        },
        newsCreate() {
            if(this.$store.state?.dashboard?.editDrawer)
                return this.$store.state.dashboard.editDrawer
            else
                return false
        }
    },
    methods: {
        taskCheck() {
            if(this.meetingsCreate) {
                this.$store.commit('meeting/SET_EDIT_DRAWER', { show: false, model: 'main' })
            }
            if(this.newsCreate) {
                this.$store.commit('dashboard/TOGGLE_EDIT_DRAWER', false)
            }
        },
        meetingsCheck() {
            if(this.taskCreate) {
                this.$store.commit('task/SET_EDIT_DRAWER', false)
            }
            if(this.newsCreate) {
                this.$store.commit('dashboard/TOGGLE_EDIT_DRAWER', false)
            }
        },
        newsCheck() {
            if(this.taskCreate) {
                this.$store.commit('task/SET_EDIT_DRAWER', false)
            }
            if(this.meetingsCreate) {
                this.$store.commit('meeting/SET_EDIT_DRAWER', { show: false, model: 'main' })
            }
        },
        checkPage() {
            if(this.taskCreate) {
                this.$store.commit('task/SET_EDIT_DRAWER', false)
            }
            if(this.meetingsCreate) {
                this.$store.commit('meeting/SET_EDIT_DRAWER', { show: false, model: 'main' })
            }
            if(this.newsCreate) {
                this.$store.commit('dashboard/TOGGLE_EDIT_DRAWER', false)
            }
        }
    },
    mounted() {
        if ("launchQueue" in window && "targetURL" in window.LaunchParams.prototype) {
            window.launchQueue.setConsumer(launchParams => {
                if (launchParams.targetURL) {
                    try {
                        if(launchParams.targetURL.includes('createTask')) {
                            this.taskCheck()
                            this.$store.commit('task/SET_EDIT_DRAWER', true)
                        } else if(launchParams.targetURL.includes('createMeetings')) {
                            this.meetingsCheck()
                            this.$store.commit('meeting/SET_EDIT_DRAWER', { show: true, model: 'main' })
                        } else if(launchParams.targetURL.includes('createNews')) {
                            this.newsCheck()
                            this.$store.commit('dashboard/TOGGLE_EDIT_DRAWER', true)
                        } else {
                            this.checkPage()
                            const link = new URL(launchParams.targetURL)
                            const query = {}
                            link.searchParams.forEach((value, key) => {
                                query[key] = value
                            })
                            const currentFullPath = this.$route.fullPath
                            const targetFullPath = link.pathname + link.search + (link.hash || '')
                            if(link.pathname && currentFullPath !== targetFullPath) {
                                this.$router.push({
                                    path: link.pathname,
                                    query,
                                    hash: link.hash || undefined
                                })
                            }
                        }
                    } catch(e) {
                        console.log(e)
                    }
                }
            })
        }
    }
}
