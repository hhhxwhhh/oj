<template>
  <div class="container">
    <Card :padding="0" class="settings-card">
      <div class="settings-layout">
        <div class="sidebar">
          <div class="user-profile">
            <div class="avatar-wrapper">
              <img class="avatar" :src="profile.avatar" alt="User Avatar" />
              <div class="avatar-overlay" @click="goRoute({ name: 'profile-setting' })">
                <Icon type="md-camera" size="20" />
              </div>
            </div>
            <div class="user-details">
              <h3 class="username">{{ profile.user.username }}</h3>
              <p class="user-role">{{ getUserRole }}</p>
            </div>
          </div>

          <div class="menu-wrapper">
            <Menu accordion @on-select="goRoute" :activeName="activeName" width="100%" class="settings-menu">
              <Menu-item name="/setting/profile">
                <Icon type="md-person" class="menu-icon" />
                <span class="menu-text">{{ $t('m.Profile') }}</span>
              </Menu-item>
              <Menu-item name="/setting/account">
                <Icon type="md-settings" class="menu-icon" />
                <span class="menu-text">{{ $t('m.Account') }}</span>
              </Menu-item>
              <Menu-item name="/setting/security">
                <Icon type="md-lock" class="menu-icon" />
                <span class="menu-text">{{ $t('m.Security') }}</span>
              </Menu-item>
            </Menu>
          </div>

          <div class="sidebar-footer">
            <p class="version">v{{ version }}</p>
          </div>
        </div>

        <div class="content-area">
          <transition name="fade-transform" mode="out-in">
            <router-view></router-view>
          </transition>
        </div>
      </div>
    </Card>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  name: 'settings',
  data() {
    return {
      version: process.env.VERSION || '1.0'
    }
  },
  methods: {
    goRoute(routePath) {
      this.$router.push(routePath)
    }
  },
  computed: {
    ...mapGetters(['profile']),
    activeName() {
      return this.$route.path
    },
    getUserRole() {
      const user = this.profile.user || {}
      switch (user.admin_type) {
        case 'Super Admin':
          return this.$t('m.Super_Administrator')
        case 'Admin':
          return this.$t('m.Administrator')
        default:
          return this.$t('m.Regular_User')
      }
    }
  }
}
</script>

<style lang="less" scoped>
.container {
  width: 90%;
  min-width: 800px;
  max-width: 1200px;
  margin: 30px auto;
  padding: 0 15px;
}

.settings-card {
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  overflow: hidden;

  .settings-layout {
    display: flex;
    min-height: 650px;

    .sidebar {
      flex: 0 0 260px;
      width: 260px;
      background: linear-gradient(180deg, #f0f8ff 0%, #e6f7ff 100%);
      border-right: 1px solid #dcdee2;
      display: flex;
      flex-direction: column;

      .user-profile {
        padding: 30px 20px 20px;
        text-align: center;

        .avatar-wrapper {
          position: relative;
          width: 90px;
          height: 90px;
          margin: 0 auto 15px;
          border-radius: 50%;
          overflow: hidden;
          border: 3px solid #fff;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
          cursor: pointer;
          transition: all 0.3s ease;

          &:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.16);

            .avatar-overlay {
              opacity: 1;
            }
          }

          .avatar {
            width: 100%;
            height: 100%;
            object-fit: cover;
          }

          .avatar-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.6);
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: opacity 0.3s ease;

            i {
              color: #fff;
            }
          }
        }

        .user-details {
          .username {
            margin: 0 0 5px;
            font-size: 18px;
            font-weight: 600;
            color: #2c3e50;
          }

          .user-role {
            margin: 0;
            font-size: 13px;
            color: #7f8c8d;
          }
        }
      }

      .menu-wrapper {
        flex: 1;
        padding: 10px 0;

        .settings-menu {
          background: transparent;
          border-right: none;

          /deep/ .ivu-menu-item {
            padding: 14px 20px;
            margin: 2px 10px;
            border-radius: 6px;
            transition: all 0.3s;
            font-size: 15px;
            display: flex;
            align-items: center;

            &:hover {
              background-color: rgba(45, 140, 240, 0.1);
              color: #2d8cf0;
            }

            &.ivu-menu-item-active {
              background-color: #2d8cf0;
              color: #fff;

              &:hover {
                background-color: #2d8cf0;
                color: #fff;
              }

              .menu-icon {
                color: #fff;
              }
            }

            .menu-icon {
              margin-right: 12px;
              width: 20px;
              text-align: center;
              font-size: 18px;
            }

            .menu-text {
              flex: 1;
            }
          }
        }
      }

      .sidebar-footer {
        padding: 20px 0 15px;
        text-align: center;

        .version {
          margin: 0;
          font-size: 12px;
          color: #999;
        }
      }
    }

    .content-area {
      flex: 1;
      padding: 30px;
      background: #fff;
    }
  }
}

// 动画效果
.fade-transform-enter-active,
.fade-transform-leave-active {
  transition: all 0.3s ease;
}

.fade-transform-enter {
  opacity: 0;
  transform: translateX(30px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

// 响应式设计
@media (max-width: 992px) {
  .container {
    min-width: auto;
    width: 95%;
  }

  .settings-card .settings-layout .sidebar {
    flex: 0 0 220px;
    width: 220px;
  }
}

@media (max-width: 768px) {
  .settings-card .settings-layout {
    flex-direction: column;

    .sidebar {
      width: 100%;
      flex: 0 0 auto;

      .user-profile {
        display: flex;
        align-items: center;
        padding: 20px;
        text-align: left;

        .avatar-wrapper {
          width: 70px;
          height: 70px;
          margin: 0 15px 0 0;
        }

        .user-details {
          text-align: left;
        }
      }

      .menu-wrapper {
        .settings-menu /deep/ .ivu-menu-item {
          padding: 12px 15px;
          font-size: 14px;
        }
      }
    }
  }
}

@media (max-width: 576px) {
  .container {
    padding: 0 10px;
  }

  .settings-card .settings-layout .content-area {
    padding: 20px 15px;
  }
}
</style>

<style lang="less">
.setting-main {
  position: relative;
  margin: 0;
  padding: 0;

  .setting-content {
    margin-left: 0;
  }

  .mini-container {
    width: 100%;
    max-width: 500px;
  }

  .section-title {
    font-size: 22px;
    font-weight: 600;
    color: #2c3e50;
    margin: 0 0 25px;
    padding-bottom: 15px;
    border-bottom: 1px solid #e8eaec;
    display: flex;
    align-items: center;

    i {
      margin-right: 10px;
      color: #2d8cf0;
    }
  }

  .section-subtitle {
    font-size: 18px;
    font-weight: 500;
    color: #515a6e;
    margin: 30px 0 20px;
  }
}

// 移除iview菜单的默认样式
.ivu-menu-vertical.ivu-menu-light:after {
  width: 0;
}
</style>