<template>
  <div class="submission-container">
    <Row type="flex" justify="space-around">
      <Col :span="20" id="status">
      <Card class="status-card" :padding="20" shadow>
        <div class="status-header">
          <Icon :type="status.icon" :color="status.color" size="24" />
          <h2 class="status-title">{{ $t('m.' + status.statusName.replace(/ /g, "_")) }}</h2>
        </div>
        <div class="status-content">
          <template v-if="isCE">
            <pre class="error-info">{{ submission.statistic_info.err_info }}</pre>
          </template>
          <template v-else>
            <div class="status-details">
              <div class="detail-item">
                <Icon type="md-time" />
                <span class="detail-label">{{ $t('m.Time') }}:</span>
                <span class="detail-value">{{ submission.statistic_info.time_cost | submissionTime }}</span>
              </div>
              <div class="detail-item">
                <Icon type="md-analytics" />
                <span class="detail-label">{{ $t('m.Memory') }}:</span>
                <span class="detail-value">{{ submission.statistic_info.memory_cost | submissionMemory }}</span>
              </div>
              <div class="detail-item">
                <Icon type="md-code" />
                <span class="detail-label">{{ $t('m.Lang') }}:</span>
                <span class="detail-value">{{ submission.language }}</span>
              </div>
              <div class="detail-item">
                <Icon type="md-person" />
                <span class="detail-label">{{ $t('m.Author') }}:</span>
                <span class="detail-value">{{ submission.username }}</span>
              </div>
            </div>
          </template>
        </div>
      </Card>
      </Col>

      <!--后台返info就显示出来， 权限控制放后台 -->
      <Col v-if="submission.info && !isCE" :span="20">
      <Panel :padding="10" class="info-panel" shadow>
        <div slot="title" class="panel-title">
          <Icon type="md-list" size="18" />
          {{ $t('m.Test_Point_Details') }}
        </div>
        <Table stripe :loading="loading" :disabled-hover="true" :columns="columns" :data="submission.info.data"
          class="info-table"></Table>
      </Panel>
      </Col>

      <Col :span="20">
      <Panel :padding="0" class="code-panel" shadow>
        <div slot="title" class="panel-title">
          <Icon type="md-code" size="18" />
          {{ $t('m.Code') }}
        </div>
        <div class="code-content">
          <Highlight :code="submission.code" :language="submission.language" :border-color="status.color"></Highlight>
        </div>
      </Panel>
      </Col>

      <Col v-if="submission.can_unshare || true" :span="20">
      <div class="action-buttons">
        <!-- AI代码审查按钮 -->
        <Button type="primary" icon="md-eye" @click="reviewCode" :loading="reviewing" class="action-button">
          <Icon type="md-eye" />
          {{ $t('m.AI_Code_Review') }}
        </Button>

        <!-- 分享/取消分享按钮 -->
        <Button v-if="submission.shared" type="warning" @click="shareSubmission(false)" class="action-button">
          <Icon type="md-close" />
          {{ $t('m.UnShare') }}
        </Button>
        <Button v-else type="success" @click="shareSubmission(true)" class="action-button">
          <Icon type="md-share" />
          {{ $t('m.Share') }}
        </Button>
      </div>
      </Col>

      <Modal v-model="showReviewModal" :title="$t('m.AI_Code_Review_Result')" width="800" :footer-hide="true"
        class="review-modal">
        <div class="code-review" v-if="reviewResult && !reviewing">
          <div v-html="renderMarkdown(reviewResult)" class="markdown-body"></div>
        </div>
        <div v-else-if="reviewing" class="loading-review">
          <Spin size="large">{{ $t('m.Generating_Review') }}</Spin>
        </div>
        <div v-else class="no-review">
          <p>{{ $t('m.No_Review_Result') }}</p>
        </div>
      </Modal>
    </Row>
  </div>
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
  computed: {
    status() {
      return {
        type: JUDGE_STATUS[this.submission.result].type,
        statusName: JUDGE_STATUS[this.submission.result].name,
        color: JUDGE_STATUS[this.submission.result].color,
        icon: this.getIconForStatus(JUDGE_STATUS[this.submission.result].name)
      }
    },
    isCE() {
      return this.submission.result === -2
    },
    isAdminRole() {
      return this.$store.getters.isAdminRole
    }
  },
  methods: {
    getSubmission() {
      this.loading = true
      api.getSubmission(this.$route.params.id).then(res => {
        this.loading = false
        let data = res.data.data

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
      }, (error) => {
        this.loading = false
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
      } else if (this.submission.problem) {
        if (typeof this.submission.problem === 'object') {
          problemId = this.submission.problem.id;
        } else {
          problemId = this.submission.problem;
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

        const res = await api.reviewCode({
          code: this.submission.code,
          language: this.submission.language,
          problem_id: problemId
        });

        this.reviewResult = res.data.data.review_result;
      } catch (err) {
        this.$error('获取代码审查失败: ' + (err.response && err.response.data && err.response.data.data ? err.response.data.data : (err.message || '未知错误')));
        this.showReviewModal = false;
      } finally {
        this.reviewing = false;
      }
    },
    // 渲染Markdown方法
    renderMarkdown(content) {
      return utils.renderMarkdown(content);
    },
    getIconForStatus(statusName) {
      const iconMap = {
        'Accepted': 'md-checkmark-circle',
        'Wrong Answer': 'md-close-circle',
        'Time Limit Exceeded': 'md-time',
        'Memory Limit Exceeded': 'md-analytics',
        'Runtime Error': 'md-bug',
        'System Error': 'md-warning',
        'Compile Error': 'md-build',
        'Pending': 'md-pause',
        'Judging': 'md-play',
        'Partial Accepted': 'md-checkmark-circle-outline',
        'Submitting': 'md-cloud-upload'
      };
      return iconMap[statusName] || 'md-information-circle';
    }
  }
}
</script>

<style scoped lang="less">
.submission-container {
  padding: 20px 0;

  .status-card {
    margin-bottom: 20px;
    border-radius: 8px;
    border: none;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);

    .status-header {
      display: flex;
      align-items: center;
      margin-bottom: 15px;

      .status-title {
        margin: 0 0 0 10px;
        font-size: 22px;
        font-weight: 500;
        color: #333;
      }
    }

    .status-content {
      .error-info {
        white-space: pre-wrap;
        word-wrap: break-word;
        word-break: break-all;
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 4px;
        border-left: 4px solid #ff9900;
        font-family: "Courier New", monospace;
        font-size: 14px;
        line-height: 1.5;
        margin: 0;
      }

      .status-details {
        display: flex;
        flex-wrap: wrap;
        gap: 15px;

        .detail-item {
          display: flex;
          align-items: center;
          padding: 8px 15px;
          background-color: #f8f9fa;
          border-radius: 4px;
          flex: 1;
          min-width: 200px;

          .ivu-icon {
            margin-right: 8px;
            color: #2d8cf0;
          }

          .detail-label {
            font-weight: 500;
            margin-right: 5px;
            color: #666;
          }

          .detail-value {
            color: #333;
          }
        }
      }
    }
  }

  .info-panel {
    margin-bottom: 20px;

    .panel-title {
      font-size: 18px;
      font-weight: 500;
    }

    .info-table {
      border: none;

      /deep/ .ivu-table {
        &::before {
          height: 0;
        }

        &-thead>tr>th {
          background-color: #f8f9fa;
          font-weight: 600;
          color: #333;
          border-bottom: 1px solid #e8eaec;
        }

        &-tbody>tr>td {
          border-bottom: 1px solid #f2f2f2;
        }
      }
    }
  }

  .code-panel {
    margin-bottom: 20px;

    .panel-title {
      font-size: 18px;
      font-weight: 500;
    }

    .code-content {
      padding: 10px;
    }
  }

  .action-buttons {
    text-align: center;
    margin: 20px 0;

    .action-button {
      margin: 0 8px;
      padding: 6px 15px;
      border-radius: 4px;

      .ivu-icon {
        margin-right: 5px;
      }
    }
  }

  .review-modal {
    .code-review {
      max-height: 500px;
      overflow-y: auto;
      padding: 10px;

      &.markdown-body {
        background-color: #f9f9f9;
        border-radius: 4px;
        padding: 15px;

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
    }

    .loading-review {
      text-align: center;
      padding: 40px 20px;

      /deep/ .ivu-spin-text {
        margin-top: 10px;
      }
    }

    .no-review {
      text-align: center;
      padding: 30px;
      color: #888;
    }
  }
}
</style>