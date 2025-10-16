<template>
    <div class="markdown-editor">
        <textarea ref="editor"></textarea>
    </div>
</template>

<script>
import EasyMDE from 'easymde'
import 'easymde/dist/easymde.min.css'

export default {
    name: 'MarkdownEditor',
    props: {
        value: {
            type: String,
            default: ''
        }
    },
    data() {
        return {
            editor: null
        }
    },
    mounted() {
        this.initEditor()
    },
    methods: {
        initEditor() {
            this.editor = new EasyMDE({
                element: this.$refs.editor,
                initialValue: this.value,
                autoDownloadFontAwesome: false,
                toolbar: [
                    'bold', 'italic', 'heading', '|',
                    'quote', 'unordered-list', 'ordered-list', '|',
                    'link', 'image', 'table', '|',
                    'preview', 'side-by-side', 'fullscreen', '|',
                    'guide'
                ]
            })

            this.editor.codemirror.on('change', () => {
                const value = this.editor.value()
                this.$emit('input', value)
            })
        },
        setValue(value) {
            if (this.editor) {
                this.editor.value(value)
            }
        }
    },
    watch: {
        value(newVal) {
            if (this.editor && newVal !== this.editor.value()) {
                this.editor.value(newVal)
            }
        }
    },
    beforeDestroy() {
        if (this.editor) {
            this.editor.toTextArea()
            this.editor = null
        }
    }
}
</script>

<style scoped>
.markdown-editor {
    min-height: 300px;
}

.markdown-editor>>>.CodeMirror {
    min-height: 250px;
    height: auto;
}

.markdown-editor>>>.CodeMirror-scroll {
    min-height: 250px;
}
</style>