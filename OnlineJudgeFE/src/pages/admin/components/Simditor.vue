<template>
  <div class="simditor-fallback">
    <textarea ref="editorTextarea" :value="value" @input="handleInput" class="simditor-textarea"
      style="width: 100%; min-height: 300px; padding: 10px; border: 1px solid #dcdfe6; border-radius: 4px;"></textarea>
    <p style="color: #909399; font-size: 12px; margin-top: 5px;">
      富文本编辑器当前不可用，使用纯文本编辑
    </p>
  </div>
</template>

<script>
export default {
  name: 'Simditor',
  props: {
    value: {
      type: String,
      default: ''
    }
  },
  methods: {
    handleInput(event) {
      this.$emit('input', event.target.value);
      this.$emit('change', event.target.value);
    },

    setValue(value) {
      if (this.$refs.editorTextarea) {
        this.$refs.editorTextarea.value = value;
      }
    },

    getValue() {
      return this.$refs.editorTextarea ? this.$refs.editorTextarea.value : '';
    }
  },
  mounted() {
    // 初始化值
    if (this.value && this.$refs.editorTextarea) {
      this.$refs.editorTextarea.value = this.value;
    }
  }
}
</script>

<style scoped>
.simditor-textarea:focus {
  outline: none;
  border-color: #409eff;
}
</style>