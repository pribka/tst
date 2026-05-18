export default {
    methods: {
        getDefaultVisors(id) {
            const url = `work_groups/workgroups/${id}/default_visors/`
            return this.$http.get(url)
                .then(({ data }) => data)
        },
        haveSameIds(list1, list2) {
            const ids1 = list1.map(i => i.id).sort();
            const ids2 = list2.map(i => i.id).sort();
            if (ids1.length !== ids2.length) return false;
            return ids1.every((id, i) => id === ids2[i]);
        },

        requestReplaceVisors({ reason, id }) {
            this.getDefaultVisors(id)
                .then(defaultVisors => {
                    if (defaultVisors?.length && !this.haveSameIds(defaultVisors, this.form.visors)) {
                        this.$refs.replaceVisorsModalRef.open({ reason, defaultVisors })
                    }
                })
                .catch(error => {
                    // Не удалось получить наблюдателей по умолчанию
                    if(error?.status === 404) {
                        if(reason === 'group') {
                            this.$message.error(this.$t('task.visor_group_not_found'), 6)
                            if(this.formInject?.workgroup)
                                this.formInject.workgroup = null
                            if(this.form?.workgroup)
                                this.form.workgroup = null
                            
                        } 
                        if(reason === 'project') {
                            this.$message.error(this.$t('task.visor_project_not_found'), 6)
                            if(this.formInject?.project)
                                this.formInject.project = null
                            if(this.form?.project)
                                this.form.project = null
                        }
                    } else {
                        this.$message.error(this.$t("task.error_with_set_default_visors"))
                    }
                    console.error(error)
                })
        }

    }
}