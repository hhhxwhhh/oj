<template>
  <div class="submission-list-container">
    <Row type="flex" justify="space-around">
      <Col :span="22">
      <Card class="overview-card" :padding="20" shadow>
        <div class="overview-header">
          <Icon type="md-list" size="24" color="#2d8cf0" />
          <h2 class="overview-title">{{ title }}</h2>
        </div>
        <div class="overview-stats">
          <div class="stat-item">
            <Icon type="md-document" size="20" class="stat-icon" />
            <div class="stat-content">
              <p class="stat-label">{{ $t('m.Total') }}</p>
              <p class="stat-value">{{ total }}</p>
            </div>
          </div>
          <div class="stat-item">
            <Icon type="md-document" size="20" class="stat-icon" />
            <div class="stat-content">
              <p class="stat-label">{{ $t('m.Page') }}</p>
              <p class="stat-value">{{ page }} / {{ Math.ceil(total / limit) }}</p>
            </div>
          </div>
          <div class="stat-item">
            <Icon type="md-options" size="20" class="stat-icon" />
            <div class="stat-content">
              <p class="stat-label">{{ $t('m.Filter') }}</p>
              <p class="stat-value">{{ status }}</p>
            </div>
          </div>
        </div>
      </Card>

      <Panel shadow class="submission-panel">
        <div slot="title" class="panel-title">
          <Icon type="md-list" />
          {{ $t('m.Submission_List') }}
        </div>
        <div slot="extra" class="panel-extra">
          <ul class="filter">
            <li>
              <Dropdown @on-click="handleResultChange" class="filter-dropdown">
                <Button type="default" size="small">
                  {{ status }}
                  <Icon type="md-arrow-dropdown"></Icon>
                </Button>
                <Dropdown-menu slot="list">
                  <Dropdown-item name="">{{ $t('m.All') }}</Dropdown-item>
                  <Dropdown-item v-for="status in Object.keys(JUDGE_STATUS)" :key="status" :name="status">
                    {{ $t('m.' + JUDGE_STATUS[status].name.replace(/ /g, "_")) }}
                  </Dropdown-item>
                </Dropdown-menu>
              </Dropdown>
            </li>

            <li>
              <i-switch size="large" v-model="formFilter.myself" @on-change="handleQueryChange" class="filter-switch">
                <span slot="open">{{ $t('m.Mine') }}</span>
                <span slot="close">{{ $t('m.All') }}</span>
              </i-switch>
            </li>
            <li>
              <Input v-model="formFilter.username" :placeholder="$t('m.Search_Author')" @on-enter="handleQueryChange"
                size="small" class="filter-input" />
            </li>

            <li>
              <Button type="primary" icon="md-refresh" @click="getSubmissions" size="small">{{ $t('m.Refresh')
                }}</Button>
            </li>
          </ul>
        </div>
        <Table stripe :disabled-hover="true" :columns="columns" :data="submissions" :loading="loadingTable"
          class="submission-table"></Table>
      </Panel>

      <div class="pagination-container">
        <Pagination :total="total" :page-size="limit" @on-change="changeRoute" :current.sync="page"
          class="submission-pagination"></Pagination>
      </div>
      </Col>
    </Row>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import api from '@oj/api'
import { JUDGE_STATUS, USER_TYPE } from '@/utils/constants'
import utils from '@/utils/utils'
import time from '@/utils/time'
import Pagination from '@/pages/oj/components/Pagination'

