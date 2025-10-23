<template>
  <Card shadow :padding="10" class="announcements-card">
    <div slot="title" class="section-header">
      <Icon type="ios-notifications" class="header-icon" />
      <span class="header-title">{{ title }}</span>
    </div>
    <div slot="extra">
      <Button v-if="listVisible" type="primary" size="small" @click="init" :loading="btnLoading">
        <Icon type="ios-refresh" />
        {{ $t('m.Refresh') }}
      </Button>
      <Button v-else type="ghost" size="small" @click="goBack">
        <Icon type="ios-arrow-back" />
        {{ $t('m.Back') }}
      </Button>
    </div>

    <transition-group name="announcement-animate" mode="in-out">
      <div class="no-announcement" v-if="!announcements.length" key="no-announcement">
        <Icon type="ios-information-circle-outline" size="40" class="no-data-icon" />
        <p>{{ $t('m.No_Announcements') }}</p>
      </div>
      <template v-if="listVisible">
        <ul class="announcements-container" key="list">
          <li v-for="announcement in announcements" :key="announcement.id" class="announcement-item">
            <div class="flex-container">
              <div class="title">
                <a class="entry" @click="goAnnouncement(announcement)">
                  <Icon type="ios-document" class="entry-icon" />
                  {{ announcement.title }}
                </a>
              </div>
              <div class="date">
                <Icon type="ios-time" class="info-icon" />
                {{ announcement.create_time | localtime }}
              </div>
              <div class="creator">
                <Icon type="ios-person" class="info-icon" />
                {{ $t('m.By') }} {{ announcement.created_by.username }}
              </div>
            </div>
          </li>
        </ul>
        <Pagination v-if="!isContest" key="page" :total="total" :page-size="limit" @on-change="getAnnouncementList"
          class="pagination">
        </Pagination>
      </template>

      <template v-else>
        <div v-katex v-html="announcement.content" key="content" class="content-container markdown-body"></div>
      </template>
    </transition-group>
  </Card>
</template>

<script>
import api from '@oj/api'
import Pagination from '@oj/components/Pagination'

export default {
  name: 'Announcement',
  components: {
    Pagination
  },
  data() {
    return {
      limit: 10,
      total: 10,
      btnLoading: false,
      announcements: [],
      announcement: '',
      listVisible: true
    }
  },
  mounted() {
    this.init()
  },
  methods: {
    init() {
      if (this.isContest) {
        this.getContestAnnouncementList()
      } else {
        this.getAnnouncementList()
      }
    },
    getAnnouncementList(page = 1) {
      this.btnLoading = true
      api.getAnnouncementList((page - 1) * this.limit, this.limit).then(res => {
        this.btnLoading = false
        this.announcements = res.data.data.results
        this.total = res.data.data.total
      }, () => {
        this.btnLoading = false
      })
    },
    getContestAnnouncementList() {
      this.btnLoading = true
      api.getContestAnnouncementList(this.$route.params.contestID).then(res => {
        this.btnLoading = false
        this.announcements = res.data.data
      }, () => {
        this.btnLoading = false
      })
    },
    goAnnouncement(announcement) {
      this.announcement = announcement
      this.listVisible = false
    },
    goBack() {
      this.listVisible = true
      this.announcement = ''
    }
  },
  computed: {
    title() {
      if (this.listVisible) {
        return this.isContest ? this.$i18n.t('m.Contest_Announcements') : this.$i18n.t('m.Announcements')
      } else {
        return this.announcement.title
      }
    },
    isContest() {
      return !!this.$route.params.contestID
    }
  }
}
</script>

<style scoped lang="less">
.announcements-card {
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

  /deep/ .ivu-card-extra {
    top: 12px;
  }
}

.announcements-container {
  margin-top: -5px;
  margin-bottom: 15px;

  .announcement-item {
    padding: 15px 0;
    list-style: none;
    border-bottom: 1px solid #f0f0f0;

    &:last-child {
      border-bottom: none;
    }

    .flex-container {
      display: flex;
      align-items: center;

      .title {
        flex: 2;
        text-align: left;

        .entry {
          color: #495060;
          display: flex;
          align-items: center;
          transition: color 0.3s;

          &:hover {
            color: #2d8cf0;

            .entry-icon {
              transform: translateX(3px);
            }
          }

          .entry-icon {
            margin-right: 8px;
            color: #2d8cf0;
            transition: transform 0.3s;
          }
        }
      }

      .creator,
      .date {
        flex: 1;
        display: flex;
        align-items: center;
        color: #808695;
        font-size: 13px;

        .info-icon {
          margin-right: 5px;
          font-size: 14px;
        }
      }

      .creator {
        justify-content: flex-end;
      }

      .date {
        justify-content: center;
      }
    }
  }
}

.content-container {
  padding: 0 20px 20px 20px;
}

.no-announcement {
  text-align: center;
  padding: 40px 0;
  color: #808695;

  .no-data-icon {
    margin-bottom: 15px;
    color: #c5c8ce;
  }

  p {
    margin: 0;
    font-size: 16px;
  }
}

.pagination {
  text-align: center;
  margin-top: 10px;
}

.announcement-animate-enter-active {
  animation: fadeIn 1s;
}

// 响应式设计
@media (max-width: 768px) {
  .announcements-container {
    .announcement-item {
      .flex-container {
        flex-direction: column;
        align-items: flex-start;

        .title {
          margin-bottom: 10px;
          width: 100%;
        }

        .creator,
        .date {
          width: 100%;
          justify-content: flex-start;
          margin-bottom: 5px;
        }
      }
    }
  }
}

@media (max-width: 576px) {
  .announcements-card {
    /deep/ .ivu-card-head {
      padding: 12px 15px;
    }

    .content-container {
      padding: 0 15px 15px 15px;
    }
  }

  .announcements-container {
    .announcement-item {
      padding: 12px 0;

      .flex-container {
        .title .entry {
          font-size: 15px;
        }

        .creator,
        .date {
          font-size: 12px;
        }
      }
    }
  }
}
</style>