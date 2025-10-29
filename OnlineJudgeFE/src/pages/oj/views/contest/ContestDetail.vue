<template>
  <div class="contest-detail-container">
    <Row type="flex" :gutter="20">
      <Col :span="showMenu ? 17 : 24">
      <div id="contest-main">
        <!--children-->
        <transition name="fade-transform" mode="out-in">
          <router-view></router-view>
        </transition>
        <!--children end-->
        <div class="flex-container" v-if="route_name === 'contest-details'">
          <template>
            <div id="contest-desc">
              <Card class="contest-card" :padding="20" shadow>
                <div class="contest-header">
                  <Icon type="md-trophy" size="24" class="contest-icon" />
                  <h2 class="contest-title">{{ contest.title }}</h2>
                  <Tag type="dot" :color="countdownColor" class="countdown-tag">
                    <Icon :type="getContestStatusIcon()" />
                    <span id="countdown">{{ countdown }}</span>
                  </Tag>
                </div>

                <div class="contest-info">
                  <div class="info-item">
                    <Icon type="md-time" class="info-icon" />
                    <span class="info-label">{{ $t('m.StartAt') }}:</span>
                    <span class="info-value">{{ startTime }}</span>
                  </div>
                  <div class="info-item">
                    <Icon type="md-time" class="info-icon" />
                    <span class="info-label">{{ $t('m.EndAt') }}:</span>
                    <span class="info-value">{{ endTime }}</span>
                  </div>
                  <div class="info-item">
                    <Icon type="md-document" class="info-icon" />
                    <span class="info-label">{{ $t('m.ContestType') }}:</span>
                    <span class="info-value">{{ contestType }}</span>
                  </div>
                  <div class="info-item">
                    <Icon type="md-list" class="info-icon" />
                    <span class="info-label">{{ $t('m.Rule') }}:</span>
                    <span class="info-value">{{ ruleType }}</span>
                  </div>
                  <div class="info-item">
                    <Icon type="md-person" class="info-icon" />
                    <span class="info-label">{{ $t('m.Creator') }}:</span>
                    <span class="info-value">{{ creator }}</span>
                  </div>
                </div>

                <div v-html="contest.description" class="contest-description markdown-body"></div>

                <div v-if="passwordFormVisible" class="contest-password">
                  <div class="password-title">{{ $t('m.Contest_Password_Required') }}</div>
                  <div class="password-form">
                    <Input v-model="contestPassword" type="password" :placeholder="$t('m.Contest_Password')"
                      class="contest-password-input" @on-enter="checkPassword" />
                    <Button type="primary" @click="checkPassword" :loading="btnLoading">{{ $t('m.Enter') }}</Button>
                  </div>
                </div>
              </Card>
            </div>
          </template>
        </div>
      </div>
      </Col>

      <Col v-show="showMenu" :span="7" id="contest-menu">
      <Card class="menu-card" shadow>
        <div class="menu-header">
          <Icon type="md-menu" size="18" />
          <span class="menu-title">{{ $t('m.Contest_Menu') }}</span>
        </div>
        <VerticalMenu @on-click="handleRoute" class="contest-vertical-menu">
          <VerticalMenu-item :route="{ name: 'contest-details', params: { contestID: contestID } }" class="menu-item">
            <Icon type="md-home" />
            {{ $t('m.Overview') }}
          </VerticalMenu-item>

          <VerticalMenu-item :disabled="contestMenuDisabled"
            :route="{ name: 'contest-announcement-list', params: { contestID: contestID } }" class="menu-item">
            <Icon type="md-notifications" />
            {{ $t('m.Announcements') }}
          </VerticalMenu-item>

          <VerticalMenu-item :disabled="contestMenuDisabled"
            :route="{ name: 'contest-problem-list', params: { contestID: contestID } }" class="menu-item">
            <Icon type="md-list" />
            {{ $t('m.Problems') }}
          </VerticalMenu-item>

          <VerticalMenu-item v-if="OIContestRealTimePermission" :disabled="contestMenuDisabled"
            :route="{ name: 'contest-submission-list' }" class="menu-item">
            <Icon type="md-code" />
            {{ $t('m.Submissions') }}
          </VerticalMenu-item>

          <VerticalMenu-item v-if="OIContestRealTimePermission" :disabled="contestMenuDisabled"
            :route="{ name: 'contest-rank', params: { contestID: contestID } }" class="menu-item">
            <Icon type="md-podium" />
            {{ $t('m.Rankings') }}
          </VerticalMenu-item>

          <VerticalMenu-item v-if="showAdminHelper" :route="{ name: 'acm-helper', params: { contestID: contestID } }"
            class="menu-item admin-item">
            <Icon type="md-settings" />
            {{ $t('m.Admin_Helper') }}
          </VerticalMenu-item>
        </VerticalMenu>
      </Card>
      </Col>
    </Row>
  </div>