export default {
  name: 'submissionList',
  components: {
    Pagination
  },
  data() {
    return {
      formFilter: {
        myself: false,
        result: '',
        username: ''
      },
      columns: [
        {
          title: this.$i18n.t('m.When'),
          align: 'center',
          render: (h, params) => {
            return h('span', time.utcToLocal(params.row.create_time))
          }
        },
        {
          title: this.$i18n.t('m.ID'),
          align: 'center',
          render: (h, params) => {
            if (params.row.show_link) {
              return h('span', {
                class: 'submission-id-link',
                on: {
                  click: () => {
                    this.$router.push('/status/' + params.row.id)
                  }
                }
              }, params.row.id.slice(0, 12))
            } else {
              return h('span', params.row.id.slice(0, 12))
            }
          }
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
          title: this.$i18n.t('m.Problem'),
          align: 'center',
          render: (h, params) => {
            return h('span',
              {
                class: 'problem-link',
                on: {
                  click: () => {
                    if (this.contestID) {
                      this.$router.push(
                        {
                          name: 'contest-problem-details',
                          params: { problemID: params.row.problem, contestID: this.contestID }
                        })
                    } else {
                      this.$router.push({ name: 'problem-details', params: { problemID: params.row.problem } })
                    }
                  }
                }
              },
              params.row.problem)
          }
        },
        {
          title: this.$i18n.t('m.Time'),
          align: 'center',
          render: (h, params) => {
            return h('span', utils.submissionTimeFormat(params.row.statistic_info.time_cost))
          }
        },
        {
          title: this.$i18n.t('m.Memory'),
          align: 'center',
          render: (h, params) => {
            return h('span', utils.submissionMemoryFormat(params.row.statistic_info.memory_cost))
          }
        },
        {
          title: this.$i18n.t('m.Language'),
          align: 'center',
          key: 'language'
        },
        {
          title: this.$i18n.t('m.Author'),
          align: 'center',
          render: (h, params) => {
            return h('a', {
              class: 'author-link',
              style: {
                'display': 'inline-block',
                'max-width': '150px'
              },
              on: {
                click: () => {
                  this.$router.push(
                    {
                      name: 'user-home',
                      query: { username: params.row.username }
                    })
                }
              }
            }, params.row.username)
          }
        }
      ],
      loadingTable: false,
      submissions: [],
      total: 30,
      limit: 12,
      page: 1,
      contestID: '',
      problemID: '',
      routeName: '',
      JUDGE_STATUS: '',
      rejudge_column: false
    }
  },
  mounted() {
    this.init()
    this.JUDGE_STATUS = Object.assign({}, JUDGE_STATUS)
    // 去除submitting的状态 和 两个
    delete this.JUDGE_STATUS['9']
    delete this.JUDGE_STATUS['2']
  },
  methods: {
    init() {
      this.contestID = this.$route.params.contestID
      let query = this.$route.query
      this.problemID = query.problemID
      this.formFilter.myself = query.myself === '1'
      this.formFilter.result = query.result || ''
      this.formFilter.username = query.username || ''
      this.page = parseInt(query.page) || 1
      if (this.page < 1) {
        this.page = 1
      }
      this.routeName = this.$route.name
      this.getSubmissions()
    },
    buildQuery() {
      return {
        myself: this.formFilter.myself === true ? '1' : '0',
        result: this.formFilter.result,
        username: this.formFilter.username,
        page: this.page
      }
    },
    getSubmissions() {
      let params = this.buildQuery()
      params.contest_id = this.contestID
      params.problem_id = this.problemID
      let offset = (this.page - 1) * this.limit
      let func = this.contestID ? 'getContestSubmissionList' : 'getSubmissionList'
      this.loadingTable = true
      api[func](offset, this.limit, params).then(res => {
        let data = res.data.data
        for (let v of data.results) {
          v.loading = false
        }
        this.adjustRejudgeColumn()
        this.loadingTable = false
        this.submissions = data.results
        this.total = data.total
      }).catch(() => {
        this.loadingTable = false
      })
    },
    // 改变route， 通过监听route变化请求数据，这样可以产生route history， 用户返回时就会保存之前的状态
    changeRoute() {
      let query = utils.filterEmptyValue(this.buildQuery())
      query.contestID = this.contestID
      query.problemID = this.problemID
      let routeName = query.contestID ? 'contest-submission-list' : 'submission-list'
      this.$router.push({
        name: routeName,
        query: utils.filterEmptyValue(query)
      })
    },
    goRoute(route) {
      this.$router.push(route)
    },
    adjustRejudgeColumn() {
      if (!this.rejudgeColumnVisible || this.rejudge_column) {
        return
      }
      const judgeColumn = {
        title: this.$i18n.t('m.Option'),
        fixed: 'right',
        align: 'center',
        width: 90,
        render: (h, params) => {
          return h('Button', {
            props: {
              type: 'primary',
              size: 'small',
              loading: params.row.loading
            },
            on: {
              click: () => {
                this.handleRejudge(params.row.id, params.index)
              }
            }
          }, this.$i18n.t('m.Rejudge'))
        }
      }
      this.columns.push(judgeColumn)
      this.rejudge_column = true
    },
    handleResultChange(status) {
      this.page = 1
      this.formFilter.result = status
      this.changeRoute()
    },
    handleQueryChange() {
      this.page = 1
      this.changeRoute()
    },
    handleRejudge(id, index) {
      this.submissions[index].loading = true
      api.submissionRejudge(id).then(res => {
        this.submissions[index].loading = false
        this.$success('Succeeded')
        this.getSubmissions()
      }, () => {
        this.submissions[index].loading = false
      })
    }
  },
  computed: {
    ...mapGetters(['isAuthenticated', 'user']),
    title() {
      if (!this.contestID) {
        return this.$i18n.t('m.Status')
      } else if (this.problemID) {
        return this.$i18n.t('m.Problem_Submissions')
      } else {
        return this.$i18n.t('m.Submissions')
      }
    },
    status() {
      return this.formFilter.result === '' ? this.$i18n.t('m.Status') : this.$i18n.t('m.' + JUDGE_STATUS[this.formFilter.result].name.replace(/ /g, '_'))
    },
    rejudgeColumnVisible() {
      return !this.contestID && this.user.admin_type === USER_TYPE.SUPER_ADMIN
    }
  },
  watch: {
    '$route'(newVal, oldVal) {
      if (newVal !== oldVal) {
        this.init()
      }
    },
    'rejudgeColumnVisible'() {
      this.adjustRejudgeColumn()
    },
    'isAuthenticated'() {
      this.init()
    }
  }
}
</script>

