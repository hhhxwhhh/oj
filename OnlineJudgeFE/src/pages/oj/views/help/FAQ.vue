<template>
  <div class="faq-view">
    <Panel shadow>
      <div slot="title" class="panel-title">
        <Icon type="md-help-circle" />
        {{ $t('m.Frequently_Asked_Questions') }}
      </div>
      <div class="content">
        <div class="faq-list">
          <div class="faq-item">
            <div class="faq-question">
              <Icon type="md-information-circle" class="faq-icon info" />
              {{ $t('m.Where_is_the_input_and_the_output') }}
            </div>
            <div class="faq-answer">
              {{ $t('m.Where_is_the_input_and_the_output_answer_part_1') }}
              <code>stdin</code>
              ('{{ $t('m.Standard_Input') }}')
              {{ $t('m.Where_is_the_input_and_the_output_answer_part_3') }}
              <code>stdout</code>
              ('{{ $t('m.Standard_Output') }}')
              {{ $t('m.Where_is_the_input_and_the_output_answer_part_5') }}
              <code>scanf</code>
              {{ $t('m.Where_is_the_input_and_the_output_answer_part_6') }}
              <code>cin</code>
              {{ $t('m.Where_is_the_input_and_the_output_answer_part_7') }}
              <code>printf</code>
              {{ $t('m.Where_is_the_input_and_the_output_answer_part_8') }}
              <code>cout</code>
              {{ $t('m.Where_is_the_input_and_the_output_answer_part_9') }}
              <code>{{ $t('m.Runtime_Error') }}</code>.
            </div>
          </div>

          <div class="faq-item">
            <div class="faq-question">
              <Icon type="md-time" class="faq-icon time" />
              {{ $t('m.What_is_the_meaning_of_submission_execution_time') }}
            </div>
            <div class="faq-answer">
              {{ $t('m.What_is_the_meaning_of_submission_execution_time_answer') }}
            </div>
          </div>

          <div class="faq-item">
            <div class="faq-question">
              <Icon type="md-code" class="faq-icon code" />
              {{ $t('m.How_Can_I_use_CPP_Int64') }}
            </div>
            <div class="faq-answer">
              {{ $t('m.How_Can_I_use_CPP_Int64_answer_part_1') }}
              <code>long long</code>
              {{ $t('m.How_Can_I_use_CPP_Int64_answer_part_2') }}
              <code>cin/cout</code>
              {{ $t('m.or') }}
              <code>%lld</code>,
              {{ $t('m.using') }}
              <code>__int64</code>
              {{ $t('m.How_Can_I_use_CPP_Int64_answer_part_3') }}
              <code>{{ $t('m.Compile_Error') }}</code>.
            </div>
          </div>

          <div class="faq-item">
            <div class="faq-question">
              <Icon type="md-cafe" class="faq-icon java" />
              {{ $t('m.Java_specifications') }}
            </div>
            <div class="faq-answer">
              {{ $t('m.Java_specifications_answer_part_1') }}
              <code>Main</code>
              {{ $t('m.Java_specifications_answer_part_2') }}
              <code>Main</code>
              {{ $t('m.Java_specifications_answer_part_3') }}
            </div>
          </div>

          <div class="faq-item">
            <div class="faq-question">
              <Icon type="md-checkbox-outline" class="faq-icon presentation" />
              {{ $t('m.About_presentation_error') }}
            </div>
            <div class="faq-answer">
              {{ $t('m.About_presentation_error_answer_part_1') }}
              <b>{{ $t('m.last') }}</b>
              {{ $t('m.About_presentation_error_answer_part_2') }}
              <code>{{ $t('m.Wrong_Answer') }}</code>.
            </div>
          </div>

          <div class="faq-item">
            <div class="faq-question">
              <Icon type="md-bug" class="faq-icon bug" />
              {{ $t('m.How_to_report_bugs') }}
            </div>
            <div class="faq-answer">
              {{ $t('m.How_to_report_bugs_answer_part_1') }}
              <a href="https://github.com/QingdaoU/OnlineJudge" target="_blank">Github</a>
              {{ $t('m.How_to_report_bugs_answer_part_2') }}
            </div>
          </div>
        </div>
      </div>
    </Panel>
  </div>
</template>

<script>
import Panel from '@oj/components/Panel.vue'

export default {
  name: 'FAQ',
  components: {
    Panel
  }
}
</script>

<style lang="less" scoped>
.faq-view {
  .panel-title {
    font-weight: 500;
    font-size: 16px;
  }

  .content {
    font-size: 14px;
    padding: 10px 20px;

    .faq-list {
      .faq-item {
        padding: 20px 0;
        border-bottom: 1px solid #e8eaec;

        &:last-child {
          border-bottom: none;
        }

        .faq-question {
          display: flex;
          align-items: center;
          font-size: 16px;
          font-weight: 500;
          color: #495060;
          margin-bottom: 12px;

          .faq-icon {
            font-size: 18px;
            margin-right: 10px;

            &.info {
              color: #2d8cf0;
            }

            &.time {
              color: #b036d4;
            }

            &.code {
              color: #52c41a;
            }

            &.java {
              color: #fa8c16;
            }

            &.presentation {
              color: #722ed1;
            }

            &.bug {
              color: #ed4014;
            }
          }
        }

        .faq-answer {
          margin-left: 28px;
          color: #808695;
          line-height: 1.6;
          font-size: 14px;

          code {
            background-color: #f8f8f9;
            padding: 2px 4px;
            border-radius: 2px;
            border: 1px solid #e8eaec;
            font-family: Monaco, Menlo, "Courier New", monospace;
            font-size: 13px;
          }

          a {
            color: #2d8cf0;
            text-decoration: none;

            &:hover {
              text-decoration: underline;
            }
          }
        }
      }
    }
  }
}

// 响应式设计
@media screen and (max-width: 768px) {
  .faq-view {
    .content {
      padding: 10px;

      .faq-list {
        .faq-item {
          .faq-answer {
            margin-left: 0;
          }
        }
      }
    }
  }
}
</style>