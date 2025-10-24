<template>
  <Row type="flex" :gutter="18">
    <Col :span=19>
    <Panel shadow>
      <div slot="title">{{ $t('m.Problem_List') }}</div>
      <div slot="extra">
        <div class="filter">
          <ul>
            <li>
              <Button @click="onReset">{{ $t('m.Reset') }}</Button>
            </li>
            <li>
              <Button @click="toggleRecommended">
                <Icon :type="showRecommended ? 'md-star' : 'md-star-outline'"></Icon>
                {{ showRecommended ? $t('m.Show_All_Problems') : $t('m.Recommended_Problems') }}
              </Button>
            </li>
            <li>
              <Button @click="handleTagsVisible(!tagsVisible)">
                <Icon :type="tagsVisible ? 'md-eye-off' : 'md-eye'"></Icon>
                {{ tagsVisible ? $t('m.Hide_Tags') : $t('m.Show_Tags') }}
              </Button>
            </li>
          </ul>
        </div>
      </div>
      <Table style="width: 100%; font-size: 16px;" :columns="problemTableColumns" :data="problemList"
        :loading="loadings.table" disabled-hover ref="problemTable"></Table>
    </Panel>

    <Pagination :total="total" :page-size.sync="query.limit" @on-change="pushRouter" @on-page-size-change="pushRouter"
      :current.sync="query.page" :show-sizer="true"></Pagination>
    </Col>

    <Col :span="5">
    <Panel :padding="10">
      <div slot="title" class="taglist-title">{{ $t('m.Tags') }}</div>
      <div class="tags-carousel-container" ref="tagsCarousel" :style="{ height: carouselHeight + 'px' }">
        <div class="tags-carousel" :style="{ transform: `translateY(-${currentScrollPosition}px)` }">
          <Button v-for="tag in tagList" :key="tag.name" @click="filterByTag(tag.name)" type="ghost"
            :disabled="query.tag === tag.name" shape="circle" class="tag-btn">{{ tag.name }}
          </Button>
        </div>
      </div>
      <div class="carousel-controls">
        <Button size="small" @click="toggleCarousel">
          <Icon :type="carouselActive ? 'md-pause' : 'md-play'"></Icon>
          {{ carouselActive ? $t('m.Pause') : $t('m.Play') }}
        </Button>
      </div>

      <Button long id="pick-one" @click="pickone">
        <Icon type="shuffle"></Icon>
        {{ $t('m.Pick_One') }}
      </Button>
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
      limit: 20,
      total: 0,
      loadings: {
        table: true,
        tag: true,
        recommendation: false
      },
      routeName: '',
      query: {
        keyword: '',
        difficulty: '',
        tag: '',
        page: 1,
        limit: 10
      },
      showRecommended: false,
      recommendedProblemList: [], // 存储推荐题目列表
      tagsVisible: true,// 跟踪tags显示状态
      carouselActive: true, // 轮播是否激活
      currentScrollPosition: 0, // 当前滚动位置
      carouselInterval: null, // 轮播定时器
      carouselSpeed: 30, // 轮播速度（像素/秒）
      carouselHeight: 200, // 轮播容器高度
      resizeTimer: null, // 防抖定时器
    }
  },
  mounted() {
    this.init()
    this.startCarousel()
    this.updateCarouselHeight()
    this.setupResizeObserver()
  },
  beforeDestroy() {
    this.stopCarousel()
    if (this.resizeTimer) {
      clearTimeout(this.resizeTimer)
    }
    window.removeEventListener('resize', this.handleResize)
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
      //默认打开tags列
      this.$nextTick(() => {
        this.handleTagsVisible(true)
      })
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

      if (this.showRecommended) {
        // 获取推荐题目
        this.loadings.recommendation = true
        api.getRecommendedProblems(this.query.limit).then(res => {
          this.loadings.table = false
          this.loadings.recommendation = false

          // 确保推荐题目的数据结构与普通题目一致
          let recommendedData = res.data.data || []
          this.recommendedProblemList = recommendedData.map(problem => {
            // 确保推荐题目具有表格所需的所有字段
            return {
              _id: problem.problem_display_id || problem._id || '',
              title: problem.title || '',
              difficulty: problem.difficulty || 'Mid',
              submission_number: problem.submission_count || problem.submission_number || 0,
              accepted_number: problem.accepted_count || problem.accepted_number || 0,
              // 添加tags字段，如果不存在则设为空数组
              tags: problem.tags || [],
              ...problem // 保留其他字段
            }
          })

          this.problemList = this.recommendedProblemList
          this.total = this.recommendedProblemList.length

          // 如果tags开关是打开的，需要重新添加tags列
          if (this.tagsVisible) {
            this.$nextTick(() => {
              this.addTagsColumn()
            })
          }
        }).catch(err => {
          this.loadings.table = false
          this.loadings.recommendation = false
          console.error('Failed to load recommended problems:', err)
          this.$error('获取推荐题目失败')
        })
      } else {
        // 获取默认题目列表
        api.getProblemList(offset, this.limit, this.query).then(res => {
          this.loadings.table = false
          this.total = res.data.data.total
          this.problemList = res.data.data.results
          if (this.isAuthenticated) {
            this.addStatusColumn(this.problemTableColumns, res.data.data.results)
          }

          // 如果tags开关是打开的，需要重新添加tags列
          if (this.tagsVisible) {
            this.$nextTick(() => {
              this.addTagsColumn()
            })
          }
        }, res => {
          this.loadings.table = false
        })
      }
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
      this.tagsVisible = value
      if (value) {
        this.$nextTick(() => {
          this.addTagsColumn()
        })
      } else {
        // 移除tags列
        const tagsColumnIndex = this.problemTableColumns.findIndex(col => col.title === this.$i18n.t('m.Tags'))
        if (tagsColumnIndex !== -1) {
          this.problemTableColumns.splice(tagsColumnIndex, 1)
        }
      }
    },
    addTagsColumn() {
      // 先检查是否已存在tags列
      const tagsColumnIndex = this.problemTableColumns.findIndex(col => col.title === this.$i18n.t('m.Tags'))
      if (tagsColumnIndex !== -1) {
        // 如果已存在，先移除
        this.problemTableColumns.splice(tagsColumnIndex, 1)
      }

      // 添加tags列
      this.problemTableColumns.push({
        title: this.$i18n.t('m.Tags'),
        align: 'center',
        render: (h, params) => {
          let tags = []
          if (params.row.tags && Array.isArray(params.row.tags)) {
            params.row.tags.forEach(tag => {
              // 处理不同格式的tags数据
              let tagName = typeof tag === 'string' ? tag : (tag.name || tag.title || JSON.stringify(tag))
              tags.push(h('Tag', {
                props: {
                  color: 'blue'
                },
                style: {
                  margin: '2px'
                }
              }, tagName))
            })
          }
          return h('div', {
            style: {
              margin: '8px 0',
              display: 'flex',
              flexWrap: 'wrap'
            }
          }, tags)
        }
      })
    },
    onReset() {
      this.query.keyword = ''
      this.query.difficulty = ''
      this.query.tag = ''
      this.query.page = 1
      this.showRecommended = false
      this.tagsVisible = false // 重置tags显示状态
      // 移除tags列
      const tagsColumnIndex = this.problemTableColumns.findIndex(col => col.title === this.$i18n.t('m.Tags'))
      if (tagsColumnIndex !== -1) {
        this.problemTableColumns.splice(tagsColumnIndex, 1)
      }
      this.pushRouter()
    },
    pickone() {
      api.pickone().then(res => {
        this.$success('Good Luck')
        this.$router.push({ name: 'problem-details', params: { problemID: res.data.data } })
      })
    },
    toggleRecommended() {
      this.showRecommended = !this.showRecommended
      this.query.page = 1 // 重置到第一页
      this.getProblemList()
    },
    getACRate(acceptedCount, submissionCount) {
      if (submissionCount === 0) return '0%'
      return Math.round(acceptedCount / submissionCount * 100) + '%'
    },
    updateCarouselHeight() {
      this.$nextTick(() => {
        if (this.$refs.problemTable && this.$refs.tagsCarousel) {
          // 获取问题列表表格的高度
          const tableElement = this.$refs.problemTable.$el
          if (tableElement) {
            // 计算表格的实际高度
            const tableHeight = tableElement.clientHeight

            // 设置轮播容器高度与表格高度一致
            // 减去一些边距和控件高度，确保视觉平衡
            this.carouselHeight = Math.max(tableHeight - 40, 150) // 最小高度150px
          }
        }
      })
    },

    setupResizeObserver() {
      // 监听窗口大小变化，动态调整轮播高度
      window.addEventListener('resize', this.handleResize)
    },

    handleResize() {
      // 防抖处理，避免频繁更新
      clearTimeout(this.resizeTimer)
      this.resizeTimer = setTimeout(() => {
        this.updateCarouselHeight()
      }, 200)
    },

    startCarousel() {
      this.stopCarousel() // 先停止现有的轮播
      if (this.carouselActive && this.tagList.length > 0) {
        this.carouselInterval = setInterval(() => {
          if (this.$refs.tagsCarousel) {
            const containerHeight = this.carouselHeight
            const contentElement = this.$refs.tagsCarousel.querySelector('.tags-carousel')

            if (contentElement) {
              const contentHeight = contentElement.scrollHeight

              // 只有当内容高度大于容器高度时才需要滚动
              if (contentHeight > containerHeight) {
                this.currentScrollPosition += 1 // 每次滚动1像素

                // 如果滚动到底部，回到顶部
                if (this.currentScrollPosition >= contentHeight - containerHeight) {
                  this.currentScrollPosition = 0
                }
              } else {
                // 如果内容高度小于容器高度，不需要滚动
                this.currentScrollPosition = 0
              }
            }
          }
        }, 1000 / this.carouselSpeed) // 根据速度计算间隔时间
      }
    },
    stopCarousel() {
      if (this.carouselInterval) {
        clearInterval(this.carouselInterval)
        this.carouselInterval = null
      }
    },
    toggleCarousel() {
      this.carouselActive = !this.carouselActive
      if (this.carouselActive) {
        this.startCarousel()
      } else {
        this.stopCarousel()
      }
    },
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
    },
    tagList(newVal) {
      // 当tagList更新时，重置轮播位置并重新开始
      this.currentScrollPosition = 0
      if (this.carouselActive) {
        this.$nextTick(() => {
          this.startCarousel()
        })
      }
    },

    // 监听问题列表数据变化，更新轮播高度
    problemList() {
      this.$nextTick(() => {
        this.updateCarouselHeight()
      })
    },

    // 监听分页变化，更新轮播高度
    'query.limit'() {
      this.$nextTick(() => {
        this.updateCarouselHeight()
      })
    },

    // 监听推荐题目开关，更新轮播高度
    showRecommended() {
      this.$nextTick(() => {
        this.updateCarouselHeight()
      })
    },
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

.filter {
  li {
    display: inline-block;
    margin-right: 10px;
  }
}

.tags-carousel-container {
  min-height: 150px;
  /* 最小高度 */
  overflow: hidden;
  position: relative;
  margin-bottom: 10px;
  border: 1px solid #e8eaec;
  border-radius: 4px;
  background-color: #f8f8f9;
  transition: height 0.3s ease-in-out;
  /* 高度变化过渡效果 */
}

.tags-carousel {
  transition: transform 0.3s ease-in-out;
  padding: 10px;
}

.carousel-controls {
  text-align: center;
  margin-bottom: 10px;
}

.carousel-controls button {
  margin: 0 5px;
}
</style>