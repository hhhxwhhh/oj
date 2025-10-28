<template>
  <Row type="flex">
    <Col :span="24">
    <Panel id="contest-card" shadow class="contest-list-panel">
      <div slot="title" class="panel-title">
        <Icon type="md-trophy" class="title-icon" />
        {{ query.rule_type === '' ? this.$i18n.t('m.All') : query.rule_type }} {{ $t('m.Contests') }}
      </div>
      <div slot="extra" class="panel-extra">
        <ul class="filter">
          <li>
            <Dropdown @on-click="onRuleChange">
              <Button type="primary" ghost>
                {{ query.rule_type === '' ? this.$i18n.t('m.Rule') : this.$i18n.t('m.' + query.rule_type) }}
                <Icon type="md-arrow-dropdown"></Icon>
              </Button>
              <Dropdown-menu slot="list">
                <Dropdown-item name="">{{ $t('m.All') }}</Dropdown-item>
                <Dropdown-item name="OI">{{ $t('m.OI') }}</Dropdown-item>
                <Dropdown-item name="ACM">{{ $t('m.ACM') }}</Dropdown-item>
              </Dropdown-menu>
            </Dropdown>
          </li>
          <li>
            <Dropdown @on-click="onStatusChange">
              <Button type="primary" ghost>
                {{ query.status === '' ? this.$i18n.t('m.Status') : this.$i18n.t('m.' +
                  CONTEST_STATUS_REVERSE[query.status].name.replace(/ /g, "_")) }}
                <Icon type="md-arrow-dropdown"></Icon>
              </Button>
              <Dropdown-menu slot="list">
                <Dropdown-item name="">{{ $t('m.All') }}</Dropdown-item>
                <Dropdown-item name="0">{{ $t('m.Underway') }}</Dropdown-item>
                <Dropdown-item name="1">{{ $t('m.Not_Started') }}</Dropdown-item>
                <Dropdown-item name="-1">{{ $t('m.Ended') }}</Dropdown-item>
              </Dropdown-menu>
            </Dropdown>
          </li>
          <li>
            <Input id="keyword" @on-enter="changeRoute" @on-click="changeRoute" v-model="query.keyword"
              icon="ios-search" placeholder="Keyword" class="search-input" />
          </li>
        </ul>
      </div>
      <div v-if="contests.length == 0" class="no-contest">
        <Icon type="ios-alert-outline" size="40" class="no-contest-icon" />
        <p>{{ $t('m.No_contest') }}</p>
      </div>
      <div v-else>
        <div class="contest-list">
          <div v-for="contest in contests" :key="contest.title" class="contest-item">
            <Row type="flex" justify="space-between" align="middle">
              <Col :span="2" class="contest-icon-col">
              <img class="trophy" src="../../../../assets/Cup.png" :alt="$t('m.Contest')" />
              </Col>
              <Col :span="16" class="contest-main">
              <div class="contest-title">
                <a class="entry" @click.stop="goContest(contest)">
                  {{ contest.title }}
                </a>
                <template v-if="contest.contest_type != 'Public'">
                  <Icon type="ios-lock" class="lock-icon" size="18"></Icon>
                </template>
              </div>
              <ul class="contest-detail">
                <li class="detail-item">
                  <Icon type="md-calendar" class="detail-icon calendar-icon"></Icon>
                  <span class="detail-text">{{ contest.start_time | localtime('YYYY-M-D HH:mm') }}</span>
                </li>
                <li class="detail-item">
                  <Icon type="md-time" class="detail-icon time-icon"></Icon>
                  <span class="detail-text">{{ getDuration(contest.start_time, contest.end_time) }}</span>
                </li>
                <li class="detail-item">
                  <Button size="small" shape="circle" @click="onRuleChange(contest.rule_type)"
                    :type="contest.rule_type === 'ACM' ? 'primary' : 'success'" class="rule-type-btn">
                    {{ contest.rule_type }}
                  </Button>
                </li>
              </ul>
              </Col>
              <Col :span="6" class="contest-status-col">
              <Tag type="dot" :color="CONTEST_STATUS_REVERSE[contest.status].color" class="status-tag">
                {{ $t('m.' + CONTEST_STATUS_REVERSE[contest.status].name.replace(/ /g, "_")) }}
              </Tag>
              </Col>
            </Row>
          </div>
        </div>
      </div>
    </Panel>
    <Pagination :total="total" :page-size.sync="limit" @on-change="changeRoute" :current.sync="page" :show-sizer="true"
      @on-page-size-change="changeRoute" class="contest-pagination"></Pagination>
    </Col>
  </Row>
</template>

<script>
import api from '@oj/api'
import { mapGetters } from 'vuex'
import utils from '@/utils/utils'
import Pagination from '@/pages/oj/components/Pagination'
import time from '@/utils/time'
import { CONTEST_STATUS_REVERSE, CONTEST_TYPE } from '@/utils/constants'
import Panel from '@oj/components/Panel.vue'

const limit = 10

