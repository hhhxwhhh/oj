<template>
  <div class="acm-rank-container">
    <Row type="flex" justify="space-around">
      <Col :span="22">
      <!-- 顶部概览卡片 -->
      <Card class="overview-card" :padding="20" shadow>
        <div class="overview-header">
          <Icon type="md-trophy" size="24" color="#ff9900" />
          <h2 class="overview-title">{{ $t('m.ACM_Ranklist') }}</h2>
        </div>
        <div class="overview-stats">
          <div class="stat-item">
            <Icon type="md-people" size="20" class="stat-icon" />
            <div class="stat-content">
              <p class="stat-label">{{ $t('m.Total_Users') }}</p>
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
            <Icon type="md-star" size="20" class="stat-icon" />
            <div class="stat-content">
              <p class="stat-label">{{ $t('m.First_Place') }}</p>
              <p class="stat-value" v-if="dataRank.length > 0">{{ dataRank[0].user.username }}</p>
              <p class="stat-value" v-else>--</p>
            </div>
          </div>
        </div>
      </Card>

      <!-- 图表展示区 -->
      <Panel :padding="15" class="chart-panel" shadow>
        <div slot="title" class="panel-title">
          <Icon type="md-analytics" />
          {{ $t('m.ACM_Score_Chart') }}
        </div>
        <div class="chart-description">
          {{ $t('m.Top_10_ACM_Participants') }}
        </div>

        <div class="echarts">
          <ECharts :options="options" ref="chart" auto-resize></ECharts>
        </div>
      </Panel>

      <!-- 排名表格 -->
      <Panel :padding="0" class="rank-table-panel" shadow>
        <div slot="title" class="panel-title">
          <Icon type="md-list" />
          {{ $t('m.Detailed_Rankings') }}
        </div>
        <div class="table-container">
          <Table :data="dataRank" :columns="columns" :loading="loadingTable" size="large" class="rank-table"></Table>
        </div>
      </Panel>

      <!-- 分页器 -->
      <div class="pagination-container">
        <Pagination :total="total" :page-size.sync="limit" :current.sync="page" @on-change="getRankData" show-sizer
          @on-page-size-change="getRankData(1)" class="rank-pagination"></Pagination>
      </div>
      </Col>
    </Row>
  </div>
</template>

<script>
import api from '@oj/api'
import Pagination from '@oj/components/Pagination'
import utils from '@/utils/utils'
import { RULE_TYPE } from '@/utils/constants'

