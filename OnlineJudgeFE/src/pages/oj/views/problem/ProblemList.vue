<template>
  <Row type="flex" :gutter="18">
    <Col :span=19>
    <Panel shadow>
      <div slot="title">{{ $t('m.Problem_List') }}</div>
      <div slot="extra">
        <ul class="filter">
          <li>
            <Dropdown @on-click="filterByDifficulty">
              <span>{{ query.difficulty === '' ? this.$i18n.t('m.Difficulty') : this.$i18n.t('m.' + query.difficulty) }}
                <Icon type="arrow-down-b"></Icon>
              </span>
              <Dropdown-menu slot="list">
                <Dropdown-item name="">{{ $t('m.All') }}</Dropdown-item>
                <Dropdown-item name="Low">{{ $t('m.Low') }}</Dropdown-item>
                <Dropdown-item name="Mid">{{ $t('m.Mid') }}</Dropdown-item>
                <Dropdown-item name="High">{{ $t('m.High') }}</Dropdown-item>
              </Dropdown-menu>
            </Dropdown>
          </li>
          <li>
            <i-switch size="large" @on-change="handleTagsVisible">
              <span slot="open">{{ $t('m.Tags') }}</span>
              <span slot="close">{{ $t('m.Tags') }}</span>
            </i-switch>
          </li>
          <li>
            <Input v-model="query.keyword" @on-enter="filterByKeyword" @on-click="filterByKeyword" placeholder="keyword"
              icon="ios-search-strong" />
          </li>
          <li>
            <Button type="info" @click="onReset">
              <Icon type="refresh"></Icon>
              {{ $t('m.Reset') }}
            </Button>
          </li>
        </ul>
      </div>
      <Table style="width: 100%; font-size: 16px;" :columns="problemTableColumns" :data="problemList"
        :loading="loadings.table" disabled-hover></Table>
    </Panel>
    <Pagination :total="total" :page-size.sync="query.limit" @on-change="pushRouter" @on-page-size-change="pushRouter"
      :current.sync="query.page" :show-sizer="true"></Pagination>

    </Col>

    <Col :span="5">
    <Panel :padding="10">
      <div slot="title" class="taglist-title">{{ $t('m.Tags') }}</div>
      <Button v-for="tag in tagList" :key="tag.name" @click="filterByTag(tag.name)" type="ghost"
        :disabled="query.tag === tag.name" shape="circle" class="tag-btn">{{ tag.name }}
      </Button>

      <Button long id="pick-one" @click="pickone">
        <Icon type="shuffle"></Icon>
        {{ $t('m.Pick_One') }}
      </Button>
    </Panel>

    <!-- 添加推荐题目模块 -->
    <Panel :padding="10" v-if="recommendedProblems.length > 0" class="recommendation-panel">
      <div slot="title" class="recommendation-title">
        <Icon type="md-compass" /> {{ $t('m.Recommended_For_You') }}
      </div>
      <div class="recommendation-content">
        <div v-for="problem in recommendedProblems" :key="problem.problem_id" class="recommendation-item"
          @click="goToProblem(problem.problem_display_id)">
          <div class="problem-main">
            <span class="problem-id">{{ problem.problem_display_id }}</span>
            <span class="problem-title">{{ problem.title }}</span>
          </div>
          <div class="problem-meta">
            <Tag :color="getDifficultyColor(problem.difficulty)" size="small">
              {{ $t('m.' + problem.difficulty) }}
            </Tag>
          </div>
        </div>
      </div>
    </Panel>

    <Spin v-if="loadings.tag" fix size="large"></Spin>
    </Col>
  </Row>
</template>

<script>
import { mapGetters } from 'vuex'
import api from '@oj/api'
import utils from '@/utils/utils'
import { ProblemMixin } from '@oj/components/mixins'
import Pagination from '@oj/components/Pagination'

