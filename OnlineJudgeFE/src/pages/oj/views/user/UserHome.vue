<template>
  <div class="container">
    <Card :padding="0">
      <div class="user-header">
        <div class="avatar-wrapper">
          <img class="avatar" :src="profile.avatar" />
        </div>
        <div class="user-info">
          <h2>{{ profile.user.username }}</h2>
          <p v-if="profile.school" class="school">@{{ profile.school }}</p>
          <p v-if="profile.mood" class="mood">{{ profile.mood }}</p>
        </div>
      </div>
    </Card>


    <Card :padding="20" class="stats-card">
      <div class="flex-container">
        <div class="stat-item">
          <p class="stat-label">{{ $t('m.UserHomeSolved') }}</p>
          <p class="stat-value">{{ profile.accepted_number }}</p>
        </div>
        <div class="stat-item">
          <p class="stat-label">{{ $t('m.UserHomeserSubmissions') }}</p>
          <p class="stat-value">{{ profile.submission_number }}</p>
        </div>
        <div class="stat-item">
          <p class="stat-label">{{ $t('m.UserHomeScore') }}</p>
          <p class="stat-value">{{ profile.total_score }}</p>
        </div>
      </div>
    </Card>
    <Card :padding="20" class="stats-card ability-card" v-if="abilityData">
      <div class="flex-container">
        <div class="stat-item">
          <Icon type="md-speedometer" size="24" class="ability-icon" />
          <div class="ability-info">
            <p class="stat-label">编程能力评分</p>
            <p class="stat-value ability-score">{{ abilityData.overall_score.toFixed(0) }}</p>
          </div>
        </div>
        <div class="stat-item">
          <Icon type="md-medal" size="24" class="ability-icon" />
          <div class="ability-info">
            <p class="stat-label">能力等级</p>
            <p class="stat-value">
              <Tag :color="getLevelColor(abilityData.level)" class="level-tag">
                {{ getLevelDisplay(abilityData.level) }}
              </Tag>
            </p>
          </div>
        </div>
        <div class="stat-item">
          <Icon type="md-bulb" size="24" class="ability-icon" />
          <div class="ability-info">
            <p class="stat-label">建议关注</p>
            <p class="stat-value recommendation-text">{{ getMainRecommendation() }}</p>
          </div>
        </div>
        <div class="stat-item action-item">
          <Button type="primary" size="small" @click="goToAbilityDashboard" class="detail-report-btn" long>
            <Icon type="md-document" /> 详细报告
          </Button>
          <p class="action-description">查看完整能力分析</p>
        </div>
      </div>
    </Card>

    <div class="content-grid">
      <Card :padding="20" class="section-card">
        <div id="learning-paths" v-if="learningPaths.length > 0">
          <div class="section-header">
            <Icon type="ios-book" size="20" class="section-icon"></Icon>
            <h3 class="section-title">{{ $t('m.My_Learning_Path') }}</h3>
          </div>

          <div class="learning-paths-container">
            <div class="learning-path-card" v-for="path of learningPaths" :key="path.id">
              <div class="path-header">
                <h4 class="path-title">{{ path.title }}</h4>
              </div>
              <div class="path-content">
                <p class="path-description">{{ path.description }}</p>
                <div class="path-meta">
                  <span class="path-duration">
                    <Icon type="ios-time-outline" size="14"></Icon>
                    {{ path.estimated_duration }} {{ $t('m.Hours') }}
                  </span>
                </div>
              </div>
              <div class="path-footer">
                <Button type="primary" size="small" @click="goLearningPath(path.id)" long>
                  {{ $t('m.Continue_Learning') }}
                </Button>
              </div>
            </div>
          </div>

          <div class="section-footer">
            <Button type="ghost" @click="goToLearningPathAll" long>
              {{ $t('m.View_All_Learning_Paths') }}
              <Icon type="ios-arrow-forward" size="14"></Icon>
            </Button>
          </div>
        </div>
      </Card>

      <Card :padding="20" class="section-card" v-if="recommendedProblems.length > 0">
        <div id="recommended-problems">
          <div class="section-header">
            <Icon type="ios-star" size="20" class="section-icon"></Icon>
            <h3 class="section-title">{{ $t('m.Recommended_For_You') }}</h3>
          </div>

          <div class="problems-container">
            <div class="problem-item" v-for="problem of recommendedProblems" :key="problem.problem_id">
              <Button type="primary" size="small" @click="goProblem(problem.problem_display_id)">
                {{ problem.problem_display_id }}
              </Button>
              <div class="problem-info">
                <h4 class="problem-title">{{ problem.title }}</h4>
                <p class="problem-reason">{{ problem.reason }}</p>
              </div>
            </div>
          </div>
        </div>
      </Card>

      <Card :padding="20" class="section-card">
        <div id="problems">
          <div class="section-header">
            <Icon type="ios-list-box" size="20" class="section-icon"></Icon>
            <h3 class="section-title">
              {{ $t('m.List_Solved_Problems') }}
              <Poptip v-if="refreshVisible" trigger="hover" placement="right-start">
                <Icon type="ios-help-circle-outline" size="16" class="help-icon"></Icon>
                <div slot="content">
                  <p>{{ $t('m.If_problem_id_does_not_exist') }}</p>
                  <Button type="info" size="small" @click="freshProblemDisplayID">
                    {{ $t('m.Regenerate') }}
                  </Button>
                </div>
              </Poptip>
            </h3>
          </div>

          <div class="problems-container">
            <div class="problem-item" v-for="problemID of problems" :key="problemID">
              <Button type="ghost" size="small" @click="goProblem(problemID)">
                {{ problemID }}
              </Button>
            </div>
            <p v-if="!problems.length" class="no-problems">
              {{ $t('m.UserHomeIntro') }}
            </p>
          </div>
        </div>
      </Card>
    </div>

    <Card :padding="20" class="social-card">
      <div id="icons">
        <a :href="profile.github" v-if="profile.github">
          <Icon type="logo-github" size="24"></Icon>
        </a>
        <a :href="'mailto:' + profile.user.email" v-if="profile.user.email">
          <Icon type="ios-mail" size="24"></Icon>
        </a>
        <a :href="profile.blog" v-if="profile.blog">
          <Icon type="ios-link" size="24"></Icon>
        </a>
      </div>
    </Card>
  </div>
