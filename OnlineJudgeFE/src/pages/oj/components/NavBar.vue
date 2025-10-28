<template>
  <div id="header">
    <Menu theme="light" mode="horizontal" @on-select="handleRoute" :active-name="activeMenu" class="oj-menu">
      <div class="logo"><span>{{ website.website_name }}</span></div>
      <Menu-item name="/">
        <Icon type="home"></Icon>
        {{ $t('m.Home') }}
      </Menu-item>
      <Menu-item name="/problem">
        <Icon type="ios-keypad"></Icon>
        {{ $t('m.NavProblems') }}
      </Menu-item>
      <Menu-item name="/contest">
        <Icon type="trophy"></Icon>
        {{ $t('m.Contests') }}
      </Menu-item>
      <Menu-item name="/status">
        <Icon type="ios-pulse-strong"></Icon>
        {{ $t('m.NavStatus') }}
      </Menu-item>
      <Menu-item name="/learning-path">
        <Icon type="ios-book"></Icon>
        {{ $t('m.Learning_Path') }}
      </Menu-item>
      <Menu-item name="/knowledge-points">
        <Icon type="ios-bookmarks" />
        {{ $t('m.Knowledge_Points') }}
      </Menu-item>
      <Menu-item name="/knowledge-graph">
        <Icon type="social-nodejs" />
        {{ $t('m.Knowledge_Graph') }}
      </Menu-item>
      <Submenu name="rank">
        <template slot="title">
          <Icon type="podium"></Icon>
          {{ $t('m.Rank') }}
        </template>
        <Menu-item name="/acm-rank">
          {{ $t('m.ACM_Rank') }}
        </Menu-item>
        <Menu-item name="/oi-rank">
          {{ $t('m.OI_Rank') }}
        </Menu-item>
      </Submenu>
      <Submenu name="about">
        <template slot="title">
          <Icon type="information-circled"></Icon>
          {{ $t('m.About') }}
        </template>
        <Menu-item name="/about">
          {{ $t('m.Judger') }}
        </Menu-item>
        <Menu-item name="/FAQ">
          {{ $t('m.FAQ') }}
        </Menu-item>
      </Submenu>
      <template v-if="!isAuthenticated">
        <div class="btn-menu">
          <Button type="primary" ghost ref="loginBtn" shape="circle" @click="handleBtnClick('login')">{{ $t('m.Login')
            }}
          </Button>
          <Button v-if="website.allow_register" type="primary" ghost shape="circle" @click="handleBtnClick('register')"
            style="margin-left: 5px;">{{ $t('m.Register') }}
          </Button>
        </div>
      </template>
      <template v-else>
        <Dropdown class="drop-menu" @on-click="handleRoute" placement="bottom" trigger="click">
          <Button type="text" class="drop-menu-title">
            <!-- 添加头像显示 -->
            <img :src="profile.avatar || '/public/avatar/default.png'" class="navbar-avatar" />
            <span class="username">{{ user.username }}</span>
            <Icon type="arrow-down-b"></Icon>
          </Button>
          <Dropdown-menu slot="list">
            <Dropdown-item name="/user-home">{{ $t('m.MyHome') }}</Dropdown-item>
            <Dropdown-item name="/status?myself=1">{{ $t('m.MySubmissions') }}</Dropdown-item>
            <Dropdown-item name="/learning-path">{{ $t('m.Learning_Path') }}</Dropdown-item>
            <Dropdown-item name="/knowledge-points">{{ $t('m.Knowledge_Points') }}</Dropdown-item>
            <Dropdown-item name="/setting/profile">{{ $t('m.Settings') }}</Dropdown-item>
            <Dropdown-item v-if="isAdminRole" name="/admin">{{ $t('m.Management') }}</Dropdown-item>
            <Dropdown-item divided name="/logout">{{ $t('m.Logout') }}</Dropdown-item>
          </Dropdown-menu>
        </Dropdown>
      </template>
    </Menu>
    <Modal v-model="modalVisible" :width="400">
      <div slot="header" class="modal-title">{{ $t('m.Welcome_to') }} {{ website.website_name_shortcut }}</div>
      <component :is="modalStatus.mode" v-if="modalVisible"></component>
      <div slot="footer" style="display: none"></div>
    </Modal>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'
import login from '@oj/views/user/Login'
import register from '@oj/views/user/Register'

