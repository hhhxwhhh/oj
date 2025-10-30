import Vue from "vue";
import router from "./router";
import axios from "axios";
import utils from "@/utils/utils";

Vue.prototype.$http = axios;
axios.defaults.baseURL = "/api";
axios.defaults.xsrfHeaderName = "X-CSRFToken";
axios.defaults.xsrfCookieName = "csrftoken";

export default {
  // 登录
  login(username, password) {
    return ajax("login", "post", {
      data: {
        username,
        password
      }
    });
  },
  logout() {
    return ajax("logout", "get");
  },
  getProfile() {
    return ajax("profile", "get");
  },
  // 获取公告列表
  getAnnouncementList(offset, limit) {
    return ajax("admin/announcement", "get", {
      params: {
        paging: true,
        offset,
        limit
      }
    });
  },
  // 删除公告
  deleteAnnouncement(id) {
    return ajax("admin/announcement", "delete", {
      params: {
        id
      }
    });
  },
  // 修改公告
  updateAnnouncement(data) {
    return ajax("admin/announcement", "put", {
      data
    });
  },
  // 添加公告
  createAnnouncement(data) {
    return ajax("admin/announcement", "post", {
      data
    });
  },
  // 获取用户列表
  getUserList(offset, limit, keyword) {
    let params = { paging: true, offset, limit };
    if (keyword) {
      params.keyword = keyword;
    }
    return ajax("admin/user", "get", {
      params: params
    });
  },
  // 获取单个用户信息
  getUser(id) {
    return ajax("admin/user", "get", {
      params: {
        id
      }
    });
  },
  // 编辑用户
  editUser(data) {
    return ajax("admin/user", "put", {
      data
    });
  },
  deleteUsers(id) {
    return ajax("admin/user", "delete", {
      params: {
        id
      }
    });
  },
  importUsers(users) {
    return ajax("admin/user", "post", {
      data: {
        users
      }
    });
  },
  generateUser(data) {
    return ajax("admin/generate_user", "post", {
      data
    });
  },
  getLanguages() {
    return ajax("languages", "get");
  },
  getSMTPConfig() {
    return ajax("admin/smtp", "get");
  },
  createSMTPConfig(data) {
    return ajax("admin/smtp", "post", {
      data
    });
  },
  editSMTPConfig(data) {
    return ajax("admin/smtp", "put", {
      data
    });
  },
  testSMTPConfig(email) {
    return ajax("admin/smtp_test", "post", {
      data: {
        email
      }
    });
  },
  getWebsiteConfig() {
    return ajax("admin/website", "get");
  },
  editWebsiteConfig(data) {
    return ajax("admin/website", "post", {
      data
    });
  },
  getJudgeServer() {
    return ajax("admin/judge_server", "get");
  },
  deleteJudgeServer(hostname) {
    return ajax("admin/judge_server", "delete", {
      params: {
        hostname: hostname
      }
    });
  },
  updateJudgeServer(data) {
    return ajax("admin/judge_server", "put", {
      data
    });
  },
  getInvalidTestCaseList() {
    return ajax("admin/prune_test_case", "get");
  },
  pruneTestCase(id) {
    return ajax("admin/prune_test_case", "delete", {
      params: {
        id
      }
    });
  },
  createContest(data) {
    return ajax("admin/contest", "post", {
      data
    });
  },
  getContest(id) {
    return ajax("admin/contest", "get", {
      params: {
        id
      }
    });
  },
  editContest(data) {
    return ajax("admin/contest", "put", {
      data
    });
  },
  getContestList(offset, limit, keyword) {
    let params = { paging: true, offset, limit };
    if (keyword) {
      params.keyword = keyword;
    }
    return ajax("admin/contest", "get", {
      params: params
    });
  },
  getContestAnnouncementList(contestID) {
    return ajax("admin/contest/announcement", "get", {
      params: {
        contest_id: contestID
      }
    });
  },
  createContestAnnouncement(data) {
    return ajax("admin/contest/announcement", "post", {
      data
    });
  },
  deleteContestAnnouncement(id) {
    return ajax("admin/contest/announcement", "delete", {
      params: {
        id
      }
    });
  },
  updateContestAnnouncement(data) {
    return ajax("admin/contest/announcement", "put", {
      data
    });
  },
  getProblemTagList(params) {
    return ajax("problem/tags", "get", {
      params
    });
  },
  compileSPJ(data) {
    return ajax("admin/compile_spj", "post", {
      data
    });
  },
  createProblem(data) {
    return ajax("admin/problem", "post", {
      data
    });
  },
  editProblem(data) {
    return ajax("admin/problem", "put", {
      data
    });
  },
  deleteProblem(id) {
    return ajax("admin/problem", "delete", {
      params: {
        id
      }
    });
  },
  getProblem(id) {
    return ajax("admin/problem", "get", {
      params: {
        id
      }
    });
  },
  getProblemList(params) {
    params = utils.filterEmptyValue(params);
    return ajax("admin/problem", "get", {
      params
    });
  },
  getContestProblemList(params) {
    params = utils.filterEmptyValue(params);
    return ajax("admin/contest/problem", "get", {
      params
    });
  },
  getContestProblem(id) {
    return ajax("admin/contest/problem", "get", {
      params: {
        id
      }
    });
  },
  createContestProblem(data) {
    return ajax("admin/contest/problem", "post", {
      data
    });
  },
  editContestProblem(data) {
    return ajax("admin/contest/problem", "put", {
      data
    });
  },
  deleteContestProblem(id) {
    return ajax("admin/contest/problem", "delete", {
      params: {
        id
      }
    });
  },
  makeContestProblemPublic(data) {
    return ajax("admin/contest_problem/make_public", "post", {
      data
    });
  },
  addProblemFromPublic(data) {
    return ajax("admin/contest/add_problem_from_public", "post", {
      data
    });
  },
  getReleaseNotes() {
    return ajax("admin/versions", "get");
  },
  getDashboardInfo() {
    return ajax("admin/dashboard_info", "get");
  },
  getSessions() {
    return ajax("sessions", "get");
  },
  exportProblems(data) {
    return ajax("export_problem", "post", {
      data
    });
  },
  getProblemTagsStats() {
    return ajax("admin/generate_problem_tags", "get");
  },

  generateProblemTags(data) {
    return ajax("admin/generate_problem_tags", "post", {
      data
    });
  },
  bulkOperation(data) {
    return ajax("admin/problem_bulk_operation", "post", {
      data
    });
  },
  generateAIProblem(data) {
    return ajax("ai/problem/generate", "post", {
      data
    });
  },
  // AI Models
  getAIModels() {
    return ajax("admin/ai_model/list", "get");
  },
  createAIModel(data) {
    return ajax("admin/ai_model", "post", {
      data
    });
  },
  updateAIModel(data) {
    return ajax("admin/ai_model", "put", {
      data
    });
  },
  deleteAIModel(id) {
    return ajax("admin/ai_model", "delete", {
      params: {
        id
      }
    });
  },
  createAssignment(data) {
    return ajax("admin/assignments/", "post", {
      data
    });
  },
  getAssignmentList(page, page_size) {
    return ajax("admin/assignments/", "get", {
      params: {
        page,
        page_size
      }
    });
  },

  getAssignment(assignmentId) {
    return ajax(`admin/assignments/${assignmentId}/`, "get");
  },
  updateAssignment(assignmentId, data) {
    return ajax(`admin/assignments/${assignmentId}/`, "put", {
      data
    });
  },
  deleteAssignment(assignmentId) {
    return ajax(`admin/assignments/${assignmentId}/`, "delete");
  },
  getAssignmentProblems(assignmentId) {
    return ajax(`admin/assignments/${assignmentId}/problems/`, "get");
  },
  addProblemToAssignment(assignmentId, data) {
    return ajax(`admin/assignments/${assignmentId}/problems/add/`, "post", {
      data
    });
  },
  removeProblemFromAssignment(assignmentId, problemId) {
    return ajax(
      `admin/assignments/${assignmentId}/problems/${problemId}/`,
      "delete"
    );
  },
  assignAssignmentToStudents(assignmentId, data) {
    return ajax(`admin/assignments/${assignmentId}/assign/`, "post", {
      data
    });
  },
  getAssignedStudents(assignmentId) {
    return ajax(`admin/assignments/${assignmentId}/students/`, "get");
  },
  getStudentAssignmentProgress(studentAssignmentId) {
    return ajax(
      `admin/student-assignments/${studentAssignmentId}/progress/`,
      "get"
    );
  },
  getAssignmentDetailedStatistics(assignmentId) {
    return ajax(
      `admin/assignments/${assignmentId}/detailed-statistics/`,
      "get"
    );
  },
  // 作业分析相关API
  getAssignmentProblemDifficultyStatistics(assignmentId) {
    return ajax(
      `admin/assignments/${assignmentId}/problem-difficulty-statistics/`,
      "get"
    );
  },

  getAssignmentStudentPerformanceTrend(assignmentId) {
    return ajax(
      `admin/assignments/${assignmentId}/student-performance-trend/`,
      "get"
    );
  },

  getAssignmentTopPerformingStudents(assignmentId) {
    return ajax(
      `admin/assignments/${assignmentId}/top-performing-students/`,
      "get"
    );
  },

  getAssignmentProblemStatistics(assignmentId) {
    return ajax(`admin/assignments/${assignmentId}/problem-statistics/`, "get");
  },

  exportAssignmentStatistics(assignmentId) {
    return ajax(`admin/assignments/${assignmentId}/export-statistics/`, "get");
  },

  initializeKnowledgePoints() {
    return ajax("ai/knowledge_point/initialize", "post");
  },
  getContestAnalytics(contestId) {
    return ajax("admin/contest/analytics", "get", {
      params: {
        contest_id: contestId
      }
    });
  }
};
/**
 * @param url
 * @param method get|post|put|delete...
 * @param params like queryString. if a url is index?a=1&b=2, params = {a: '1', b: '2'}
 * @param data post data, use for method put|post
 * @returns {Promise}
 */
