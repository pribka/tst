import base from './mobules/base/ru'
import task from '@apps/vue2TaskComponent/lang/ru'
import chat from '@apps/vue2ChatComponent/lang/ru'
import profiler from './mobules/profiler/ru'
import group from '@apps/Groups/lang/ru'
import project from '@apps/Projects/lang/ru'
import noty from '@apps/Notifications/lang/ru'
import support from '@apps/Support/lang/ru'
import meeting from '@apps/vue2MeetingComponent/lang/ru'
import files from '@apps/vue2Files/lang/ru'
import upload from './mobules/upload/ru'
import reports from './mobules/reports/ru'
import reports1 from '@apps/Reports/lang/ru'
import calendar from '@apps/Calendar/lang/ru'
//import auth from './mobules/auth/ru'
import table from './mobules/table/ru'
import dashboard from '@apps/Dashboard/lang/ru'
//import inquiries from '@apps/Inquiries/lang/ru'
import history from '@apps/History/lang/ru'
import comment from '@apps/vue2CommentsComponent/lang/ru'
import invest from '@apps/InvestProject/lang/ru'
import sports from '@apps/SportsFacilities/lang/ru'
import gallery from '@apps/UIModules/Gallery/lang/ru'
import gantt from '@apps/UIModules/Gant/lang/ru'
import okr from '@apps/OKR/lang/ru'
//import team from '@apps/Team/lang/ru'
import consolidation from '@apps/Consolidation/lang/ru'
import helpdesk from '@apps/HelpDesk/lang/ru'
import workplan from '@apps/WorkPlan/lang/ru'
import planner from '@apps/Planner/lang/ru'
import approvals from '@apps/RequestApprovals/lang/ru'
import ai_assistant from '@apps/AIAssistant/lang/ru'
import directories from '@apps/Directories/lang/ru'
import deals from '@apps/Deals/lang/ru'
import remote from './mobules/remote/ru'
import onlyoffice from './mobules/onlyoffice/ru'
import emoji from './mobules/emoji/ru'

export default {
    ...base,
    ...remote,
    ...approvals,
    ...workplan,
    ...planner,
    ...consolidation,
    ...reports1,
    ...support,
    ...noty,
    ...task,
    ...chat,
    ...profiler,
    ...group,
    ...meeting,
    ...files,
    ...upload,
    ...reports,
    ...calendar,
    //...auth,
    ...table,
    ...dashboard,
    //...inquiries,
    ...history,
    ...comment,
    ...invest,
    ...sports,
    ...gallery,
    ...project,
    ...gantt,
    ...okr,
    //...team,
    ...helpdesk,
    ...directories,
    ...deals,
    ...ai_assistant,
    ...onlyoffice,
    ...emoji,
}