export default {
  components: {
    login,
    register
  },
  mounted() {
    this.getProfile()
  },
  methods: {
    ...mapActions(['getProfile', 'changeModalStatus']),
    handleRoute(route) {
      if (route && route.indexOf('admin') < 0) {
        this.$router.push(route)
      } else {
        window.open('/admin/')
      }
    },
    handleBtnClick(mode) {
      this.changeModalStatus({
        visible: true,
        mode: mode
      })
    }
  },
  computed: {
    ...mapGetters(['website', 'modalStatus', 'user', 'isAuthenticated', 'isAdminRole', 'profile']),
    // 跟随路由变化
    activeMenu() {
      return '/' + this.$route.path.split('/')[1]
    },
    modalVisible: {
      get() {
        return this.modalStatus.visible
      },
      set(value) {
        this.changeModalStatus({ visible: value })
      }
    }
  }
}
</script>
<style lang="less" scoped>
#header {
  min-width: 300px;
  position: fixed;
  top: 0;
  left: 0;
  height: 60px;
  width: 100%;
  z-index: 1000;
  background-color: #fff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.15);
  border-bottom: 1px solid #e8f4ff;

  .oj-menu {
    background: #fff;
    height: 60px;
    display: flex;
    align-items: center;
    padding: 0 2%;

    /deep/ .ivu-menu-item,
    /deep/ .ivu-menu-submenu-title {
      margin: 0 2px;
      height: 60px;
      line-height: 60px;
      padding: 0 15px !important;
      white-space: nowrap;
      font-size: 14px;
      color: #515a6e;
      transition: all 0.3s ease;
      border-bottom: 2px solid transparent;

      display: flex;
      align-items: center;

      .ivu-icon {
        margin-right: 6px;
        font-size: 16px;
      }

      &:hover {
        color: #1890ff;
        background-color: rgba(24, 144, 255, 0.05);
      }

      &.ivu-menu-item-active {
        color: #1890ff;
        border-bottom: 2px solid #1890ff;
        background-color: rgba(24, 144, 255, 0.03);
      }
    }

    /deep/ .ivu-menu-submenu {
      &:hover {
        .ivu-menu-submenu-title {
          color: #1890ff;
          background-color: rgba(24, 144, 255, 0.05);
        }
      }
    }
  }

  .logo {
    margin-right: 25px;
    font-size: 20px;
    font-weight: 600;
    line-height: 60px;
    white-space: nowrap;
    color: #1890ff;
    height: 60px;
    display: flex;
    align-items: center;
    padding: 0 5px;

    span {
      display: inline-block;
      transition: transform 0.3s ease;
    }

    &:hover span {
      transform: scale(1.03);
    }
  }

  .drop-menu {
    margin-left: auto;
    margin-right: 20px;
    position: relative;
    right: 0;

    &-title {
      font-size: 14px;
      display: flex;
      align-items: center;
      height: 60px;
      padding: 0 15px;
      border-radius: 4px;
      transition: all 0.3s ease;

      &:hover {
        background-color: rgba(24, 144, 255, 0.05);
      }

      .navbar-avatar {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        margin-right: 10px;
        object-fit: cover;
        border: 2px solid #e8f4ff;
        transition: all 0.3s ease;
        vertical-align: middle;
      }

      .username {
        margin-right: 8px;
        font-weight: 500;
        max-width: 120px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        color: #515a6e;
      }

      &:hover {
        .navbar-avatar {
          border-color: #1890ff;
          transform: scale(1.05);
        }

        .username {
          color: #1890ff;
        }
      }
    }
  }

  .btn-menu {
    margin-left: auto;
    margin-right: 20px;
    height: 60px;
    display: flex;
    align-items: center;

    .ivu-btn {
      margin-left: 12px;
      white-space: nowrap;
      border-radius: 20px;
      transition: all 0.3s ease;
      border-color: #1890ff;
      color: #1890ff;

      &:hover {
        background-color: #e8f4ff;
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(24, 144, 255, 0.2);
      }
    }
  }
}

.modal {
  &-title {
    font-size: 18px;
    font-weight: 600;
    color: #1890ff;
  }
}

// 响应式优化 - 在小屏幕上进一步优化
@media (max-width: 1200px) {
  .oj-menu {
    padding: 0 1%;

    /deep/ .ivu-menu-item,
    /deep/ .ivu-menu-submenu-title {
      padding: 0 12px !important;
      font-size: 13px;
      margin: 0 1px;

      .ivu-icon {
        margin-right: 4px;
        font-size: 15px;
      }
    }

    .logo {
      font-size: 18px;
      margin-right: 20px;
    }

    .btn-menu {
      margin-right: 15px;

      .ivu-btn {
        margin-left: 8px;
        padding: 4px 15px;
      }
    }

    .drop-menu {
      margin-right: 15px;

      &-title {
        padding: 0 12px;

        .navbar-avatar {
          width: 32px;
          height: 32px;
        }

        .username {
          max-width: 100px;
        }
      }
    }
  }
}

@media (max-width: 992px) {
  .oj-menu {

    /deep/ .ivu-menu-item,
    /deep/ .ivu-menu-submenu-title {
      padding: 0 10px !important;
      font-size: 12px;
      margin: 0;

      .ivu-icon {
        margin-right: 3px;
        font-size: 14px;
      }
    }

    .logo {
      font-size: 16px;
      margin-right: 15px;
    }

    .drop-menu-title {
      .username {
        max-width: 80px;
      }
    }

    .btn-menu {
      margin-right: 10px;

      .ivu-btn {
        margin-left: 6px;
        padding: 2px 12px;
        font-size: 12px;
      }
    }
  }
}

@media (max-width: 768px) {
  .oj-menu {
    .logo {
      font-size: 15px;
      margin-right: 10px;
    }

    /deep/ .ivu-menu-item:not(.ivu-menu-item-active),
    /deep/ .ivu-menu-submenu:not(.ivu-menu-submenu-active) {
      span:not(.ivu-icon) {
        display: none;
      }

      .ivu-icon {
        margin-right: 0;
        font-size: 16px;
      }
    }

    .btn-menu {
      margin-right: 8px;

      .ivu-btn span {
        display: none;
      }

      .ivu-btn .ivu-icon {
        margin-right: 0;
      }

      .ivu-btn {
        width: 32px;
        height: 32px;
        padding: 0;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
      }
    }

    .drop-menu {
      margin-right: 8px;

      &-title {
        padding: 0 10px;

        .username {
          display: none;
        }

        .navbar-avatar {
          margin-right: 0;
        }
      }
    }
  }
}
</style>