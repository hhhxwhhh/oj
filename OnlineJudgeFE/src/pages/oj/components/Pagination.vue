<template>
  <div class="pagination-container">
    <Page :total="total" :page-size="pageSize" @on-change="onChange" @on-page-size-change="onPageSizeChange"
      :show-sizer="showSizer" :page-size-opts="[10, 30, 50, 100, 200]" :current="current" :show-elevator="true"
      :show-total="true" :class="{ 'pagination-compact': !showSizer }">
    </Page>
  </div>
</template>

<script>
export default {
  name: 'Pagination',
  props: {
    total: {
      required: true,
      type: Number
    },
    pageSize: {
      required: false,
      type: Number,
      default: 10
    },
    showSizer: {
      required: false,
      type: Boolean,
      default: false
    },
    current: {
      required: false,
      type: Number,
      default: 1
    }
  },
  methods: {
    onChange(page) {
      if (page < 1) {
        page = 1
      }
      this.$emit('update:current', page)
      this.$emit('on-change', page)
    },
    onPageSizeChange(pageSize) {
      this.$emit('update:pageSize', pageSize)
      this.$emit('on-page-size-change', pageSize)
    }
  }
}
</script>

<style scoped lang="less">
.pagination-container {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin: 20px 0;
  padding: 15px 0;

  &::before {
    content: '';
    flex-grow: 1;
  }

  .ivu-page {
    display: inline-flex;
    align-items: center;
    border-radius: 6px;
    background-color: #fff;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.09);
    padding: 8px 12px;

    &:hover {
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
  }
}

.pagination-compact {
  padding: 8px 12px;

  .ivu-page-item {
    margin: 0 2px;
  }
}
</style>

<style lang="less">
// 分页组件样式定制
.pagination-container {
  .ivu-page {

    // 总数显示
    .ivu-page-total {
      margin-right: 15px;
      color: #515a6e;
      font-size: 14px;
    }

    // 页码项样式
    .ivu-page-item {
      min-width: 32px;
      height: 32px;
      line-height: 30px;
      border: 1px solid #dcdee2;
      border-radius: 4px;
      margin: 0 4px;
      transition: all 0.2s ease-in-out;

      a {
        color: #515a6e;
        font-weight: 500;
      }

      &:hover {
        border-color: #1890ff;

        a {
          color: #1890ff;
        }
      }

      &.ivu-page-item-active {
        background-color: #1890ff;
        border-color: #1890ff;

        a {
          color: #fff;
        }

        &:hover {
          background-color: #40a9ff;
          border-color: #40a9ff;
        }
      }
    }

    // 上一页/下一页按钮
    .ivu-page-prev,
    .ivu-page-next {
      min-width: 32px;
      height: 32px;
      line-height: 30px;
      border: 1px solid #dcdee2;
      border-radius: 4px;
      margin: 0 4px;

      a {
        color: #515a6e;
        font-size: 12px;
      }

      &:hover {
        border-color: #1890ff;

        a {
          color: #1890ff;
        }
      }

      &.ivu-page-disabled {
        opacity: 0.6;
        cursor: not-allowed;

        &:hover {
          border-color: #dcdee2;

          a {
            color: #ccc;
          }
        }
      }
    }

    // 跳转区域
    .ivu-page-options {
      display: flex;
      align-items: center;
      margin-left: 15px;

      .ivu-page-options-elevator {
        display: flex;
        align-items: center;

        input {
          border-radius: 4px;

          &:hover,
          &:focus {
            border-color: #1890ff;
          }
        }
      }

      .ivu-page-options-sizer {
        min-width: 85px;
        margin: 0 10px;

        .ivu-select-selection {
          border-radius: 4px;
          height: 32px;
          min-height: 32px;

          .ivu-select-placeholder,
          .ivu-select-selected-value {
            height: 30px;
            line-height: 30px;
          }
        }
      }
    }

    // 简洁模式下的样式
    &.pagination-compact {

      .ivu-page-item,
      .ivu-page-prev,
      .ivu-page-next {
        min-width: 28px;
        height: 28px;
        line-height: 26px;
        margin: 0 2px;
      }

      .ivu-page-options {
        margin-left: 10px;
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .pagination-container {
    justify-content: center;

    .ivu-page {
      .ivu-page-total {
        display: none;
      }

      .ivu-page-options {
        .ivu-page-options-elevator {
          display: none;
        }
      }
    }
  }
}
</style>