export default {
  name: 'ProblemList',
  mixins: [ProblemMixin],
  components: {
    Pagination
  },
  data() {
    return {
      tagList: [],
      problemTableColumns: [
        {
          title: '#',
          key: '_id',
          width: 80,
          render: (h, params) => {
            return h('Button', {
              props: {
                type: 'text',
                size: 'large'
              },
              on: {
                click: () => {
                  this.$router.push({ name: 'problem-details', params: { problemID: params.row._id } })
                }
              },
              style: {
                padding: '2px 0'
              }
            }, params.row._id)
          }
        },
        {
          title: this.$i18n.t('m.Title'),
          width: 400,
          render: (h, params) => {
            return h('Button', {
              props: {
                type: 'text',
                size: 'large'
              },
              on: {
                click: () => {
                  this.$router.push({ name: 'problem-details', params: { problemID: params.row._id } })
                }
              },
              style: {
                padding: '2px 0',
                overflowX: 'auto',
                textAlign: 'left',
                width: '100%'
              }
            }, params.row.title)
          }
        },
        {
          title: this.$i18n.t('m.Level'),
          render: (h, params) => {
            let t = params.row.difficulty
            let color = 'blue'
            if (t === 'Low') color = 'green'
            else if (t === 'High') color = 'yellow'
            return h('Tag', {
              props: {
                color: color
              }
            }, this.$i18n.t('m.' + params.row.difficulty))
          }
        },
        {
          title: this.$i18n.t('m.Total'),
          key: 'submission_number'
        },
        {
          title: this.$i18n.t('m.AC_Rate'),
          render: (h, params) => {
            return h('span', this.getACRate(params.row.accepted_number, params.row.submission_number))
          }
        }
      ],
      problemList: [],
      recommendedProblems: [], // 添加推荐题目数据
      limit: 20,
      total: 0,
      loadings: {
        table: true,
        tag: true
      },
      routeName: '',
      query: {
        keyword: '',
        difficulty: '',
        tag: '',
        page: 1,
        limit: 10
      }
    }
  },
  mounted() {
    this.init()
    this.loadRecommendedProblems() // 加载推荐题目
  },
  methods: {
    init(simulate = false) {
      this.routeName = this.$route.name
      let query = this.$route.query
      this.query.difficulty = query.difficulty || ''
      this.query.keyword = query.keyword || ''
      this.query.tag = query.tag || ''
      this.query.page = parseInt(query.page) || 1
      if (this.query.page < 1) {
        this.query.page = 1
      }
      this.query.limit = parseInt(query.limit) || 10
      if (!simulate) {
        this.getTagList()
      }
      this.getProblemList()
    },
    pushRouter() {
      this.$router.push({
        name: 'problem-list',
        query: utils.filterEmptyValue(this.query)
      })
    },
    getProblemList() {
      let offset = (this.query.page - 1) * this.query.limit
      this.loadings.table = true
      api.getProblemList(offset, this.limit, this.query).then(res => {
        this.loadings.table = false
        this.total = res.data.data.total
        this.problemList = res.data.data.results
        if (this.isAuthenticated) {
          this.addStatusColumn(this.problemTableColumns, res.data.data.results)
        }
      }, res => {
        this.loadings.table = false
      })
    },
    getTagList() {
      api.getProblemTagList().then(res => {
        this.tagList = res.data.data
        this.loadings.tag = false
      }, res => {
        this.loadings.tag = false
      })
    },
    filterByTag(tagName) {
      this.query.tag = tagName
      this.query.page = 1
      this.pushRouter()
    },
    filterByDifficulty(difficulty) {
      this.query.difficulty = difficulty
      this.query.page = 1
      this.pushRouter()
    },
    filterByKeyword() {
      this.query.page = 1
      this.pushRouter()
    },
    handleTagsVisible(value) {
      if (value) {
        this.problemTableColumns.push(
          {
            title: this.$i18n.t('m.Tags'),
            align: 'center',
            render: (h, params) => {
              let tags = []
              params.row.tags.forEach(tag => {
                tags.push(h('Tag', {}, tag))
              })
              return h('div', {
                style: {
                  margin: '8px 0'
                }
              }, tags)
            }
          })
      } else {
        this.problemTableColumns.splice(this.problemTableColumns.length - 1, 1)
      }
    },
    onReset() {
      this.$router.push({ name: 'problem-list' })
    },
    pickone() {
      api.pickone().then(res => {
        this.$success('Good Luck')
        this.$router.push({ name: 'problem-details', params: { problemID: res.data.data } })
      })
    },
    // 添加推荐相关方法
    loadRecommendedProblems() {
      api.getRecommendedProblems(5).then(res => {
        this.recommendedProblems = res.data.data || []
      }).catch(err => {
        console.error('Failed to load recommended problems:', err)
      })
    },
    getDifficultyColor(difficulty) {
      const colorMap = {
        'Low': 'success',
        'Mid': 'warning',
        'High': 'error'
      }
      return colorMap[difficulty] || 'default'
    },
    goToProblem(problemID) {
      this.$router.push({ name: 'problem-details', params: { problemID } })
    }
  },
  computed: {
    ...mapGetters(['isAuthenticated'])
  },
  watch: {
    '$route'(newVal, oldVal) {
      if (newVal !== oldVal) {
        this.init(true)
      }
    },
    'isAuthenticated'(newVal) {
      if (newVal === true) {
        this.init()
      }
    }
  }
}
</script>

<style scoped lang="less">
.taglist-title {
  margin-left: -10px;
  margin-bottom: -10px;
}

.tag-btn {
  margin-right: 5px;
  margin-bottom: 10px;
}

#pick-one {
  margin-top: 10px;
}

// 添加推荐样式
.recommendation-panel {
  margin-top: 20px;

  .recommendation-title {
    font-weight: 500;
  }

  .recommendation-content {
    .recommendation-item {
      padding: 8px 0;
      border-bottom: 1px solid #e8eaec;
      cursor: pointer;
      transition: background-color 0.2s;

      &:last-child {
        border-bottom: none;
      }

      &:hover {
        background-color: #f8f8f9;
      }

      .problem-main {
        display: flex;
        align-items: center;
        margin-bottom: 4px;

        .problem-id {
          font-weight: 600;
          color: #2d8cf0;
          margin-right: 8px;
          font-family: monospace;
          font-size: 12px;
        }

        .problem-title {
          flex: 1;
          font-size: 13px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
      }

      .problem-meta {
        display: flex;
        align-items: center;
      }
    }
  }
}
</style>