import Vue from 'vue'

const normalizeFiles = data => Array.isArray(data) ? data : [data]

const mergeUniqueFiles = (...lists) => {
    const mergedFiles = []
    const addedIds = new Set()

    lists.flat().forEach(file => {
        if(!file)
            return

        const fileId = file.id
        if(fileId !== undefined && addedIds.has(fileId))
            return

        if(fileId !== undefined)
            addedIds.add(fileId)

        mergedFiles.push(file)
    })

    return mergedFiles
}

export default {
    SET_FILE_LIST(state, { data, key, page }) {
        data.page = page
        const incomingFiles = data.results || []
        
        if(state.files[key]) {
            const existFileList = state.files[key].results
            state.files[key] = data
            Vue.set(state.files[key], 'results', mergeUniqueFiles(incomingFiles, existFileList))
        } else {
            data.results = incomingFiles
            Vue.set(state.files, key, data)
        }
    },
    ADD_FILE(state, { data, key }) {
        if(!state.files[key]) {
            Vue.set(state.files, key, {
                results: []
            })
        }

        const filesToAdd = normalizeFiles(data)
        Vue.set(state.files[key], 'results', mergeUniqueFiles(filesToAdd, state.files[key].results))
    },
    REMOVE_FILES(state, {removedFiles, key}) {
        if(!state.files[key]?.results?.length)
            return

        const removedIds = new Set(removedFiles.map(file => file.id))
        Vue.set(
            state.files[key],
            'results',
            state.files[key].results.filter(file => !removedIds.has(file.id))
        )
    },
    SET_FILE_VIEW_TYPE(state, viewType) {
        localStorage.setItem('filesViewType', viewType)
    },
    RENAME_FILE(state, { fileId, newFileName, newFileDesc, key }) {
        const renamingFile = state.files[key].results.find(file => file.id === fileId)
        renamingFile.name = newFileName
        renamingFile.description = newFileDesc
    },
    CLEAR_ALL(state, sourceId) {
        if(state.files[sourceId]) {
            state.files[sourceId].next = true
            state.files[sourceId].page = 0
            state.files[sourceId].results.splice(0)
        }
    }
}
