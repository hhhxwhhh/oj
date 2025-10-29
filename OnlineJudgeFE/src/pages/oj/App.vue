<template>
  <div class="app-container">
    <NavBar></NavBar>
    <div class="content-app">
      <transition name="fade-transform" mode="out-in">
        <router-view></router-view>
      </transition>
      <div class="footer">
        <div class="footer-content">
          <div class="footer-info" v-html="website.website_footer"></div>
          <div class="footer-meta">
            <p>Powered by <a href="https://github.com/hhhxwhhh/oj" target="_blank">OnlineJudge</a>
              <span v-if="version" class="version-tag">Version: {{ version }}</span>
            </p>
          </div>
        </div>
      </div>
    </div>
    <BackTop :height="200" :bottom="60">
      <div class="backtop">
        <Icon type="md-arrow-round-up" size="24" color="#fff"></Icon>
      </div>
    </BackTop>
  </div>
</template>

<script>
import { mapActions, mapState } from 'vuex'
import NavBar from '@oj/components/NavBar.vue'

export default {
  name: 'app',
  components: {
    NavBar
  },
  data() {
    return {
      version: process.env.VERSION
    }
  },
  created() {
    try {
      document.body.removeChild(document.getElementById('app-loader'))
    } catch (e) {
    }
  },
  mounted() {
    this.getWebsiteConfig()
  },
  methods: {
    ...mapActions(['getWebsiteConfig', 'changeDomTitle'])
  },
  computed: {
    ...mapState(['website'])
  },
  watch: {
    'website'() {
      this.changeDomTitle()
    },
    '$route'() {
      this.changeDomTitle()
    }
  }
}
</script>

<style lang="less">
* {
  -webkit-box-sizing: border-box;
  -moz-box-sizing: border-box;
  box-sizing: border-box;
}

a {
  text-decoration: none;
  background-color: transparent;
  color: #2d8cf0;

  &:active,
  &:hover {
    outline-width: 0;
    color: #57a3f3;
    text-decoration: underline;
  }
}

.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

@media screen and (max-width: 1200px) {
  .content-app {
    margin-top: 160px;
    padding: 0 2%;
    flex: 1;
    display: flex;
    flex-direction: column;
  }
}

@media screen and (min-width: 1200px) {
  .content-app {
    margin-top: 80px;
    padding: 0 2%;
    flex: 1;
    display: flex;
    flex-direction: column;
  }
}

.footer {
  margin-top: auto;
  padding: 20px 0;
  background-color: #f8f9fa;
  border-top: 1px solid #e8eaec;

  .footer-content {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;

    .footer-info {
      text-align: center;
      color: #515a6e;
      font-size: 14px;
      margin-bottom: 10px;

      a {
        color: #2d8cf0;

        &:hover {
          color: #57a3f3;
        }
      }
    }

    .footer-meta {
      text-align: center;
      color: #808695;
      font-size: 13px;

      p {
        margin: 0;
      }

      a {
        color: #2d8cf0;
        font-weight: 500;

        &:hover {
          color: #57a3f3;
        }
      }

      .version-tag {
        display: inline-block;
        background-color: #e6f2ff;
        color: #2d8cf0;
        padding: 2px 8px;
        border-radius: 3px;
        margin-left: 8px;
        font-size: 12px;
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

// 自定义返回顶部按钮
.backtop {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(45, 140, 240, 0.8);
  box-shadow: 0 2px 10px rgba(45, 140, 240, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;

  &:hover {
    background: rgba(45, 140, 240, 1);
    box-shadow: 0 4px 15px rgba(45, 140, 240, 0.4);
    transform: translateY(-2px);
  }
}

// 响应式设计
@media screen and (max-width: 768px) {
  .content-app {
    padding: 0 3%;
  }

  .footer {
    padding: 15px 0;

    .footer-content {
      padding: 0 15px;

      .footer-info {
        font-size: 13px;
      }

      .footer-meta {
        font-size: 12px;

        .version-tag {
          display: block;
          margin: 5px 0 0 0;
        }
      }
    }
  }
}
</style>