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
            <div class="no-contest-content">
              <Icon type="trophy" size="48" class="no-contest-icon" />
              <p>{{ $t('m.No_Upcoming_Contests') }}</p>
            </div>
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
      border-radius: 8px;
      box-shadow: 0 2px 12px rgba(24, 144, 255, 0.15);
      transition: all 0.3s ease;
      border: 1px solid #e8f4ff;

      &:hover {
        box-shadow: 0 6px 16px rgba(24, 144, 255, 0.25);
        transform: translateY(-2px);
      }

      /deep/ .ivu-card-head {
        border-bottom: 1px solid #e8f4ff;
        padding: 16px 24px;
        background: linear-gradient(120deg, #f0f8ff 0%, #e6f7ff 100%);
        border-radius: 8px 8px 0 0;

        .section-header {
          display: flex;
          align-items: center;
          font-size: 20px;
          font-weight: 600;
          color: #1890ff;

          .header-icon {
            margin-right: 12px;
            color: #1890ff;
            font-size: 22px;
          }
        }
      }

      /deep/ .ivu-card-body {
        padding: 0;
      }

      .contest-carousel-wrapper {
        .contest-carousel {
          /deep/ .ivu-carousel-list {
            height: 320px;
          }

          /deep/ .ivu-carousel-arrow {
            color: #1890ff;
            font-size: 20px;
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.9);
            box-shadow: 0 4px 12px rgba(24, 144, 255, 0.2);
            transition: all 0.3s ease;

            &:hover {
              background: #fff;
              transform: scale(1.1);
            }
          }

          .contest-content {
            height: 320px;
            padding: 30px 50px;
            display: flex;
            flex-direction: column;
            background: linear-gradient(135deg, #f0f8ff 0%, #e6f7ff 100%);
            position: relative;
            overflow: hidden;

            &::before {
              content: "";
              position: absolute;
              top: -50px;
              right: -50px;
              width: 200px;
              height: 200px;
              border-radius: 50%;
              background: rgba(24, 144, 255, 0.05);
            }

            &::after {
              content: "";
              position: absolute;
              bottom: -80px;
              left: -30px;
              width: 250px;
              height: 250px;
              border-radius: 50%;
              background: rgba(24, 144, 255, 0.03);
            }

            .contest-title {
              font-size: 24px;
              font-weight: 700;
              color: #1890ff;
              margin: 0 0 25px;
              text-align: center;
              cursor: pointer;
              transition: all 0.3s ease;
              position: relative;
              z-index: 1;

              &:hover {
                color: #096dd9;
                transform: scale(1.02);
              }
            }

            .contest-info {
              display: flex;
              justify-content: center;
              flex-wrap: wrap;
              gap: 20px;
              margin-bottom: 25px;
              position: relative;
              z-index: 1;

              .info-item {
                display: flex;
                align-items: center;
                background: rgba(255, 255, 255, 0.8);
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 14px;
                color: #515a6e;
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
                transition: all 0.3s ease;

                &:hover {
                  transform: translateY(-2px);
                  box-shadow: 0 4px 10px rgba(24, 144, 255, 0.15);
                  background: #fff;
                }

                .info-icon {
                  margin-right: 8px;
                  color: #1890ff;
                  font-size: 16px;
                }
              }
            }

            .contest-description {
              flex: 1;
              margin-bottom: 25px;
              display: flex;
              align-items: center;
              position: relative;
              z-index: 1;

              blockquote {
                text-align: center;
                margin: 0;
                color: #515a6e;
                font-size: 15px;
                line-height: 1.7;
                max-height: 100px;
                overflow: hidden;
                background: rgba(255, 255, 255, 0.7);
                padding: 15px 20px;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
              }
            }

            .contest-action {
              text-align: center;
              position: relative;
              z-index: 1;

              .ivu-btn {
                padding: 8px 24px;
                font-size: 15px;
                border-radius: 20px;
                background: linear-gradient(120deg, #1890ff 0%, #096dd9 100%);
                border: none;
                box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
                transition: all 0.3s ease;

                &:hover {
                  transform: translateY(-2px);
                  box-shadow: 0 6px 16px rgba(24, 144, 255, 0.4);
                }

                i {
                  margin-left: 8px;
                  transition: transform 0.3s ease;
                }

                &:hover i {
                  transform: translateX(3px);
                }
              }
            }
          }
        }
      }

      .no-contest {
        height: 320px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(120deg, #f0f8ff 0%, #e6f7ff 100%);
        border-radius: 0 0 8px 8px;

        .no-contest-content {
          text-align: center;
          padding: 20px;

          .no-contest-icon {
            color: #1890ff;
            margin-bottom: 20px;
            opacity: 0.7;
          }

          p {
            margin: 0;
            color: #515a6e;
            font-size: 18px;
            font-weight: 500;
          }
        }
      }
    }

    .announcement-section {
      /deep/ .ivu-card {
        border-radius: 8px;
        box-shadow: 0 2px 12px rgba(24, 144, 255, 0.15);
        transition: all 0.3s ease;
        border: 1px solid #e8f4ff;

        &:hover {
          box-shadow: 0 6px 16px rgba(24, 144, 255, 0.25);
          transform: translateY(-2px);
        }
      }

      /deep/ .ivu-card-head {
        border-bottom: 1px solid #e8f4ff;
        padding: 16px 24px;
        background: linear-gradient(120deg, #f0f8ff 0%, #e6f7ff 100%);
        border-radius: 8px 8px 0 0;

        .section-header {
          display: flex;
          align-items: center;
          font-size: 20px;
          font-weight: 600;
          color: #1890ff;

          .header-icon {
            margin-right: 12px;
            color: #1890ff;
            font-size: 22px;
          }
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .home-container {
    padding: 18px 0;

    .home-content {
      .contest-section {
        /deep/ .ivu-card-head {
          padding: 15px 20px;
        }

        .contest-carousel-wrapper {
          .contest-carousel {
            /deep/ .ivu-carousel-list {
              height: 300px;
            }

            .contest-content {
              padding: 25px 40px;
              height: 300px;

              .contest-title {
                font-size: 22px;
                margin-bottom: 20px;
              }

              .contest-info {
                gap: 15px;

                .info-item {
                  padding: 6px 14px;
                  font-size: 13px;
                }
              }

              .contest-description {
                blockquote {
                  font-size: 14px;
                  max-height: 80px;
                  padding: 12px 18px;
                }
              }
            }
          }
        }

        .no-contest {
          height: 300px;

          .no-contest-content {
            p {
              font-size: 17px;
            }
          }
        }
      }
    }
  }
}

@media (max-width: 992px) {
  .home-container {
    padding: 16px 0;

    .home-content {
      .contest-section {
        /deep/ .ivu-card-head {
          padding: 14px 18px;
        }

        .contest-carousel-wrapper {
          .contest-carousel {
            /deep/ .ivu-carousel-list {
              height: 280px;
            }

            .contest-content {
              padding: 20px 30px;
              height: 280px;

              .contest-title {
                font-size: 20px;
                margin-bottom: 18px;
              }

              .contest-info {
                gap: 12px;

                .info-item {
                  padding: 5px 12px;
                  font-size: 12px;
                }
              }

              .contest-description {
                blockquote {
                  font-size: 13px;
                  max-height: 70px;
                  padding: 10px 15px;
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

          .no-contest-content {
            p {
              font-size: 16px;
            }
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