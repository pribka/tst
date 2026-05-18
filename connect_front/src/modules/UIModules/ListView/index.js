import List from './List.vue'
import ListItem from './ListItem.vue'

export default {
    install(Vue) {
        Vue.component('ListView', List)
        Vue.component('ListViewItem', ListItem)
    }
}