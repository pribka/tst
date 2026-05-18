export default {
    methods: {
        fileOpenSwitch(file) {
            this.$nextTick(() => {
                const dropdownRef = this.$refs[`file_dropdown_${file.id}`]
                const dropdown = Array.isArray(dropdownRef) ? dropdownRef[0] : dropdownRef
                if(dropdown && typeof dropdown.openFileDetail === 'function')
                    dropdown.openFileDetail()
            })
        }
    }
}