export default {
  name: 'acm-rank',
  components: {
    Pagination
  },
  data() {
    return {
      page: 1,
      limit: 30,
      total: 0,
      loadingTable: false,
      dataRank: [],
      columns: [
        {
          align: 'center',
          width: 60,
          render: (h, params) => {
            return h('span', {
              class: {
                'rank-first': params.index + (this.page - 1) * this.limit + 1 === 1,
                'rank-second': params.index + (this.page - 1) * this.limit + 1 === 2,
                'rank-third': params.index + (this.page - 1) * this.limit + 1 === 3,
                'rank-normal': params.index + (this.page - 1) * this.limit + 1 > 3
              }
            }, params.index + (this.page - 1) * this.limit + 1)
          }
        },
        {
          title: this.$i18n.t('m.User_User'),
          align: 'center',
          render: (h, params) => {
            return h('a', {
              class: 'username-link',
              style: {
                'display': 'inline-block',
                'max-width': '200px'
              },
              on: {
                click: () => {
                  this.$router.push(
                    {
                      name: 'user-home',
                      query: { username: params.row.user.username }
                    })
                }
              }
            }, params.row.user.username)
          }
        },
        {
          title: this.$i18n.t('m.mood'),
          align: 'center',
          key: 'mood'
        },
        {
          title: this.$i18n.t('m.AC'),
          align: 'center',
          key: 'accepted_number',
          render: (h, params) => {
            return h('span', {
              class: 'ac-count'
            }, params.row.accepted_number)
          }
        },
        {
          title: this.$i18n.t('m.Total'),
          align: 'center',
          key: 'submission_number'
        },
        {
          title: this.$i18n.t('m.Rating'),
          align: 'center',
          render: (h, params) => {
            const acRate = utils.getACRate(params.row.accepted_number, params.row.submission_number)
            return h('span', {
              class: {
                'rate-high': acRate >= '60%',
                'rate-medium': acRate >= '30%' && acRate < '60%',
                'rate-low': acRate < '30%'
              }
            }, acRate)
          }
        }
      ],
      options: {
        tooltip: {
          trigger: 'axis'
        },
        legend: {
          data: [this.$i18n.t('m.AC'), this.$i18n.t('m.Total')]
        },
        grid: {
          x: '3%',
          x2: '3%'
        },
        toolbox: {
          show: true,
          feature: {
            dataView: { show: true, readOnly: true },
            magicType: { show: true, type: ['line', 'bar', 'stack'] },
            saveAsImage: { show: true }
          },
          right: '10%'
        },
        calculable: true,
        xAxis: [
          {
            type: 'category',
            data: ['root'],
            axisLabel: {
              interval: 0,
              showMinLabel: true,
              showMaxLabel: true,
              align: 'center',
              formatter: (value, index) => {
                return utils.breakLongWords(value, 10)
              }
            }
          }
        ],
        yAxis: [
          {
            type: 'value'
          }
        ],
        series: [
          {
            name: this.$i18n.t('m.AC'),
            type: 'bar',
            data: [0],
            markPoint: {
              data: [
                { type: 'max', name: 'max' }
              ]
            }
          },
          {
            name: this.$i18n.t('m.Total'),
            type: 'bar',
            data: [0],
            markPoint: {
              data: [
                { type: 'max', name: 'max' }
              ]
            }
          }
        ]
      }
    }
  },
  mounted() {
    this.getRankData(1)
  },
  methods: {
    getRankData(page) {
      let offset = (page - 1) * this.limit
      let bar = this.$refs.chart
      bar.showLoading({ maskColor: 'rgba(250, 250, 250, 0.8)' })
      this.loadingTable = true
      api.getUserRank(offset, this.limit, RULE_TYPE.ACM).then(res => {
        this.loadingTable = false
        if (page === 1) {
          this.changeCharts(res.data.data.results.slice(0, 10))
        }
        this.total = res.data.data.total
        this.dataRank = res.data.data.results
        bar.hideLoading()
      }).catch(() => {
        this.loadingTable = false
        bar.hideLoading()
      })
    },
    changeCharts(rankData) {
      let [usernames, acData, totalData] = [[], [], []]
      rankData.forEach(ele => {
        usernames.push(ele.user.username)
        acData.push(ele.accepted_number)
        totalData.push(ele.submission_number)
      })
      this.options.xAxis[0].data = usernames
      this.options.series[0].data = acData
      this.options.series[1].data = totalData
    }
  }
}
</script>

<style scoped lang="less">
.acm-rank-container {
  .overview-card {
    margin-bottom: 20px;

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

  .chart-panel {
    margin-bottom: 20px;

    .panel-title {
      font-size: 18px;
      font-weight: 500;
    }

    .chart-description {
      color: #808695;
      font-size: 14px;
      margin-bottom: 15px;
    }

    .echarts {
      margin: 0 auto;
      width: 95%;
      height: 400px;
    }
  }

  .rank-table-panel {
    margin-bottom: 20px;

    .panel-title {
      font-size: 18px;
      font-weight: 500;
    }

    .table-container {
      padding: 10px;

      .rank-table {
        border: none;
      }
    }
  }

  .pagination-container {
    display: flex;
    justify-content: center;
    margin-bottom: 20px;

    .rank-pagination {
      text-align: center;
    }
  }

  // 排名样式
  .rank-first {
    font-weight: bold;
    color: #ff9900;
    font-size: 18px;
  }

  .rank-second {
    font-weight: bold;
    color: #c0c0c0;
    font-size: 16px;
  }

  .rank-third {
    font-weight: bold;
    color: #cd7f32;
    font-size: 15px;
  }

  .rank-normal {
    font-weight: normal;
    color: #515a6e;
  }

  .username-link {
    color: #2d8cf0;

    &:hover {
      color: #57a3f3;
      text-decoration: underline;
    }
  }

  .ac-count {
    font-weight: bold;
    color: #19be6b;
  }

  .rate-high {
    color: #19be6b;
    font-weight: bold;
  }

  .rate-medium {
    color: #2d8cf0;
  }

  .rate-low {
    color: #ed4014;
  }
}
</style>