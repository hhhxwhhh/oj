<template>
  <Card :padding="padding" :shadow="shadow" :dis-hover="disHover" :bordered="bordered" class="oj-panel">
    <div slot="title" class="panel-title">
      <slot name="title"></slot>
    </div>
    <div slot="extra" class="panel-extra">
      <slot name="extra"></slot>
    </div>
    <div class="panel-body">
      <slot></slot>
    </div>
  </Card>
</template>

<script>
export default {
  name: 'Panel',
  props: {
    shadow: {
      required: false,
      type: Boolean,
      default: false
    },
    padding: {
      required: false,
      type: Number,
      default: 0
    },
    disHover: {
      required: false,
      type: Boolean,
      default: false
    },
    bordered: {
      required: false,
      type: Boolean,
      default: true
    }
  }
}
</script>

<style lang="less">
@import (reference) '../../../styles/common.less';

.oj-panel {
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s ease;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .ivu-card-head {
    background-color: #f8f9fa;
    border-bottom: 1px solid #e9ecef;
    padding: 12px 20px;
  }
}

.panel-title {
  .section-title;
  padding: 5px 15px;
  font-weight: 600;
  color: #495057;
  display: flex;
  align-items: center;

  /* 完全移除蓝色竖线 */
  &::before {
    display: none;
  }
}

.panel-extra {
  line-height: 40px;

  .ivu-input-icon {
    line-height: 40px;
  }

  ul.filter {
    >li {
      display: inline-block;
      padding: 0 10px;
    }
  }
}

.panel-body {
  word-break: break-all;
  word-wrap: break-word;
  padding: 20px;

  &:empty {
    padding: 0;
  }
}

@media (max-width: 768px) {
  .oj-panel {
    border-radius: 0;
  }

  .panel-body {
    padding: 15px;
  }
}
</style>