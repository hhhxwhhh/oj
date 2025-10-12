<template>
  <textarea ref="editorTextarea"></textarea>
</template>

<script>
export default {
  name: 'Simditor',
  props: {
    value: {
      type: String,
      default: ''
    },
    toolbar: {
      type: Array,
      default: () => [
        'title',
        'bold',
        'italic',
        'underline',
        'strikethrough',
        'fontScale',
        'color',
        '|',
        'ol',
        'ul',
        'blockquote',
        'code',
        'table',
        '|',
        'link',
        'image',
        'hr',
        '|',
        'indent',
        'outdent',
        'alignment'
      ]
    },
    config: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      editor: null
    }
  },
  mounted() {
    this.$nextTick(() => {
      this.initEditor()
    })
  },
  methods: {
    initEditor() {
      // 延迟加载 Simditor，避免初始化问题
      import('tar-simditor').then((module) => {
        const Simditor = module.default;

        // 修复 Simditor，确保 connect 方法存在
        if (typeof Simditor.connect !== 'function') {
          Simditor.connect = function () {
            console.warn('Simditor.connect is not implemented');
          };
        }

        // 确保 textarea 元素存在
        if (this.$refs.editorTextarea) {
          // 销毁已存在的编辑器实例
          if (this.editor) {
            this.editor.destroy();
            this.editor = null;
          }

          // 创建新的编辑器实例
          this.editor = new Simditor({
            textarea: this.$refs.editorTextarea,
            toolbar: this.toolbar,
            pasteImage: true,
            ...this.config
          });

          // 设置初始值
          if (this.value) {
            this.editor.setValue(this.value);
          }

          // 绑定事件
          this.editor.on('valuechanged', (e, src) => {
            this.$emit('input', this.editor.getValue());
            this.$emit('change', this.editor.getValue());
          });
        }
      }).catch((error) => {
        console.error('Failed to load Simditor:', error);
        this.$emit('load-error', error);
      });
    },

    setValue(value) {
      if (this.editor) {
        this.editor.setValue(value);
      }
    },

    getValue() {
      if (this.editor) {
        return this.editor.getValue();
      }
      return '';
    }
  },
  watch: {
    value(newVal) {
      if (this.editor && this.editor.getValue() !== newVal) {
        this.editor.setValue(newVal);
      }
    }
  },
  beforeDestroy() {
    // 销毁编辑器实例
    if (this.editor) {
      this.editor.destroy();
      this.editor = null;
    }
  }
}
</script>

<style>
@import '~tar-simditor/styles/simditor.css';
</style>