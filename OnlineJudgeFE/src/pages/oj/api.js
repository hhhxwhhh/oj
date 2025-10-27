import Vue from "vue";
import store from "@/store";
import axios from "axios";

Vue.prototype.$http = axios;
axios.defaults.baseURL = "/api";
axios.defaults.xsrfHeaderName = "X-CSRFToken";
axios.defaults.xsrfCookieName = "csrftoken";

export default {
  getWebsiteConf(params) {
    return ajax("website", "get", {
      params
    });
  },
  getAnnouncementList(offset, limit) {
    let params = {
      offset: offset,
      limit: limit
    };
    return ajax("announcement", "get", {
      params
    });
  },
  getAIModels() {
    return ajax("ai/models", "get");
  },
  login(data) {
    return ajax("login", "post", {
      data
    });
  },
  checkUsernameOrEmail(username, email) {
    return ajax("check_username_or_email", "post", {
      data: {
        username,
        email
      }
    });
  },
  // 注册
  register(data) {
    return ajax("register", "post", {
      data
    });
  },
  logout() {
    return ajax("logout", "get");
  },
  getCaptcha() {
    return ajax("captcha", "get");
  },
  getUserInfo(username = undefined) {
    return ajax("profile", "get", {
      params: {
        username
      }
    });
  },
  updateProfile(profile) {
    return ajax("profile", "put", {
      data: profile
    });
  },
  freshDisplayID(userID) {
    return ajax("profile/fresh_display_id", "get", {
      params: {
        user_id: userID
      }
    });
  },
  twoFactorAuth(method, data) {
    return ajax("two_factor_auth", method, {
      data
    });
  },
  tfaRequiredCheck(username) {
    return ajax("tfa_required", "post", {
      data: {
        username
      }
    });
  },
  getSessions() {
    return ajax("sessions", "get");
  },
  deleteSession(sessionKey) {
    return ajax("sessions", "delete", {
      params: {
        session_key: sessionKey
      }
    });
  },
  applyResetPassword(data) {
    return ajax("apply_reset_password", "post", {
      data
    });
  },
  resetPassword(data) {
    return ajax("reset_password", "post", {
      data
    });
  },
  changePassword(data) {
    return ajax("change_password", "post", {
      data
    });
  },
  changeEmail(data) {
    return ajax("change_email", "post", {
      data
    });
  },
  getLanguages() {
    return ajax("languages", "get");
  },
  getProblemTagList() {
    return ajax("problem/tags", "get");
  },
  getProblemList(offset, limit, searchParams) {
    let params = {
      paging: true,
      offset,
      limit
    };
    Object.keys(searchParams).forEach(element => {
      if (searchParams[element]) {
        params[element] = searchParams[element];
      }
    });
    return ajax("problem", "get", {
      params: params
    });
  },
  pickone() {
    return ajax("pickone", "get");
  },
  getProblem(problemID) {
    return ajax("problem", "get", {
      params: {
        problem_id: problemID
      }
    });
  },
  getContestList(offset, limit, searchParams) {
    let params = {
      offset,
      limit
    };
    if (searchParams !== undefined) {
      Object.keys(searchParams).forEach(element => {
        if (searchParams[element]) {
          params[element] = searchParams[element];
        }
      });
    }
    return ajax("contests", "get", {
      params
    });
  },
  getContest(id) {
    return ajax("contest", "get", {
      params: {
        id
      }
    });
  },
  getContestAccess(contestID) {
    return ajax("contest/access", "get", {
      params: {
        contest_id: contestID
      }
    });
  },
  checkContestPassword(contestID, password) {
    return ajax("contest/password", "post", {
      data: {
        contest_id: contestID,
        password
      }
    });
  },
  getContestAnnouncementList(contestId) {
    return ajax("contest/announcement", "get", {
      params: {
        contest_id: contestId
      }
    });
  },
  getContestProblemList(contestId) {
    return ajax("contest/problem", "get", {
      params: {
        contest_id: contestId
      }
    });
  },
  getContestProblem(problemID, contestID) {
    return ajax("contest/problem", "get", {
      params: {
        contest_id: contestID,
        problem_id: problemID
      }
    });
  },
  submitCode(data) {
    return ajax("submission", "post", {
      data
    });
  },
  getSubmissionList(offset, limit, params) {
    params.limit = limit;
    params.offset = offset;
    return ajax("submissions", "get", {
      params
    });
  },
  getContestSubmissionList(offset, limit, params) {
    params.limit = limit;
    params.offset = offset;
    return ajax("contest_submissions", "get", {
      params
    });
  },
  getSubmission(id) {
    return ajax("submission", "get", {
      params: {
        id
      }
    });
  },
  submissionExists(problemID) {
    return ajax("submission_exists", "get", {
      params: {
        problem_id: problemID
      }
    });
  },
  submissionRejudge(id) {
    return ajax("admin/submission/rejudge", "get", {
      params: {
        id
      }
    });
  },
  updateSubmission(data) {
    return ajax("submission", "put", {
      data
    });
  },
  getUserRank(offset, limit, rule = "acm") {
    let params = {
      offset,
      limit,
      rule
    };
    return ajax("user_rank", "get", {
      params
    });
  },
  getContestRank(params) {
    return ajax("contest_rank", "get", {
      params
    });
  },
  getACMACInfo(params) {
    return ajax("admin/contest/acm_helper", "get", {
      params
    });
  },
  updateACInfoCheckedStatus(data) {
    return ajax("admin/contest/acm_helper", "put", {
      data
    });
  },

  //所有和AI相关的接口都在下面
  getAIModels() {
    return ajax("admin/ai_model/list", "get");
  },
  createAIConversation(data) {
    return ajax("ai/conversation", "post", {
      data
    });
  },
  getKnowledgePoints() {
    return ajax("ai/knowledge_point", "get");
  },
  getKnowledgeRecommendations(data) {
    return ajax("ai/knowledge_point/recommend", "post", {
      data: data || {}
    });
  },
  getAIConversations() {
    return ajax("ai/conversations", "get");
  },
  getAIMessages(conversationId) {
    return ajax("ai/message", "get", {
      params: {
        conversation_id: conversationId
      }
    });
  },
  sendAIMessage(data) {
    return ajax("ai/message", "post", {
      data
    });
  },
  getCodeExplanation(data) {
    return ajax("ai/code/explain", "post", {
      data
    });
  },
  getProblemSolution(data) {
    return ajax("ai/problem/solution", "post", {
      data
    });
  },
  reviewCode(data) {
    return ajax("ai/code/review", "post", {
      data
    });
  },
  getSubmissionDiagnosis(data) {
    return ajax("ai/submission/diagnose", "post", {
      data
    });
  },
  getRecommendedProblems() {
    return ajax("ai/problems/recommend", "get");
  },
  submitRecommendationFeedback(data) {
    return ajax("ai/recommendation/feedback", "post", {
      data
    });
  },
  sendFeedback(data) {
    return ajax("ai/feedback", "post", {
      data
    });
  },
  getNextProblemRecommendation(data) {
    return ajax("ai/next_problem", "post", {
      data
    });
  },
  getSubmissionStatus(submissionId) {
    return ajax("submission_status", "get", {
      params: {
        id: submissionId
      }
    });
  },
  generateLearningPath(data) {
    return ajax("ai/learning_path", "post", {
      data
    });
  },

  getLearningPaths() {
    return ajax("ai/learning_path", "get");
  },

  getLearningPathDetail(pathId) {
    return ajax(`ai/learning_path/${pathId}`, "get");
  },
  getCodeDiagnosis(submissionId) {
    return ajax("ai/code/diagnose", "post", {
      data: {
        submission_id: submissionId
      }
    });
  },
  getRealTimeSuggestion(data) {
    return ajax("ai/code/suggestion", "post", {
      data
    });
  },
  getCodeAutoCompletion(data) {
    return ajax("ai/code/autocomplete", "post", {
      data
    });
  },
  getRealTimeDiagnosis(data) {
    return ajax("ai/code/realtime_diagnosis", "post", {
      data
    });
  },
  getKnowledgePointGraph() {
    return ajax("ai/knowledge_point/graph", "get");
  },
  getKnowledgePoint(knowledgePointId) {
    return ajax("ai/knowledge_point", "get", {
      params: {
        id: knowledgePointId
      }
    });
  },
  getKnowledgePointProblems(knowledgePointId, offset, limit) {
    return ajax("ai/knowledge_point/problems", "get", {
      params: {
        knowledge_point_id: knowledgePointId,
        offset: offset,
        limit: limit
      }
    });
  },

  updateLearningPathNode(nodeId, data) {
    return ajax(`ai/learning_path/node/${nodeId}`, "put", {
      data
    });
  },
  // 编程能力评估接口
  assessProgrammingAbility() {
    return ajax("ai/ability/assess", "post");
  },
  getProgrammingAbilityReport() {
    return ajax("ai/ability/compare", "get");
  },
  getAbilityComparison() {
    return ajax("ai/ability/compare", "get");
  },
  //引入NLP技术的接口
  analyzeProblemComplexity(problemId) {
    return ajax("ai/nlp_analysis", "post", {
      data: {
        problem_id: problemId
      }
    });
  },
  getProblemComplexity(problemId) {
    return ajax("ai/nlp_analysis", "get", {
      params: {
        problem_id: problemId
      }
    });
  },
  //ollama接口
  getCodeAutoCompletion(data) {
    return ajax("ai/code/autocomplete", "post", {
      data
    });
  },
  getOllamaCodeCompletion(data) {
    return ajax("ollama/code/complete", "post", {
      data
    });
  },
  getOllamaModels() {
    return ajax("ollama/models", "get");
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
        // API正常返回(status=20x), 是否错误通过有无error判断
        if (res.data.error !== null) {
          // 修复：传递完整的错误对象，而不仅仅是data字段
          Vue.prototype.$error(res.data.data || res.data.error);
          reject(res);
          // 若后端返回为登录，则为session失效，应退出当前登录用户
          if (
            res.data.data &&
            res.data.data.startsWith &&
            res.data.data.startsWith("Please login")
          ) {
            store.dispatch("changeModalStatus", {
              mode: "login",
              visible: true
            });
          }
        } else {
          resolve(res);
        }
      },
      res => {
        reject(res);
        let errorMessage = "Network error or server unavailable";
        if (res && res.response && res.response.data) {
          if (res.response.data.data) {
            errorMessage = res.response.data.data;
          } else if (res.response.data.error) {
            errorMessage = res.response.data.error;
          }
        } else if (res && res.message) {
          errorMessage = res.message;
        }
        Vue.prototype.$error(errorMessage);
      }
    );
  });
}
