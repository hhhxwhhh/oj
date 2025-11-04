<template>
  <div class="code-mirror-container">
    <div class="code-mirror-header">
      <Row type="flex" justify="space-between" class="header-content">
        <Col :span="12" class="left-controls">
        <div class="control-group">
          <label class="control-label">{{ $t('m.Language') }}:</label>
          <Select :value="language" @on-change="onLangChange" class="language-select control-input"
            :disabled="disabled">
            <Option v-for="item in availableLanguages" :key="item.name" :value="item.name">
              {{ item.name }}
            </Option>
          </Select>
        </div>

        <div class="control-buttons">
          <Tooltip :content="$t('m.Reset_to_default_code_definition')" placement="top">
            <Button icon="md-refresh" @click="onResetClick" :disabled="disabled" class="control-button" />
          </Tooltip>

          <Tooltip :content="$t('m.Upload_file')" placement="top">
            <Button icon="md-cloud-upload" @click="onUploadFile" :disabled="disabled" class="control-button" />
          </Tooltip>

          <input type="file" id="file-uploader" style="display: none" @change="onUploadFileDone" :disabled="disabled">
        </div>
        </Col>

        <Col :span="12" class="right-controls">
        <div class="control-group theme-selector">
          <label class="control-label">{{ $t('m.Theme') }}:</label>
          <Select :value="theme" @on-change="onThemeChange" class="theme-select control-input" :disabled="disabled">
            <Option v-for="item in themes" :key="item.value" :value="item.value">
              {{ item.label }}
            </Option>
          </Select>
        </div>

        <div v-if="useOllama" class="ai-controls">
          <Tooltip :content="ollamaAvailable ? $t('m.AI_Code_Assist_Enabled') : $t('m.AI_Code_Assist_Unavailable')"
            placement="top">
            <Icon type="md-bulb" :class="['ai-status-icon', { 'enabled': ollamaAvailable }]" />
          </Tooltip>
        </div>
        </Col>
      </Row>
    </div>

    <div class="editor-wrapper">
      <div v-if="isLoading" class="editor-loading-overlay">
        <Spin size="large" />
        <p class="loading-text">{{ $t('m.Loading_Editor') }}</p>
      </div>

      <codemirror :value="value" :options="editorOptions" @input="onEditorCodeChange" @cursorActivity="onCursorActivity"
        ref="myEditor" class="code-editor" :class="{ 'loading': isLoading }" />
    </div>

    <div v-if="suggestions.length > 0" class="suggestions-panel">
      <div v-for="(suggestion, index) in suggestions" :key="index" class="suggestion-item"
        @click="applySuggestion(suggestion)">
        <div class="suggestion-content">
          <Icon type="md-code" class="suggestion-icon" />
          <span class="suggestion-text">{{ suggestion.text }}</span>
        </div>
        <div v-if="suggestion.description" class="suggestion-description">
          {{ suggestion.description }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import utils from '@/utils/utils'
import api from '@oj/api'
import { codemirror } from 'vue-codemirror-lite'

// 主题
import 'codemirror/theme/monokai.css'
import 'codemirror/theme/solarized.css'
import 'codemirror/theme/material.css'

// 语言模式
import 'codemirror/mode/clike/clike.js'
import 'codemirror/mode/python/python.js'
import 'codemirror/mode/go/go.js'
import 'codemirror/mode/javascript/javascript.js'
import 'codemirror/mode/rust/rust.js'
import 'codemirror/mode/php/php.js'

// 选中行高亮
import 'codemirror/addon/selection/active-line.js'

// 代码折叠
import 'codemirror/addon/fold/foldgutter.css'
import 'codemirror/addon/fold/foldgutter.js'
import 'codemirror/addon/fold/brace-fold.js'
import 'codemirror/addon/fold/indent-fold.js'

// 自动补全
import 'codemirror/addon/hint/show-hint.css'
import 'codemirror/addon/hint/show-hint.js'
import 'codemirror/addon/hint/anyword-hint.js'

// 搜索
import 'codemirror/addon/search/search.js'
import 'codemirror/addon/search/searchcursor.js'
import 'codemirror/addon/search/jump-to-line.js'

// 括号匹配
import 'codemirror/addon/edit/matchbrackets.js'
import 'codemirror/addon/edit/closebrackets.js'

// 行号和状态栏
import 'codemirror/addon/display/rulers.js'

// 添加 keyMap 插件导入
import 'codemirror/keymap/sublime.js'
import 'codemirror/keymap/vim.js'
import 'codemirror/keymap/emacs.js'


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
      default: () => []
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
    },
    useOllama: {
      type: Boolean,
      default: false
    },
    disabled: {
      type: Boolean,
      default: false
    },
    height: {
      type: [String, Number],
      default: 'auto'
    }
  },
  data() {
    return {
      isLoading: false,
      availableLanguages: [],
      editorOptions: {
        tabSize: 4,
        mode: 'text/x-csrc',
        theme: 'solarized',
        lineNumbers: true,
        line: true,
        styleActiveLine: true,
        lineWrapping: true,
        foldGutter: true,
        matchBrackets: true,
        autoCloseBrackets: true,
        gutters: ['CodeMirror-linenumbers', 'CodeMirror-foldgutter'],
        styleSelectedText: true,
        highlightSelectionMatches: {
          showToken: /\w/,
          annotateScrollbar: true
        },
        hintOptions: {
          completeSingle: false
        },
        rulers: [{ column: 80, className: 'ruler-80' }],
        keyMap: 'default',
        extraKeys: {
          'Ctrl-Space': () => this.triggerAutoCompletion(),
          'Ctrl-F': 'findPersistent',
          'Ctrl-R': 'replace',
          'Alt-F': 'findPersistentNext',
          'Alt-Shift-F': 'findPersistentPrev'
        }
      },
      modeMap: {},
      themes: [
        { label: this.$i18n ? this.$i18n.t('m.Monokai') : 'Monokai', value: 'monokai' },
        { label: this.$i18n ? this.$i18n.t('m.Solarized_Light') : 'Solarized Light', value: 'solarized' },
        { label: this.$i18n ? this.$i18n.t('m.Material') : 'Material', value: 'material' },
        { label: this.$i18n ? this.$i18n.t('m.Default') : 'Default', value: 'default' }
      ],
      suggestions: [],
      suggestionTimer: null,
      completionTimer: null,
      lastCursorPosition: null,
      autoCompletionEnabled: true,
      autoCompletionDelay: 800,
      debounceTimer: null,
      completionCache: new Map(),
      ollamaAvailable: false,
      ollamaModels: [],
      selectedOllamaModel: null
    }
  },
  computed: {
    editor() {
      return this.$refs.myEditor ? this.$refs.myEditor.editor : null
    },
    editorHeight() {
      if (this.height === 'auto') {
        return '300px'
      }
      return typeof this.height === 'number' ? `${this.height}px` : this.height
    }
  },
  async mounted() {
    this.isLoading = true
    try {
      await this.initLanguages()
      await this.initEditor()

      if (this.useOllama) {
        await this.checkOllamaAvailability()
      }
    } catch (error) {
      console.error('CodeMirror initialization error:', error)
    } finally {
      this.isLoading = false
    }
  },
  beforeDestroy() {
    this.clearTimers()
  },
  watch: {
    theme(newVal) {
      if (this.editor) {
        this.editor.setOption('theme', newVal)
      }
    },
    language(newVal) {
      if (this.editor) {
        this.editor.setOption('mode', this.modeMap[newVal] || 'text/plain')
      }
    },
    useOllama: {
      handler(newVal) {
        if (newVal) {
          this.checkOllamaAvailability()
        }
      },
      immediate: true
    },
    disabled(newVal) {
      if (this.editor) {
        this.editor.setOption('readOnly', newVal)
      }
    }
  },
  methods: {
    async initLanguages() {
      try {
        const languages = this.languages.length > 0
          ? this.languages.map(name => ({ name }))
          : await utils.getLanguages()

        this.availableLanguages = languages

        // 构建语言到模式的映射
        const modeMap = {}
        languages.forEach(lang => {
          if (lang.content_type) {
            modeMap[lang.name] = lang.content_type
          } else {
            // 默认映射
            const defaultModes = {
              'C': 'text/x-csrc',
              'C++': 'text/x-c++src',
              'Java': 'text/x-java',
              'Python': 'text/x-python',
              'Python3': 'text/x-python',
              'JavaScript': 'text/javascript',
              'Go': 'text/x-go',
              'Rust': 'text/x-rustsrc',
              'PHP': 'application/x-httpd-php'
            }
            modeMap[lang.name] = defaultModes[lang.name] || 'text/plain'
          }
        })

        this.modeMap = modeMap
      } catch (error) {
        console.error('Failed to initialize languages:', error)
        // 使用默认语言配置
        this.availableLanguages = [
          { name: 'C' },
          { name: 'C++' },
          { name: 'Java' },
          { name: 'Python' },
          { name: 'Python3' }
        ]

        this.modeMap = {
          'C': 'text/x-csrc',
          'C++': 'text/x-c++src',
          'Java': 'text/x-java',
          'Python': 'text/x-python',
          'Python3': 'text/x-python'
        }
      }
    },

    async initEditor() {
      if (!this.editor) return

      // 设置初始语言模式
      const mode = this.modeMap[this.language] || 'text/x-csrc'
      this.editor.setOption('mode', mode)

      // 设置主题
      this.editor.setOption('theme', this.theme)

      // 设置只读状态
      this.editor.setOption('readOnly', this.disabled)

      // 添加事件监听器
      this.setupEventListeners()

      // 聚焦编辑器
      if (!this.disabled) {
        this.$nextTick(() => {
          this.editor.focus()
        })
      }
    },

    setupEventListeners() {
      if (!this.editor) return

      // 键盘事件
      this.editor.on('keydown', this.handleKeyDown)

      // 代码更改事件
      this.editor.on('change', this.handleChange)

      // 光标活动事件
      this.editor.on('cursorActivity', this.handleCursorActivity)
    },

    handleKeyDown(cm, event) {
      // Ctrl+Space触发自动补全
      if (event.ctrlKey && event.key === ' ' && !this.disabled) {
        event.preventDefault()
        this.triggerAutoCompletion()
      }
    },

    handleChange() {
      this.resetAutoCompletionTimer()
      this.scheduleSuggestions()
    },

    handleCursorActivity(cm) {
      const cursor = cm.getCursor()
      if (!this.lastCursorPosition ||
        this.lastCursorPosition.line !== cursor.line ||
        this.lastCursorPosition.ch !== cursor.ch) {
        this.lastCursorPosition = { ...cursor }
        this.scheduleSuggestions(cm)
      }
    },

    onEditorCodeChange(newCode) {
      if (!this.disabled) {
        this.$emit('input', newCode)
        this.$emit('update:value', newCode)
        this.suggestions = []
      }
    },

    onLangChange(newVal) {
      if (!this.disabled) {
        const mode = this.modeMap[newVal] || 'text/plain'
        if (this.editor) {
          this.editor.setOption('mode', mode)
        }
        this.$emit('changeLang', newVal)
      }
    },

    onThemeChange(newTheme) {
      if (!this.disabled) {
        if (this.editor) {
          this.editor.setOption('theme', newTheme)
        }
        this.$emit('changeTheme', newTheme)
      }
    },

    onResetClick() {
      if (!this.disabled) {
        this.$emit('resetCode')
      }
    },

    onUploadFile() {
      if (!this.disabled) {
        document.getElementById('file-uploader').click()
      }
    },

    onUploadFileDone(event) {
      if (this.disabled) return

      const file = event.target.files[0]
      if (!file) return

      const fileReader = new FileReader()
      fileReader.onload = (e) => {
        const text = e.target.result
        if (this.editor) {
          this.editor.setValue(text)
        }
        event.target.value = ''
        this.$emit('fileUploaded', file.name)
      }
      fileReader.readAsText(file, 'UTF-8')
    },

    resetAutoCompletionTimer() {
      this.clearCompletionTimer()

      if (this.autoCompletionEnabled && !this.disabled) {
        this.completionTimer = setTimeout(() => {
          this.triggerAutoCompletion()
        }, this.autoCompletionDelay)
      }
    },

    clearCompletionTimer() {
      if (this.completionTimer) {
        clearTimeout(this.completionTimer)
        this.completionTimer = null
      }
    },

    clearTimers() {
      if (this.suggestionTimer) {
        clearTimeout(this.suggestionTimer)
        this.suggestionTimer = null
      }
      this.clearCompletionTimer()
      if (this.debounceTimer) {
        clearTimeout(this.debounceTimer)
        this.debounceTimer = null
      }
    },

    async triggerAutoCompletion() {
      if (this.disabled || !this.autoCompletionEnabled) return

      if (!this.editor) return

      const code = this.editor.getValue()
      const cursor = this.editor.getCursor()
      const line = this.editor.getLine(cursor.line) || ''

      // 提取前缀
      let start = cursor.ch
      while (start > 0 && /[\w$.]/.test(line.charAt(start - 1))) {
        start--
      }

      const prefix = line.slice(start, cursor.ch)

      // 检查是否在字符串内部
      const lineBeforeCursor = line.substring(0, cursor.ch)
      const quoteCount = (lineBeforeCursor.match(/["']/g) || []).length
      const inString = quoteCount % 2 === 1

      if (inString) return

      try {
        if (this.useOllama && this.ollamaAvailable) {
          await this.fetchOllamaAutoCompletion(code, prefix, cursor)
        } else {
          await this.fetchAutoCompletion(code, prefix, cursor)
        }
      } catch (error) {
        console.error('Auto completion error:', error)
      }
    },

    async fetchAutoCompletion(code, prefix, cursor) {
      if (this.disabled) return

      try {
        const cacheKey = `${code.substring(0, 100)}-${prefix}-${cursor.line}-${cursor.ch}`
        if (this.completionCache.has(cacheKey)) {
          const cached = this.completionCache.get(cacheKey)
          if (Date.now() - cached.timestamp < 30000) { // 30秒缓存
            this.showAutoCompletionHints(cached.data, prefix)
            return
          }
        }

        const res = await api.getCodeAutoCompletion({
          code: code,
          language: this.language,
          prefix: prefix,
          cursor_position: {
            line: cursor.line,
            ch: cursor.ch
          },
          problem_id: this.problemId
        })

        if (res.data && res.data.data && res.data.data.completions) {
          const completions = res.data.data.completions
          this.completionCache.set(cacheKey, {
            data: completions,
            timestamp: Date.now()
          })
          this.showAutoCompletionHints(completions, prefix)
        }
      } catch (err) {
        console.error('Code auto completion failed:', err)
      }
    },

    async fetchOllamaAutoCompletion(code, prefix, cursor) {
      if (this.disabled || !this.ollamaAvailable) return

      try {
        const res = await api.getOllamaCodeCompletion({
          code: code,
          language: this.language,
          prefix: prefix,
          cursor_position: {
            line: cursor.line,
            ch: cursor.ch
          },
          problem_id: this.problemId
        })

        if (res.data && res.data.data && res.data.data.completions) {
          const completions = res.data.data.completions
          this.showAutoCompletionHints(completions, prefix)
        }
      } catch (err) {
        console.error('Ollama code completion failed:', err)
        // 回退到默认补全
        await this.fetchAutoCompletion(code, prefix, cursor)
      }
    },

    async checkOllamaAvailability() {
      if (!this.useOllama || this.disabled) return

      try {
        const res = await api.getOllamaModels()
        if (res.data && res.data.data && res.data.data.length > 0) {
          this.ollamaAvailable = true
          this.ollamaModels = res.data.data
          this.selectedOllamaModel = res.data.data.find(m => m.is_active) || res.data.data[0]
        } else {
          this.ollamaAvailable = false
        }
      } catch (err) {
        this.ollamaAvailable = false
        console.warn('Ollama not available:', err)
      }
    },

    showAutoCompletionHints(completions, prefix) {
      if (!this.editor || this.disabled || !completions || !completions.length) return

      const hints = {
        list: completions.map(item => ({
          text: item.text,
          displayText: item.text + (item.description ? ` - ${item.description}` : ''),
          className: 'code-autocomplete-hint',
          render: (element, self, data) => {
            const wrapper = document.createElement('div')
            wrapper.className = 'autocomplete-item'

            const text = document.createElement('div')
            text.className = 'autocomplete-text'
            text.textContent = data.text

            if (data.description) {
              const desc = document.createElement('div')
              desc.className = 'autocomplete-description'
              desc.textContent = data.description
              wrapper.appendChild(text)
              wrapper.appendChild(desc)
            } else {
              wrapper.appendChild(text)
            }

            element.appendChild(wrapper)
          }
        })),
        from: this.editor.getCursor(),
        to: this.editor.getCursor()
      }

      // 计算替换范围
      const cursor = this.editor.getCursor()
      const line = this.editor.getLine(cursor.line) || ''
      let start = cursor.ch

      while (start > 0 && /[\w$._]/.test(line.charAt(start - 1))) {
        start--
      }

      // 处理函数调用场景
      if (cursor.ch > 0 && line.charAt(cursor.ch - 1) === '(') {
        let parenCount = 1
        let searchPos = cursor.ch - 2
        while (searchPos >= 0 && parenCount > 0) {
          const char = line.charAt(searchPos)
          if (char === '(') {
            parenCount--
          } else if (char === ')') {
            parenCount++
          }
          if (parenCount > 0) searchPos--
        }

        while (searchPos > 0 && /[\w$.]/.test(line.charAt(searchPos - 1))) {
          searchPos--
        }

        if (searchPos >= 0) {
          start = searchPos
        }
      }

      hints.from = { line: cursor.line, ch: start }
      hints.to = { line: cursor.line, ch: cursor.ch }

      // 显示补全提示
      this.editor.showHint({
        hint: () => hints,
        completeSingle: false,
        alignWithWord: false
      })
    },

    scheduleSuggestions() {
      if (this.disabled) return

      if (this.suggestionTimer) {
        clearTimeout(this.suggestionTimer)
      }

      this.suggestionTimer = setTimeout(() => {
        this.fetchRealTimeSuggestions()
      }, 1000)
    },

    applySuggestion(suggestion) {
      if (this.disabled || !suggestion) return

      this.suggestions = []

      if (typeof suggestion === 'string') {
        this.insertTextAtCursor(suggestion)
      } else if (typeof suggestion === 'object') {
        if (suggestion.type === 'completion' && suggestion.text) {
          this.insertTextAtCursor(suggestion.text)
        } else if (suggestion.replacement && suggestion.range) {
          this.replaceTextInRange(suggestion)
        } else if (suggestion.text) {
          this.insertTextAtCursor(suggestion.text)
        } else {
          this.insertTextAtCursor(suggestion.toString())
        }
      }

      if (this.editor) {
        this.editor.focus()
      }

      this.$emit('suggestionApplied', suggestion)
    },

    insertTextAtCursor(text) {
      if (!this.editor || !text) return

      const cursor = this.editor.getCursor()
      this.editor.replaceRange(text, cursor)
      const newCursor = {
        line: cursor.line,
        ch: cursor.ch + text.length
      }
      this.editor.setCursor(newCursor)
    },

    replaceTextInRange(suggestion) {
      if (!this.editor || !suggestion.replacement || !suggestion.range) return

      const from = {
        line: suggestion.range.start.line,
        ch: suggestion.range.start.character
      }
      const to = {
        line: suggestion.range.end.line,
        ch: suggestion.range.end.character
      }
      this.editor.replaceRange(suggestion.replacement, from, to)

      const newCursor = {
        line: to.line,
        ch: to.ch + (suggestion.replacement.length - (to.ch - from.ch))
      }
      this.editor.setCursor(newCursor)
    },

    async fetchRealTimeSuggestions() {
      if (this.disabled) return

      const code = this.editor ? this.editor.getValue() : ''

      if (!code || code.trim() === '') {
        this.suggestions = []
        this.$emit('suggestions', [])
        return
      }

      try {
        const res = await api.getRealTimeSuggestion({
          code: code,
          language: this.language,
          problem_id: this.problemId
        })

        const suggestions = res.data && res.data.data ? res.data.data || [] : []
        this.suggestions = suggestions
        this.$emit('suggestions', suggestions)
      } catch (err) {
        console.error('Real-time suggestions error:', err)
        this.suggestions = []
        this.$emit('suggestions', [])
      }
    }
  }
}
</script>

<style lang="less" scoped>
.code-mirror-container {
  margin: 0 0 15px 0;
  position: relative;

  .code-mirror-header {
    background-color: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 6px 6px 0 0;
    padding: 12px 15px;

    .header-content {
      display: flex;
      align-items: center;

      .left-controls,
      .right-controls {
        display: flex;
        align-items: center;
        gap: 15px;
      }

      .control-group {
        display: flex;
        align-items: center;
        gap: 8px;

        .control-label {
          font-weight: 500;
          color: #495057;
          white-space: nowrap;
        }

        .control-input {
          min-width: 140px;
        }
      }

      .control-buttons {
        display: flex;
        gap: 8px;

        .control-button {
          min-width: 36px;
        }
      }

      .theme-selector {
        margin-left: auto;
      }

      .ai-controls {
        display: flex;
        align-items: center;
        margin-left: 10px;

        .ai-status-icon {
          font-size: 20px;
          color: #6c757d;

          &.enabled {
            color: #28a745;
            animation: pulse 2s infinite;
          }
        }
      }
    }
  }

  .editor-wrapper {
    position: relative;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 6px 6px;

    .editor-loading-overlay {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(255, 255, 255, 0.8);
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      z-index: 10;
      border-radius: 0 0 6px 6px;

      .loading-text {
        margin-top: 10px;
        color: #6c757d;
        font-size: 14px;
      }
    }

    .code-editor {
      &.loading {
        opacity: 0.7;
      }
    }
  }

  .suggestions-panel {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    background: white;
    border: 1px solid #ddd;
    border-radius: 6px;
    max-height: 200px;
    overflow-y: auto;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    z-index: 100;
    transform: translateY(100%);
    margin-top: 5px;

    .suggestion-item {
      padding: 10px 15px;
      border-bottom: 1px solid #eee;
      cursor: pointer;
      transition: background-color 0.2s;

      &:hover {
        background-color: #f8f9fa;
      }

      &:last-child {
        border-bottom: none;
      }

      .suggestion-content {
        display: flex;
        align-items: center;
        gap: 8px;

        .suggestion-icon {
          color: #007bff;
        }

        .suggestion-text {
          font-weight: 500;
          font-family: monospace;
        }
      }

      .suggestion-description {
        font-size: 12px;
        color: #6c757d;
        margin-top: 4px;
        padding-left: 24px;
      }
    }
  }
}

@keyframes pulse {
  0% {
    opacity: 1;
  }

  50% {
    opacity: 0.6;
  }

  100% {
    opacity: 1;
  }
}

@media (max-width: 768px) {
  .code-mirror-container {
    .code-mirror-header {
      .header-content {
        flex-direction: column;
        gap: 10px;
        align-items: stretch;

        .left-controls,
        .right-controls {
          justify-content: space-between;
        }

        .control-group {
          .control-input {
            min-width: 100px;
          }
        }
      }
    }
  }
}
</style>

<style>
.CodeMirror {
  height: auto !important;
  border-radius: 0 0 6px 6px;
}

.CodeMirror-scroll {
  min-height: 300px;
  max-height: 600px;
}

.CodeMirror-hints {
  z-index: 9999 !important;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border: 1px solid #ddd;
  max-width: 500px;
}

.CodeMirror-hint {
  padding: 6px 10px;
  border-radius: 4px;
  margin: 2px 0;
}

.autocomplete-item {
  display: flex;
  flex-direction: column;
  padding: 6px 8px;
}

.autocomplete-text {
  font-weight: 500;
  font-family: monospace;
  font-size: 14px;
  color: #333;
}

.autocomplete-description {
  font-size: 12px;
  color: #666;
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.CodeMirror-hint-active .autocomplete-item {
  background-color: #e0e0e0;
}

.ruler-80 {
  border-left: 1px solid #e9ecef;
}

@media (max-width: 768px) {
  .CodeMirror-scroll {
    min-height: 250px;
  }
}
</style>