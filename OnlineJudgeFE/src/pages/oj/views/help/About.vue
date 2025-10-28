<template>
  <div class="about-view">
    <Panel class="container" shadow>
      <div slot="title" class="panel-title">
        <Icon type="md-code-working" />
        {{ $t('m.Compiler') }} & {{ $t('m.Judger') }}
      </div>
      <div class="content">
        <div class="languages-section">
          <div v-for="lang in languages" :key="lang.name" class="language-item">
            <div class="language-header">
              <span class="language-name">{{ lang.name }}</span>
              <span class="language-description">({{ lang.description }})</span>
            </div>
            <div class="compile-command">
              <pre class="command-code">{{ lang.config.compile.compile_command }}</pre>
            </div>
          </div>
        </div>
      </div>
    </Panel>

    <Panel :padding="15" class="container" shadow>
      <div slot="title" class="panel-title">
        <Icon type="md-help-circle" />
        {{ $t('m.Result_Explanation') }}
      </div>
      <div class="content">
        <div class="explanations">
          <div class="explanation-item">
            <div class="explanation-header">
              <Icon type="md-time" class="status-icon pending" />
              <b>{{ $t('m.Pending') }} & {{ $t('m.Judging') }}</b>
            </div>
            <p class="explanation-desc">{{ $t('m.Pending_Judging_Description') }}</p>
          </div>

          <div class="explanation-item">
            <div class="explanation-header">
              <Icon type="md-close-circle" class="status-icon compile-error" />
              <b>{{ $t('m.Compile_Error') }}</b>
            </div>
            <p class="explanation-desc">{{ $t('m.Compile_Error_Description') }}</p>
          </div>

          <div class="explanation-item">
            <div class="explanation-header">
              <Icon type="md-checkmark-circle" class="status-icon accepted" />
              <b>{{ $t('m.Accepted') }}</b>
            </div>
            <p class="explanation-desc">{{ $t('m.Accepted_Description') }}</p>
          </div>

          <div class="explanation-item">
            <div class="explanation-header">
              <Icon type="md-close" class="status-icon wrong-answer" />
              <b>{{ $t('m.Wrong_Answer') }}</b>
            </div>
            <p class="explanation-desc">{{ $t('m.Wrong_Answer_Description') }}</p>
          </div>

          <div class="explanation-item">
            <div class="explanation-header">
              <Icon type="md-bug" class="status-icon runtime-error" />
              <b>{{ $t('m.Runtime_Error') }}</b>
            </div>
            <p class="explanation-desc">{{ $t('m.Runtime_Error_Description') }}</p>
          </div>

          <div class="explanation-item">
            <div class="explanation-header">
              <Icon type="md-timer" class="status-icon time-limit" />
              <b>{{ $t('m.Time_Limit_Exceeded') }}</b>
            </div>
            <p class="explanation-desc">{{ $t('m.Time_Limit_Exceeded_Description') }}</p>
          </div>

          <div class="explanation-item">
            <div class="explanation-header">
              <Icon type="md-disc" class="status-icon memory-limit" />
              <b>{{ $t('m.Memory_Limit_Exceeded') }}</b>
            </div>
            <p class="explanation-desc">{{ $t('m.Memory_Limit_Exceeded_Description') }}</p>
          </div>

          <div class="explanation-item">
            <div class="explanation-header">
              <Icon type="md-warning" class="status-icon system-error" />
              <b>{{ $t('m.System_Error') }}</b>
            </div>
            <p class="explanation-desc">{{ $t('m.System_Error_Description') }}</p>
          </div>
        </div>
      </div>
    </Panel>
  </div>
</template>

<script>
import utils from '@/utils/utils'
import Panel from '@oj/components/Panel.vue'

export default {
  name: 'About',
  components: {
    Panel
  },
  data() {
    return {
      languages: []
    }
  },
  beforeRouteEnter(to, from, next) {
    utils.getLanguages().then(languages => {
      next(vm => {
        vm.languages = languages
      })
    })
  }
}
</script>

<style scoped lang="less">
.about-view {
  .panel-title {
    font-weight: 500;
    font-size: 16px;
  }

  .container {
    margin-bottom: 20px;

    .content {
      font-size: 14px;

      .languages-section {
        .language-item {
          padding: 15px 0;
          border-bottom: 1px solid #e8eaec;

          &:last-child {
            border-bottom: none;
          }

          .language-header {
            margin-bottom: 10px;

            .language-name {
              font-weight: 500;
              color: #495060;
              font-size: 16px;
            }

            .language-description {
              color: #808695;
              margin-left: 8px;
            }
          }

          .compile-command {
            .command-code {
              background-color: #f8f8f9;
              padding: 12px;
              border-radius: 4px;
              border: 1px solid #e8eaec;
              font-family: Monaco, Menlo, "Courier New", monospace;
              font-size: 13px;
              line-height: 1.5;
              overflow-x: auto;
              margin: 0;
            }
          }
        }
      }

      .explanations {
        .explanation-item {
          padding: 15px 0;
          border-bottom: 1px solid #e8eaec;

          &:last-child {
            border-bottom: none;
          }

          .explanation-header {
            display: flex;
            align-items: center;
            margin-bottom: 8px;

            .status-icon {
              margin-right: 10px;
              font-size: 18px;

              &.pending {
                color: #2d8cf0;
              }

              &.compile-error {
                color: #ed4014;
              }

              &.accepted {
                color: #52c41a;
              }

              &.wrong-answer {
                color: #ff9900;
              }

              &.runtime-error {
                color: #ff6600;
              }

              &.time-limit {
                color: #b036d4;
              }

              &.memory-limit {
                color: #ff3399;
              }

              &.system-error {
                color: #ed4014;
              }
            }

            b {
              font-size: 15px;
              color: #495060;
            }
          }

          .explanation-desc {
            margin: 0 0 0 28px;
            color: #808695;
            line-height: 1.6;
            font-size: 14px;
          }
        }
      }
    }
  }
}

// 响应式设计
@media screen and (max-width: 768px) {
  .about-view {
    .container {
      .content {
        padding: 0 10px;

        .explanations {
          .explanation-item {
            .explanation-desc {
              margin-left: 0;
            }
          }
        }
      }
    }
  }
}
</style>