import Dashboard from "./general/Dashboard.vue";
import Announcement from "./general/Announcement.vue";
import User from "./general/User.vue";
import Conf from "./general/Conf.vue";
import JudgeServer from "./general/JudgeServer.vue";
import PruneTestCase from "./general/PruneTestCase.vue";
import Problem from "./problem/Problem.vue";
import ProblemList from "./problem/ProblemList.vue";
import ContestList from "./contest/ContestList.vue";
import Contest from "./contest/Contest.vue";
import Login from "./general/Login.vue";
import Home from "./Home.vue";
import ProblemImportOrExport from "./problem/ImportAndExport.vue";
import AIModel from "./general/AIModel.vue";
import AIGenerateProblem from "./problem/AIGenerateProblem.vue";
import Init_knowledge from "./ai/Init_knowledge.vue";
const GenerateTags = () => import("./problem/GenerateTags.vue");
export {
  Announcement,
  User,
  Conf,
  JudgeServer,
  Problem,
  ProblemList,
  Contest,
  ContestList,
  Login,
  Home,
  PruneTestCase,
  Dashboard,
  ProblemImportOrExport,
  AIModel,
  GenerateTags,
  AIGenerateProblem,
  Init_knowledge
};
