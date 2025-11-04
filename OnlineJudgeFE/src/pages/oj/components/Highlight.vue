<template>
  <div class="highlight-container">
    <div class="highlight-header" v-if="showHeader">
      <span class="language-tag">{{ languageDisplay }}</span>
      <div class="header-actions">
        <Tooltip content="复制代码" placement="top">
          <Button size="small" icon="ios-copy" type="text" @click="copyCode" class="action-button">
          </Button>
        </Tooltip>
        <Tooltip :content="isExpanded ? '收起代码' : '展开代码'" placement="top">
          <Button size="small" :icon="isExpanded ? 'ios-arrow-up' : 'ios-arrow-down'" type="text" @click="toggleExpand"
            class="action-button">
          </Button>
        </Tooltip>
      </div>
    </div>
    <pre v-highlight="displayCode" :class="{ 'collapsed': !isExpanded && collapsible }">
      <code :class="languageClass" :style="styleObject"></code>
    </pre>
    <div v-if="collapsible && !isExpanded" class="expand-overlay" @click="toggleExpand">
      <span class="expand-text">点击展开剩余 {{ lineCount - maxLines }} 行</span>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Highlight',
  data() {
    return {
      styleObject: {
        'border-left': '3px solid #1890ff'
      },
      isExpanded: true
    }
  },
  props: {
    language: {
      type: String,
      default: ''
    },
    code: {
      required: true,
      type: String
    },
    borderColor: {
      type: String,
      default: '#1890ff'
    },
    collapsible: {
      type: Boolean,
      default: false
    },
    maxLines: {
      type: Number,
      default: 15
    },
    showHeader: {
      type: Boolean,
      default: true
    }
  },
  computed: {
    languageClass() {
      return this.language ? `language-${this.language}` : '';
    },
    languageDisplay() {
      const languageMap = {
        'cpp': 'C++',
        'c': 'C',
        'java': 'Java',
        'python': 'Python',
        'python3': 'Python 3',
        'javascript': 'JavaScript',
        'go': 'Go',
        'rust': 'Rust',
        'php': 'PHP'
      };
      return languageMap[this.language] || this.language || 'Code';
    },
    lineCount() {
      return this.code ? this.code.split('\n').length : 0;
    },
    displayCode() {
      if (!this.collapsible || this.isExpanded) {
        return this.code;
      }
      const lines = this.code.split('\n');
      return lines.slice(0, this.maxLines).join('\n');
    }
  },
  watch: {
    'borderColor'(newVal, oldVal) {
      this.styleObject['border-left'] = `3px solid ${newVal}`;
    }
  },
  methods: {
    copyCode() {
      const textarea = document.createElement('textarea');
      textarea.value = this.code;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);

      this.$Message.success('代码已复制到剪贴板');
    },
    toggleExpand() {
      this.isExpanded = !this.isExpanded;
    }
  }
}
</script>

<style scoped lang="less">
.highlight-container {
  position: relative;
  margin: 15px 0;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.09);
  transition: box-shadow 0.3s ease;

  &:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  }
}

.highlight-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #f8f9fa;
  padding: 8px 15px;
  border-bottom: 1px solid #e9ecef;

  .language-tag {
    font-size: 12px;
    font-weight: 600;
    color: #495057;
    background-color: #e9ecef;
    padding: 4px 10px;
    border-radius: 4px;
    text-transform: uppercase;
  }

  .header-actions {
    display: flex;
    gap: 5px;

    .action-button {
      color: #6c757d;
      transition: color 0.2s ease;

      &:hover {
        color: #1890ff;
      }
    }
  }
}

pre {
  padding: 0;
  margin: 0;
  border-radius: 0 0 6px 6px;
  max-height: none;
  transition: max-height 0.3s ease;

  &.collapsed {
    max-height: 300px;
    overflow: hidden;
    position: relative;
  }

  code {
    padding: 20px;
    font-size: 1.05em;
    line-height: 1.5;
    background: #f8f9fa !important;

    // 确保代码块不会溢出容器
    overflow-x: auto;
    white-space: pre;

    // 添加滚动条样式
    &::-webkit-scrollbar {
      height: 8px;
    }

    &::-webkit-scrollbar-track {
      background: #f1f1f1;
    }

    &::-webkit-scrollbar-thumb {
      background: #c1c1c1;
      border-radius: 4px;

      &:hover {
        background: #a8a8a8;
      }
    }
  }
}

.expand-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 60px;
  background: linear-gradient(to bottom, rgba(255, 255, 255, 0), rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 1));
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding-bottom: 10px;
  cursor: pointer;

  .expand-text {
    color: #1890ff;
    font-size: 14px;
    font-weight: 500;
    background-color: rgba(255, 255, 255, 0.9);
    padding: 6px 12px;
    border-radius: 4px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

    &:hover {
      background-color: #e6f7ff;
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .highlight-container {
    margin: 10px 0;

    pre code {
      padding: 15px;
      font-size: 0.95em;
    }

    .highlight-header {
      padding: 6px 12px;

      .language-tag {
        font-size: 11px;
        padding: 3px 8px;
      }
    }
  }
}
</style>
