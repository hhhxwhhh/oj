<template>
  <Row type="flex" justify="space-around">
    <Col :span="20" id="status">
    <Alert :type="status.type" showIcon>
      <span class="title">{{ $t('m.' + status.statusName.replace(/ /g, "_")) }}</span>
      <div slot="desc" class="content">
        <template v-if="isCE">
          <pre>{{ submission.statistic_info.err_info }}</pre>
        </template>
        <template v-else>
          <span>{{ $t('m.Time') }}: {{ submission.statistic_info.time_cost | submissionTime }}</span>
          <span>{{ $t('m.Memory') }}: {{ submission.statistic_info.memory_cost | submissionMemory }}</span>
          <span>{{ $t('m.Lang') }}: {{ submission.language }}</span>
          <span>{{ $t('m.Author') }}: {{ submission.username }}</span>
        </template>
      </div>
    </Alert>
    </Col>

    <!--后台返info就显示出来， 权限控制放后台 -->
    <Col v-if="submission.info && !isCE" :span="20">
    <Table stripe :loading="loading" :disabled-hover="true" :columns="columns" :data="submission.info.data"></Table>
    </Col>

    <Col :span="20">
    <Highlight :code="submission.code" :language="submission.language" :border-color="status.color"></Highlight>
    </Col>

    <Col v-if="submission.can_unshare || true" :span="20">
    <div class="action-buttons">
      <!-- AI代码审查按钮 -->
      <Button type="primary" icon="eye" @click="reviewCode" :loading="reviewing" class="action-button">
        AI代码审查
      </Button>

      <!-- 分享/取消分享按钮 -->
      <Button v-if="submission.shared" type="warning" @click="shareSubmission(false)" class="action-button">
        {{ $t('m.UnShare') }}
      </Button>
      <Button v-else type="success" @click="shareSubmission(true)" class="action-button">
        {{ $t('m.Share') }}
      </Button>
    </div>
    </Col>

    <Modal v-model="showReviewModal" title="AI代码审查结果" width="800" :footer-hide="true">
      <div class="code-review" v-if="reviewResult && !reviewing">
        <div v-html="renderMarkdown(reviewResult)"></div>
      </div>
      <div v-else-if="reviewing" class="loading-review">
        <Spin size="large">正在生成审查结果...</Spin>
      </div>
      <div v-else>
        <p>暂无审查结果</p>
      </div>
    </Modal>
  </Row>

</template>

<script>
import api from '@oj/api'
import { JUDGE_STATUS } from '@/utils/constants'
import utils from '@/utils/utils'
import Highlight from '@/pages/oj/components/Highlight'