</template>

<script>
import { mapActions } from 'vuex'
import time from '@/utils/time'
import api from '@oj/api'

export default {
  data() {
    return {
      username: '',
      profile: {},
      problems: [],
      recommendedProblems: [],
      learningPaths: [],
      abilityData: null,
    }
  },
  mounted() {
    this.init()
  },
  methods: {
    ...mapActions(['changeDomTitle']),
    init() {
      this.username = this.$route.query.username
      api.getUserInfo(this.username).then(res => {
        this.changeDomTitle({ title: res.data.data.user.username })
        this.profile = res.data.data
        this.getSolvedProblems()
        this.getRecommendedProblems()
        this.getLearningPaths()
        let registerTime = time.utcToLocal(this.profile.user.create_time, 'YYYY-MM-D')
        console.log('The guy registered at ' + registerTime + '.')
        this.getAbilityData()
      })
    },
    getLevelColor(level) {
      const levelMap = {
        'beginner': '#ed4014',
        'intermediate': '#2d8cf0',
        'advanced': '#ff9900',
        'expert': '#19be6b'
      };
      return levelMap[level] || '#2d8cf0';
    },
    getSolvedProblems() {
      let ACMProblems = this.profile.acm_problems_status.problems || {}
      let OIProblems = this.profile.oi_problems_status.problems || {}
      let ACProblems = []
      for (let problems of [ACMProblems, OIProblems]) {
        Object.keys(problems).forEach(problemID => {
          if (problems[problemID]['status'] === 0) {
            ACProblems.push(problems[problemID]['_id'])
          }
        })
      }
      ACProblems.sort()
      this.problems = ACProblems
    },
    goToAbilityDashboard() {
      this.$router.push({ name: 'ability-dashboard' })
    },
    getAbilityData() {
      api.getProgrammingAbilityReport().then(res => {
        this.abilityData = res.data.data;
      }).catch(err => {
        console.error('Failed to load ability data:', err);
      });
    },

    getLearningPaths() {
      api.getLearningPaths().then(res => {
        this.learningPaths = res.data.data.slice(0, 3);
      }).catch(err => {
        console.error('Failed to load learning paths:', err)
      })
    },
    getRecommendedProblems() {
      api.getRecommendedProblems(5).then(res => {
        this.recommendedProblems = res.data.data || []
      }).catch(err => {
        console.error('Failed to load recommended problems:', err)
      })
    },
    goProblem(problemID) {
      this.$router.push({ name: 'problem-details', params: { problemID: problemID } })
    },
    goLearningPath(pathId) {
      this.$router.push({ name: 'learning-path', query: { pathId: pathId } })
    },
    goToLearningPathAll() {
      this.$router.push({ name: 'learning-path' })
    },
    getLevelDisplay(level) {
      const levelMap = {
        'beginner': '入门',
        'intermediate': '中级',
        'advanced': '高级',
        'expert': '专家'
      };
      return levelMap[level] || level;
    },
    getMainRecommendation() {
      if (!this.abilityData || !this.abilityData.analysis_report) return '暂无';
      const recommendations = this.abilityData.analysis_report.recommendations;
      if (recommendations && recommendations.length > 0) {
        // 返回第一条建议的类型
        const typeMap = {
          'basic_programming': '基础',
          'data_structures': '数据结构',
          'algorithm_design': '算法',
          'problem_solving': '解题能力'
        };
        return typeMap[recommendations[0].type] || '学习计划';
      }
      return '暂无';
    },
    freshProblemDisplayID() {
      api.freshDisplayID().then(res => {
        this.$success('Update successfully')
        this.init()
      })
    }
  },
  computed: {
    refreshVisible() {
      if (!this.username) return true
      if (this.username && this.username === this.$store.getters.user.username) return true
      return false
    }
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
.container {
  position: relative;
  width: 80%;
  max-width: 1200px;
  margin: 30px auto;
  padding: 20px 0;

  .user-header {
    display: flex;
    padding: 30px;
    background: linear-gradient(120deg, #a1c4fd 0%, #c2e9fb 100%);
    border-radius: 4px 4px 0 0;

    .avatar-wrapper {
      width: 100px;
      height: 100px;
      border-radius: 50%;
      overflow: hidden;
      border: 3px solid rgba(255, 255, 255, 0.5);
      margin-right: 20px;
      flex-shrink: 0;

      .avatar {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
    }

    .user-info {
      display: flex;
      flex-direction: column;
      justify-content: center;
      color: #fff;

      h2 {
        margin: 0 0 5px 0;
        font-size: 24px;
        font-weight: 600;
        color: #fff;
      }

      .school {
        margin: 5px 0;
        font-size: 16px;
        opacity: 0.9;
      }

      .mood {
        margin: 5px 0;
        font-size: 14px;
        opacity: 0.8;
      }
    }
  }

  .stats-card {
    margin: 20px 0;

    .flex-container {
      display: flex;
      text-align: center;

      .stat-item {
        flex: 1;
        padding: 15px;

        .stat-label {
          margin: 0;
          font-size: 14px;
          color: #808695;
        }

        .stat-value {
          margin: 5px 0 0;
          font-size: 24px;
          font-weight: 600;
          color: #2d8cf0;
        }
      }

      .stat-item:not(:last-child) {
        border-right: 1px solid #e8eaec;
      }
    }
  }

  .content-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 20px;
    margin: 20px 0;
  }

  .section-card {
    .section-header {
      display: flex;
      align-items: center;
      margin-bottom: 20px;
      padding-bottom: 10px;
      border-bottom: 1px solid #e8eaec;

      .section-icon {
        color: #2d8cf0;
        margin-right: 10px;
      }

      .section-title {
        margin: 0;
        font-size: 18px;
        font-weight: 600;
        color: #495060;
        display: flex;
        align-items: center;

        .help-icon {
          margin-left: 8px;
          color: #c5c8ce;
          cursor: pointer;
        }
      }
    }

    .section-footer {
      margin-top: 15px;
      padding-top: 15px;
      border-top: 1px solid #f5f7f9;
    }

    .learning-paths-container {
      display: grid;
      gap: 15px;

      .learning-path-card {
        border: 1px solid #e8eaec;
        border-radius: 4px;
        padding: 15px;
        transition: all 0.3s ease;
        background: #fff;

        &:hover {
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          border-color: #5cadff;
        }

        .path-header {
          margin-bottom: 10px;

          .path-title {
            margin: 0;
            font-size: 16px;
            font-weight: 600;
            color: #495060;
          }
        }

        .path-content {
          .path-description {
            color: #657180;
            font-size: 14px;
            line-height: 1.5;
            margin-bottom: 15px;
          }

          .path-meta {
            .path-duration {
              display: flex;
              align-items: center;
              font-size: 13px;
              color: #808695;

              i {
                margin-right: 5px;
              }
            }
          }
        }

        .path-footer {
          margin-top: 10px;
        }
      }
    }

    .problems-container {
      display: grid;
      gap: 10px;

      .problem-item {
        display: flex;
        align-items: center;
        padding: 8px 0;

        .ivu-btn {
          margin-right: 15px;
          flex-shrink: 0;
        }

        .problem-info {
          flex: 1;

          .problem-title {
            margin: 0 0 3px 0;
            font-size: 14px;
            font-weight: 500;
            color: #495060;
          }

          .problem-reason {
            margin: 0;
            font-size: 12px;
            color: #808695;
          }
        }
      }

      .no-problems {
        text-align: center;
        color: #808695;
        font-style: italic;
        margin: 20px 0;
      }
    }
  }

  .social-card {
    text-align: center;

    #icons {
      a {
        display: inline-block;
        margin: 0 15px;
        color: #808695;
        transition: all 0.3s ease;

        &:hover {
          color: #2d8cf0;
          transform: scale(1.1);
        }

        i {
          vertical-align: middle;
        }
      }
    }
  }

  @media (max-width: 768px) {
    width: 95%;
    padding: 10px 0;

    .user-header {
      flex-direction: column;
      text-align: center;

      .avatar-wrapper {
        margin: 0 auto 15px;
      }
    }

    .content-grid {
      grid-template-columns: 1fr;
    }

    .stats-card .flex-container {
      flex-direction: column;

      .stat-item:not(:last-child) {
        border-right: none;
        border-bottom: 1px solid #e8eaec;
      }
    }
  }
}

.ability-card {
  background: linear-gradient(135deg, #f5f7fa 0%, #e4edf9 100%);
  border: 1px solid #d0dfff;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(45, 140, 240, 0.1);

  .flex-container {
    display: flex;
    align-items: center;

    .stat-item {
      flex: 1;
      display: flex;
      align-items: center;
      padding: 15px;
      border-right: 1px solid rgba(197, 200, 206, 0.3);

      &:last-child {
        border-right: none;
      }

      .ability-icon {
        color: #2d8cf0;
        margin-right: 15px;
        flex-shrink: 0;
      }

      .ability-info {
        .stat-label {
          margin: 0 0 5px 0;
          font-size: 13px;
          color: #808695;
          font-weight: normal;
        }

        .stat-value {
          margin: 0;
          font-size: 18px;
          font-weight: 600;
          color: #495060;

          &.ability-score {
            font-size: 22px;
            color: #2d8cf0;
          }

          .level-tag {
            font-size: 14px;
            padding: 3px 10px;
          }
        }

        .recommendation-text {
          font-size: 14px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
      }
    }

    .action-item {
      flex-direction: column;
      justify-content: center;
      align-items: center;
      border-right: none;

      .detail-report-btn {
        width: 120px;
        height: 36px;
        font-size: 14px;
        font-weight: 500;
        border-radius: 20px;
        background: linear-gradient(135deg, #2d8cf0 0%, #5cadff 100%);
        border: none;
        box-shadow: 0 4px 8px rgba(45, 140, 240, 0.3);
        transition: all 0.3s ease;

        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 6px 12px rgba(45, 140, 240, 0.4);
        }

        &:active {
          transform: translateY(0);
        }

        i {
          margin-right: 5px;
        }
      }

      .action-description {
        margin: 8px 0 0 0;
        font-size: 12px;
        color: #808695;
        text-align: center;
      }
    }
  }
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .ability-card .flex-container {
    flex-wrap: wrap;

    .stat-item {
      flex: 0 0 50%;
      border-right: none;
      border-bottom: 1px solid rgba(197, 200, 206, 0.3);

      &:nth-child(2) {
        border-bottom: none;
      }

      &:last-child {
        flex: 0 0 100%;
        border-bottom: none;
        padding-top: 20px;
      }
    }

    .action-item {
      align-items: center;
    }
  }
}

@media (max-width: 768px) {
  .ability-card .flex-container .stat-item {
    flex: 0 0 100%;
    border-right: none;
    border-bottom: 1px solid rgba(197, 200, 206, 0.3);

    &:last-child {
      border-bottom: none;
    }
  }

  .detail-report-btn {
    width: 100% !important;
    max-width: 200px;
  }
}
</style>