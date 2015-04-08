import PageService from '../services/PageService';
import AppDispatcher from '../dispatcher';


const PageTypeActions = {
    populate(data) {
        AppDispatcher.dispatch({
            eventName: 'PAGETYPES_POPULATE',
            data
        });
    }
}

export default PageTypeActions;