export default {
  name: 'submissionDetails',
  components: {
    Highlight
  },
  data() {
    return {
      columns: [
        {
          title: this.$i18n.t('m.ID'),
          align: 'center',
          type: 'index'
        },
        {
          title: this.$i18n.t('m.Status'),
          align: 'center',
          render: (h, params) => {
            return h('Tag', {
              props: {
                color: JUDGE_STATUS[params.row.result].color
              }
            }, this.$i18n.t('m.' + JUDGE_STATUS[params.row.result].name.replace(/ /g, '_')))
          }
        },
        {
          title: this.$i18n.t('m.Memory'),
          align: 'center',
          render: (h, params) => {
            return h('span', utils.submissionMemoryFormat(params.row.memory))
          }
        },
        {
          title: this.$i18n.t('m.Time'),
          align: 'center',
          render: (h, params) => {
            return h('span', utils.submissionTimeFormat(params.row.cpu_time))
          }
        }
      ],
      submission: {
        result: '0',
        code: '',
        problem_id: null,
        info: {
          data: []
        },
        statistic_info: {
          time_cost: '',
          memory_cost: ''
        }
      },
      isConcat: false,
      loading: false,
      // 添加AI代码审查相关数据
      reviewing: false,
      showReviewModal: false,
      reviewResult: ''
    }
  },
  mounted() {
    this.getSubmission()
  },
  methods: {
    getSubmission() {
      this.loading = true
      api.getSubmission(this.$route.params.id).then(res => {
        this.loading = false
        let data = res.data.data
        console.log('获取到的提交数据:', data); // 添加调试信息

        if (data.info && data.info.data && !this.isConcat) {
          // score exist means the submission is OI problem submission
          if (data.info.data[0].score !== undefined) {
            this.isConcat = true
            const scoreColumn = {
              title: this.$i18n.t('m.Score'),
              align: 'center',
              key: 'score'
            }
            this.columns.push(scoreColumn)
            this.loadingTable = false
          }
          if (this.isAdminRole) {
            this.isConcat = true
            const adminColumn = [
              {
                title: this.$i18n.t('m.Real_Time'),
                align: 'center',
                render: (h, params) => {
                  return h('span', utils.submissionTimeFormat(params.row.real_time))
                }
              },
              {
                title: this.$i18n.t('m.Signal'),
                align: 'center',
                key: 'signal'
              }
            ]
            this.columns = this.columns.concat(adminColumn)
          }
        }
        this.submission = data
        console.log('处理后的提交数据:', this.submission); // 调试信息
      }, (error) => {
        this.loading = false
        console.error('获取提交详情失败:', error); // 错误日志
      })
    },
    shareSubmission(shared) {
      let data = { id: this.submission.id, shared: shared }
      api.updateSubmission(data).then(res => {
        this.getSubmission()
        this.$success(this.$i18n.t('m.Succeeded'))
      }, () => {
      })
    },
    // AI代码审查方法
    async reviewCode() {
      // 检查必要字段并提供具体错误信息
      console.log('当前提交数据:', this.submission); // 调试信息

      if (!this.submission) {
        this.$error('提交数据为空，无法进行审查');
        return;
      }

      const missingFields = [];

      if (!this.submission.code || this.submission.code.trim() === '') {
        missingFields.push('代码');
      }
      let problemId = null;
      if (this.submission.problem_id) {
        problemId = this.submission.problem_id;
        console.log("通过problem_id:", problemId);
      } else if (this.submission.problem) {
        if (typeof this.submission.problem === 'object') {
          problemId = this.submission.problem.id;
          console.log("通过problem对象:", problemId);
        } else {
          problemId = this.submission.problem;
          console.log("通过problem字符串:", problemId);
        }
      }

      if (!problemId) {
        missingFields.push('题目ID');
      }

      if (!this.submission.language) {
        missingFields.push('编程语言');
      }

      if (missingFields.length > 0) {
        this.$error('缺少以下必要信息: ' + missingFields.join(', '));
        return;
      }

      try {
        this.reviewing = true;
        this.showReviewModal = true;
        this.reviewResult = '';

        console.log('调用代码审查API，参数:', {
          code: this.submission.code,
          language: this.submission.language,
          problem_id: problemId
        }); // 调试信息

        const res = await api.reviewCode({
          code: this.submission.code,
          language: this.submission.language,
          problem_id: problemId
        });

        this.reviewResult = res.data.data.review_result;
      } catch (err) {
        console.error('代码审查失败:', err); // 错误日志
        this.$error('获取代码审查失败: ' + (err.response && err.response.data && err.response.data.data ? err.response.data.data : (err.message || '未知错误')));
        this.showReviewModal = false;
      } finally {
        this.reviewing = false;
      }
    },
    // 渲染Markdown方法
    renderMarkdown(content) {
      return utils.renderMarkdown(content);
    }
  },
  computed: {
    status() {
      return {
        type: JUDGE_STATUS[this.submission.result].type,
        statusName: JUDGE_STATUS[this.submission.result].name,
        color: JUDGE_STATUS[this.submission.result].color
      }
    },
    isCE() {
      return this.submission.result === -2
    },
    isAdminRole() {
      return this.$store.getters.isAdminRole
    }
  }
}
</script>

<style scoped lang="less">
#status {
  .title {
    font-size: 20px;
  }

  .content {
    margin-top: 10px;
    font-size: 14px;

    span {
      margin-right: 10px;
    }

    pre {
      white-space: pre-wrap;
      word-wrap: break-word;
      word-break: break-all;
    }
  }
}

.admin-info {
  margin: 5px 0;

  &-content {
    font-size: 16px;
    padding: 10px;
  }
}

pre {
  border: none;
  background: none;
}

// 修改AI代码审查相关样式
.action-buttons {
  text-align: center;
  margin: 15px 0;

  .action-button {
    margin: 0 5px;
  }
}

.code-review {
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

.loading-review {
  text-align: center;
  padding: 40px 20px;

  /deep/ .ivu-spin-text {
    margin-top: 10px;
  }
}
</style>