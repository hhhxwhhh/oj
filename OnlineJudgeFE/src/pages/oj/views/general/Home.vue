<template>
  <div class="home-container">
    <Row type="flex" justify="space-around">
      <Col :span="22">
      <div class="home-content">
        <!-- 竞赛轮播 -->
        <Card shadow class="contest-section" :padding="0">
          <div slot="title" class="section-header">
            <Icon type="trophy" class="header-icon" />
            <span class="header-title">{{ $t('m.Upcoming_Contests') }}</span>
          </div>
          <div v-if="contests.length" class="contest-carousel-wrapper">
            <Carousel v-model="index" trigger="hover" autoplay :autoplay-speed="6000" class="contest-carousel"
              arrow="hover">
              <CarouselItem v-for="(contest, idx) of contests" :key="idx">
                <div class="contest-content">
                  <h3 class="contest-title" @click="goContest(contest.id)">
                    {{ contest.title }}
                  </h3>
                  <div class="contest-info">
                    <div class="info-item">
                      <Icon type="ios-calendar" class="info-icon" />
                      <span>{{ contest.start_time | localtime('YYYY-MM-DD HH:mm') }}</span>
                    </div>
                    <div class="info-item">
                      <Icon type="ios-time" class="info-icon" />
                      <span>{{ getDuration(contest.start_time, contest.end_time) }}</span>
                    </div>
                    <div class="info-item">
                      <Icon type="trophy" class="info-icon" />
                      <span>{{ contest.rule_type }}</span>
                    </div>
                  </div>
                  <div class="contest-description">
                    <blockquote v-html="contest.description"></blockquote>
                  </div>
                  <div class="contest-action">
                    <Button type="primary" @click="goContest(contest.id)" size="large">
                      {{ $t('m.View_Contest') }}
                      <Icon type="ios-arrow-forward" />
                    </Button>
                  </div>
                </div>
              </CarouselItem>
            </Carousel>
          </div>
          <div v-else class="no-contest">
            <p>{{ $t('m.No_Upcoming_Contests') }}</p>
          </div>
        </Card>

        <!-- 公告区域 -->
        <div class="announcement-section">
          <Announcements></Announcements>
        </div>
      </div>
      </Col>
    </Row>
  </div>
</template>

<script>
import Announcements from './Announcements.vue'
import api from '@oj/api'
import time from '@/utils/time'
import { CONTEST_STATUS } from '@/utils/constants'

export default {
  name: 'home',
  components: {
    Announcements
  },
  data() {
    return {
      contests: [],
      index: 0
    }
  },
  mounted() {
    let params = { status: CONTEST_STATUS.NOT_START }
    api.getContestList(0, 5, params).then(res => {
      this.contests = res.data.data.results
    })
  },
  methods: {
    getDuration(startTime, endTime) {
      return time.duration(startTime, endTime)
    },
    goContest(contestId) {
      this.$router.push({
        name: 'contest-details',
        params: { contestID: contestId }
      })
    }
  }
}
</script>

