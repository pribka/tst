export default {
    getTablePageSize: state => tableName => {
        const pageSize = Number(localStorage.getItem(`meetingTable_${tableName}`))
        return pageSize 
    }
}