export default {
  name: 'contest-list',
  components: {
    Pagination,
    Panel
  },
  data() {
    return {
      page: 1,
      query: {
        status: '',
        keyword: '',
        rule_type: ''
      },
      limit: limit,
      total: 0,
      rows: '',
      contests: [],
      CONTEST_STATUS_REVERSE: CONTEST_STATUS_REVERSE,
      //      for password modal use
      cur_contest_id: ''
    }
  },
  beforeRouteEnter(to, from, next) {
    api.getContestList(0, limit).then((res) => {
      next((vm) => {
        vm.contests = res.data.data.results
        vm.total = res.data.data.total
      })
    }, (res) => {
      next()
    })
  },
  methods: {
    init() {
      let route = this.$route.query
      this.query.status = route.status || ''
      this.query.rule_type = route.rule_type || ''
      this.query.keyword = route.keyword || ''
      this.page = parseInt(route.page) || 1
      this.limit = parseInt(route.limit) || 10
      this.getContestList(this.page)
    },
    getContestList(page = 1) {
      let offset = (page - 1) * this.limit
      api.getContestList(offset, this.limit, this.query).then((res) => {
        this.contests = res.data.data.results
        this.total = res.data.data.total
      })
    },
    changeRoute() {
      let query = Object.assign({}, this.query)
      query.page = this.page
      query.limit = this.limit

      this.$router.push({
        name: 'contest-list',
        query: utils.filterEmptyValue(query)
      })
    },
    onRuleChange(rule) {
      this.query.rule_type = rule
      this.page = 1
      this.changeRoute()
    },
    onStatusChange(status) {
      this.query.status = status
      this.page = 1
      this.changeRoute()
    },
    goContest(contest) {
      this.cur_contest_id = contest.id
      if (contest.contest_type !== CONTEST_TYPE.PUBLIC && !this.isAuthenticated) {
        this.$error(this.$i18n.t('m.Please_login_first'))
        this.$store.dispatch('changeModalStatus', { visible: true })
      } else {
        this.$router.push({ name: 'contest-details', params: { contestID: contest.id } })
      }
    },

    getDuration(startTime, endTime) {
      return time.duration(startTime, endTime)
    }
  },
  computed: {
    ...mapGetters(['isAuthenticated', 'user'])
  },
  watch: {
    '$route'(newVal, oldVal) {
      if (newVal !== oldVal) {
        this.init()
      }
    }
  }

}
</script>
<style lang="less" scoped>
.contest-list-panel {
  .panel-title {
    font-weight: 500;
    display: flex;
    align-items: center;

    .title-icon {
      margin-right: 8px;
      color: #2d8cf0;
    }
  }

  .panel-extra {
    .filter {
      display: flex;
      align-items: center;

      >li {
        padding: 0 5px;

        .search-input {
          width: 200px;
          margin-left: 10px;
        }
      }
    }
  }

  .no-contest {
    text-align: center;
    padding: 60px 0;

    .no-contest-icon {
      color: #c5c8ce;
      margin-bottom: 15px;
    }

    p {
      font-size: 16px;
      color: #808695;
    }
  }

  .contest-list {
    .contest-item {
      padding: 20px;
      border-bottom: 1px solid #e8eaec;
      transition: all 0.3s ease;

      &:hover {
        background-color: #f8f8f9;
        transform: translateY(-2px);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
      }

      &:last-child {
        border-bottom: none;
      }

      .contest-icon-col {
        text-align: center;

        .trophy {
          height: 40px;
        }
      }

      .contest-main {
        .contest-title {
          font-size: 18px;
          margin-bottom: 15px;
          display: flex;
          align-items: center;

          .entry {
            color: #495060;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;

            &:hover {
              color: #2d8cf0;
            }
          }

          .lock-icon {
            margin-left: 10px;
            color: #ff9900;
          }
        }

        .contest-detail {
          display: flex;
          flex-wrap: wrap;

          .detail-item {
            display: flex;
            align-items: center;
            margin-right: 20px;
            margin-bottom: 8px;

            .detail-icon {
              font-size: 16px;
              margin-right: 6px;
            }

            .calendar-icon {
              color: #2d8cf0;
            }

            .time-icon {
              color: #52c41a;
            }

            .detail-text {
              font-size: 14px;
              color: #808695;
            }

            .rule-type-btn {
              font-weight: 500;
            }
          }
        }
      }

      .contest-status-col {
        text-align: center;

        .status-tag {
          font-size: 14px;
          font-weight: 500;
          padding: 5px 15px;
        }
      }
    }
  }
}

.contest-pagination {
  margin: 20px;
  float: right;
}

// 响应式设计
@media screen and (max-width: 768px) {
  .contest-list-panel {
    .panel-extra {
      .filter {
        >li {
          .search-input {
            width: 120px;
          }
        }
      }
    }

    .contest-list {
      .contest-item {
        padding: 15px 10px;

        .contest-main {
          .contest-title {
            font-size: 16px;
          }

          .contest-detail {
            .detail-item {
              margin-right: 10px;

              .detail-text {
                font-size: 13px;
              }
            }
          }
        }
      }
    }
  }
}

@media screen and (max-width: 576px) {
  .contest-list-panel {
    .panel-extra {
      .filter {
        >li {
          padding: 0 2px;

          .search-input {
            width: 100px;
            margin-left: 5px;
          }
        }
      }
    }

    .contest-list {
      .contest-item {
        .contest-icon-col {
          .trophy {
            height: 30px;
          }
        }

        .contest-main {
          .contest-title {
            font-size: 15px;
            margin-bottom: 10px;
          }

          .contest-detail {
            .detail-item {
              margin-right: 8px;
              margin-bottom: 5px;
            }
          }
        }

        .contest-status-col {
          .status-tag {
            font-size: 12px;
            padding: 3px 10px;
          }
        }
      }
    }
  }
}
</style>