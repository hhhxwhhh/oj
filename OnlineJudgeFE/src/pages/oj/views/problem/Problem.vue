<template>
  <div class="problem-container">
    <!-- 左侧题目信息区 -->
    <div class="problem-left-panel">
      <!-- 题目描述区域 -->
      <div class="problem-info-panel">
        <Panel :padding="20" shadow>
          <div slot="title" class="panel-title">{{ problem.title }}</div>
          <div id="problem-content" class="markdown-body" v-katex>
            <p class="title">{{ $t('m.Description') }}</p>
            <p class="content" v-html="problem.description"></p>

            <p class="title">{{ $t('m.Input') }} <span v-if="problem.io_mode.io_mode == 'File IO'">({{ $t('m.FromFile')
            }}: {{ problem.io_mode.input }})</span></p>
            <p class="content" v-html="problem.input_description"></p>

            <p class="title">{{ $t('m.Output') }} <span v-if="problem.io_mode.io_mode == 'File IO'">({{ $t('m.ToFile')
            }}: {{ problem.io_mode.output }})</span></p>
            <p class="content" v-html="problem.output_description"></p>

            <div v-for="(sample, index) of problem.samples" :key="index">
              <div class="flex-container sample">
                <div class="sample-input">
                  <p class="title">{{ $t('m ample_Input') }} {{ index + 1 }}
                    <a class="copy" v-clipboard:copy="sample.input" v-clipboard:success="onCopy"
                      v-clipboard:error="onCopyError">
                      <Icon type="clipboard"></Icon>
                    </a>
                  </p>
                  <pre>{{ sample.input }}</pre>
                </div>
                <div class="sample-output">
                  <p class="title">{{ $t('m ample_Output') }} {{ index + 1 }}</p>
                  <pre>{{ sample.output }}</pre>
                </div>
              </div>
            </div>

            <div v-if="problem.hint">
              <p class="title">{{ $t('m.Hint') }}</p>
              <Card dis-hover class="hint-card">
                <div class="content" v-html="problem.hint"></div>
              </Card>
            </div>

            <div v-if="problem.source">
              <p class="title">{{ $t('m.Source') }}</p>
              <p class="content">{{ problem.source }}</p>
            </div>
          </div>
        </Panel>
      </div>
    </div>

    <!-- 中间代码编辑区 -->
    <div class="problem-center-panel">
      <Card :padding="20" id="submit-code" dis-hover class="submit-card">
        <div class="code-editor-header">
          <div style="margin-bottom: 10px;">
            <i-switch v-model="useOllama" size="large">
              <span slot="open">Ollama</span>
              <span slot="close">默认AI</span>
            </i-switch>
            <span style="margin-left: 10px;">使用Ollama本地AI模型进行代码补全</span>
          </div>
        </div>

        <!-- 添加代码编辑器容器 -->
        <div class="code-editor-container">
          <CodeMirror ref="codeMirror" :value.sync="code" :languages="problem.languages" :language="language"
            :theme="theme" @resetCode="onResetToTemplate" @changeTheme="onChangeTheme" @changeLang="onChangeLang"
            @suggestions="onSuggestionsReceived"></CodeMirror>
        </div>

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
          <CodeDiagnostic :diagnosis-issues="diagnosisIssues" :suggestions="suggestions"
            @refresh-diagnosis="refreshDiagnosis" @refresh-suggestions="refreshSuggestions">
          </CodeDiagnostic>
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

    <!-- 右侧AI聊天区 -->
    <div class="problem-right-panel">
      <Card class="ai-chat-card">
        <div slot="title" class="ai-chat-header">
          <Icon type="chatbox-working"></Icon>
          <span class="card-title">AI 助手</span>
          <div class="ai-options">
            <Checkbox v-model="includeProblem">题目</Checkbox>
            <Checkbox v-model="includeCode">代码</Checkbox>
          </div>
        </div>
        <div class="ai-chat-container">
          <div class="ai-chat-messages" ref="chatMessages">
            <div v-for="(message, index) in aiMessages" :key="index" :class="['ai-message', message.role]">
              <div class="message-header">
                <Icon :type="message.role === 'user' ? 'person' : 'android'" />
                <span class="message-sender">{{ message.role === 'user' ? '你' : 'AI助手' }}</span>
              </div>
              <div class="message-content"
                v-html="message.role === 'user' ? message.content : renderMarkdown(message.content)"></div>
            </div>
          </div>
          <div class="ai-chat-input">
            <Input v-model="aiInputMessage" type="textarea" :rows="3" placeholder="向AI助手提问..."
              @on-enter="sendAIMessage" />
            <div class="ai-chat-actions">
              <Button type="primary" @click="sendAIMessage" :loading="aiSending">
                <Icon type="paper-airplane" /> 发送
              </Button>
              <Button @click="clearAIChat">
                <Icon type="trash-a" /> 清空
              </Button>
            </div>
          </div>
        </div>
      </Card>
    </div>

    <!-- 原有模态框保持不变 -->
    <Modal v-model="graphVisible" class="statistic-modal">
      <div id="pieChart-detail">
        <ECharts :options="largePie" :initOptions="largePieInitOpts"></ECharts>
      </div>
      <div slot="footer">
        <Button type="ghost" @click="graphVisible = false">{{ $t('m.Close') }}</Button>
      </div>
    </Modal>

    <Modal v-model="showExplanationModal" :title="$t('m.Code_Explanation')" width="800" class="explanation-modal">
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

    <Modal v-model="showComplexityModal" :title="$t('m.Complexity_Analysis')" width="600" :loading="loadingComplexity"
      @on-cancel="closeComplexityModal" class="complexity-modal">
      <div v-if="loadingComplexity" class="complexity-loading">
        <Spin size="large" />
        <p style="text-align: center; margin-top: 10px;">{{ $t('m.Loading_Complexity_Data') }}</p>
      </div>

      <div v-else-if="complexityData" class="complexity-content">
        <div class="complexity-header">
          <div class="complexity-level">
            <Tag :color="getComplexityColor(complexityData.complexity_score)" class="level-tag">
              {{ getComplexityLevelText(complexityData.complexity_score) }}
            </Tag>
            <div class="level-label">{{ $t('m.Complexity_Level') }}</div>
          </div>
          <div class="complexity-score">
            <div class="score-value">{{ complexityData.complexity_score.toFixed(1) }}</div>
            <div class="score-label">{{ $t('m.Complexity_Score') }}</div>
          </div>
        </div>

        <div class="complexity-grid">
          <div class="metric-item">
            <Icon type="ios-book" size="24" class="metric-icon" />
            <div class="metric-value">{{ complexityData.word_count }}</div>
            <div class="metric-label">{{ $t('m.Word_Count') }}</div>
          </div>
          <div class="metric-item">
            <Icon type="ios-chatbubbles" size="24" class="metric-icon" />
            <div class="metric-value">{{ complexityData.sentence_count }}</div>
            <div class="metric-label">{{ $t('m.Sentence_Count') }}</div>
          </div>
        </div>

        <div class="detail-section" v-if="complexityData.keywords && complexityData.keywords.length">
          <h4>{{ $t('m.Keywords') }}</h4>
          <div class="keywords-container">
            <Tag v-for="(keyword, index) in complexityData.keywords" :key="index" color="primary" class="keyword-tag">
              {{ keyword }}
            </Tag>
          </div>
        </div>

        <div class="detail-section" v-if="complexityData.readability_score || complexityData.grade_level">
          <h4>{{ $t('m.Readability_Analysis') }}</h4>
          <div class="readability-grid">
            <div class="readability-item" v-if="complexityData.readability_score">
              <div class="readability-value">{{ complexityData.readability_score.toFixed(1) }}</div>
              <div class="readability-label">{{ $t('m.Readability_Score') }}</div>
            </div>
            <div class="readability-item" v-if="complexityData.grade_level">
              <div class="readability-value">{{ complexityData.grade_level }}</div>
              <div class="readability-label">{{ $t('m.Grade_Level') }}</div>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="no-complexity-data">
        <Icon type="ios-information-circle-outline" size="48" class="info-icon" />
        <p>{{ $t('m.No_Complexity_Data_Available') }}</p>
      </div>

      <div slot="footer">
        <Button @click="closeComplexityModal">{{ $t('m.Close') }}</Button>
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
import CodeDiagnostic from '../../components/CodeDiagnostic.vue'
import ProblemComplexity from '../../components/ProblemComplexity.vue'
// 只显示这些状态的图形占用
const filtedStatus = ['-1', '-2', '0', '1', '2', '3', '4', '8']

