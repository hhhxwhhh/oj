<template>
  <div class="flex-container">
    <div id="problem-main">
      <!--problem main-->
      <Panel :padding="40" shadow>
        <div slot="title">{{ problem.title }}</div>
        <div id="problem-content" class="markdown-body" v-katex>
          <p class="title">{{ $t('m.Description') }}</p>
          <p class="content" v-html=problem.description></p>
          <!-- {{$t('m.music')}} -->
          <p class="title">{{ $t('m.Input') }} <span v-if="problem.io_mode.io_mode == 'File IO'">({{ $t('m.FromFile')
          }}: {{
                problem.io_mode.input }})</span></p>
          <p class="content" v-html=problem.input_description></p>

          <p class="title">{{ $t('m.Output') }} <span v-if="problem.io_mode.io_mode == 'File IO'">({{ $t('m.ToFile') }}:
              {{
                problem.io_mode.output }})</span></p>
          <p class="content" v-html=problem.output_description></p>

          <div v-for="(sample, index) of problem.samples" :key="index">
            <div class="flex-container sample">
              <div class="sample-input">
                <p class="title">{{ $t('m.Sample_Input') }} {{ index + 1 }}
                  <a class="copy" v-clipboard:copy="sample.input" v-clipboard:success="onCopy"
                    v-clipboard:error="onCopyError">
                    <Icon type="clipboard"></Icon>
                  </a>
                </p>
                <pre>{{ sample.input }}</pre>
              </div>
              <div class="sample-output">
                <p class="title">{{ $t('m.Sample_Output') }} {{ index + 1 }}</p>
                <pre>{{ sample.output }}</pre>
              </div>
            </div>
          </div>

          <div v-if="problem.hint">
            <p class="title">{{ $t('m.Hint') }}</p>
            <Card dis-hover>
              <div class="content" v-html=problem.hint></div>
            </Card>
          </div>

          <div v-if="problem.source">
            <p class="title">{{ $t('m.Source') }}</p>
            <p class="content">{{ problem.source }}</p>
          </div>

        </div>
      </Panel>
      <!--problem main end-->
      <Card :padding="20" id="submit-code" dis-hover>
        <CodeMirror :value.sync="code" :languages="problem.languages" :language="language" :theme="theme"
          @resetCode="onResetToTemplate" @changeTheme="onChangeTheme" @changeLang="onChangeLang"></CodeMirror>

        <Row type="flex" justify="space-between">
          <Col :span="10">
          <div class="status" v-if="statusVisible">
            <template v-if="!this.contestID || (this.contestID && OIContestRealTimePermission)">
              <span>{{ $t('m.Status') }}</span>
              <Tag type="dot" :color="submissionStatus.color" @click.native="handleRoute('/status/' + submissionId)">
                {{ $t('m.' + submissionStatus.text.replace(/ /g, "_")) }}
              </Tag>
            </template>
            <template v-else-if="this.contestID && !OIContestRealTimePermission">
              <Alert type="success" show-icon>{{ $t('m.Submitted_successfully') }}</Alert>
            </template>
          </div>
          <div v-if="submitting">
            <Alert type="info" show-icon>{{ $t('m.Submitting') }}...</Alert>
          </div>
          <div v-else-if="problem.my_status === 0">
            <Alert type="success" show-icon>{{ $t('m.You_have_solved_the_problem') }}</Alert>
          </div>
          <div v-else-if="this.contestID && !OIContestRealTimePermission && submissionExists">
            <Alert type="success" show-icon>{{ $t('m.You_have_submitted_a_solution') }}</Alert>
          </div>
          <div v-if="contestEnded">
            <Alert type="warning" show-icon>{{ $t('m.Contest_has_ended') }}</Alert>
          </div>
          <div v-if="diagnosisIssues.length > 0" class="real-time-diagnosis">
            <div class="diagnosis-header">
              <h4>{{ $t('m.Real_Time_Diagnosis') }}</h4>
              <Button size="small" @click="refreshDiagnosis">{{ $t('m.Refresh') }}</Button>
            </div>
            <div class="diagnosis-content">
              <div v-for="(group, type) in groupedDiagnosisIssues" :key="type" class="diagnosis-group">
                <div class="group-header">
                  <Icon :type="getIssueIcon(type)" :style="{ color: getIssueColor(type) }"></Icon>
                  <span class="group-title">{{ getIssueTypeName(type) }}</span>
                  <Tag :color="getIssueColor(type)">{{ group.length }}</Tag>
                </div>
                <ul class="issue-list">
                  <li v-for="(issue, index) in group" :key="index" class="issue-item">
                    {{ issue.message }}
                  </li>
                </ul>
              </div>
            </div>
          </div>
          </Col>


          <Col :span="12">
          <template v-if="captchaRequired">
            <div class="captcha-container">
              <Tooltip v-if="captchaRequired" content="Click to refresh" placement="top">
                <img :src="captchaSrc" @click="getCaptchaSrc" />
              </Tooltip>
              <Input v-model="captchaCode" class="captcha-code" />
            </div>
          </template>

          <!-- 将解释代码按钮和提交按钮放在一起 -->
          <div class="problem-buttons">
            <Button type="info" icon="information-circled" @click="explainCode" :loading="explaining"
              :disabled="!code || explaining" class="btn-explain">
              {{ $t('m.Explain_Code') }}
            </Button>
            <Button type="warning" icon="edit" :loading="submitting" @click="submitCode"
              :disabled="problemSubmitDisabled || submitted" class="btn-submit">
              <span v-if="submitting">{{ $t('m.Submitting') }}</span>
              <span v-else>{{ $t('m.Submit') }}</span>
            </Button>
            <Button v-if="result && result.result !== undefined && result.result !== 9 && !contestID"
              :type="result.result === 0 ? 'success' : 'primary'" icon="ios-navigate" @click="goToRecommendation"
              class="btn-recommend">
              {{ result.result === 0 ? $t('m.View_Recommended_Problems') : $t('m.Get_Code_Diagnosis') }}
            </Button>
          </div>

          </Col>
        </Row>
      </Card>
    </div>

    <div id="right-column">
      <VerticalMenu @on-click="handleRoute">
        <template v-if="this.contestID">
          <VerticalMenuItem :route="{ name: 'contest-problem-list', params: { contestID: contestID } }">
            <Icon type="ios-photos"></Icon>
            {{ $t('m.Problems') }}
          </VerticalMenuItem>

          <VerticalMenuItem :route="{ name: 'contest-announcement-list', params: { contestID: contestID } }">
            <Icon type="chatbubble-working"></Icon>
            {{ $t('m.Announcements') }}
          </VerticalMenuItem>
        </template>

        <VerticalMenuItem v-if="!this.contestID || OIContestRealTimePermission" :route="submissionRoute">
          <Icon type="navicon-round"></Icon>
          {{ $t('m.Submissions') }}
        </VerticalMenuItem>

        <template v-if="this.contestID">
          <VerticalMenuItem v-if="!this.contestID || OIContestRealTimePermission"
            :route="{ name: 'contest-rank', params: { contestID: contestID } }">
            <Icon type="stats-bars"></Icon>
            {{ $t('m.Rankings') }}
          </VerticalMenuItem>
          <VerticalMenuItem :route="{ name: 'contest-details', params: { contestID: contestID } }">
            <Icon type="home"></Icon>
            {{ $t('m.View_Contest') }}
          </VerticalMenuItem>
        </template>
      </VerticalMenu>


      <Card id="info">
        <div slot="title" class="header">
          <Icon type="information-circled"></Icon>
          <span class="card-title">{{ $t('m.Information') }}</span>
        </div>
        <ul>
          <li>
            <p>ID</p>
            <p>{{ problem._id }}</p>
          </li>
          <li>
            <p>{{ $t('m.Time_Limit') }}</p>
            <p>{{ problem.time_limit }}MS</p>
          </li>
          <li>
            <p>{{ $t('m.Memory_Limit') }}</p>
            <p>{{ problem.memory_limit }}MB</p>
          </li>
          <li>
            <p>{{ $t('m.IOMode') }}</p>
            <p>{{ problem.io_mode.io_mode }}</p>
          </li>
          <li>
            <p>{{ $t('m.Created') }}</p>
            <p>{{ problem.created_by.username }}</p>
          </li>
          <li v-if="problem.difficulty">
            <p>{{ $t('m.Level') }}</p>
            <p>{{ $t('m.' + problem.difficulty) }}</p>
          </li>
          <li v-if="problem.total_score">
            <p>{{ $t('m.Score') }}</p>
            <p>{{ problem.total_score }}</p>
          </li>
          <li>
            <p>{{ $t('m.Tags') }}</p>
            <p>
              <Poptip trigger="hover" placement="left-end">
                <a>{{ $t('m.Show') }}</a>
                <div slot="content">
                  <Tag v-for="tag in problem.tags" :key="tag">{{ tag }}</Tag>
                </div>
              </Poptip>
            </p>
          </li>
        </ul>
      </Card>

      <Card id="pieChart" :padding="0" v-if="!this.contestID || OIContestRealTimePermission">
        <div slot="title">
          <Icon type="ios-analytics"></Icon>
          <span class="card-title">{{ $t('m.Statistic') }}</span>
          <Button type="ghost" size="small" id="detail" @click="graphVisible = !graphVisible">Details</Button>
        </div>
        <div class="echarts">
          <ECharts :options="pie"></ECharts>
        </div>
      </Card>
      <AIAssistant :problem="problem" :code="code" ref="aiAssistant"></AIAssistant>

    </div>

    <Modal v-model="graphVisible">
      <div id="pieChart-detail">
        <ECharts :options="largePie" :initOptions="largePieInitOpts"></ECharts>
      </div>
      <div slot="footer">
        <Button type="ghost" @click="graphVisible = false">{{ $t('m.Close') }}</Button>
      </div>
    </Modal>

    <!-- 添加代码解释模态框 -->
    <Modal v-model="showExplanationModal" :title="$t('m.Code_Explanation')" width="800">
      <div class="modal-actions" style="text-align: right; margin-bottom: 10px;">
        <Button v-if="codeExplanation && !explaining" @click="exportExplanationToPDF" type="primary" size="small"
          icon="ios-download-outline">
          {{ $t('m.Export_Explanation') }}
        </Button>
      </div>
      <div class="code-explanation" v-if="codeExplanation && !explaining">
        <div v-html="renderMarkdown(codeExplanation)"></div>
      </div>
      <div v-else-if="explaining" class="loading-explanation">
        <Spin size="large">{{ $t('m.Generating_Explanation') }}</Spin>
      </div>
      <div v-else>
        <p>{{ $t('m.No_Explanation_Available') }}</p>
      </div>
      <div slot="footer">
        <Button @click="showExplanationModal = false">{{ $t('m.Close') }}</Button>
      </div>
    </Modal>

  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'
