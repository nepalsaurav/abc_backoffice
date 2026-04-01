
import Dasboard from "./views/Dashboard.svelte"
import ImportTransactions from "./views/ImportTransactions.svelte"
import CorporateActions from "./views/CorporateAction.svelte"
import NotFound from "./views/NotFound.svelte"



export const routes = {
    // Exact path
    '/': Dasboard,
    "/import_transactions": ImportTransactions,
    "/corporate_action": CorporateActions,
    '*': NotFound
}