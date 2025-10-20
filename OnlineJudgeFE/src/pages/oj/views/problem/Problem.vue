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
          <div v-else-if="problem.my_status === 0">
            <Alert type="success" show-icon>{{ $t('m.You_have_solved_the_problem') }}</Alert>
          </div>
          <div v-else-if="this.contestID && !OIContestRealTimePermission && submissionExists">
            <Alert type="success" show-icon>{{ $t('m.You_have_submitted_a_solution') }}</Alert>
          </div>
          <div v-if="contestEnded">
            <Alert type="warning" show-icon>{{ $t('m.Contest_has_ended') }}</Alert>
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
    <Modal v-model="showExplanationModal" :title="$t('m.Code_Explanation')" width="800" :footer-hide="true">
      <div class="code-explanation" v-if="codeExplanation && !explaining">
        <div v-html="renderMarkdown(codeExplanation)"></div>
      </div>
      <div v-else-if="explaining" class="loading-explanation">
        <Spin size="large">{{ $t('m.Generating_Explanation') }}</Spin>
      </div>
      <div v-else>
        <p>{{ $t('m.No_Explanation_Available') }}</p>
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
    VerticalMenuItem
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
      codeExplanation: ''
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
    checkSubmissionStatus() {
      // 使用setTimeout避免一些问题
      if (this.refreshStatus) {
        // 如果之前的提交状态检查还没有停止,则停止,否则将会失去timeout的引用造成无限请求
        clearTimeout(this.refreshStatus)
      }
      const checkStatus = () => {
        let id = this.submissionId
        api.getSubmission(id).then(res => {
          this.result = res.data.data
          if (Object.keys(res.data.data.statistic_info).length !== 0) {
            this.submitting = false
            this.submitted = false
            clearTimeout(this.refreshStatus)
            this.init()
          } else {
            this.refreshStatus = setTimeout(checkStatus, 2000)
          }
        }, res => {
          this.submitting = false
          clearTimeout(this.refreshStatus)
        })
      }
      this.refreshStatus = setTimeout(checkStatus, 2000)
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
      const submitFunc = (data, detailsVisible) => {
        this.statusVisible = true
        api.submitCode(data).then(res => {
          this.submissionId = res.data.data && res.data.data.submission_id
          // 定时检查状态
          this.submitting = false
          this.submissionExists = true
          if (!detailsVisible) {
            this.$Modal.success({
              title: this.$i18n.t('m.Success'),
              content: this.$i18n.t('m.Submit_code_successfully')
            })
            return
          }
          this.submitted = true
          this.checkSubmissionStatus()
          //
          // 提交成功后给用户一个选择，可以查看提交状态或查看推荐题目
          this.$Modal.confirm({
            title: this.$i18n.t('m.Submit_Success'),
            content: this.$i18n.t('m.View_Submission_Or_Recommendation'),
            okText: this.$i18n.t('m.View_Submission'),
            cancelText: this.$i18n.t('m.View_Recommendation'),
            onOk: () => {
              this.$router.push({
                name: 'submission-details',
                params: { id: this.submissionId }
              });
            },
            onCancel: () => {
              this.$router.push({
                name: 'next-problem-recommendation',
                params: { problemID: this.problem._id },
                query: {
                  result: res.data.data.result
                }
              });
            }
          });
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
              // 暂时解决对话框与后面提示对话框冲突的问题(否则一闪而过）
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
        this.$error(this.$i18n.t('m.Failed_to_get_Code_Explanation') + ': ' + (err.message || ''));

        // 修复可选链操作符问题
        let errorMessage = '';
        if (err.response && err.response.data && err.response.data.data) {
          errorMessage = err.response.data.data;
        } else if (err.message) {
          errorMessage = err.message;
        }

        this.codeExplanation = this.$i18n.t('m.Failed_to_get_Code_Explanation') + '. ' + errorMessage;
      } finally {
        // 重置加载状态
        this.explaining = false;
      }
    },


    // 添加渲染Markdown方法
    renderMarkdown(content) {
      return utils.renderMarkdown(content);
    }
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
    }
  },
  beforeRouteLeave(to, from, next) {
    // 防止切换组件后仍然不断请求
    clearInterval(this.refreshStatus)

    this.$store.commit(types.CHANGE_CONTEST_ITEM_VISIBLE, { menu: true })
    storage.set(buildProblemCodeKey(this.problem._id, from.params.contestID), {
      code: this.code,
      language: this.language,
      theme: this.theme
    })
    next()
  },
  watch: {
    '$route'() {
      this.init()
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
</style>