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
    },
    useOllama: {
      type: Boolean,
      default: false
    },
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
        },
        ollamaAvailable: false,
        ollamaModels: [],
        selectedOllamaModel: null,
        suggestions: [],
        suggestionTimer: null,
        completionTimer: null, // 用于代码补全的定时器
        lastCursorPosition: null,
        // 添加一个状态来控制是否启用自动补全
        autoCompletionEnabled: true,
        // 设置自动补全的延迟时间（毫秒）
        autoCompletionDelay: 800,
        // 添加防抖控制
        debounceTimer: null,
        // 添加补全缓存
        completionCache: new Map()
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
      completionTimer: null, // 用于代码补全的定时器
      lastCursorPosition: null,
      // 添加一个状态来控制是否启用自动补全
      autoCompletionEnabled: true,
      // 设置自动补全的延迟时间（毫秒）
      autoCompletionDelay: 800
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

    // 添加代码更改事件监听器
    this.editor.on('change', () => {
      this.onCodeChange()
    })

    // 监听光标活动
    this.editor.on('cursorActivity', (cm) => {
      this.onCursorActivity(cm)
    })

    if (this.useOllama) {
      this.checkOllamaAvailability();
    }
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
    onCodeChange() {
      // 当代码发生变化时，重置自动补全定时器
      this.resetAutoCompletionTimer()

      // 同时触发实时建议（如果需要）
      this.scheduleSuggestions()
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
    resetAutoCompletionTimer() {
      // 清除现有的自动补全定时器
      if (this.completionTimer) {
        clearTimeout(this.completionTimer)
      }

      // 如果启用了自动补全，则设置新的定时器
      if (this.autoCompletionEnabled) {
        this.completionTimer = setTimeout(() => {
          this.triggerAutoCompletion()
        }, this.autoCompletionDelay)
      }
    },
    triggerAutoCompletion() {
      // 只有在启用自动补全时才执行
      if (!this.autoCompletionEnabled) return

      // 触发自动补全
      const code = this.editor.getValue()
      const cursor = this.editor.getCursor()
      const line = this.editor.getLine(cursor.line)

      // 改进前缀提取逻辑 - 更准确地处理函数调用场景
      let start = cursor.ch
      let end = start

      // 向前查找单词边界（支持更多字符类型）
      while (start > 0 && /[\w$.]/.test(line.charAt(start - 1))) {
        start--
      }

      // 向后查找单词边界
      while (end < line.length && /[\w$.]/.test(line.charAt(end))) {
        end++
      }

      const prefix = line.slice(start, end)

      // 特殊处理：如果光标前是点号，我们也应该触发补全
      let triggerCompletion = prefix.length > 0

      // 如果没有前缀但光标前是点号，也触发补全
      if (!triggerCompletion && cursor.ch > 0 && line.charAt(cursor.ch - 1) === '.') {
        triggerCompletion = true
      }

      // 如果没有前缀但在行首或空格后，也触发补全
      if (!triggerCompletion && (cursor.ch === 0 || /\s/.test(line.charAt(cursor.ch - 1)))) {
        triggerCompletion = true
      }

      // 特殊处理：在字符串内部时不触发自动补全
      const lineBeforeCursor = line.substring(0, cursor.ch);
      const quoteCount = (lineBeforeCursor.match(/["']/g) || []).length;
      const inString = quoteCount % 2 === 1;

      if (inString) {
        triggerCompletion = false;
      }

      console.log('触发自动补全，前缀:', prefix);

      // 触发补全（即使前缀为空）
      if (triggerCompletion) {
        // 根据配置决定使用哪种补全方式
        if (this.useOllama && this.ollamaAvailable) {
          this.fetchOllamaAutoCompletion(code, prefix, cursor)
        } else {
          this.fetchAutoCompletion(code, prefix, cursor)
        }
      }
    },
    async fetchAutoCompletion(code, prefix, cursor) {
      console.log('获取代码自动补全');
      console.log('代码:', code);
      console.log('前缀:', prefix);

      try {
        const res = await api.getCodeAutoCompletion({
          code: code,
          language: this.language,
          prefix: prefix,
          cursor_position: {
            line: cursor.line,
            ch: cursor.ch
          },
          problem_id: this.problemId
        });

        console.log('自动补全响应:', res);

        if (res.data && res.data.data && res.data.data.completions) {
          const completions = res.data.data.completions;
          // 使用CodeMirror内置的hint功能显示补全建议
          this.showAutoCompletionHints(completions, prefix);
        }
      } catch (err) {
        console.error('获取代码自动补全失败:', err);
      }
    },
    async fetchOllamaAutoCompletion(code, prefix, cursor) {
      console.log('使用Ollama获取代码自动补全');
      console.log('代码:', code);
      console.log('前缀:', prefix);

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
        });

        console.log('Ollama自动补全响应:', res);

        if (res.data && res.data.data && res.data.data.completions) {
          const completions = res.data.data.completions;
          // 使用CodeMirror内置的hint功能显示补全建议
          this.showAutoCompletionHints(completions, prefix);
        }
      } catch (err) {
        console.error('获取Ollama代码自动补全失败:', err);
        // 如果Ollama失败，回退到默认补全
        this.fetchAutoCompletion(code, prefix, cursor);
      }
    },
    async checkOllamaAvailability() {
      try {
        const res = await api.getOllamaModels();
        if (res.data && res.data.data && res.data.data.length > 0) {
          this.ollamaAvailable = true;
          this.ollamaModels = res.data.data;
          // 选择第一个激活的模型，或者默认第一个模型
          this.selectedOllamaModel = res.data.data.find(m => m.is_active) || res.data.data[0];
        } else {
          this.ollamaAvailable = false;
        }
      } catch (err) {
        console.error('检查Ollama可用性失败:', err);
        this.ollamaAvailable = false;
      }
    },
    showAutoCompletionHints(completions, prefix) {
      if (completions.length > 0) {
        // 构造CodeMirror hint格式的数据
        const hints = {
          list: completions.map(item => ({
            text: item.text,
            displayText: item.text + (item.description ? ' - ' + item.description : ''),
            className: 'code-autocomplete-hint',
            // 添加渲染函数以支持更丰富的显示
            render: (element, self, data) => {
              const wrapper = document.createElement('div');
              wrapper.className = 'autocomplete-item';

              const text = document.createElement('div');
              text.className = 'autocomplete-text';
              text.textContent = data.text;

              if (data.description) {
                const desc = document.createElement('div');
                desc.className = 'autocomplete-description';
                desc.textContent = data.description;
                wrapper.appendChild(text);
                wrapper.appendChild(desc);
              } else {
                wrapper.appendChild(text);
              }

              element.appendChild(wrapper);
            }
          })),
          from: this.editor.getCursor(),
          to: this.editor.getCursor()
        };

        // 移动光标到前缀的开始位置
        const cursor = this.editor.getCursor();
        const line = this.editor.getLine(cursor.line)
        let start = cursor.ch

        // 计算前缀的起始位置 - 更精确地计算
        while (start > 0 && /[\w$._]/.test(line.charAt(start - 1))) {
          start--
        }

        // 特殊处理：如果光标前是左括号，我们应该替换整个函数调用
        if (cursor.ch > 0 && line.charAt(cursor.ch - 1) === '(') {
          // 找到匹配的左括号位置
          let parenCount = 1;
          let searchPos = cursor.ch - 2;
          while (searchPos >= 0 && parenCount > 0) {
            if (line.charAt(searchPos) === '(') {
              parenCount--;
            } else if (line.charAt(searchPos) === ')') {
              parenCount++;
            }
            if (parenCount > 0) {
              searchPos--;
            }
          }

          // 找到函数名开始位置
          while (searchPos > 0 && /[\w$.]/.test(line.charAt(searchPos - 1))) {
            searchPos--;
          }

          if (searchPos >= 0) {
            start = searchPos;
          }
        }

        const from = { line: cursor.line, ch: start };
        const to = { line: cursor.line, ch: cursor.ch };
        hints.from = from;
        hints.to = to;

        // 显示补全提示
        this.editor.showHint({
          hint: () => hints,
          completeSingle: false,
          alignWithWord: false
        });
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

      // 只有当代码不为空时才获取建议
      if (!code || code.trim() === '') {
        this.$emit('suggestions', [])
        return
      }

      try {
        const res = await api.getRealTimeSuggestion({
          code: code,
          language: this.language,
          problem_id: this.problemId
        })

        console.log('实时建议API响应:', res)
        // 正确处理API响应并传递给父组件
        if (res.data && res.data.data) {
          this.$emit('suggestions', res.data.data)
        } else {
          this.$emit('suggestions', [])
        }
      } catch (err) {
        console.error('获取实时建议失败:', err)
        // 出错时也通知父组件
        this.$emit('suggestions', [])
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
    },
    'useOllama'(newVal) {
      if (newVal) {
        this.checkOllamaAvailability();
      }
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

/* 添加自定义代码补全样式 */
.CodeMirror-hint {
  padding: 4px 8px;
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

.CodeMirror-hints {
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border: 1px solid #ddd;
  max-width: 500px;
}

.CodeMirror-hint-active {
  border-radius: 4px;
}
</style>