<style lang="less" scoped>
.home-container {
  width: 100%;
  padding: 20px 0;

  .home-content {
    .contest-section {
      margin-bottom: 20px;
      border-radius: 4px;
      box-shadow: 0 1px 6px rgba(0, 0, 0, 0.05);
      transition: box-shadow 0.3s ease;

      &:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      }

      /deep/ .ivu-card-head {
        border-bottom: 1px solid #e8eaec;
        padding: 14px 20px;
        background-color: #f8f9fa;

        .section-header {
          display: flex;
          align-items: center;
          font-size: 18px;
          font-weight: 500;
          color: #515a6e;

          .header-icon {
            margin-right: 10px;
            color: #2d8cf0;
            font-size: 20px;
          }
        }
      }

      /deep/ .ivu-card-body {
        padding: 0;
      }

      .contest-carousel-wrapper {
        .contest-carousel {
          /deep/ .ivu-carousel-list {
            height: 280px;
          }

          /deep/ .ivu-carousel-arrow {
            color: #2d8cf0;
            font-size: 18px;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.8);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
          }

          .contest-content {
            height: 280px;
            padding: 25px 40px;
            display: flex;
            flex-direction: column;
            background: linear-gradient(120deg, #f0f8ff 0%, #e6f7ff 100%);

            .contest-title {
              font-size: 22px;
              font-weight: 600;
              color: #495060;
              margin: 0 0 20px;
              text-align: center;
              cursor: pointer;
              transition: color 0.3s;

              &:hover {
                color: #2d8cf0;
              }
            }

            .contest-info {
              display: flex;
              justify-content: center;
              flex-wrap: wrap;
              gap: 15px;
              margin-bottom: 20px;

              .info-item {
                display: flex;
                align-items: center;
                background: rgba(255, 255, 255, 0.7);
                padding: 6px 12px;
                border-radius: 16px;
                font-size: 13px;
                color: #515a6e;

                .info-icon {
                  margin-right: 5px;
                  color: #2d8cf0;
                }
              }
            }

            .contest-description {
              flex: 1;
              margin-bottom: 20px;
              display: flex;
              align-items: center;

              blockquote {
                text-align: center;
                margin: 0;
                color: #657180;
                font-size: 14px;
                line-height: 1.6;
                max-height: 80px;
                overflow: hidden;
              }
            }

            .contest-action {
              text-align: center;

              .ivu-btn {
                padding: 6px 20px;
                font-size: 14px;

                i {
                  margin-left: 5px;
                }
              }
            }
          }
        }
      }

      .no-contest {
        height: 280px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #f8f9fa;

        p {
          margin: 0;
          color: #808695;
          font-size: 16px;
        }
      }
    }

    .announcement-section {
      /deep/ .ivu-card {
        border-radius: 4px;
        box-shadow: 0 1px 6px rgba(0, 0, 0, 0.05);
        transition: box-shadow 0.3s ease;

        &:hover {
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
      }

      /deep/ .ivu-card-head {
        border-bottom: 1px solid #e8eaec;
        padding: 14px 20px;
        background-color: #f8f9fa;

        .section-header {
          display: flex;
          align-items: center;
          font-size: 18px;
          font-weight: 500;
          color: #515a6e;

          .header-icon {
            margin-right: 10px;
            color: #2d8cf0;
            font-size: 20px;
          }
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .home-container {
    padding: 15px 0;

    .home-content {
      .contest-section {
        /deep/ .ivu-card-head {
          padding: 12px 15px;
        }

        .contest-carousel-wrapper {
          .contest-carousel {
            /deep/ .ivu-carousel-list {
              height: 250px;
            }

            .contest-content {
              padding: 20px 25px;
              height: 250px;

              .contest-title {
                font-size: 18px;
                margin-bottom: 15px;
              }

              .contest-info {
                gap: 10px;

                .info-item {
                  padding: 4px 10px;
                  font-size: 12px;
                }
              }

              .contest-description {
                blockquote {
                  font-size: 13px;
                  max-height: 60px;
                }
              }
            }
          }
        }

        .no-contest {
          height: 250px;

          p {
            font-size: 15px;
          }
        }
      }
    }
  }
}

@media (max-width: 576px) {
  .home-container {
    padding: 10px 0;

    .home-content {
      .contest-section {
        .contest-carousel-wrapper {
          .contest-carousel {
            /deep/ .ivu-carousel-list {
              height: 280px;
            }

            .contest-content {
              padding: 15px 20px;
              height: 280px;

              .contest-info {
                flex-direction: column;
                align-items: center;
              }

              .contest-description {
                blockquote {
                  font-size: 12px;
                }
              }

              .contest-action {
                .ivu-btn {
                  padding: 5px 15px;
                  font-size: 13px;
                }
              }
            }
          }
        }

        .no-contest {
          height: 280px;
        }
      }
    }
  }
}
</style>