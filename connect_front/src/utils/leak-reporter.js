// leak-reporter.js
export default {
    install(Vue){
        const live = {}
        Vue.mixin({
            beforeCreate(){
                const n = this.$options.name || 'Anonymous'
                live[n] = (live[n] || 0) + 1
            },
            beforeDestroy(){
                const n = this.$options.name || 'Anonymous'
                live[n] = (live[n] || 0) - 1
            }
        })
        setInterval(()=>{
            const rows = Object.entries(live).filter(([k,v])=>v>0).sort((a,b)=>b[1]-a[1]).slice(0,20)
            console.table(rows)
        },3000)
        window.__liveComponents = live
    }
}