import { types } from '@/store'
import api from '@oj/api'
import Panel from '@oj/components/Panel.vue'
import CodeMirror from '@oj/components/CodeMirror.vue'
import moment from 'moment'
import utils from '@/utils/utils'
import katex from 'katex'
import 'katex/dist/katex.min.css'
import ECharts from 'vue-echarts/components/ECharts.vue'
import 'echarts/lib/chart/pie'
import 'echarts/lib/component/title'
import 'echarts/lib/component/tooltip'
import 'echarts/lib/component/dataZoom'
import 'echarts/lib/component/legend'
import Highlight from '../../components/Highlight.vue'
import AIAssistant from '../../components/AIAssistant.vue'
import { pie, largePie } from './chartData'
import storage from '@/utils/storage'
import { buildProblemCodeKey, JUDGE_STATUS, CONTEST_STATUS } from '@/utils/constants'
import VerticalMenu from '../../components/verticalMenu/verticalMenu.vue'
import VerticalMenuItem from '../../components/verticalMenu/verticalMenu-item.vue'
import NextProblemRecommendation from './NextProblemRecommendation.vue'

// 只显示这些状态的图形占用
const filtedStatus = ['-1', '-2', '0', '1', '2', '3', '4', '8']

export default {
  name: 'Problem',
  components: {
    Panel,
    ECharts,
    Highlight,
    CodeMirror,
    AIAssistant,
    VerticalMenu,
    VerticalMenuItem,
    NextProblemRecommendation
  },

  data() {
    return {
      statusVisible: false,
      captchaRequired: false,
      graphVisible: false,
      submissionExists: false,
      captchaCode: '',
      captchaSrc: '',
      contestID: '',
      problemID: '',
      submitting: false,
      code: '',
      language: 'C++',
      theme: 'solarized',
      submissionId: '',
      submitted: false,
      result: {
        result: 9
      },
      problem: {
        title: '',
        description: '',
        hint: '',
        my_status: '',
        template: {},
        languages: [],
        created_by: {
          username: ''
        },
        tags: [],
        io_mode: { 'io_mode': 'Standard IO' }
      },
      pie: pie,
      largePie: largePie,
      // echarts 无法获取隐藏dom的大小，需手动指定
      largePieInitOpts: {
        width: '500',
        height: '480'
      },
      // 添加代码解释相关数据
      explaining: false,
      showExplanationModal: false,
      codeExplanation: '',
      showCodeSnippetModal: false,
      selectedCodeSnippet: '',
      snippetExplanation: '',
      // 添加实时诊断相关数据
      diagnosisTimer: null,
      diagnosisIssues: [],
      diagnosisLoading: false
    }
  },
  beforeRouteEnter(to, from, next) {
    let problemCode = storage.get(buildProblemCodeKey(to.params.problemID, to.params.contestID))
    if (problemCode) {
      next(vm => {
        vm.language = problemCode.language
        vm.code = problemCode.code
        vm.theme = problemCode.theme
      })
    } else {
      next()
    }
  },
  mounted() {
    this.$store.commit(types.CHANGE_CONTEST_ITEM_VISIBLE, { menu: false })
    this.init()
    // 启动实时诊断定时器
    this.startDiagnosisTimer()
  },
  methods: {
    ...mapActions(['changeDomTitle']),
    init() {
      this.$Loading.start()
      this.contestID = this.$route.params.contestID
      this.problemID = this.$route.params.problemID
      let func = this.$route.name === 'problem-details' ? 'getProblem' : 'getContestProblem'
      api[func](this.problemID, this.contestID).then(res => {
        this.$Loading.finish()
        let problem = res.data.data
        this.changeDomTitle({ title: problem.title })
        api.submissionExists(problem.id).then(res => {
          this.submissionExists = res.data.data
        })
        problem.languages = problem.languages.sort()
        this.problem = problem
        if (problem.statistic_info) {
          this.changePie(problem)
        }

        // 在beforeRouteEnter中修改了, 说明本地有code，无需加载template
        if (this.code !== '') {
          return
        }
        // try to load problem template
        this.language = this.problem.languages[0]
        let template = this.problem.template
        if (template && template[this.language]) {
          this.code = template[this.language]
        }
      }, () => {
        this.$Loading.error()
      })
    },
    startDiagnosisTimer() {
      // 每30秒进行一次实时诊断
      this.diagnosisTimer = setInterval(() => {
        if (this.code && this.code.trim() !== '') {
          this.performRealTimeDiagnosis()
        }
      }, 30000)
    },

    async performRealTimeDiagnosis() {
      if (this.diagnosisLoading) return

      this.diagnosisLoading = true
      try {
        const res = await api.getRealTimeDiagnosis({
          code: this.code,
          language: this.language,
          problem_id: this.problem.id
        })

        if (res.data && res.data.data) {
          const data = res.data.data
          this.diagnosisIssues = []

          // 收集所有诊断问题
          if (data.syntax_errors) {
            data.syntax_errors.forEach(error => {
              this.diagnosisIssues.push({
                type: 'syntax',
                message: error
              })
            })
          }

          if (data.logic_errors) {
            data.logic_errors.forEach(error => {
              this.diagnosisIssues.push({
                type: 'logic',
                message: error
              })
            })
          }

          if (data.performance_issues) {
            data.performance_issues.forEach(issue => {
              this.diagnosisIssues.push({
                type: 'performance',
                message: issue
              })
            })
          }

          if (data.best_practices) {
            data.best_practices.forEach(practice => {
              this.diagnosisIssues.push({
                type: 'best_practice',
                message: practice
              })
            })
          }
        }
      } catch (err) {
        console.error('Real-time diagnosis failed:', err)
      } finally {
        this.diagnosisLoading = false
      }
    },

    refreshDiagnosis() {
      if (this.code && this.code.trim() !== '') {
        this.performRealTimeDiagnosis()
      }
    },
    getIssueTypeName(type) {
      const typeNames = {
        syntax: this.$t('m.Syntax_Errors'),
        logic: this.$t('m.Logic_Errors'),
        performance: this.$t('m.Performance_Issues'),
        best_practice: this.$t('m.Best_Practices')
      }
      return typeNames[type] || type
    },
    getIssueIcon(type) {
      const icons = {
        syntax: 'ios-close-circle',
        logic: 'ios-bug',
        performance: 'ios-speedometer',
        best_practice: 'ios-thumbs-up'
      }
      return icons[type] || 'ios-information-circle'
    },
    getIssueColor(type) {
      const colors = {
        syntax: '#ed4014',        // 红色 - 语法错误
        logic: '#ff9900',         // 橙色 - 逻辑错误
        performance: '#2d8cf0',   // 蓝色 - 性能问题
        best_practice: '#19be6b'  // 绿色 - 最佳实践
      }
      return colors[type] || '#2d8cf0'
    },

    changePie(problemData) {
      // 只显示特定的一些状态
      for (let k in problemData.statistic_info) {
        if (filtedStatus.indexOf(k) === -1) {
          delete problemData.statistic_info[k]
        }
      }
      let acNum = problemData.accepted_number
      let data = [
        { name: 'WA', value: problemData.submission_number - acNum },
        { name: 'AC', value: acNum }
      ]
      this.pie.series[0].data = data
      // 只把大图的AC selected下，这里需要做一下deepcopy
      let data2 = JSON.parse(JSON.stringify(data))
      data2[1].selected = true
      this.largePie.series[1].data = data2

      // 根据结果设置legend,没有提交过的legend不显示
      let legend = Object.keys(problemData.statistic_info).map(ele => JUDGE_STATUS[ele].short)
      if (legend.length === 0) {
        legend.push('AC', 'WA')
      }
      this.largePie.legend.data = legend

      // 把ac的数据提取出来放在最后
      let acCount = problemData.statistic_info['0']
      delete problemData.statistic_info['0']

      let largePieData = []
      Object.keys(problemData.statistic_info).forEach(ele => {
        largePieData.push({ name: JUDGE_STATUS[ele].short, value: problemData.statistic_info[ele] })
      })
      largePieData.push({ name: 'AC', value: acCount })
      this.largePie.series[0].data = largePieData
    },
    handleRoute(route) {
      this.$router.push(route)
    },
    onChangeLang(newLang) {
      if (this.problem.template[newLang]) {
        if (this.code.trim() === '') {
          this.code = this.problem.template[newLang]
        }
      }
      this.language = newLang
    },
    onChangeTheme(newTheme) {
      this.theme = newTheme
    },
    onResetToTemplate() {
      this.$Modal.confirm({
        content: this.$i18n.t('m.Are_you_sure_you_want_to_reset_your_code'),
        onOk: () => {
          let template = this.problem.template
          if (template && template[this.language]) {
            this.code = template[this.language]
          } else {
            this.code = ''
          }
        }
      })
    },
    checkSubmissionStatus(detailsVisible) {
      // 使用setTimeout避免一些问题
      if (this.refreshStatus) {
        clearTimeout(this.refreshStatus)
      }

      const checkStatus = () => {
        // 确保submissionId存在
        if (!this.submissionId) {
          this.submitting = false
          return
        }

        // 使用新的API端点轮询提交状态
        api.getSubmission(this.submissionId).then(res => {
          this.result = res.data.data
          // 检查是否判题完成（result不是PENDING或JUDGING）
          if (res.data.data.result !== 9 && res.data.data.result !== 7) {
            this.submitting = false
            this.submitted = false
            clearTimeout(this.refreshStatus)
            this.init()

            // 判题完成后，如果需要跳转到推荐页面则跳转
            if (!detailsVisible) {
              // 对于OI比赛非实时权限的情况，不需要跳转
              return
            }

          } else {
            // 如果仍在判题中，继续轮询
            this.refreshStatus = setTimeout(checkStatus, 1000)
          }
        }, res => {
          this.submitting = false
          clearTimeout(this.refreshStatus)
          console.error('Failed to get submission status:', res)
        })
      }

      // 增加轮询频率，提供更快的反馈
      this.refreshStatus = setTimeout(checkStatus, 1000)
    },
    submitCode() {
      if (this.code.trim() === '') {
        this.$error(this.$i18n.t('m.Code_can_not_be_empty'))
        return
      }
      this.submissionId = ''
      this.result = { result: 9 }
      this.submitting = true
      let data = {
        problem_id: this.problem.id,
        language: this.language,
        code: this.code,
        contest_id: this.contestID
      }
      if (this.captchaRequired) {
        data.captcha = this.captchaCode
      }

      // 添加一个标志来跟踪是否需要跳转到推荐页面
      const submitFunc = (data, detailsVisible) => {
        this.statusVisible = true
        api.submitCode(data).then(res => {
          this.submissionId = res.data.data && res.data.data.submission_id
          this.submitting = false
          this.submissionExists = true

          // 立即显示提交成功消息
          this.$success(this.$i18n.t('m.Submit_code_successfully'))

          // 立即开始检查提交状态
          this.submitted = true
          this.checkSubmissionStatus(detailsVisible)
        }, res => {
          this.getCaptchaSrc()
          if (res.data.data.startsWith('Captcha is required')) {
            this.captchaRequired = true
          }
          this.submitting = false
          this.statusVisible = false
        })
      }

      if (this.contestRuleType === 'OI' && !this.OIContestRealTimePermission) {
        if (this.submissionExists) {
          this.$Modal.confirm({
            title: '',
            content: '<h3>' + this.$i18n.t('m.You_have_submission_in_this_problem_sure_to_cover_it') + '<h3>',
            onOk: () => {
              setTimeout(() => {
                submitFunc(data, false)
              }, 1000)
            },
            onCancel: () => {
              this.submitting = false
            }
          })
        } else {
          submitFunc(data, false)
        }
      } else {
        submitFunc(data, true)
      }
    },
    onCopy(event) {
      this.$success('Code copied')
    },
    onCopyError(e) {
      this.$error('Failed to copy code')
    },


    // 添加代码解释方法
    async explainCode() {
      // 检查是否有代码
      if (!this.code || this.code.trim() === '') {
        this.$error(this.$i18n.t('m.No_Code_To_Explain'));
        return;
      }

      try {
        // 设置加载状态
        this.explaining = true;
        this.showExplanationModal = true;
        this.codeExplanation = '';

        // 调用后端API获取代码解释
        const res = await api.getCodeExplanation({
          code: this.code,
          language: this.language
        });

        // 设置解释结果
        if (res.data && res.data.data && res.data.data.explanation) {
          this.codeExplanation = res.data.data.explanation;
        } else {
          this.codeExplanation = this.$i18n.t('m.No_Explanation_Available');
        }
      } catch (err) {
        // 处理错误
        console.error('Code explanation error:', err);
        this.$error(this.$i18n.t('m.Failed_to_get_Code_Explanation'));

        // 更简洁地处理错误消息
        let errorMessage = this.$i18n.t('m.Failed_to_get_Code_Explanation');
        if (err.response && err.response.data && err.response.data.data) {
          errorMessage += ': ' + err.response.data.data;
        } else if (err.message) {
          errorMessage += ': ' + err.message;
        }

        this.codeExplanation = errorMessage;
      } finally {
        // 重置加载状态
        this.explaining = false;
      }
    },

    // 添加代码片段解释方法
    async explainCodeSnippet(snippet) {
      if (!snippet || snippet.trim() === '') {
        this.$error(this.$i18n.t('m.No_Code_To_Explain'));
        return;
      }

      try {
        this.snippetExplanation = '';
        // 调用后端API获取代码片段解释
        const res = await api.getCodeExplanation({
          code: snippet,
          language: this.language
        });

        if (res.data && res.data.data && res.data.data.explanation) {
          this.snippetExplanation = res.data.data.explanation;
        } else {
          this.snippetExplanation = this.$i18n.t('m.No_Explanation_Available');
        }
      } catch (err) {
        console.error('Code snippet explanation error:', err);
        this.$error(this.$i18n.t('m.Failed_to_get_Code_Explanation'));
        let errorMessage = this.$i18n.t('m.Failed_to_get_Code_Explanation');
        if (err.response && err.response.data && err.response.data.data) {
          errorMessage += ': ' + err.response.data.data;
        } else if (err.message) {
          errorMessage += ': ' + err.message;
        }
        this.snippetExplanation = errorMessage;
      }
    },
    // 添加选择代码片段的方法
    onCodeSnippetSelected(snippet) {
      this.selectedCodeSnippet = snippet;
      this.showCodeSnippetModal = true;
      this.explainCodeSnippet(snippet);
    },
    // 添加导出解释为PDF的方法
    exportExplanationToPDF() {
      if (!this.codeExplanation) {
        this.$Message.warning(this.$t('m.No_Explanation_To_Export'));
        return;
      }

      try {
        // 创建一个新窗口用于打印
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
          <!DOCTYPE html>
          <html>
            <head>
              <meta charset="utf-8">
              <title>代码解释 - ${this.problem.title}</title>
              <style>
                body { 
                  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif; 
                  margin: 20px auto; 
                  line-height: 1.6;
                  max-width: 800px;
                  color: #333;
                  background: #fff;
                }
                h1 { 
                  color: #2c3e50; 
                  border-bottom: 2px solid #3498db;
                  padding-bottom: 10px;
                  margin: 20px 0;
                }
                h2 { 
                  color: #34495e; 
                  margin: 25px 0 15px 0;
                  padding-bottom: 8px;
                  border-bottom: 1px solid #eee;
                }
                h3 { 
                  color: #555; 
                  margin: 20px 0 10px 0;
                }
                p {
                  margin: 10px 0;
                  text-align: justify;
                }
                pre { 
                  background: #f8f9fa; 
                  padding: 15px; 
                  border-radius: 6px;
                  overflow-x: auto;
                  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                  font-size: 14px;
                  border: 1px solid #e9ecef;
                  margin: 15px 0;
                }
                code { 
                  font-family: 'Consolas', 'Monaco', 'Courier New', monospace; 
                  background: #f8f9fa;
                  padding: 2px 6px;
                  border-radius: 4px;
                  font-size: 14px;
                }
                pre code {
                  background: none;
                  padding: 0;
                }
                blockquote {
                  border-left: 4px solid #3498db;
                  padding: 10px 20px;
                  margin: 20px 0;
                  background: #f8f9fa;
                  border-radius: 0 4px 4px 0;
                }
                ul, ol {
                  padding-left: 30px;
                  margin: 15px 0;
                }
                li {
                  margin: 8px 0;
                }
                hr {
                  border: 0;
                  border-top: 1px solid #eee;
                  margin: 30px 0;
                }
                .header {
                  text-align: center;
                  margin-bottom: 30px;
                  padding-bottom: 20px;
                  border-bottom: 1px solid #eee;
                }
                .problem-info {
                  background: #e3f2fd;
                  padding: 15px;
                  border-radius: 6px;
                  margin: 20px 0;
                }
                .problem-info p {
                  margin: 5px 0;
                }
                .footer {
                  margin-top: 40px;
                  padding-top: 20px;
                  border-top: 1px solid #eee;
                  font-size: 14px;
                  color: #666;
                  text-align: center;
                }
                @media print {
                  body {
                    margin: 10px auto;
                  }
                  pre {
                    white-space: pre-wrap;
                    word-wrap: break-word;
                  }
                }
              </style>
            </head>
            <body>
              <div class="header">
                <h1>题目: ${this.problem.title}</h1>
                <div class="problem-info">
                  <p><strong>题目ID:</strong> ${this.problem._id}</p>
                  <p><strong>时间限制:</strong> ${this.problem.time_limit}MS</p>
                  <p><strong>内存限制:</strong> ${this.problem.memory_limit}MB</p>
                </div>
              </div>
              
              <h2>代码解释</h2>
              <div class="explanation-content">
                ${this.codeExplanation}
              </div>
              
              <div class="footer">
                <p><strong>导出时间:</strong> ${new Date().toLocaleString()}</p>
                <p><strong>在线查看:</strong> ${window.location.href}</p>
              </div>
              
              <script>
                // 页面加载完成后自动打印
                window.onload = function() {
                  window.print();
                };
              <\/script>
            </body>
          </html>
        `);
        printWindow.document.close();
      } catch (error) {
        console.error('导出PDF失败:', error);
        this.$Message.error('导出失败，请重试');
      }
    },
    // 添加渲染Markdown方法
    renderMarkdown(content) {
      return utils.renderMarkdown(content);
    },
    goToRecommendation() {
      if (!this.problemID || !this.result || this.result.result === undefined) {
        console.error('缺少必要数据')
        this.$error('无法跳转到推荐页面：缺少必要数据')
        return
      }

      // 如果提交成功，跳转到推荐页面
      if (this.result.result === 0) {
        this.$router.push({
          name: 'next-problem-recommendation',
          params: {
            problemID: this.problemID
          },
          query: {
            result: this.result.result,
            submission_id: this.submissionId
          }
        }).catch(err => {
          console.error('路由跳转失败:', err)
          this.$error('页面跳转失败: ' + err.message)
        })
      } else {
        // 如果提交失败，跳转到诊断页面
        this.$router.push({
          name: 'code-diagnosis',
          query: {
            submissionId: this.submissionId,
            problemId: this.problemID
          }
        }).catch(err => {
          console.error('路由跳转失败:', err)
          this.$error('页面跳转失败: ' + err.message)
        })
      }
    },
  },
  computed: {
    ...mapGetters(['problemSubmitDisabled', 'contestRuleType', 'OIContestRealTimePermission', 'contestStatus']),
    contest() {
      return this.$store.state.contest.contest
    },
    contestEnded() {
      return this.contestStatus === CONTEST_STATUS.ENDED
    },
    submissionStatus() {
      return {
        text: JUDGE_STATUS[this.result.result]['name'],
        color: JUDGE_STATUS[this.result.result]['color']
      }
    },
    submissionRoute() {
      if (this.contestID) {
        return { name: 'contest-submission-list', query: { problemID: this.problemID } }
      } else {
        return { name: 'submission-list', query: { problemID: this.problemID } }
      }
    },
    groupedDiagnosisIssues() {
      const groups = {}
      this.diagnosisIssues.forEach(issue => {
        if (!groups[issue.type]) {
          groups[issue.type] = []
        }
        groups[issue.type].push(issue)
      })
      return groups
    }

  },

  watch: {
    '$route'() {
      this.init()
    }
  },
  beforeRouteLeave(to, from, next) {
    // 防止切换组件后仍然不断请求
    if (this.refreshStatus) {
      clearTimeout(this.refreshStatus)
      this.refreshStatus = null
    }

    this.$store.commit(types.CHANGE_CONTEST_ITEM_VISIBLE, { menu: true })
    storage.set(buildProblemCodeKey(this.problem._id, from.params.contestID), {
      code: this.code,
      language: this.language,
      theme: this.theme
    })
    next()
  },
  beforeDestroy() {
    // 清除定时器
    if (this.diagnosisTimer) {
      clearInterval(this.diagnosisTimer)
    }
  }
}
</script>

<style lang="less" scoped>
.card-title {
  margin-left: 8px;
}

.flex-container {
  #problem-main {
    flex: auto;
    margin-right: 18px;
  }

  #right-column {
    flex: none;
    width: 220px;
  }
}

#problem-content {
  margin-top: -50px;

  .title {
    font-size: 20px;
    font-weight: 400;
    margin: 25px 0 8px 0;
    color: #3091f2;

    .copy {
      padding-left: 8px;
    }
  }

  p.content {
    margin-left: 25px;
    margin-right: 20px;
    font-size: 15px
  }

  .sample {
    align-items: stretch;

    &-input,
    &-output {
      width: 50%;
      flex: 1 1 auto;
      display: flex;
      flex-direction: column;
      margin-right: 5%;
    }

    pre {
      flex: 1 1 auto;
      align-self: stretch;
      border-style: solid;
      background: transparent;
    }
  }
}

#submit-code {
  margin-top: 20px;
  margin-bottom: 20px;

  .status {
    float: left;

    span {
      margin-right: 10px;
      margin-left: 10px;
    }
  }

  .captcha-container {
    display: inline-block;

    .captcha-code {
      width: auto;
      margin-top: -20px;
      margin-left: 20px;
    }
  }
}

// 添加按钮样式
.problem-buttons {
  text-align: right;

  .btn-explain {
    margin-right: 10px;
  }
}

#info {
  margin-bottom: 20px;
  margin-top: 20px;

  ul {
    list-style-type: none;

    li {
      border-bottom: 1px dotted #e9eaec;
      margin-bottom: 10px;

      p {
        display: inline-block;
      }

      p:first-child {
        width: 90px;
      }

      p:last-child {
        float: right;
      }
    }
  }
}

.fl-right {
  float: right;
}

#pieChart {
  .echarts {
    height: 250px;
    width: 210px;
  }

  #detail {
    position: absolute;
    right: 10px;
    top: 10px;
  }
}

#pieChart-detail {
  margin-top: 20px;
  width: 500px;
  height: 480px;
}

// 添加代码解释相关样式
.code-explanation {
  max-height: 500px;
  overflow-y: auto;
  padding: 15px;
  background-color: #f9f9f9;
  border-radius: 4px;

  /deep/ h1,
  /deep/ h2,
  /deep/ h3 {
    margin: 10px 0;
  }

  /deep/ p {
    margin: 8px 0;
    line-height: 1.6;
  }

  /deep/ pre {
    background: #f0f0f0;
    padding: 12px;
    border-radius: 4px;
    overflow-x: auto;
    margin: 10px 0;
  }

  /deep/ code {
    background: #f0f0f0;
    padding: 2px 4px;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
  }

  /deep/ ul,
  /deep/ ol {
    padding-left: 20px;
  }
}

.loading-explanation {
  text-align: center;
  padding: 40px 20px;

  /deep/ .ivu-spin-text {
    margin-top: 10px;
  }
}

.problem-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.btn-explain,
.btn-submit,
.btn-recommend {
  flex: 1;
  min-width: 120px;
}

@media screen and (max-width: 768px) {
  .problem-buttons {
    flex-direction: column;
  }

  .btn-explain,
  .btn-submit,
  .btn-recommend {
    width: 100%;
    margin-bottom: 10px;
  }
}

.real-time-diagnosis {
  margin-top: 15px;
  border: 1px solid #dddee1;
  border-radius: 4px;
  background-color: #f8f8f9;

  .diagnosis-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 15px;
    border-bottom: 1px solid #dddee1;
    background-color: #fff;
    border-radius: 4px 4px 0 0;

    h4 {
      margin: 0;
      color: #495060;
      font-weight: normal;

      i {
        margin-right: 8px;
        color: #2d8cf0;
      }
    }

    .ivu-btn {
      min-width: auto;
    }
  }

  .diagnosis-content {
    padding: 10px 15px;
  }

  .diagnosis-group {
    margin-bottom: 15px;

    &:last-child {
      margin-bottom: 0;
    }

    .group-header {
      display: flex;
      align-items: center;
      margin-bottom: 8px;
      padding: 5px 10px;
      background-color: #fff;
      border-radius: 3px;
      border-left: 3px solid #ccc;

      i {
        margin-right: 8px;
        font-size: 16px;
      }

      .group-title {
        flex: 1;
        font-weight: 500;
        color: #495060;
      }

      .ivu-tag {
        margin: 0;
      }
    }

    &.syntax {
      .group-header {
        border-left-color: #ed4014;
      }
    }

    &.logic {
      .group-header {
        border-left-color: #ff9900;
      }
    }

    &.performance {
      .group-header {
        border-left-color: #2d8cf0;
      }
    }

    &.best_practice {
      .group-header {
        border-left-color: #19be6b;
      }
    }

    .issue-list {
      margin: 0;
      padding-left: 25px;

      .issue-item {
        margin: 5px 0;
        padding: 3px 0;
        color: #657180;
        font-size: 13px;
        line-height: 1.4;
      }
    }
  }
}
</style>