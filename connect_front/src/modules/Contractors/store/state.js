/* available contractors types:
    - contractors
    - leads
*/
const contractorsType = localStorage.getItem('contractorsType') || 'contractors'

export default {
    contractors: {},
    contractorsTable: {},
    contractorsType: contractorsType,
    models: {
        contractors: 'catalogs.ContractorModel',
        leads: 'catalogs.PotentialContractorModel',
    },
    activeGridType: null,
    gridType: [],
}