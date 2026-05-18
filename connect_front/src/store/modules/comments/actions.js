import axios from '@/config/axios'

export default {
    getReactions({ commit, state }) {
        return new Promise((resolve, reject) => {
            if(state.reactions.length)
                resolve(state.reactions)
            else {
                axios.get('/reactions/', {
                    params: {
                        page_size: 10
                    }
                })
                    .then(({ data }) => {
                        if(data?.results?.length)
                            commit('SET_REACTIONS', data.results)
                        resolve(data)
                    })
                    .catch(e => {
                        console.log(e)
                        reject(e)
                    })
            }
        })
    },
}
