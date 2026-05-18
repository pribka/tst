import axios from '@/config/axios'

export default {
    getFiles({ commit }, { rootId, folderId, params }) {
        params = params || {}
        const isFolder = !!folderId
        if(isFolder)
            params.folder = folderId
    
        const fileListKey = isFolder ? folderId : rootId
        
        return new Promise((resolve, reject) => {
            axios.get(`attachments/${ rootId }/`, { params })
                .then(({ data }) => {
                    commit('SET_FILE_LIST', {
                        data: data, 
                        key: fileListKey,
                        page: params.page,
                    })
                    resolve(data)
                })
                .catch(error => {
                    reject(error)
                })
        }) 
    },
    getFoundFiles({ commit }, { rootId, folderId, params }) {
        params = params || {}
        const isFolder = !!folderId
        if(isFolder)
            params.folder = folderId
    
        const fileListKey = 'found_files'
        
        return new Promise((resolve, reject) => {
            axios.get(`attachments/${ rootId }/`, { params })
                .then(({ data }) => {
                    commit('SET_FILE_LIST', {
                        data: data, 
                        key: fileListKey,
                        page: params.page,
                    })
                    resolve(data)
                })
                .catch(error => {
                    reject(error)
                })
        }) 
    },
    getMyFiles({ commit }, { folderId, params }) {
        params = params || {}
        const isFolder = !!folderId
        if(isFolder)
            params.folder = folderId
    
        const fileListKey = isFolder ? folderId : 'my_files'
        return new Promise((resolve, reject) => {
            axios.get(`files/`, { params })
                .then(({ data }) => {
                    commit('SET_FILE_LIST', {
                        data: data,
                        key: fileListKey,
                        page: params.page
                    })
                    resolve(data)
                })
                .catch(error => {
                    reject(error)
                })
        })
    },
    getTrashFiles({ commit }, { folderId, params }) {
        params = params || {}
        const isFolder = !!folderId
        if(isFolder)
            params.folder = folderId

        const fileListKey = isFolder ? folderId : 'trash'
        return new Promise((resolve, reject) => {
            axios.get(`files/trash/`, { params })
                .then(({ data }) => {
                    commit('SET_FILE_LIST', {
                        data: data,
                        key: fileListKey,
                        page: params.page
                    })
                    resolve(data)
                })
                .catch(error => {
                    reject(error)
                })
        })
    },
    uploadFiles({ commit }, { files, rootId, folderId }) {
        const isFolder = !!folderId
        folderId = isFolder ? folderId : null
        const fileListKey = isFolder ? folderId : rootId
        return new Promise((resolve, reject) => {
            axios.post(`attachments/${ rootId }/add_files/`, {
                files: files,
                folder: folderId
            })
                .then(({ data }) => {
                    const alreadyExistFiles = []
                    const filesToAdd = data.filter(file => {
                        if(file.created)
                            return file
                        alreadyExistFiles.push(file)
                    })

              
                    commit('ADD_FILE', {
                        data: filesToAdd, 
                        key: fileListKey
                    })
                    resolve(alreadyExistFiles)
                })
                .catch(error => {
                    reject(error)
                })
        }) 
    },
    createFolder({ commit }, { folderName, folderDesc, rootId, folderId }) {
        const isFolder = !!folderId
        folderId = isFolder ? folderId : null
        const fileListKey = isFolder ? folderId : rootId
        return new Promise((resolve, reject) => {
            axios.post(`attachments/${ rootId }/add_folder/`, {
                name: folderName,
                description: folderDesc,
                parent: folderId,
            })
                .then(({ data }) => {
                    commit('ADD_FILE', {
                        data: data, 
                        key: fileListKey
                    })
                    resolve(data)
                })
                .catch(error => {
                    reject(error)
                })
        }) 
    },
    createMyFolder({ commit }, { folderName, folderDesc, folderId }) {
        const isFolder = !!folderId
        folderId = isFolder ? folderId : null
        // const fileListKey = isFolder ? folderId : rootId
        const fileListKey = isFolder ? folderId : 'my_files'
        return new Promise((resolve, reject) => {
            axios.post(`files/add_folder/`, {
                name: folderName,
                description: folderDesc,
                parent: folderId,
            })
                .then(({ data }) => {
                    commit('ADD_FILE', {
                        data: data, 
                        key: fileListKey
                    })
                    resolve(data)
                })
                .catch(error => {
                    reject(error)
                })
        }) 
    },
    deleteFiles({ commit }, { rootId, folderId, files, folders }) {
        const isFolder = !!folderId
        folderId = isFolder ? folderId : null
        const fileListKey = isFolder ? folderId : rootId
        
        const folderIds = [],
            fileIds = []
        
        for(const file of files)
            fileIds.push(file.id)
        for(const file of folders)
            folderIds.push(file.id)

        return new Promise((resolve, reject) => {
            axios.post(`attachments/${ rootId }/remove_files/`, { 
                folder: folderId,
                files: fileIds,
                folders: folderIds

            })
                .then(({ data }) => {
                    commit('REMOVE_FILES', {
                        removedFiles: [...folders, ...files], 

                        key: fileListKey
                    })
                    resolve(data)
                })
                .catch(error => {
                    reject(error)
                })
        })
    },
    deleteFilesFromTrash({ commit }, { folderId, files, folders }) {
        const isFolder = !!folderId
        folderId = isFolder ? folderId : null
        const fileListKey = isFolder ? folderId : 'trash'

        const folderIds = [],
            fileIds = []
        
        for(const file of files)
            fileIds.push(file.id)
        for(const file of folders)
            folderIds.push(file.id)

        return new Promise((resolve, reject) => {
            axios.post(`files/delete_files/`, { 
                folder: folderId,
                files: fileIds,
                folders: folderIds
            })
                .then(({ data }) => {
                    commit('REMOVE_FILES', {
                        removedFiles: [...folders, ...files], 
                        key: fileListKey
                    })
                    resolve(data)
                })
                .catch(error => {
                    reject(error)
                })
        })
    },
    deleteMyFiles({ commit }, { folderId, files, folders }) {
        const isFolder = !!folderId
        folderId = isFolder ? folderId : null
        const fileListKey = isFolder ? folderId : 'my_files'

        const folderIds = [],
            fileIds = []
        
        for(const file of files)
            fileIds.push(file.id)
        for(const file of folders)
            folderIds.push(file.id)
        return new Promise((resolve, reject) => {
            axios.post(`files/remove_files/`, { 
                folder: folderId,
                files: fileIds,
                folders: folderIds
            })
                .then(({ data }) => {
                    commit('ADD_FILE', { 
                        data: [...folders, ...files], 
                        key: 'trash'
                    })
                    commit('REMOVE_FILES', {
                        removedFiles: [...folders, ...files], 
                        key: fileListKey
                    })
                    resolve(data)
                })
                .catch(error => {
                    reject(error)
                })
        })
    },

    // "folder": - родительская папка

    // "folders":[список папок для удаления]
    // }
    // Внимание! Позволяет удалять только пустые папки. Непустые папки удалить запрещено, так как еще не отработано удаление фалов.


    renameFile({ commit }, { rootId, folderId, fileId, newFileName, newFileDesc }) {
        const isFolder = !!folderId
        folderId = isFolder ? folderId : null
        const fileListKey = isFolder ? folderId : rootId
        return new Promise((resolve, reject) => {
            axios.patch(`attachments/${ fileId }/update_file/`, {
                name: newFileName,
                description: newFileDesc
            })
                .then(({ data }) => {
                    commit('RENAME_FILE', {
                        fileId: fileId,
                        newFileName: newFileName,
                        newFileDesc: newFileDesc,
                        key: fileListKey
                    })
                    resolve(data)
                })
                .catch(error => {
                    reject(error)
                })
        }) 
    },
    renameMyFile({ commit }, { folderId, fileId, newFileName, newFileDesc }) {
        const isFolder = !!folderId
        folderId = isFolder ? folderId : null
        const fileListKey = isFolder ? folderId : 'my_files'
        return new Promise((resolve, reject) => {
            axios.patch(`files/update_file/`, {
                name: newFileName,
                description: newFileDesc
            })
                .then(({ data }) => {
                    commit('RENAME_FILE', {
                        fileId: fileId,
                        newFileName: newFileName,
                        newFileDesc: newFileDesc,
                        key: fileListKey
                    })
                    resolve(data)
                })
                .catch(error => {
                    reject(error)
                })
        }) 
    },
    renameFolder({ commit }, { rootId, folderId, fileId, newFileName, newFileDesc }) {
        const isFolder = !!folderId
        folderId = isFolder ? folderId : null
        const fileListKey = isFolder ? folderId : rootId
        return new Promise((resolve, reject) => {
            axios.put(`attachments/${ rootId }/update_folder/`, {
                id: fileId,
                name: newFileName,
                description: newFileDesc
            })
                .then(({ data }) => {
                    commit('RENAME_FILE', {
                        fileId: fileId,
                        newFileName: newFileName,
                        newFileDesc: newFileDesc,
                        key: fileListKey
                    })
                    resolve(data)
                })
                .catch(error => {
                    reject(error)
                })
        }) 
    },
    renameMyFolder({ commit }, { folderId, fileId, newFileName, newFileDesc }) {
        const isFolder = !!folderId
        folderId = isFolder ? folderId : null
        const fileListKey = isFolder ? folderId : 'my_files'
        return new Promise((resolve, reject) => {
            axios.put(`files/update_folder/`, {
                id: fileId,
                name: newFileName,
                description: newFileDesc
            })
                .then(({ data }) => {
                    commit('RENAME_FILE', {
                        fileId: fileId,
                        newFileName: newFileName,
                        newFileDesc: newFileDesc,
                        key: fileListKey
                    })
                    resolve(data)
                })
                .catch(error => {
                    reject(error)
                })
        }) 
    },
    fileCount({ commit }, { rootId, folderId}) {
        const params = folderId ? { folder: folderId} : {} 
        return new Promise((resolve, reject) => {
            axios.get(`attachments/${ rootId }/aggregate/`, { params })
                .then(({ data }) => {
              
                    // commit('RENAME_FILE', {
                    //     fileId: fileId,
                    //     newFileName: newFileName,
                    //     key: fileListKey
                    // })
                    resolve(data)
                })
                .catch(error => {
                    reject(error)
                })
        }) 
    },
    myFileCount({ commit }, { folderId }) {
        return new Promise((resolve, reject) => {
            axios.get(`files/aggregate/`, {
                params: {
                    folder: folderId
                }
            })
                .then(({ data }) => {
                    resolve(data)
                })
                .catch(error => {
                    reject(error)
                })
        }) 
    },
    moveFiles({ commit }, { rootId, from, where, files}) {
        const fileList = [],
            foldersList = []

        for(const file of files)
            if(file.obj_type === 'folder')
                foldersList.push(file.id)
            else
                fileList.push(file.id)

        return new Promise((resolve, reject) => {
            axios.post(`attachments/${ rootId }/move_files/`, { 
                folder: where,
                files: fileList,
                folders: foldersList,
                current_folder: rootId ? null : from
            })
                .then(({ data }) => {

                    const movedFiles = [...fileList, ...foldersList]
                    commit('ADD_FILE', { 
                        data: files, 
                        key: where || rootId
                    })
                    commit('REMOVE_FILES', { 
                        removedFiles: movedFiles, 
                        key: from
                    })

                    resolve(data)
                })
                .catch(error => {
                    reject(error)
                })
        }) 
    },
    moveMyFiles({ commit }, { from, where, files}) {
        const fileList = [],
            foldersList = []

        for(const file of files)
            if(file.obj_type === 'folder')
                foldersList.push(file.id)
            else
                fileList.push(file.id)

        return new Promise((resolve, reject) => {
            axios.post(`files/move_files/`, { 
                folder: where,
                files: fileList,
                folders: foldersList,
                current_folder: 'my_files' ? null : from
            })
                .then(({ data }) => {
                    commit('ADD_FILE', { 
                        data: files, 
                        key: where || 'my_files'
                    })
                    commit('REMOVE_FILES', { 
                        removedFiles: files, 
                        key: from
                    })

                    resolve(data)
                })
                .catch(error => {
                    reject(error)
                })
        }) 
    },
    downloadFolderAsZIP({ commit }, { rootId, folderId }) {
        return new Promise((resolve, reject) => {
            axios.post(`attachments/${ rootId }/zip/`, { 
                folder: folderId,
            })
                .then(({ data }) => {
                    resolve(data)
                })
                .catch(error => {
                    reject(error)
                })
        }) 
    },
    downloadMyFolderAsZIP({ commit }, { folderId }) {
        return new Promise((resolve, reject) => {
            axios.post(`files/zip/`, { 
                folder: folderId,
            })
                .then(({ data }) => {
                    resolve(data)
                })
                .catch(error => {
                    reject(error)
                })
        }) 
    },
    restoreFiles({ commit }, { folderId, files, folders }) {
        const fileList = [],
            foldersList = []

        for(const file of files)
            fileList.push(file.id)
            
        for(const file of folders)
            foldersList.push(file.id)

        const isFolder = !!folderId
        folderId = isFolder ? folderId : null
        const fileListKey = isFolder ? folderId : 'my_files'

        return new Promise((resolve, reject) => {
            axios.post(`files/restore/`, { 
                folder: folderId,
                files: fileList,
                folders: foldersList
            })
                .then(({ data }) => {
                    const movedFiles = [...fileList, ...foldersList]

                    commit('ADD_FILE', { 
                        data: [...files, ...folders], 
                        key: 'my_files'
                    })
                    commit('REMOVE_FILES', { 
                        removedFiles: [...files, ...folders], 
                        key: 'trash'
                    })

                    resolve(data)
                })
                .catch(error => {
                    reject(error)
                })
        })
    },
    getFoldersForRestore({ commit }, { folderId }) {
        const params = {}
        const isFolder = !!folderId
        if(isFolder)
            params.folder = folderId
        const key = 'restore-'
        const fileListKey = isFolder ? `${key}${folderId}` : key+'my_files'

        return new Promise((resolve, reject) => {
            axios.get(`files/folders/`, { params })
                .then(({ data }) => {
                    commit('SET_FILE_LIST', {
                        data: data,
                        key: fileListKey,
                        page: params.page
                    })

                    resolve(data)
                })
                .catch(error => {
                    reject(error)
                })
        })
    },
    clearTrash({ commit }) {
        return new Promise((resolve, reject) => {
            axios.post(`files/trash/clear/`)
                .then(({ data }) => {
                    commit('CLEAR_ALL', 'trash')

                    resolve(data)
                })
                .catch(error => {
                    reject(error)
                })
        })
    }
}