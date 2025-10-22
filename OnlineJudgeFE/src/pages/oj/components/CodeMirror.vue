<template>
  <div style="margin: 0px 0px 15px 0px">
    <Row type="flex" justify="space-between" class="header">
      <Col :span=12>
      <div>
        <span>{{ $t('m.Language') }}:</span>
        <Select :value="language" @on-change="onLangChange" class="adjust">
          <Option v-for="item in languages" :key="item" :value="item">{{ item }}
          </Option>
        </Select>

        <Tooltip :content="this.$i18n.t('m.Reset_to_default_code_definition')" placement="top"
          style="margin-left: 10px">
          <Button icon="refresh" @click="onResetClick"></Button>
        </Tooltip>

        <Tooltip :content="this.$i18n.t('m.Upload_file')" placement="top" style="margin-left: 10px">
          <Button icon="upload" @click="onUploadFile"></Button>
        </Tooltip>

        <input type="file" id="file-uploader" style="display: none" @change="onUploadFileDone">

      </div>
      </Col>
      <Col :span=12>
      <div class="fl-right">
        <span>{{ $t('m.Theme') }}:</span>
        <Select :value="theme" @on-change="onThemeChange" class="adjust">
          <Option v-for="item in themes" :key="item.label" :value="item.value">{{ item.label }}
          </Option>
        </Select>
      </div>
      </Col>
    </Row>
    <div class="editor-container">
      <codemirror :value="value" :options="options" @change="onEditorCodeChange" @cursorActivity="onCursorActivity"
        ref="myEditor">
      </codemirror>
      <div v-if="suggestions.length > 0" class="suggestions-panel">
        <div v-for="(suggestion, index) in suggestions" :key="index" class="suggestion-item"
          @click="applySuggestion(suggestion)">
          {{ suggestion }}
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import utils from '@/utils/utils'
import api from '@oj/api'
import { codemirror } from 'vue-codemirror-lite'

// theme
import 'codemirror/theme/monokai.css'
import 'codemirror/theme/solarized.css'
import 'codemirror/theme/material.css'

// mode
import 'codemirror/mode/clike/clike.js'
import 'codemirror/mode/python/python.js'
import 'codemirror/mode/go/go.js'
import 'codemirror/mode/javascript/javascript.js'

// active-line.js
import 'codemirror/addon/selection/active-line.js'

// foldGutter
import 'codemirror/addon/fold/foldgutter.css'
import 'codemirror/addon/fold/foldgutter.js'
import 'codemirror/addon/fold/brace-fold.js'
import 'codemirror/addon/fold/indent-fold.js'

// autocomplete
import 'codemirror/addon/hint/show-hint.css'
import 'codemirror/addon/hint/show-hint.js'
import 'codemirror/addon/hint/anyword-hint.js'

