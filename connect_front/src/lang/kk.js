import base from './mobules/base/kk'
import task from '@apps/vue2TaskComponent/lang/kk'
import chat from '@apps/vue2ChatComponent/lang/kk'
import profiler from './mobules/profiler/kk'
import group from '@apps/Groups/lang/kk'
import project from '@apps/Projects/lang/kk'
import noty from '@apps/Notifications/lang/kk'
import support from '@apps/Support/lang/kk'
import meeting from '@apps/vue2MeetingComponent/lang/kk'
import files from '@apps/vue2Files/lang/kk'
import upload from './mobules/upload/kk'
import reports from './mobules/reports/kk'
import reports1 from '@apps/Reports/lang/kk'
import calendar from '@apps/Calendar/lang/kk'
import table from './mobules/table/kk'
import dashboard from '@apps/Dashboard/lang/kk'
//import inquiries from '@apps/Inquiries/lang/kk'
import history from '@apps/History/lang/kk'
import comment from '@apps/vue2CommentsComponent/lang/kk'
import invest from '@apps/InvestProject/lang/kk'
import sports from '@apps/SportsFacilities/lang/kk'
import gallery from '@apps/UIModules/Gallery/lang/kk'
import gantt from '@apps/UIModules/Gant/lang/kk'
import okr from '@apps/OKR/lang/kk'
//import team from '@apps/Team/lang/kk'
import helpdesk from '@apps/HelpDesk/lang/kk'
import workplan from '@apps/WorkPlan/lang/kk'
import planner from '@apps/Planner/lang/kk'
import consolidation from '@apps/Consolidation/lang/kk'
import approvals from '@apps/RequestApprovals/lang/kk'
import ai_assistant from '@apps/AIAssistant/lang/kk'
import directories from '@apps/Directories/lang/kk'
import deals from '@apps/Deals/lang/kk'
import remote from './mobules/remote/kk'
import onlyoffice from './mobules/onlyoffice/kk'
import emoji from './mobules/emoji/kk'

export default {
    ...base,
    ...remote,
    ...approvals,
    ...consolidation,
    ...workplan,
    ...planner,
    ...support,
    ...noty,
    ...task,
    ...chat,
    ...profiler,
    ...group,
    ...meeting,
    ...files,
    ...upload,
    ...reports1,
    ...reports,
    ...calendar,
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
    ...ai_assistant,
    ...directories,
    ...deals,
    ...onlyoffice,
    ...emoji,
}
