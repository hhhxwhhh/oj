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
          <Button type="ghost" ref="loginBtn" shape="circle" @click="handleBtnClick('login')">{{ $t('m.Login') }}
          </Button>
          <Button v-if="website.allow_register" type="ghost" shape="circle" @click="handleBtnClick('register')"
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
  height: auto;
  width: 100%;
  z-index: 1000;
  background-color: #fff;
  box-shadow: 0 1px 5px 0 rgba(0, 0, 0, 0.1);

  .oj-menu {
    background: #fdfdfd;
    height: 60px;
    display: flex;
    align-items: center;
    padding: 0 1%;

    // 控制菜单项间距和样式
    /deep/ .ivu-menu-item,
    /deep/ .ivu-menu-submenu-title {
      margin: 0 5px;
      height: 60px;
      line-height: 60px;
      padding: 0 12px !important; // 固定内边距
      white-space: nowrap; // 防止文字换行
      font-size: 14px;

      // 确保图标和文字在同一行
      display: flex;
      align-items: center;

      .ivu-icon {
        margin-right: 5px;
      }
    }
  }

  .logo {
    margin-right: 15px;
    font-size: 18px;
    font-weight: 600;
    line-height: 60px;
    white-space: nowrap;
  }

  .drop-menu {
    margin-left: auto;
    margin-right: 10px;
    position: relative;
    right: 0;

    &-title {
      font-size: 14px;
      display: flex;
      align-items: center;
      height: 60px;
      padding: 0 10px;

      .navbar-avatar {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        margin-right: 10px;
        object-fit: cover;
        border: 2px solid #e8eaec;
        transition: all 0.3s ease;
        vertical-align: middle;
      }

      .username {
        margin-right: 5px;
        font-weight: 500;
        max-width: 120px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      &:hover {
        .navbar-avatar {
          border-color: #5cadff;
          transform: scale(1.05);
        }
      }
    }
  }

  .btn-menu {
    margin-left: auto;
    margin-right: 10px;
    height: 60px;
    display: flex;
    align-items: center;

    .ivu-btn {
      margin-left: 10px;
      white-space: nowrap;
    }
  }
}

.modal {
  &-title {
    font-size: 18px;
    font-weight: 600;
  }
}

// 响应式优化 - 在小屏幕上进一步优化
@media (max-width: 1200px) {
  .oj-menu {

    /deep/ .ivu-menu-item,
    /deep/ .ivu-menu-submenu-title {
      padding: 0 10px !important;
      font-size: 13px;

      .ivu-icon {
        margin-right: 3px;
      }
    }

    .logo {
      font-size: 16px;
      margin-right: 10px;
    }
  }
}

@media (max-width: 992px) {
  .oj-menu {

    /deep/ .ivu-menu-item,
    /deep/ .ivu-menu-submenu-title {
      padding: 0 8px !important;
      font-size: 12px;
    }

    .logo {
      font-size: 14px;
      margin-right: 5px;
    }

    .drop-menu-title {
      .username {
        max-width: 80px;
      }
    }
  }
}
</style>