<style scoped lang="less">
.submission-list-container {
  padding: 20px 0;

  .overview-card {
    margin-bottom: 20px;
    border-radius: 8px;
    border: none;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);

    .overview-header {
      display: flex;
      align-items: center;
      margin-bottom: 15px;

      .overview-title {
        margin: 0 0 0 10px;
        font-size: 22px;
        font-weight: 500;
      }
    }

    .overview-stats {
      display: flex;
      justify-content: space-around;
      text-align: center;

      .stat-item {
        display: flex;
        align-items: center;

        .stat-icon {
          margin-right: 10px;
          color: #2d8cf0;
        }

        .stat-content {
          .stat-label {
            margin: 0;
            font-size: 14px;
            color: #808695;
          }

          .stat-value {
            margin: 5px 0 0;
            font-size: 18px;
            font-weight: 600;
            color: #17233d;
          }
        }
      }
    }
  }

  .submission-panel {
    margin-bottom: 20px;

    .panel-title {
      font-size: 18px;
      font-weight: 500;
    }

    .panel-extra {
      .filter {
        display: flex;
        align-items: center;
        gap: 10px;

        li {
          list-style: none;
        }

        .filter-dropdown {
          /deep/ .ivu-btn {
            padding: 2px 8px;
          }
        }

        .filter-switch {
          /deep/ .ivu-switch {
            min-width: 50px;
          }
        }

        .filter-input {
          width: 150px;
        }
      }
    }

    .submission-table {
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

  .pagination-container {
    display: flex;
    justify-content: center;
    margin-bottom: 20px;

    .submission-pagination {
      /deep/ .ivu-page {
        &-options {
          margin-left: 15px;
        }
      }
    }
  }

  // 链接样式
  .submission-id-link,
  .problem-link {
    color: #2d8cf0;
    cursor: pointer;

    &:hover {
      color: #57a3f3;
      text-decoration: underline;
    }
  }

  .author-link {
    color: #2d8cf0;

    &:hover {
      color: #57a3f3;
      text-decoration: underline;
    }
  }

  // 响应式设计
  @media (max-width: 768px) {
    .overview-stats {
      flex-direction: column;

      .stat-item {
        margin-bottom: 10px;
      }
    }

    .panel-extra {
      .filter {
        flex-wrap: wrap;

        .filter-input {
          width: 120px;
        }
      }
    }
  }
}
</style>