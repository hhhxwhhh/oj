<template>
    <div class="ai-assistant">
        <!-- 悬浮球按钮 -->
        <div class="floating-ball" @click="toggleAIAssistant">
            <div class="floating-ball-inner">
                <Icon type="md-chatbubbles" size="20"></Icon>
                <div class="pulse"></div>
            </div>
        </div>

        <!-- 弹出式聊天窗口 -->
        <div v-if="showAIAssistant" class="chat-popup">
            <div class="chat-overlay" @click="showAIAssistant = false"></div>
            <div class="chat-window">
                <div class="chat-header">
                    <div class="header-title">
                        <Icon type="md-chatbubbles" size="16"></Icon>
                        {{ $t('m.AI_Assistant') }}
                    </div>
                    <div class="header-actions">
                        <Button type="text" size="small" @click="isAIExpanded = !isAIExpanded">
                            <Icon :type="isAIExpanded ? 'md-remove' : 'md-add'"></Icon>
                        </Button>
                        <Button type="text" size="small" @click="showAIAssistant = false">
                            <Icon type="md-close"></Icon>
                        </Button>
                    </div>
                </div>

                <div v-show="isAIExpanded" class="chat-content">
                    <div class="model-selection" v-if="aiModels.length > 0">
                        <Select v-model="selectedModel" size="small" style="width:200px">
                            <Option v-for="model in aiModels" :value="model.id" :key="model.id">
                                <Icon type="md-cube" /> {{ model.name }}
                            </Option>
                        </Select>
                    </div>

                    <div class="chat-history" ref="chatHistory">
                        <div v-for="(message, index) in chatMessages" :key="index" :class="['message', message.type]">
                            <div class="avatar">
                                <Icon v-if="message.type === 'user'" type="md-person"></Icon>
                                <Icon v-else type="md-chatbubbles"></Icon>
                            </div>
                            <div class="message-content">
                                <div v-if="message.type === 'user'" class="text" v-html="message.content"></div>
                                <div v-else class="text" v-html="renderMarkdown(message.content)"></div>
                            </div>
                        </div>
                        <div v-if="isLoading" class="message ai">
                            <div class="avatar">
                                <Icon type="md-chatbubbles"></Icon>
                            </div>
                            <div class="message-content">
                                <div class="typing-indicator">
                                    <span></span>
                                    <span></span>
                                    <span></span>
                                </div>
                            </div>
                        </div>
                        <!-- 欢迎信息 -->
                        <div v-if="chatMessages.length === 0 && !isLoading" class="welcome-message">
                            <div class="welcome-icon">
                                <Icon type="md-chatbubbles" size="40"></Icon>
                            </div>
                            <h3>{{ $t('m.Welcome_to_AI_Assistant') }}</h3>
                            <p>{{ $t('m.You_can_ask_anything_about_this_problem') }}</p>
                        </div>
                    </div>

                    <div class="chat-input">
                        <Input v-model="userMessage" type="textarea" :rows="3"
                            :placeholder="$t('m.Ask_something_about_this_problem')"
                            @on-keyup.enter.exact="sendMessage" />
                        <div class="actions">
                            <Button type="primary" size="small" @click="sendMessage" :loading="isLoading"
                                :disabled="!userMessage.trim()" class="send-button">
                                <Icon type="md-send" />
                                {{ $t('m.Send') }}
                            </Button>
                            <Button type="default" size="small" @click="clearChat" class="clear-button">
                                <Icon type="md-trash" />
                                {{ $t('m.Clear') }}
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
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
            conversationId: null,
            aiModels: [],
            selectedModel: null
        }
    },
    mounted() {
        this.loadAIModels()
    },
    methods: {
        toggleAIAssistant() {
            this.showAIAssistant = !this.showAIAssistant
        },
        //加载AI模型列表
        async loadAIModels() {
            try {
                const res = await api.getAIModels()
                this.aiModels = res.data.data
                if (this.aiModels.length > 0) {
                    this.selectedModel = this.aiModels[0].id
                }
            } catch (err) {
                console.error("Failed to load AI models.", err)
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
                    role: "user",
                    model_id: this.selectedModel
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
    .floating-ball {
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 60px;
        height: 60px;
        cursor: pointer;
        z-index: 1000;
        display: flex;
        align-items: center;
        justify-content: center;

        .floating-ball-inner {
            position: relative;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #2d8cf0, #57a3f3);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            box-shadow: 0 4px 15px rgba(45, 140, 240, 0.3);
            transition: all 0.3s ease;
            z-index: 2;

            &:hover {
                transform: scale(1.1);
                box-shadow: 0 6px 20px rgba(45, 140, 240, 0.4);
            }

            .pulse {
                position: absolute;
                width: 100%;
                height: 100%;
                border-radius: 50%;
                background: inherit;
                animation: pulse 2s infinite;
                z-index: -1;
            }
        }
    }

    .chat-popup {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: 1001;

        .chat-overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.3);
        }

        .chat-window {
            position: absolute;
            bottom: 100px;
            right: 30px;
            width: 420px;
            max-width: calc(100% - 60px);
            background: #ffffff;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            display: flex;
            flex-direction: column;
            max-height: 70vh;
            overflow: hidden;
            animation: slideUp 0.3s ease;

            .chat-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 15px 20px;
                border-bottom: 1px solid #e8eaec;
                background: #f8f9fa;
                color: #2d8cf0;

                .header-title {
                    font-weight: 500;
                    font-size: 18px;
                    display: flex;
                    align-items: center;

                    i {
                        margin-right: 8px;
                    }
                }

                .header-actions {
                    display: flex;

                    button {
                        margin-left: 5px;
                        color: #808695;

                        &:hover {
                            background-color: #e6f2ff;
                            color: #2d8cf0;
                        }
                    }
                }
            }

            .chat-content {
                padding: 20px;
                overflow: hidden;
                display: flex;
                flex-direction: column;
                flex: 1;
                background-color: #fff;

                .model-selection {
                    margin-bottom: 20px;
                    text-align: right;

                    /deep/ .ivu-select-selection {
                        border-radius: 4px;
                        border-color: #dcdee2;
                    }

                    /deep/ .ivu-select-focused .ivu-select-selection {
                        border-color: #57a3f3;
                        box-shadow: 0 0 0 2px rgba(45, 140, 240, 0.2);
                    }
                }

                .chat-history {
                    flex: 1;
                    overflow-y: auto;
                    margin-bottom: 20px;
                    padding: 15px;
                    border: 1px solid #e8eaec;
                    border-radius: 6px;
                    background-color: #fafafa;

                    .welcome-message {
                        text-align: center;
                        padding: 20px;
                        color: #808695;

                        .welcome-icon {
                            color: #2d8cf0;
                            margin-bottom: 15px;
                        }

                        h3 {
                            margin: 10px 0;
                            color: #333;
                            font-weight: 500;
                        }

                        p {
                            font-size: 14px;
                            line-height: 1.5;
                        }
                    }

                    .message {
                        display: flex;
                        margin-bottom: 20px;
                        animation: fadeIn 0.3s ease;

                        &.user {
                            flex-direction: row-reverse;

                            .avatar {
                                background: linear-gradient(135deg, #2d8cf0, #57a3f3);
                                color: white;
                            }

                            .message-content {
                                .text {
                                    background: #2d8cf0;
                                    color: white;
                                }
                            }
                        }

                        &.ai {
                            .avatar {
                                background: linear-gradient(135deg, #808695, #515a6e);
                                color: white;
                            }

                            .message-content {
                                .text {
                                    background-color: #f0f0f0;
                                    color: #333;
                                }
                            }
                        }

                        .avatar {
                            width: 36px;
                            height: 36px;
                            border-radius: 50%;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            flex-shrink: 0;
                            margin: 0 12px;
                            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
                        }

                        .message-content {
                            max-width: 80%;
                            display: flex;
                            flex-direction: column;

                            .text {
                                padding: 12px 16px;
                                border-radius: 18px;
                                word-wrap: break-word;
                                white-space: pre-wrap;
                                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
                                font-size: 14px;
                                line-height: 1.5;

                                /deep/ pre {
                                    background: rgba(0, 0, 0, 0.05);
                                    padding: 10px;
                                    border-radius: 4px;
                                    overflow-x: auto;
                                }

                                /deep/ code {
                                    background: rgba(0, 0, 0, 0.05);
                                    padding: 2px 4px;
                                    border-radius: 3px;
                                }
                            }
                        }
                    }

                    .typing-indicator {
                        display: flex;
                        padding: 12px 16px;
                        background-color: #f0f0f0;
                        border-radius: 18px;

                        span {
                            height: 8px;
                            width: 8px;
                            background: #999;
                            border-radius: 50%;
                            margin: 0 3px;
                            animation: typing 1s infinite;

                            &:nth-child(2) {
                                animation-delay: 0.2s;
                            }

                            &:nth-child(3) {
                                animation-delay: 0.4s;
                            }
                        }
                    }
                }

                .chat-input {
                    /deep/ .ivu-input {
                        border-radius: 4px;
                        margin-bottom: 10px;
                        border-color: #dcdee2;

                        &:focus {
                            border-color: #57a3f3;
                            box-shadow: 0 0 0 2px rgba(45, 140, 240, 0.2);
                        }
                    }

                    .actions {
                        display: flex;
                        justify-content: flex-end;

                        .send-button {
                            background: linear-gradient(135deg, #2d8cf0, #57a3f3);
                            border: none;
                            border-radius: 4px;
                            margin-left: 10px;

                            &:hover {
                                background: linear-gradient(135deg, #57a3f3, #84c0f7);
                            }
                        }

                        .clear-button {
                            border-radius: 4px;
                            margin-left: 10px;
                            border-color: #dcdee2;
                            color: #515a6e;

                            &:hover {
                                border-color: #57a3f3;
                                color: #2d8cf0;
                            }
                        }
                    }
                }
            }
        }
    }

    @keyframes pulse {
        0% {
            transform: scale(1);
            opacity: 1;
        }

        100% {
            transform: scale(1.4);
            opacity: 0;
        }
    }

    @keyframes slideUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }

        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }

        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes typing {

        0%,
        100% {
            transform: translateY(0);
        }

        50% {
            transform: translateY(-3px);
        }
    }
}
</style>