export default {
  name: 'Problem',
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
      largePieInitOpts: {
        width: '500',
        height: '480'
      },
      explaining: false,
      showExplanationModal: false,
      codeExplanation: '',
      diagnosisIssues: [],
      diagnosisLoading: false,
      suggestions: [],
      suggestionTimer: null,
      lastCursorPosition: null,
      activeAIPanelTab: 'diagnosis',
      complexityData: null,
      showComplexityModal: false,
      loadingComplexity: false,
      useOllama: false,
      aiMessages: [
        {
          role: 'assistant',
          content: '你好！我是你的AI编程助手。你可以问我关于这道题的任何问题，我会尽力帮助你。'
        }
      ],
      aiInputMessage: '',
      aiSending: false,
      includeProblem: true,
      includeCode: true,
      toggleInfo: true
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
    this.startDiagnosisTimer()
  },
  methods: {
    ...mapActions(['changeDomTitle']),
    init() {
      this.$Loading.start()
      console.log('开始初始化问题:', this.problemID, this.contestID)

      this.contestID = this.$route.params.contestID
      this.problemID = this.$route.params.problemID

      let func = this.$route.name === 'problem-details' ? 'getProblem' : 'getContestProblem'

      api[func](this.problemID, this.contestID).then(res => {
        console.log('API响应:', res)
        this.$Loading.finish()

        if (!res.data || !res.data.data) {
          console.error('API返回数据为空')
          this.$error(this.$t('m.Failed_to_load_problem_data'))
          return
        }

        let problem = res.data.data

        // 验证关键字段
        if (!problem.title) {
          console.error('题目标题不存在')
          this.$error(this.$t('m.Invalid_problem_data'))
          return
        }

        // 处理空值并确保是HTML格式
        problem.description = this.formatHtmlContent(problem.description) || '<p>暂无描述</p>'
        problem.input_description = this.formatHtmlContent(problem.input_description) || '<p>暂无输入描述</p>'
        problem.output_description = this.formatHtmlContent(problem.output_description) || '<p>暂无输出描述</p>'
        problem.hint = this.formatHtmlContent(problem.hint) || ''
        problem.source = problem.source || ''

        // 确保数组字段正确
        if (!Array.isArray(problem.samples)) {
          problem.samples = []
        }

        if (!Array.isArray(problem.tags)) {
          problem.tags = []
        }

        if (!Array.isArray(problem.languages)) {
          problem.languages = []
        }

        // 转换数组为字符串（如果需要）
        if (Array.isArray(problem.description)) {
          problem.description = problem.description.join('\n')
        }
        if (Array.isArray(problem.input_description)) {
          problem.input_description = problem.input_description.join('\n')
        }
        if (Array.isArray(problem.output_description)) {
          problem.output_description = problem.output_description.join('\n')
        }

        // 调用 changeDomTitle action 设置页面标题
        try {
          this.changeDomTitle({ title: problem.title })
        } catch (e) {
          console.error('设置页面标题失败:', e)
          // 备选方案
          document.title = problem.title + ' - OnlineJudge'
        }

        api.submissionExists(problem.id).then(res => {
          this.submissionExists = res.data.data
        }).catch(err => {
          console.warn('获取提交状态失败:', err)
        })

        problem.languages = problem.languages.sort()
        this.problem = problem

        // 检查数据
        console.log('加载的题目数据:', {
          title: problem.title,
          description_length: problem.description.length,
          input_description_length: problem.input_description.length,
          output_description_length: problem.output_description.length
        })

        // 加载题目复杂度信息
        this.loadProblemComplexity()
        if (problem.statistic_info) {
          this.changePie(problem)
        }

        // 加载模板代码
        if (this.code === '') {
          this.language = this.problem.languages.length > 0 ? this.problem.languages[0] : 'C++'
          let template = this.problem.template
          if (template && template[this.language]) {
            this.code = template[this.language]
          }
        }
      }, error => {
        console.error('API调用失败:', error)
        this.$Loading.error()
        this.$error(this.$t('m.Failed_to_load_problem_data'))
      })
    },
    formatHtmlContent(content) {
      if (!content) return '';

      // 如果已经是HTML格式（包含标签），直接返回
      if (typeof content === 'string' && /<[a-z][\s\S]*>/i.test(content)) {
        return content;
      }

      // 如果是纯文本，转换为HTML格式
      if (typeof content === 'string') {
        // 将换行符转换为<br>标签
        return '<p>' + content.replace(/\n/g, '<br>') + '</p>';
      }

      return content;
    },




    startDiagnosisTimer() {
      // 每30秒进行一次实时诊断
      this.diagnosisTimer = setInterval(() => {
        if (this.code && this.code.trim() !== '') {
          this.performRealTimeDiagnosis()
        }
      }, 30000)
    },
    async showComplexityAnalysis() {
      this.showComplexityModal = true;
      if (!this.complexityData && !this.loadingComplexity) {
        await this.loadProblemComplexity();
      }
    },
    onSuggestionsReceived(suggestionsData) {
      console.log('收到CodeMirror组件的建议:', suggestionsData);
      if (suggestionsData) {
        // 根据响应结构正确处理建议
        if (Array.isArray(suggestionsData)) {
          // 如果直接返回数组
          this.suggestions = suggestionsData;
        } else if (typeof suggestionsData === 'object') {
          // 如果返回对象，合并所有建议类型
          this.suggestions = [
            ...(suggestionsData.suggestions || []),
            ...(suggestionsData.completions || []),
            ...(suggestionsData.issues || []),
            ...(suggestionsData.knowledge_points || [])
          ];
        }
      } else {
        this.suggestions = [];
      }
    },
    handleAIPanelTabChange(name) {
      this.activeAIPanelTab = name;
    },
    async fetchRealTimeSuggestions() {

      if (!this.code || this.code.trim() === '') {
        console.log('代码为空，不获取建议')
        this.suggestions = []
        return
      }

      try {
        const res = await api.getRealTimeSuggestion({
          code: this.code,
          language: this.language,
          problem_id: this.problem.id
        })

        console.log('API响应:', res)
        if (res.data && res.data.data) {
          const data = res.data.data
          // 合并所有建议
          this.suggestions = [
            ...(data.suggestions || []),
            ...(data.completions || []),
            ...(data.issues || []),
            ...(data.knowledge_points || [])
          ]
          console.log('处理后的建议:', this.suggestions)
        } else {
          this.suggestions = []
        }
      } catch (err) {
        console.error('获取实时建议失败:', err)
        this.suggestions = []
      }
    },
    refreshSuggestions() {
      console.log('手动刷新建议')
      // 直接调用CodeMirror组件的方法
      if (this.$refs.codemirror && typeof this.$refs.codemirror.fetchRealTimeSuggestions === 'function') {
        this.$refs.codemirror.fetchRealTimeSuggestions()
      } else {
        console.log('无法找到CodeMirror组件或fetchRealTimeSuggestions方法')
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
    async getProblemComplexity(problemId) {
      // 如果已经获取过复杂度信息，直接返回
      if (this.problemComplexityMap[problemId]) {
        return this.problemComplexityMap[problemId];
      }

      try {
        const res = await api.getProblemComplexity(problemId);
        this.$set(this.problemComplexityMap, problemId, res.data.data);
        return res.data.data;
      } catch (err) {
        // 获取失败时返回默认值
        const defaultComplexity = { complexity_score: 0 };
        this.$set(this.problemComplexityMap, problemId, defaultComplexity);
        return defaultComplexity;
      }
    },
    async loadProblemComplexity() {
      if (this.loadingComplexity) return; // 防止重复加载

      this.loadingComplexity = true;
      try {
        const res = await api.getProblemComplexity(this.problem.id);
        this.complexityData = res.data.data;
      } catch (err) {
        this.$error(this.$t('m.Failed_to_load_complexity_data'));
        this.complexityData = null;
      } finally {
        this.loadingComplexity = false;
      }
    },
    getComplexityLevelText(score) {
      if (score >= 80) return this.$t('m.Very_Complex');
      if (score >= 60) return this.$t('m.Complex');
      if (score >= 40) return this.$t('m.Moderate');
      if (score >= 20) return this.$t('m.Simple');
      return this.$t('m.Very_Simple');
    },

    getComplexityColor(score) {
      if (score >= 80) return '#ed4014'; // 红色
      if (score >= 60) return '#ff9900'; // 橙色
      if (score >= 40) return '#2d8cf0'; // 蓝色
      if (score >= 20) return '#19be6b'; // 绿色
      return '#515a6e'; // 灰色
    },
    closeComplexityModal() {
      this.showComplexityModal = false;
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
    async sendAIMessage() {
      if (!this.aiInputMessage.trim() || this.aiSending) return;

      // 添加用户消息到聊天记录
      this.aiMessages.push({
        role: 'user',
        content: this.aiInputMessage
      });

      // 构造发送给AI的内容
      let aiQuery = this.aiInputMessage;

      if (this.includeProblem) {
        aiQuery += `\n\n题目信息:\n${this.problem.title}\n${this.problem.description}`;
      }

      if (this.includeCode && this.code) {
        aiQuery += `\n\n当前代码:\n${this.code}`;
      }

      this.aiSending = true;
      this.aiInputMessage = ''; // 清空输入框

      try {
        // 滚动到底部
        this.$nextTick(() => {
          if (this.$refs.chatMessages) {
            this.$refs.chatMessages.scrollTop = this.$refs.chatMessages.scrollHeight;
          }
        });

        const res = await api.sendAIMessage({
          message: aiQuery,
          problem_id: this.problem.id
        });

        if (res.data && res.data.data) {
          // 添加AI回复到聊天记录
          this.aiMessages.push({
            role: 'assistant',
            content: res.data.data.response || res.data.data.content || '抱歉，我没有理解你的问题。'
          });
        } else {
          throw new Error('Invalid response from AI');
        }
      } catch (err) {
        console.error('AI消息发送失败:', err);
        this.aiMessages.push({
          role: 'assistant',
          content: '抱歉，我现在无法回答你的问题。请稍后再试。'
        });
      } finally {
        this.aiSending = false;
        // 滚动到底部
        this.$nextTick(() => {
          if (this.$refs.chatMessages) {
            this.$refs.chatMessages.scrollTop = this.$refs.chatMessages.scrollHeight;
          }
        });
      }
    },

    clearAIChat() {
      this.aiMessages = [
        {
          role: 'assistant',
          content: '你好！我是你的AI编程助手。你可以问我关于这道题的任何问题，我会尽力帮助你。'
        }
      ];
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
    showAIPanel() {
      return this.diagnosisIssues.length > 0 || this.suggestions.length > 0;
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
@primary-color: #1890ff;
@secondary-color: #52c41a;
@warning-color: #fa8c16;
@error-color: #ed4014;
@text-color: #515a6e;
@border-color: #e8f4ff;
@background-color: #f8f9fa;

.problem-container {
  display: flex;
  gap: 20px;
  padding: 20px;
  height: calc(100vh - 80px);
  background-color: #ffffff;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

.problem-left-panel {
  flex: 1;
  min-width: 400px;
  max-width: 500px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.problem-info-panel {
  flex: 1;
  min-height: 0;
  border-radius: 8px;
  overflow: hidden;

  /deep/ .ivu-card {
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  /deep/ .ivu-card-body {
    flex: 1;
    overflow-y: auto;
    padding: 15px;
    background-color: @background-color;
  }
}

.problem-center-panel {
  flex: 2;
  min-width: 600px;
  max-width: 800px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.problem-right-panel {
  flex: 1;
  min-width: 300px;
  max-width: 400px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

// 标题样式
.panel-title {
  font-size: 24px;
  font-weight: 600;
  color: @primary-color;
  margin: 0;
  padding: 0;
}

// 描述内容样式
#problem-content {
  margin-top: -30px;

  .title {
    font-size: 18px;
    font-weight: 600;
    margin: 25px 0 8px 0;
    color: @primary-color;
    position: relative;
    padding-bottom: 8px;
    border-bottom: 2px solid @border-color;

    .copy {
      padding-left: 8px;
      color: @primary-color;
      cursor: pointer;
      transition: color 0.3s;

      &:hover {
        color: @secondary-color;
      }
    }
  }

  p.content {
    margin-left: 25px;
    margin-right: 20px;
    font-size: 15px;
    line-height: 1.7;
    color: @text-color;
  }

  .sample {
    align-items: stretch;
    margin: 15px 0;

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
      background: @background-color;
      border: 1px solid @border-color;
      border-radius: 4px;
      padding: 12px;
      font-family: 'Monaco', 'Consolas', 'Courier New', monospace;
      font-size: 14px;
      line-height: 1.4;
      overflow-x: auto;
    }
  }
}

.hint-card {
  border-radius: 4px;
  border: 1px solid @border-color;
  background: @background-color;
  margin: 15px 0;

  /deep/ .ivu-card-body {
    padding: 15px;
  }

  .content {
    color: @text-color;
    line-height: 1.6;
  }
}

.submit-card {
  margin-top: 20px;
  margin-bottom: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid @border-color;
  transition: all 0.3s ease;

  &:hover {
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
    transform: translateY(-2px);
  }

  /deep/ .ivu-card-head {
    border-bottom: 1px solid @border-color;
    padding: 14px 20px;
    background: linear-gradient(120deg, #f0f8ff 0%, #e6f7ff 100%);
    border-radius: 8px 8px 0 0;
  }

  /deep/ .ivu-card-body {
    padding: 20px;
  }

  .status {
    float: left;
    display: flex;
    align-items: center;
    margin-bottom: 15px;

    span {
      margin-right: 10px;
      margin-left: 10px;
      font-weight: 500;
      color: @text-color;
    }

    /deep/ .ivu-tag {
      font-weight: 500;
      padding: 4px 10px;
      border-radius: 4px;
    }
  }

  .captcha-container {
    display: inline-block;
    margin-bottom: 15px;

    img {
      cursor: pointer;
      border-radius: 4px;
      border: 1px solid @border-color;
    }

    .captcha-code {
      width: auto;
      margin-top: -20px;
      margin-left: 20px;
    }
  }
}

// 代码编辑器样式
.code-editor-container {
  width: 100%;
  height: 400px;
  margin-bottom: 20px;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

  /deep/ .CodeMirror {
    height: 100% !important;
    border: none;
    background: @background-color;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 14px;
    line-height: 1.5;
  }

  /deep/ .CodeMirror-scroll {
    height: 100% !important;
  }

  /deep/ .CodeMirror-gutter {
    background: #f0f0f0;
    border-right: 1px solid #ddd;
  }

  /deep/ .CodeMirror-line {
    padding: 0;
  }
}

// 按钮样式
.problem-buttons {
  text-align: right;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 15px;

  .btn-explain,
  .btn-submit,
  .btn-recommend {
    flex: 1;
    min-width: 120px;
    border-radius: 20px;
    font-weight: 500;
    transition: all 0.3s ease;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
  }

  .btn-explain {
    background: linear-gradient(120deg, @primary-color 0%, #096dd9 100%);
    border: none;
    color: white;

    &:hover {
      box-shadow: 0 4px 12px rgba(@primary-color, 0.3);
    }
  }

  .btn-submit {
    background: linear-gradient(120deg, @warning-color 0%, #d46b08 100%);
    border: none;
    color: white;

    &:hover {
      box-shadow: 0 4px 12px rgba(@warning-color, 0.3);
    }
  }

  .btn-recommend {
    background: linear-gradient(120deg, @secondary-color 0%, #389e0d 100%);
    border: none;
    color: white;

    &:hover {
      box-shadow: 0 4px 12px rgba(@secondary-color, 0.3);
    }
  }
}

// AI助手样式
.ai-chat-card {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid @border-color;
  transition: all 0.3s ease;

  &:hover {
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
    transform: translateY(-2px);
  }

  .ai-chat-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 16px;
    background: linear-gradient(120deg, #f0f8ff 0%, #e6f7ff 100%);
    border-radius: 8px 8px 0 0;

    .card-title {
      font-size: 18px;
      font-weight: 600;
      color: @primary-color;
      margin-left: 8px;
    }

    .ai-options {
      display: flex;
      gap: 10px;
    }
  }

  .ai-chat-container {
    height: calc(100% - 60px);
    display: flex;
    flex-direction: column;
  }

  .ai-chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 15px;
    background-color: @background-color;
  }

  .ai-chat-input {
    padding: 15px;
    border-top: 1px solid @border-color;
    background-color: white;
  }

  .ai-message {
    margin-bottom: 15px;
    padding: 10px;
    border-radius: 8px;
    max-width: 80%;
    word-wrap: break-word;

    &.user {
      background-color: #e6f7ff;
      align-self: flex-end;
      border-bottom-right-radius: 0;
    }

    &.assistant {
      background-color: @background-color;
      align-self: flex-start;
      border-bottom-left-radius: 0;
    }
  }

  .message-header {
    display: flex;
    align-items: center;
    margin-bottom: 8px;

    .message-sender {
      margin-left: 8px;
      font-weight: 500;
      color: @text-color;
    }
  }

  .message-content {
    color: @text-color;
    line-height: 1.6;
  }
}

.submit-card {
  margin-top: 20px;
  margin-bottom: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.15);
  border: 1px solid #e8f4ff;
  transition: all 0.3s ease;

  &:hover {
    box-shadow: 0 6px 16px rgba(24, 144, 255, 0.25);
    transform: translateY(-2px);
  }

  /deep/ .ivu-card-head {
    border-bottom: 1px solid #e8f4ff;
    padding: 14px 20px;
    background: linear-gradient(120deg, #f0f8ff 0%, #e6f7ff 100%);
    border-radius: 8px 8px 0 0;
  }

  /deep/ .ivu-card-body {
    padding: 20px;
    position: relative;
  }

  // 添加CodeMirror容器样式
  .code-editor-container {
    width: 100%;
    height: 400px;
    margin-bottom: 20px;
    border-radius: 6px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

    /deep/ .CodeMirror {
      height: 100% !important;
      border: none;
      background: #f8f9fa;
      font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
      font-size: 14px;
      line-height: 1.5;
    }

    /deep/ .CodeMirror-scroll {
      height: 100% !important;
    }

    /deep/ .CodeMirror-gutter {
      background: #f0f0f0;
      border-right: 1px solid #ddd;
    }

    /deep/ .CodeMirror-line {
      padding: 0;
    }
  }
}
</style>