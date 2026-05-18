import moment from 'moment'

export default {
    isObjectiveListEmpty(state) {
        return state.objectives.length === 0
    },
    objectivesNumber(state) {
        return state.objectives.length
    },
    averageProgress(state) {
        if (state.objectives.length) {
            return parseInt(100 * state.objectives.reduce((sum, result) => sum + result.progress, 0) / state.objectives.length)
        } else {
            return 0
        }
    },
    atRisk(state) {
        return typeof state.objectivesCount.at_risk === 'number' && !Number.isNaN(state.objectivesCount.at_risk) ? state.objectivesCount.at_risk : '-'
    },
    achieved(state) {
        return typeof state.objectivesCount.achieved === 'number' && !Number.isNaN(state.objectivesCount.achieved) ? state.objectivesCount.achieved : '-'
    },
    missionEditDate(state) {
        return state.mission?.updated_at ? moment(state.mission.updated_at).format('DD.MM.YYYY') : '-'
    },
    isMissionEditAvailable(state) {
        return state?.actions?.create_mission?.availability || false
    },
    isObjectiveCreateAvailable(state) {
        return state?.actions?.create_objectives?.availability || false
    },
    statusLabelMap(state) {
        return state.statuses.reduce((map, status) => {
            map[status.code] = {
                label: status.name,
                hex_color: status.hex_color
            }
            return map
        }, {})
    },
    anyLoading(state) {
        return state.addMetricLoading ||
               state.departmentsLoading ||
               state.loading ||
               state.missionLoading ||
               state.objectiveDetailLoading ||
               state.objectivesCountLoading ||
               state.objectivesLoading ||
               state.remindersLoading ||
               state.stakeholdersLoading ||
               false
    },
    objectiveVisibility(state) {
        let objectiveVisibility = undefined
        if (state.objectiveDetail) {
            if (state.objectiveDetail.is_public) {
                objectiveVisibility = 'isPublic'
            } else if (state.objectiveDetail.visors.length) {
                objectiveVisibility = 'withVisors'
            } else {
                objectiveVisibility = 'onlyOwner'
            }
        }
        return objectiveVisibility
    }
}