export default {
  name: 'CodeMirror',
  components: {
    codemirror
  },
  props: {
    value: {
      type: String,
      default: ''
    },
    languages: {
      type: Array,
      default: () => {
        return ['C', 'C++', 'Java', 'Python2']
      }
    },
    language: {
      type: String,
      default: 'C++'
    },
    theme: {
      type: String,
      default: 'solarized'
    },
    problemId: {
      type: [String, Number],
      default: null
    }
  },
  data() {
    return {
      options: {
        // codemirror options
        tabSize: 4,
        mode: 'text/x-csrc',
        theme: 'solarized',
        lineNumbers: true,
        line: true,
        // 代码折叠
        foldGutter: true,
        gutters: ['CodeMirror-linenumbers', 'CodeMirror-foldgutter'],
        // 选中文本自动高亮，及高亮方式
        styleSelectedText: true,
        lineWrapping: true,
        highlightSelectionMatches: { showToken: /\w/, annotateScrollbar: true },
        // 自动补全
        hintOptions: {
          completeSingle: false
        }
      },
      mode: {
        'C++': 'text/x-csrc'
      },
      themes: [
        { label: this.$i18n.t('m.Monokai'), value: 'monokai' },
        { label: this.$i18n.t('m.Solarized_Light'), value: 'solarized' },
        { label: this.$i18n.t('m.Material'), value: 'material' }
      ],
      suggestions: [],
      suggestionTimer: null,
      lastCursorPosition: null
    }
  },
  mounted() {
    utils.getLanguages().then(languages => {
      let mode = {}
      languages.forEach(lang => {
        mode[lang.name] = lang.content_type
      })
      this.mode = mode
      this.editor.setOption('mode', this.mode[this.language])
    })
    this.editor.focus()

    // 添加键盘事件监听器
    this.editor.on('keydown', (cm, event) => {
      // Ctrl+Space触发自动补全
      if (event.ctrlKey && event.key === ' ') {
        event.preventDefault()
        this.triggerAutoCompletion()
      }
    })

    // 添加代码更改事件监听器，用于触发实时建议
    this.editor.on('change', () => {
      this.scheduleSuggestions()
    })
  },
  methods: {
    onEditorCodeChange(newCode) {
      this.$emit('update:value', newCode)
      // 当代码改变时，清除之前的建议
      this.suggestions = []
    },
    onLangChange(newVal) {
      this.editor.setOption('mode', this.mode[newVal])
      this.$emit('changeLang', newVal)
    },
    onThemeChange(newTheme) {
      this.editor.setOption('theme', newTheme)
      this.$emit('changeTheme', newTheme)
    },
    onResetClick() {
      this.$emit('resetCode')
    },
    onUploadFile() {
      document.getElementById('file-uploader').click()
    },
    onUploadFileDone() {
      let f = document.getElementById('file-uploader').files[0]
      let fileReader = new window.FileReader()
      let self = this
      fileReader.onload = function (e) {
        var text = e.target.result
        self.editor.setValue(text)
        document.getElementById('file-uploader').value = ''
      }
      fileReader.readAsText(f, 'UTF-8')
    },
    onCursorActivity(cm) {
      const cursor = cm.getCursor()
      // 只有当光标位置发生变化时才触发
      if (!this.lastCursorPosition ||
        this.lastCursorPosition.line !== cursor.line ||
        this.lastCursorPosition.ch !== cursor.ch) {
        this.lastCursorPosition = { ...cursor }
        this.scheduleSuggestions(cm)
      }
    },
    scheduleSuggestions() {
      // 清除之前的定时器
      if (this.suggestionTimer) {
        clearTimeout(this.suggestionTimer)
      }

      // 设置新的定时器，延迟1秒触发建议
      this.suggestionTimer = setTimeout(() => {
        this.fetchRealTimeSuggestions()
      }, 1000)
    },

    applySuggestion(suggestion) {
      // 应用建议（这里可以进一步定制）
      this.suggestions = []
      // 可以添加更多逻辑来实际应用建议
    },
    async fetchRealTimeSuggestions() {
      const code = this.editor.getValue()

      try {
        const res = await api.getRealTimeSuggestion({
          code: code,
          language: this.language,
          problem_id: this.problemId
        })

        // 这里可以通过事件将建议传递给父组件
        this.$emit('suggestions', res.data.data || [])
      } catch (err) {
        console.error('获取实时建议失败:', err)
      }
    },
    triggerAutoCompletion() {
      // 触发自动补全
      const code = this.editor.getValue()
      const cursor = this.editor.getCursor()
      const line = this.editor.getLine(cursor.line)
      let start = cursor.ch
      let end = start
      while (end < line.length && /[\w$]/.test(line.charAt(end))) ++end
      while (start && /[\w$]/.test(line.charAt(start - 1))) --start
      const prefix = line.slice(start, end)

      if (prefix.length > 0) {
        this.fetchAutoCompletion(code, prefix)
      }
    },
    async fetchAutoCompletion(code, prefix) {
      try {
        const res = await api.getCodeAutoCompletion({
          code: code,
          language: this.language,
          prefix: prefix,
          problem_id: this.problemId
        })

        if (res.data && res.data.data && res.data.data.completions) {
          const completions = res.data.data.completions
          // 使用CodeMirror的hint功能显示补全建议
          const hints = completions.map(item => item.text)
          this.showCompletions(hints)
        }
      } catch (err) {
        console.error('Failed to fetch auto completion:', err)
      }
    },
    showCompletions(completions) {
      if (completions.length > 0) {
        // 简单实现：将补全建议显示在建议面板中
        this.suggestions = completions
      }
    }
  },
  computed: {
    editor() {
      // get current editor object
      return this.$refs.myEditor.editor
    }
  },
  watch: {
    'theme'(newVal, oldVal) {
      this.editor.setOption('theme', newVal)
    }
  }
}
</script>

<style lang="less" scoped>
.header {
  margin: 5px 5px 15px 5px;

  .adjust {
    width: 150px;
    margin-left: 10px;
  }

  .fl-right {
    float: right;
  }
}

.editor-container {
  position: relative;
}

.suggestions-panel {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 10;
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  max-height: 200px;
  overflow-y: auto;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.suggestion-item {
  padding: 8px 12px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  font-size: 14px;

  &:hover {
    background-color: #f5f5f5;
  }

  &:last-child {
    border-bottom: none;
  }
}
</style>

<style>
.CodeMirror {
  height: auto !important;
}

.CodeMirror-scroll {
  min-height: 300px;
  max-height: 1000px;
}

.CodeMirror-hints {
  z-index: 9999 !important;
}
</style>