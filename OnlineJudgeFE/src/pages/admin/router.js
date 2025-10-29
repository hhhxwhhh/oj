import Vue from "vue";
import VueRouter from "vue-router";
// 引入 view 组件
import {
  Announcement,
  Conf,
  Contest,
  ContestList,
  Home,
  JudgeServer,
  Login,
  Problem,
  ProblemList,
  User,
  PruneTestCase,
  Dashboard,
  ProblemImportOrExport,
  AIModel
} from "./views";
Vue.use(VueRouter);
import ContestAnalytics from "./views/contest/ContestAnalytics.vue";
import Init_knowledge from "./views/ai/Init_knowledge.vue";
import AssignmentDetail from "./views/assignment/AssignmentDetail.vue";
import CreateAssignment from "./views/assignment/CreateAssignment.vue";
import AssignmentList from "./views/assignment/AssignmentList.vue";
import StudentProgress from "./views/assignment/StudentProgress.vue";
const GenerateTags = () => import("./views/problem/GenerateTags.vue");

export default new VueRouter({
  mode: "history",
  base: "/admin/",
  scrollBehavior: () => ({ y: 0 }),
  routes: [
    {
      path: "/login",
      name: "login",
      component: Login
    },
    {
      path: "/init_knowledge",
      name: "init_knowledge",
      component: Init_knowledge
    },
    {
      path: "/",
      component: Home,
      children: [
        {
          path: "",
          name: "dashboard",
          component: Dashboard
        },
        {
          path: "/announcement",
          name: "announcement",
          component: Announcement
        },
        {
          path: "/user",
          name: "user",
          component: User
        },
        {
          path: "/conf",
          name: "conf",
          component: Conf
        },
        {
          path: "/judge-server",
          name: "judge-server",
          component: JudgeServer
        },
        {
          path: "/prune-test-case",
          name: "prune-test-case",
          component: PruneTestCase
        },
        {
          path: "/ai-model",
          name: "ai-model",
          component: AIModel
        },
        {
          path: "/problems",
          name: "problem-list",
          component: ProblemList
        },
        {
          path: "/problem/create",
          name: "create-problem",
          component: Problem
        },
        {
          path: "/problem/edit/:problemId",
          name: "edit-problem",
          component: Problem
        },
        {
          path: "/admin/ai/generate-problem",
          component: resolve =>
            require(["@admin/views/problem/AIGenerateProblem.vue"], resolve),
          name: "AIGenerateProblem",
          meta: { title: "AI Generate Problem", permission: "admin" }
        },
        {
          path: "/problem/batch_ops",
          name: "problem_batch_ops",
          component: ProblemImportOrExport
        },
        {
          path: "/contest/create",
          name: "create-contest",
          component: Contest
        },
        {
          path: "/contest",
          name: "contest-list",
          component: ContestList
        },
        {
          path: "/contest/:contestId/edit",
          name: "edit-contest",
          component: Contest
        },
        {
          path: "/contest/:contestId/announcement",
          name: "contest-announcement",
          component: Announcement
        },
        {
          path: "/contest/:contestId/problems",
          name: "contest-problem-list",
          component: ProblemList
        },
        {
          path: "/contest/:contestId/problem/create",
          name: "create-contest-problem",
          component: Problem
        },
        {
          path: "/contest/:contestId/problem/:problemId/edit",
          name: "edit-contest-problem",
          component: Problem
        },
        {
          path: "/contest/analytics",
          name: "contest-analytics",
          component: ContestAnalytics
        },
        {
          path: "admin/generate-tags",
          name: "generate-tags",
          component: GenerateTags,
          meta: { requiresAuth: true, title: "Generate Tags" }
        },
        {
          path: "/assignment",
          name: "assignment-list",
          component: AssignmentList
        },
        {
          path: "/assignment/create",
          name: "create-assignment",
          component: CreateAssignment
        },
        {
          path: "/assignment/:assignmentId",
          name: "assignment-detail",
          component: AssignmentDetail
        },
        {
          path:
            "/assignment/:assignmentId/student/:studentAssignmentId/progress",
          name: "student-progress",
          component: StudentProgress
        }
      ]
    },
    {
      path: "*",
      redirect: "/login"
    }
  ]
});
