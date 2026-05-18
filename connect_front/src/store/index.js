import Vue from 'vue'
import Vuex from 'vuex'

import state from './state'
import mutations from './mutations'
import actions from './actions'
import modules from './modules'
import recentUsersSyncPlugin from './plugins/recentUsersSyncPlugin'

Vue.use(Vuex)

export default new Vuex.Store({
    state,
    mutations,
    actions,
    modules,
    plugins: [recentUsersSyncPlugin]
})