</template>

<script>
import moment from 'moment'
import api from '@oj/api'
import { mapState, mapGetters, mapActions } from 'vuex'
import { types } from '@/store'
import { CONTEST_STATUS_REVERSE, CONTEST_STATUS } from '@/utils/constants'
import time from '@/utils/time'

export default {
  name: 'ContestDetail',
  components: {},
  data() {
    return {
      CONTEST_STATUS: CONTEST_STATUS,
      route_name: '',
      btnLoading: false,
      contestID: '',
      contestPassword: '',
    }
  },
  mounted() {
    this.contestID = this.$route.params.contestID
    this.route_name = this.$route.name
    this.$store.dispatch('getContest').then(res => {
      this.changeDomTitle({ title: res.data.data.title })
      let data = res.data.data
      let endTime = moment(data.end_time)
      if (endTime.isAfter(moment(data.now))) {
        this.timer = setInterval(() => {
          this.$store.commit(types.NOW_ADD_1S)
        }, 1000)
      }
    })
  },
  methods: {
    ...mapActions(['changeDomTitle']),
    handleRoute(route) {
      this.$router.push(route)
    },
    checkPassword() {
      if (this.contestPassword === '') {
        this.$error(this.$t('m.Password_Cannot_Be_Empty'))
        return
      }
      this.btnLoading = true
      api.checkContestPassword(this.contestID, this.contestPassword).then((res) => {
        this.$success(this.$t('m.Entered_Successfully'))
        this.$store.commit(types.CONTEST_ACCESS, { access: true })
        this.btnLoading = false
      }, (res) => {
        this.btnLoading = false
      })
    },
    getContestStatusIcon() {
      switch (this.contestStatus) {
        case 1: return 'md-calendar'; // Not started
        case 0: return 'md-play'; // Underway
        case -1: return 'md-checkmark'; // Ended
        default: return 'md-information';
      }
    }
  },
  computed: {
    ...mapState({
      showMenu: state => state.contest.itemVisible.menu,
      contest: state => state.contest.contest,
      now: state => state.contest.now
    }),
    ...mapGetters(
      ['contestMenuDisabled', 'contestRuleType', 'contestStatus', 'countdown', 'isContestAdmin',
        'OIContestRealTimePermission', 'passwordFormVisible']
    ),
    countdownColor() {
      if (this.contestStatus) {
        return CONTEST_STATUS_REVERSE[this.contestStatus].color
      }
      return 'default'
    },
    showAdminHelper() {
      return this.isContestAdmin && this.contestRuleType === 'ACM'
    },
    startTime() {
      return this.contest.start_time ? time.utcToLocal(this.contest.start_time) : ''
    },
    endTime() {
      return this.contest.end_time ? time.utcToLocal(this.contest.end_time) : ''
    },
    contestType() {
      return this.contest.contest_type ? this.$t('m.' + this.contest.contest_type.replace(' ', '_')) : ''
    },
    ruleType() {
      return this.contest.rule_type ? this.$t('m.' + this.contest.rule_type) : ''
    },
    creator() {
      return this.contest.created_by ? this.contest.created_by.username : ''
    }
  },
  watch: {
    '$route'(newVal) {
      this.route_name = newVal.name
      this.contestID = newVal.params.contestID
      this.changeDomTitle({ title: this.contest.title })
    }
  },
  beforeDestroy() {
    clearInterval(this.timer)
    this.$store.commit(types.CLEAR_CONTEST)
  }
}
</script>

