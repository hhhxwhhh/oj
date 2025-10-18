<template>
    <div class="ai-assistant">
        <Panel :padding="10" shadow v-if="showAIAssistant">
            <div slot="title">
                <div class="ai-header">
                    <span>AI Assistant</span>
                    <Button type="text" size="small" @click="toggleAIAssistant">
                        <Icon :type="isAIExpanded ? 'minus-round' : 'plus-round'"></Icon>
                    </Button>
                </div>
            </div>

            <div v-show="isAIExpanded" class="ai-content">
                <div class="chat-history" ref="chatHistory">
                    <div v-for="(message, index) in chatMessages" :key="index" :class="['message', message.type]">
                        <div class="avatar">
                            <Icon v-if="message.type === 'user'" type="person"></Icon>
                            <Icon v-else type="android-chat"></Icon>
                        </div>
                        <div class="message-content">
                            <div v-if="message.type === 'user'" class="text" v-html="message.content"></div>
                            <div v-else class="text" v-html="renderMarkdown(message.content)"></div>
                        </div>
                    </div>
                    <div v-if="isLoading" class="message ai">
                        <div class="avatar">
                            <Icon type="android-chat"></Icon>
                        </div>
                        <div class="message-content">
                            <div class="typing-indicator">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="chat-input">
                    <Input v-model="userMessage" type="textarea" :rows="3"
                        :placeholder="$t('m.Ask_something_about_this_problem')" @on-keyup.enter.exact="sendMessage" />
                    <div class="actions">
                        <Button type="primary" size="small" @click="sendMessage" :loading="isLoading"
                            :disabled="!userMessage.trim()">
                            {{ $t('m.Send') }}
                        </Button>
                        <Button type="ghost" size="small" @click="clearChat">
                            {{ $t('m.Clear') }}
                        </Button>
                    </div>
                </div>
            </div>
        </Panel>

        <div v-else class="ai-toggle" @click="toggleAIAssistant">
            <Button long type="primary">
                <Icon type="android-chat"></Icon>
                {{ $t('m.AI_Assistant') }}
            </Button>
        </div>
    </div>
</template>

<script>
import api from '@oj/api'
import moment from 'moment'
import utils from '@/utils/utils'

export default {
    name: 'AIAssistant',
    props: {
        problem: {
            type: Object,
            required: true
        },
        code: {
            type: String,
            default: ''
        }
    },
    data() {
        return {
            showAIAssistant: false,
            isAIExpanded: true,
            userMessage: '',
            chatMessages: [],
            isLoading: false,
            conversationId: null
        }
    },
    mounted() {
        this.initAIAssistant()
    },
    methods: {
        initAIAssistant() {
            // 初始化AI助手
            this.showAIAssistant = true
        },

        toggleAIAssistant() {
            if (!this.showAIAssistant) {
                this.showAIAssistant = true
            } else {
                this.isAIExpanded = !this.isAIExpanded
            }
        },

        async sendMessage() {
            if (!this.userMessage.trim() || this.isLoading) return

            // 添加用户消息到聊天记录
            const userMsg = {
                type: 'user',
                content: this.userMessage,
                timestamp: moment().format('HH:mm')
            }
            this.chatMessages.push(userMsg)

            // 清空输入框
            const messageToSend = this.userMessage
            this.userMessage = ''

            // 显示加载状态
            this.isLoading = true
            this.$nextTick(() => {
                this.scrollToBottom()
            })

            try {
                // 如果没有会话ID，先创建会话
                if (!this.conversationId) {
                    const title = messageToSend.substring(0, 20);
                    const convRes = await api.createAIConversation({
                        title: title,
                        problem_id: this.problem._id
                    })
                    this.conversationId = convRes.data.data.id
                }

                // 发送消息到AI
                const res = await api.sendAIMessage({
                    conversation_id: this.conversationId,
                    content: messageToSend,
                    problem_id: this.problem._id,
                    code: this.code,
                    role: "user"
                })

                // 添加AI回复到聊天记录
                if (res.data && res.data.data && res.data.data.ai_message) {
                    const aiMsg = {
                        type: 'ai',
                        content: res.data.data.ai_message.content,
                        timestamp: moment().format('HH:mm')
                    }
                    this.chatMessages.push(aiMsg)
                } else {
                    // 如果没有AI模型配置，显示错误消息
                    const errorMsg = {
                        type: 'ai',
                        content: this.$i18n.t('m.Failed_to_get_AI_response') + ' (No AI response received)',
                        timestamp: moment().format('HH:mm')
                    }
                    this.chatMessages.push(errorMsg)
                }
            } catch (err) {
                console.error('AI request error:', err)
                const errorMsg = {
                    type: 'ai',
                    content: this.$i18n.t('m.Failed_to_get_AI_response') + ((err.response && err.response.status === 504) ? ' (Request timeout)' : ''),
                    timestamp: moment().format('HH:mm')
                }
                this.chatMessages.push(errorMsg)
            } finally {
                // 确保在任何情况下都关闭加载状态
                this.isLoading = false
                this.$nextTick(() => {
                    this.scrollToBottom()
                })
            }
        },
        clearChat() {
            this.chatMessages = []
            this.conversationId = null
        },

        scrollToBottom() {
            this.$nextTick(() => {
                const container = this.$refs.chatHistory
                if (container) {
                    container.scrollTop = container.scrollHeight
                }
            })
        },

        renderMarkdown(content) {
            return utils.renderMarkdown(content)
        }
    }
}
</script>

<style lang="less" scoped>
.ai-assistant {
    margin-top: 20px;

    .ai-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .ai-content {
        margin-top: 10px;
    }

    .chat-history {
        max-height: 300px;
        overflow-y: auto;
        margin-bottom: 10px;
        padding: 10px;
        border: 1px solid #e9eaec;
        border-radius: 4px;

        .message {
            display: flex;
            margin-bottom: 15px;

            &.user {
                flex-direction: row-reverse;

                .avatar {
                    background-color: #5cadff;
                    color: white;
                }

                .message-content {
                    .text {
                        background-color: #5cadff;
                        color: white;
                    }
                }
            }

            &.ai {
                .avatar {
                    background-color: #e1e1e1;
                    color: #666;
                }

                .message-content {
                    .text {
                        background-color: #f0f0f0;
                        color: #333;
                    }
                }
            }

            .avatar {
                width: 30px;
                height: 30px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
                margin: 0 10px;
            }

            .message-content {
                max-width: 80%;

                .text {
                    padding: 8px 12px;
                    border-radius: 4px;
                    word-wrap: break-word;
                    white-space: pre-wrap;
                }
            }
        }

        .typing-indicator {
            display: flex;
            padding: 8px 12px;

            span {
                height: 8px;
                width: 8px;
                background: #999;
                border-radius: 50%;
                margin: 0 2px;
                animation: typing 1s infinite;

                &:nth-child(2) {
                    animation-delay: 0.2s;
                }

                &:nth-child(3) {
                    animation-delay: 0.4s;
                }
            }
        }

        @keyframes typing {

            0%,
            100% {
                transform: translateY(0);
            }

            50% {
                transform: translateY(-5px);
            }
        }
    }

    .chat-input {
        .actions {
            margin-top: 10px;
            text-align: right;

            button {
                margin-left: 10px;
            }
        }
    }

    .ai-toggle {
        button {
            i {
                margin-right: 5px;
            }
        }
    }
}
</style>