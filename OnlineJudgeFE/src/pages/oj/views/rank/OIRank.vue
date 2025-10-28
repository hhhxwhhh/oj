<template>
  <div class="oi-rank-container">
    <Row type="flex" justify="space-around">
      <Col :span="22">
      <!-- 顶部概览卡片 -->
      <Card class="overview-card" :padding="20" shadow>
        <div class="overview-header">
          <Icon type="md-trophy" size="24" color="#ff9900" />
          <h2 class="overview-title">{{ $t('m.OI_Ranklist') }}</h2>
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
          {{ $t('m.Top_Scorers_Chart') }}
        </div>
        <div class="chart-description">
          {{ $t('m.Top_20_Users_Score_and_Submission_Chart') }}
        </div>

        <!-- 新增统计摘要卡片 -->
        <Row :gutter="15" class="chart-summary-cards">
          <Col :span="6">
          <Card class="summary-card">
            <div class="summary-content">
              <Icon type="md-trophy" size="24" color="#ff9900" />
              <div class="summary-text">
                <p class="summary-value">{{ dataRank.length > 0 ? dataRank[0].total_score : 0 }}</p>
                <p class="summary-label">最高分</p>
              </div>
            </div>
          </Card>
          </Col>
          <Col :span="6">
          <Card class="summary-card">
            <div class="summary-content">
              <Icon type="md-person-add" size="24" color="#2d8cf0" />
              <div class="summary-text">
                <p class="summary-value">{{ averageScore }}</p>
                <p class="summary-label">平均分</p>
              </div>
            </div>
          </Card>
          </Col>
          <Col :span="6">
          <Card class="summary-card">
            <div class="summary-content">
              <Icon type="md-checkmark-circle" size="24" color="#19be6b" />
              <div class="summary-text">
                <p class="summary-value">{{dataRank.length > 0 ? Math.max(...dataRank.map(u => u.accepted_number)) : 0
                  }}</p>
                <p class="summary-label">最多AC</p>
              </div>
            </div>
          </Card>
          </Col>
          <Col :span="6">
          <Card class="summary-card">
            <div class="summary-content">
              <Icon type="md-trending-up" size="24" color="#ff6104" />
              <div class="summary-text">
                <p class="summary-value">{{ submissionGrowth }}%</p>
                <p class="summary-label">提交增长</p>
              </div>
            </div>
          </Card>
          </Col>
        </Row>

        <!-- 图表控制区 -->
        <div class="chart-controls">
          <div class="chart-type-selector">
            <RadioGroup v-model="chartMode" type="button" size="small" @on-change="updateChartDisplay">
              <Radio label="combined">综合视图</Radio>
              <Radio label="score">分数视图</Radio>
              <Radio label="submissions">提交视图</Radio>
            </RadioGroup>
          </div>
          <div class="chart-actions">
            <Button size="small" @click="toggleChartLegend">
              <Icon :type="isLegendVisible ? 'md-eye-off' : 'md-eye'" />
              {{ isLegendVisible ? '隐藏图例' : '显示图例' }}
            </Button>
            <Button size="small" @click="refreshChartData">
              <Icon type="md-refresh" />
              刷新数据
            </Button>
          </div>
        </div>

        <!-- 图表容器 -->
        <div class="echarts-container">
          <ECharts :options="options" ref="chart" auto-resize></ECharts>
        </div>

        <!-- 图表数据分析 -->
        <div class="chart-analysis" v-if="dataRank.length > 0">
          <h4>数据分析洞察</h4>
          <div class="analysis-content">
            <p>
              <Icon type="md-information-circle" /> 最高分用户: <strong>{{ dataRank[0].user.username }}</strong> ({{
                dataRank[0].total_score }}分)
            </p>
            <p>
              <Icon type="md-stats" /> 平均得分率: <strong>{{ averageScoreRate }}%</strong>
            </p>
            <p>
              <Icon type="md-flame" /> 竞争激烈程度: <strong>{{ competitionLevel }}</strong>
            </p>
          </div>
        </div>
      </Panel>

      <!-- 排名表格 -->
      <Panel :padding="0" class="rank-table-panel" shadow>
        <div slot="title" class="panel-title">
          <Icon type="md-list" />
          {{ $t('m.Detailed_Rankings') }}
        </div>
        <div class="table-controls">
          <div class="search-box">
            <Input v-model="searchKeyword" :placeholder="$t('m.Search_User')" size="small" style="width: 200px;"
              @on-enter="filterUsers">
            <Icon type="ios-search" slot="prefix" />
            </Input>
            <Button type="primary" size="small" @click="filterUsers" style="margin-left: 10px;">
              {{ $t('m.Search') }}
            </Button>
            <Button type="default" size="small" @click="clearSearch" style="margin-left: 5px;">
              {{ $t('m.Reset') }}
            </Button>
          </div>
        </div>
        <div class="table-container">
          <Table :data="filteredData" :columns="columns" size="large" :loading="loadingTable" class="rank-table"
            :scroll="{ x: 'max-content' }">
          </Table>
        </div>
      </Panel>

      <!-- 分页器 -->
      <div class="pagination-container">
        <Pagination :total="total" :page-size.sync="limit" :current.sync="page" @on-change="getRankData" show-sizer
          @on-page-size-change="getRankData(1)" class="rank-pagination">
        </Pagination>
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
  name: 'oi-rank',
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
      filteredData: [],
      searchKeyword: '',
      chartMode: 'combined', // combined, score, submissions
      isLegendVisible: true,
      columns: [
        {
          title: this.$i18n.t('m.Rank'),
          align: 'center',
          width: 80,
          fixed: 'left',
          render: (h, params) => {
            const rank = params.index + (this.page - 1) * this.limit + 1
            let rankClass = 'rank-normal'
            if (rank === 1) rankClass = 'rank-first'
            else if (rank === 2) rankClass = 'rank-second'
            else if (rank === 3) rankClass = 'rank-third'

            return h('span', {
              class: ['rank-number', rankClass]
            }, rank)
          }
        },
        {
          title: this.$i18n.t('m.User_User'),
          align: 'left',
          minWidth: 180,
          fixed: 'left',
          render: (h, params) => {
            return h('div', {
              class: 'user-cell'
            }, [
              h('Avatar', {
                props: {
                  src: params.row.user.avatar,
                  size: 'small'
                },
                class: 'user-avatar'
              }),
              h('div', {
                class: 'user-info'
              }, [
                h('a', {
                  class: 'user-name',
                  on: {
                    click: () => {
                      this.$router.push({
                        name: 'user-home',
                        query: { username: params.row.user.username }
                      })
                    }
                  }
                }, params.row.user.username),
                h('span', {
                  class: 'user-mood'
                }, params.row.mood || '--')
              ])
            ])
          }
        },
        {
          title: this.$i18n.t('m.Score'),
          align: 'center',
          key: 'total_score',
          sortable: true,
          width: 120,
          sortType: 'desc',
          render: (h, params) => {
            return h('span', {
              class: 'score-value'
            }, params.row.total_score)
          }
        },
        {
          title: this.$i18n.t('m.AC'),
          align: 'center',
          key: 'accepted_number',
          sortable: true,
          width: 100,
          render: (h, params) => {
            return h('Tag', {
              props: {
                color: params.row.accepted_number > 0 ? 'success' : 'default'
              }
            }, params.row.accepted_number)
          }
        },
        {
          title: this.$i18n.t('m.Total'),
          align: 'center',
          key: 'submission_number',
          sortable: true,
          width: 100
        },
        {
          title: this.$i18n.t('m.Rating'),
          align: 'center',
          width: 120,
          render: (h, params) => {
            const rate = utils.getACRate(params.row.accepted_number, params.row.submission_number)
            let color = 'default'
            if (rate.includes('100%')) color = 'success'
            else if (rate.includes('0%')) color = 'error'
            else color = 'warning'

            return h('Tag', {
              props: {
                color: color
              }
            }, rate)
          }
        },
        {
          title: this.$i18n.t('m.Last_Activity'),
          align: 'center',
          width: 180,
          render: (h, params) => {
            return h('span', {
              class: 'activity-time'
            }, utils.fromNow(params.row.user.last_activity))
          }
        }
      ],
      options: {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross',
            crossStyle: {
              color: '#999'
            }
          }
        },
        legend: {
          data: [this.$i18n.t('m.Score'), this.$i18n.t('m.Submissions')],
          textStyle: {
            color: '#666'
          },
          show: true
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        toolbox: {
          show: true,
          feature: {
            dataView: { show: true, readOnly: true },
            magicType: { show: true, type: ['line', 'bar'] },
            saveAsImage: { show: true }
          },
          right: '10%'
        },
        calculable: true,
        xAxis: [
          {
            type: 'category',
            data: ['root'],
            boundaryGap: true,
            axisLabel: {
              interval: 0,
              showMinLabel: true,
              showMaxLabel: true,
              align: 'center',
              formatter: (value, index) => {
                return utils.breakLongWords(value, 14)
              },
              textStyle: {
                color: '#666'
              }
            },
            axisTick: {
              alignWithLabel: true
            },
            axisLine: {
              lineStyle: {
                color: '#ddd'
              }
            }
          }
        ],
        yAxis: [
          {
            type: 'value',
            name: this.$i18n.t('m.Score'),
            position: 'left',
            axisLabel: {
              textStyle: {
                color: '#666'
              }
            },
            axisLine: {
              lineStyle: {
                color: '#ddd'
              }
            },
            splitLine: {
              lineStyle: {
                type: 'dashed'
              }
            }
          },
          {
            type: 'value',
            name: this.$i18n.t('m.Submissions'),
            position: 'right',
            axisLabel: {
              textStyle: {
                color: '#666'
              }
            },
            axisLine: {
              lineStyle: {
                color: '#ddd'
              }
            },
            splitLine: {
              show: false
            }
          }
        ],
        series: [
          {
            name: this.$i18n.t('m.Score'),
            type: 'bar',
            data: [0],
            barMaxWidth: '50',
            itemStyle: {
              color: {
                type: 'linear',
                x: 0, y: 0, x2: 0, y2: 1,
                colorStops: [
                  { offset: 0, color: '#409eff' },
                  { offset: 1, color: '#2d8cf0' }
                ]
              },
              borderRadius: [4, 4, 0, 0]
            },
            emphasis: {
              itemStyle: {
                color: {
                  type: 'linear',
                  x: 0, y: 0, x2: 0, y2: 1,
                  colorStops: [
                    { offset: 0, color: '#66b1ff' },
                    { offset: 1, color: '#409eff' }
                  ]
                }
              }
            },
            markPoint: {
              data: [
                { type: 'max', name: this.$i18n.t('m.Highest_Score') }
              ]
            }
          },
          {
            name: this.$i18n.t('m.Submissions'),
            type: 'line',
            yAxisIndex: 1,
            data: [0],
            smooth: true,
            itemStyle: {
              color: '#ff9900'
            },
            lineStyle: {
              width: 3
            },
            emphasis: {
              itemStyle: {
                borderWidth: 3,
                borderColor: '#ffaa33'
              }
            },
            markPoint: {
              data: [
                { type: 'max', name: this.$i18n.t('m.Most_Submissions') }
              ]
            }
          }
        ]
      }
    }
  },
  computed: {
    averageScore() {
      if (this.dataRank.length === 0) return 0
      const sum = this.dataRank.reduce((acc, user) => acc + user.total_score, 0)
      return Math.round(sum / this.dataRank.length)
    },
    averageScoreRate() {
      if (this.dataRank.length === 0) return 0
      const maxPossibleScore = 100 // 假设满分是100
      return Math.round((this.averageScore / maxPossibleScore) * 100)
    },
    submissionGrowth() {
      // 简化的提交增长计算
      if (this.dataRank.length < 2) return 0
      const firstHalf = this.dataRank.slice(0, Math.floor(this.dataRank.length / 2))
      const secondHalf = this.dataRank.slice(Math.floor(this.dataRank.length / 2))

      const firstAvg = firstHalf.reduce((acc, user) => acc + user.submission_number, 0) / firstHalf.length
      const secondAvg = secondHalf.reduce((acc, user) => acc + user.submission_number, 0) / secondHalf.length

      return firstAvg > 0 ? Math.round(((secondAvg - firstAvg) / firstAvg) * 100) : 0
    },
    competitionLevel() {
      if (this.dataRank.length === 0) return '低'
      const scoreVariance = this.calculateScoreVariance()
      if (scoreVariance < 50) return '高'
      if (scoreVariance < 150) return '中'
      return '低'
    }
  },
  watch: {
    dataRank: {
      handler(newVal) {
        this.filteredData = [...newVal]
      },
      immediate: true
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

      api.getUserRank(offset, this.limit, RULE_TYPE.OI).then(res => {
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
      let [usernames, scores, submissions] = [[], [], []]
      rankData.forEach(ele => {
        usernames.push(ele.user.username)
        scores.push(ele.total_score)
        submissions.push(ele.submission_number)
      })
      this.options.xAxis[0].data = usernames
      this.options.series[0].data = scores
      this.options.series[1].data = submissions
    },
    calculateScoreVariance() {
      if (this.dataRank.length === 0) return 0
      const scores = this.dataRank.map(user => user.total_score)
      const mean = scores.reduce((a, b) => a + b, 0) / scores.length
      const variance = scores.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / scores.length
      return Math.round(variance)
    },
    toggleChartLegend() {
      this.isLegendVisible = !this.isLegendVisible
      this.options.legend.show = this.isLegendVisible
      this.$refs.chart.mergeOptions(this.options)
    },
    refreshChartData() {
      // 刷新图表数据
      if (this.dataRank.length > 0) {
        this.changeCharts(this.dataRank.slice(0, 10))
      }
    },
    updateChartDisplay() {
      // 根据选择的模式更新图表显示
      switch (this.chartMode) {
        case 'score':
          this.options.series[0].type = 'bar'
          this.options.series[1].type = 'bar'
          this.options.series[1].data = this.options.series[0].data.map(() => 0) // 隐藏提交数据
          break
        case 'submissions':
          this.options.series[0].type = 'bar'
          this.options.series[0].data = this.options.series[1].data.map(() => 0) // 隐藏分数数据
          this.options.series[1].type = 'line'
          break
        default: // combined
          this.options.series[0].type = 'bar'
          this.options.series[1].type = 'line'
          // 恢复原始数据
          if (this.dataRank.length > 0) {
            this.changeCharts(this.dataRank.slice(0, 10))
          }
      }
      this.$refs.chart.mergeOptions(this.options)
    },
    filterUsers() {
      if (!this.searchKeyword) {
        this.filteredData = [...this.dataRank]
        return
      }

      const keyword = this.searchKeyword.toLowerCase()
      this.filteredData = this.dataRank.filter(user =>
        user.user.username.toLowerCase().includes(keyword) ||
        (user.mood && user.mood.toLowerCase().includes(keyword))
      )
    },
    clearSearch() {
      this.searchKeyword = ''
      this.filteredData = [...this.dataRank]
    }
  }
}
</script>

<style scoped lang="less">
.oi-rank-container {
  padding: 20px 0;

  .overview-card {
    margin-bottom: 20px;
    border-radius: 8px;
    border: none;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);

    .overview-header {
      display: flex;
      align-items: center;
      margin-bottom: 20px;

      .overview-title {
        margin: 0 0 0 10px;
        font-size: 22px;
        font-weight: 600;
        color: #333;
      }
    }

    .overview-stats {
      display: flex;
      justify-content: space-between;
      flex-wrap: wrap;

      .stat-item {
        display: flex;
        align-items: center;
        padding: 15px;
        border-radius: 6px;
        background: #f8f9fa;
        flex: 1;
        min-width: 200px;
        margin: 0 10px 10px 0;
        transition: all 0.3s ease;

        &:hover {
          transform: translateY(-3px);
          box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }

        .stat-icon {
          margin-right: 15px;
          padding: 10px;
          border-radius: 50%;
          background: #e6f7ff;
          color: #409eff;
        }

        .stat-content {
          .stat-label {
            margin: 0;
            font-size: 14px;
            color: #666;
          }

          .stat-value {
            margin: 5px 0 0;
            font-size: 20px;
            font-weight: 600;
            color: #409eff;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }
        }
      }
    }
  }

  .chart-panel {
    margin-bottom: 20px;

    .chart-description {
      font-size: 14px;
      color: #666;
      margin-bottom: 15px;
      padding: 0 10px;
    }

    // 新增统计摘要卡片样式
    .chart-summary-cards {
      margin-bottom: 20px;

      .summary-card {
        border-radius: 8px;
        border: none;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);

        .summary-content {
          display: flex;
          align-items: center;

          .summary-text {
            margin-left: 10px;

            .summary-value {
              margin: 0;
              font-size: 20px;
              font-weight: 600;
              color: #333;
            }

            .summary-label {
              margin: 0;
              font-size: 12px;
              color: #888;
            }
          }
        }
      }
    }

    // 图表控制区样式
    .chart-controls {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 15px;
      padding: 0 10px;

      .chart-type-selector {
        /deep/ .ivu-radio-group-button .ivu-radio-wrapper {
          border-radius: 4px;
          margin-right: 5px;
        }
      }

      .chart-actions {
        button {
          margin-left: 8px;
        }
      }
    }

    .echarts-container {
      margin: 0 auto;
      width: 95%;
      height: 400px;
    }

    // 图表数据分析样式
    .chart-analysis {
      margin-top: 20px;
      padding: 15px;
      background: #f8f9fa;
      border-radius: 6px;
      border-left: 4px solid #409eff;

      h4 {
        margin: 0 0 10px 0;
        color: #333;
        font-weight: 600;
      }

      .analysis-content {
        p {
          margin: 8px 0;
          font-size: 14px;
          color: #666;

          strong {
            color: #333;
            font-weight: 600;
          }

          .ivu-icon {
            margin-right: 5px;
            color: #409eff;
          }
        }
      }
    }
  }

  .rank-table-panel {
    margin-bottom: 20px;

    .table-controls {
      padding: 15px 20px 0;
      display: flex;
      justify-content: flex-end;
    }

    .table-container {
      padding: 0 20px 20px;
    }

    .rank-table {
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

        &-cell-fixed-left,
        &-cell-fixed-right {
          background-color: #fff;
        }
      }
    }
  }

  .pagination-container {
    display: flex;
    justify-content: center;
    margin-bottom: 20px;

    .rank-pagination {
      /deep/ .ivu-page {
        &-options {
          margin-left: 15px;
        }
      }
    }
  }

  // 排名数字样式
  .rank-number {
    display: inline-block;
    width: 24px;
    height: 24px;
    line-height: 24px;
    text-align: center;
    border-radius: 50%;
    font-weight: 600;

    &.rank-first {
      background: linear-gradient(135deg, #ffd700, #ffa500);
      color: #fff;
      box-shadow: 0 2px 6px rgba(255, 215, 0, 0.3);
    }

    &.rank-second {
      background: linear-gradient(135deg, #c0c0c0, #a9a9a9);
      color: #fff;
      box-shadow: 0 2px 6px rgba(192, 192, 192, 0.3);
    }

    &.rank-third {
      background: linear-gradient(135deg, #cd7f32, #a0522d);
      color: #fff;
      box-shadow: 0 2px 6px rgba(205, 127, 50, 0.3);
    }

    &.rank-normal {
      background-color: #f0f2f5;
      color: #666;
    }
  }

  // 用户单元格样式
  .user-cell {
    display: flex;
    align-items: center;

    .user-avatar {
      margin-right: 10px;
    }

    .user-info {
      display: flex;
      flex-direction: column;

      .user-name {
        color: #409eff;
        font-weight: 500;
        cursor: pointer;
        text-decoration: none;
        margin-bottom: 2px;

        &:hover {
          color: #66b1ff;
          text-decoration: underline;
        }
      }

      .user-mood {
        color: #888;
        font-style: italic;
        font-size: 12px;
      }
    }
  }

  .score-value {
    font-weight: 600;
    color: #409eff;
    font-size: 16px;
  }

  .activity-time {
    color: #888;
    font-size: 12px;
  }

  // 响应式设计
  @media (max-width: 768px) {
    .overview-stats {
      flex-direction: column;

      .stat-item {
        margin-bottom: 10px;
        min-width: auto;
      }
    }

    .chart-summary-cards {
      .ivu-col {
        margin-bottom: 10px;
      }
    }

    .chart-controls {
      flex-direction: column;
      align-items: flex-start;

      .chart-actions {
        margin-top: 10px;

        button {
          margin: 0 5px 0 0;
        }
      }
    }

    .echarts-container {
      height: 300px;
    }

    .table-controls {
      justify-content: center;

      .search-box {
        width: 100%;
        display: flex;
        justify-content: center;
      }
    }
  }

  @media (max-width: 576px) {
    .overview-card {
      .overview-stats {
        .stat-item {
          padding: 10px;
          margin: 0 0 10px 0;

          .stat-icon {
            margin-right: 10px;
            padding: 8px;
          }

          .stat-content {
            .stat-label {
              font-size: 12px;
            }

            .stat-value {
              font-size: 16px;
            }
          }
        }
      }
    }

    .chart-panel {
      .echarts-container {
        height: 250px;
      }

      .chart-summary-cards {
        .summary-card {
          .summary-content {
            .summary-text {
              .summary-value {
                font-size: 18px;
              }

              .summary-label {
                font-size: 11px;
              }
            }
          }
        }
      }
    }
  }
}
</style>