<style scoped lang="less">
.contest-detail-container {
  padding: 20px 0;

  #contest-main {
    .flex-container {
      #contest-desc {
        flex: auto;

        .contest-card {
          margin-bottom: 20px;
          border-radius: 8px;
          border: none;
          box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);

          .contest-header {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 15px;

            .contest-icon {
              color: #ff9900;
            }

            .contest-title {
              margin: 0;
              font-size: 22px;
              font-weight: 500;
              flex: 1;
              min-width: 200px;
            }

            .countdown-tag {
              font-size: 16px;
              padding: 5px 15px;
              border-radius: 20px;

              #countdown {
                margin-left: 5px;
              }
            }
          }

          .contest-info {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 6px;

            .info-item {
              display: flex;
              align-items: center;

              .info-icon {
                margin-right: 10px;
                color: #2d8cf0;
                min-width: 20px;
              }

              .info-label {
                font-weight: 500;
                color: #515a6e;
                margin-right: 8px;
                white-space: nowrap;
              }

              .info-value {
                color: #333;
              }
            }
          }

          .contest-description {
            margin-bottom: 20px;
            padding: 15px 0;
          }

          .contest-password {
            margin-top: 20px;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 6px;
            border-left: 4px solid #ff9900;

            .password-title {
              font-size: 16px;
              font-weight: 500;
              margin-bottom: 15px;
              color: #333;
            }

            .password-form {
              display: flex;
              gap: 10px;
              align-items: center;
              flex-wrap: wrap;

              .contest-password-input {
                flex: 1;
                min-width: 200px;
              }

              .ivu-btn {
                border-radius: 4px;
              }
            }
          }
        }
      }
    }
  }

  #contest-menu {
    .menu-card {
      border-radius: 8px;
      border: none;
      box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);

      .menu-header {
        display: flex;
        align-items: center;
        padding: 15px;
        border-bottom: 1px solid #e8eaec;
        margin-bottom: 10px;

        .menu-title {
          margin-left: 8px;
          font-size: 16px;
          font-weight: 500;
          color: #333;
        }
      }

      .contest-vertical-menu {
        border: none;

        .menu-item {
          border-radius: 4px;
          margin: 5px 10px;
          transition: all 0.3s ease;

          &:hover:not(.ivu-menu-item-disabled) {
            background-color: #e6f2ff;
            color: #2d8cf0;
          }

          &.ivu-menu-item-active {
            background-color: #e6f2ff;
            color: #2d8cf0;
            border-radius: 4px;
          }

          .ivu-icon {
            margin-right: 8px;
          }
        }

        .admin-item {
          border-top: 1px solid #e8eaec;
          margin-top: 10px;
          padding-top: 10px;
        }
      }
    }
  }
}

// 页面切换动画
.fade-transform-enter-active {
  transition: all .4s ease;
}

.fade-transform-leave-active {
  transition: all .3s ease;
}

.fade-transform-enter {
  opacity: 0;
  transform: translateX(-30px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

// 响应式设计
@media screen and (max-width: 768px) {
  .contest-detail-container {
    padding: 10px;

    .ivu-row {
      flex-direction: column;

      .ivu-col {
        width: 100%;
        margin-bottom: 20px;
      }
    }

    #contest-menu {
      order: -1;
      margin-bottom: 20px !important;
    }

    .contest-info {
      grid-template-columns: 1fr !important;
    }

    .password-form {
      flex-direction: column;

      .contest-password-input {
        width: 100%;
        margin-bottom: 10px;
      }
    }
  }
}
</style>