function ajax(url, method, options) {
  if (options !== undefined) {
    var { params = {}, data = {} } = options;
  } else {
    params = data = {};
  }
  return new Promise((resolve, reject) => {
    axios({
      url,
      method,
      params,
      data
    }).then(
      res => {
        // API正常返回(status=20x)
        // 检查返回数据格式，兼容两种格式
        if (
          res.data &&
          (typeof res.data.error !== "undefined" ||
            typeof res.data.data !== "undefined")
        ) {
          // 标准格式 {error: null, data: {}}
          if (res.data.error !== null) {
            Vue.prototype.$error(res.data.data);
            reject(res);
          } else {
            resolve(res);
            if (method !== "get") {
              Vue.prototype.$success("Succeeded");
            }
          }
        } else {
          // 非标准格式，直接返回整个响应数据
          res.data = {
            error: null,
            data: res.data
          };
          resolve(res);
          if (method !== "get") {
            Vue.prototype.$success("Succeeded");
          }
        }
      },
      err => {
        // API请求异常，一般为Server error 或 network error
        reject(err);
        // 检查是否有响应数据
        if (err.response) {
          // 服务器返回了错误状态码
          if (err.response.data && err.response.data.data) {
            Vue.prototype.$error(err.response.data.data);
          } else {
            Vue.prototype.$error(
              `Error ${err.response.status}: ${err.response.statusText}`
            );
          }
        } else if (err.request) {
          // 请求已发出但没有收到响应
          Vue.prototype.$error("Network error or server not responding");
        } else {
          // 其他错误
          Vue.prototype.$error("An error occurred: " + err.message);
        }
      }
    );
  });
}
