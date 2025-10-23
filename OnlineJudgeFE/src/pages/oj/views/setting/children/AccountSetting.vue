<template>
  <div class="setting-main">
    <div class="account-settings">
      <Row :gutter="30">
        <Col :span="24" v-if="twoFactorAuthEnabled">
        <Alert type="warning" show-icon>
          <template slot="desc">
            <p><strong>{{ $t('m.Two_Factor_Authentication_Enabled') }}</strong></p>
            <p>{{ $t('m.Two_Factor_Authentication_Description') }}</p>
          </template>
        </Alert>
        </Col>

        <Col :span="24" v-if="visible.passwordAlert">
        <Alert type="success" show-icon>
          <template slot="desc">
            <p><strong>{{ $t('m.Password_Change_Success') }}</strong></p>
            <p>{{ $t('m.You_will_need_to_login_again') }}</p>
          </template>
        </Alert>
        </Col>

        <Col :span="24" v-if="visible.emailAlert">
        <Alert type="success" show-icon>
          <template slot="desc">
            <p><strong>{{ $t('m.Email_Change_Success') }}</strong></p>
            <p>{{ $t('m.Your_email_has_been_updated') }}</p>
          </template>
        </Alert>
        </Col>

        <Col :xs="24" :sm="24" :md="12" :lg="12">
        <Card class="setting-card">
          <div slot="title" class="card-header">
            <Icon type="md-lock" class="header-icon" />
            <span>{{ $t('m.Change_Password') }}</span>
          </div>

          <Form ref="formPassword" :model="formPassword" :rules="rulePassword" :label-width="140">
            <FormItem :label="$t('m.Old_Password')" prop="old_password">
              <Input v-model="formPassword.old_password" type="password"
                :placeholder="$t('m.Enter_your_current_password')" size="large" />
            </FormItem>

            <FormItem :label="$t('m.New_Password')" prop="new_password">
              <Input v-model="formPassword.new_password" type="password" :placeholder="$t('m.Enter_a_new_password')"
                size="large" />
              <div class="password-hint">
                {{ $t('m.Password_must_be_at_least_6_characters') }}
              </div>
            </FormItem>

            <FormItem :label="$t('m.Confirm_New_Password')" prop="again_password">
              <Input v-model="formPassword.again_password" type="password"
                :placeholder="$t('m.Confirm_your_new_password')" size="large" />
            </FormItem>

            <FormItem v-if="visible.tfaRequired" :label="$t('m.Two_Factor_Auth_Code')" prop="tfa_code">
              <Input v-model="formPassword.tfa_code" :placeholder="$t('m.Enter_your_2FA_code')" size="large">
              <Icon type="md-key" slot="prefix" />
              </Input>
            </FormItem>

            <FormItem>
              <Button type="primary" @click="changePassword" :loading="loading.btnPassword" long size="large">
                {{ $t('m.Update_Password') }}
              </Button>
            </FormItem>
          </Form>
        </Card>
        </Col>

        <Col :xs="24" :sm="24" :md="12" :lg="12">
        <Card class="setting-card">
          <div slot="title" class="card-header">
            <Icon type="md-mail" class="header-icon" />
            <span>{{ $t('m.Change_Email') }}</span>
          </div>

          <Form ref="formEmail" :model="formEmail" :rules="ruleEmail" :label-width="140">
            <FormItem :label="$t('m.Current_Password')" prop="password">
              <Input v-model="formEmail.password" type="password" :placeholder="$t('m.Enter_your_current_password')"
                size="large" />
            </FormItem>

            <FormItem :label="$t('m.Old_Email')">
              <Input v-model="formEmail.old_email" disabled size="large" />
            </FormItem>

            <FormItem :label="$t('m.New_Email')" prop="new_email">
              <Input v-model="formEmail.new_email" :placeholder="$t('m.Enter_your_new_email')" size="large">
              <Icon type="md-mail" slot="prefix" />
              </Input>
            </FormItem>

            <FormItem v-if="visible.tfaRequired" :label="$t('m.Two_Factor_Auth_Code')" prop="tfa_code">
              <Input v-model="formEmail.tfa_code" :placeholder="$t('m.Enter_your_2FA_code')" size="large">
              <Icon type="md-key" slot="prefix" />
              </Input>
            </FormItem>

            <FormItem>
              <Button type="primary" @click="changeEmail" :loading="loading.btnEmail" long size="large">
                {{ $t('m.Change_Email') }}
              </Button>
            </FormItem>
          </Form>
        </Card>
        </Col>
      </Row>
    </div>
  </div>
</template>

<script>
import api from '@oj/api'
import { FormMixin } from '@oj/components/mixins'

export default {
  mixins: [FormMixin],
  data() {
    const oldPasswordCheck = [
      { required: true, message: this.$t('m.This_field_is_required'), trigger: 'blur' },
      { min: 6, max: 20, message: this.$t('m.Password_length_invalid'), trigger: 'blur' }
    ]

    const tfaCheck = [
      { required: true, message: this.$t('m.This_field_is_required'), trigger: 'change' }
    ]

    const CheckAgainPassword = (rule, value, callback) => {
      if (value !== this.formPassword.new_password) {
        callback(new Error(this.$t('m.Password_does_not_match')))
      }
      callback()
    }

    const CheckNewPassword = (rule, value, callback) => {
      if (this.formPassword.old_password !== '') {
        if (this.formPassword.old_password === this.formPassword.new_password) {
          callback(new Error(this.$t('m.New_password_same_as_old')))
        } else {
          // 对第二个密码框再次验证
          this.$refs.formPassword.validateField('again_password')
        }
      }
      callback()
    }

    return {
      loading: {
        btnPassword: false,
        btnEmail: false
      },
      visible: {
        passwordAlert: false,
        emailAlert: false,
        tfaRequired: false
      },
      twoFactorAuthEnabled: false,
      formPassword: {
        tfa_code: '',
        old_password: '',
        new_password: '',
        again_password: ''
      },
      formEmail: {
        tfa_code: '',
        password: '',
        old_email: '',
        new_email: ''
      },
      rulePassword: {
        old_password: oldPasswordCheck,
        new_password: [
          { required: true, message: this.$t('m.This_field_is_required'), trigger: 'blur' },
          { min: 6, max: 20, message: this.$t('m.Password_length_invalid'), trigger: 'blur' },
          { validator: CheckNewPassword, trigger: 'blur' }
        ],
        again_password: [
          { required: true, message: this.$t('m.This_field_is_required'), trigger: 'change' },
          { validator: CheckAgainPassword, trigger: 'change' }
        ],
        tfa_code: tfaCheck
      },
      ruleEmail: {
        password: oldPasswordCheck,
        new_email: [
          { required: true, message: this.$t('m.This_field_is_required'), trigger: 'change' },
          { type: 'email', message: this.$t('m.Invalid_email_format'), trigger: 'change' }
        ],
        tfa_code: tfaCheck
      }
    }
  },
  mounted() {
    this.formEmail.old_email = this.$store.getters.user.email || ''
    // 检查是否启用了两步验证
    this.twoFactorAuthEnabled = this.$store.getters.user.two_factor_auth || false
  },
  methods: {
    changePassword() {
      this.validateForm('formPassword').then(valid => {
        this.loading.btnPassword = true
        let data = Object.assign({}, this.formPassword)
        delete data.again_password
        if (!this.visible.tfaRequired) {
          delete data.tfa_code
        }
        api.changePassword(data).then(res => {
          this.loading.btnPassword = false
          this.visible.passwordAlert = true
          this.$success(this.$t('m.Update_password_successfully'))
          this.$refs.formPassword.resetFields()

          setTimeout(() => {
            this.visible.passwordAlert = false
            this.$router.push({ name: 'logout' })
          }, 5000)
        }, res => {
          if (res.data.data === 'tfa_required') {
            this.visible.tfaRequired = true
          }
          this.loading.btnPassword = false
        })
      })
    },
    changeEmail() {
      this.validateForm('formEmail').then(valid => {
        this.loading.btnEmail = true
        let data = Object.assign({}, this.formEmail)
        if (!this.visible.tfaRequired) {
          delete data.tfa_code
        }
        api.changeEmail(data).then(res => {
          this.loading.btnEmail = false
          this.visible.emailAlert = true
          this.$success(this.$t('m.Change_email_successfully'))
          this.formEmail.new_email = ''
          this.formEmail.password = ''
          this.formEmail.tfa_code = ''
        }, res => {
          if (res.data.data === 'tfa_required') {
            this.visible.tfaRequired = true
          }
          this.loading.btnEmail = false
        })
      })
    }
  }
}
</script>

<style lang="less" scoped>
.account-settings {
  padding: 10px;

  .setting-card {
    margin-bottom: 20px;
    border-radius: 6px;
    box-shadow: 0 1px 6px rgba(0, 0, 0, 0.05);
    transition: box-shadow 0.3s ease;

    &:hover {
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    /deep/ .ivu-card-head {
      border-bottom: 1px solid #e8eaec;
      padding: 14px 20px;

      .card-header {
        display: flex;
        align-items: center;
        font-size: 18px;
        font-weight: 500;
        color: #515a6e;

        .header-icon {
          margin-right: 10px;
          color: #2d8cf0;
          font-size: 20px;
        }
      }
    }

    /deep/ .ivu-card-body {
      padding: 20px;
    }

    /deep/ .ivu-form-item-label {
      font-weight: 500;
      color: #515a6e;
    }

    .password-hint {
      font-size: 12px;
      color: #808695;
      margin-top: 5px;
    }
  }

  /deep/ .ivu-alert {
    border-radius: 6px;
    margin-bottom: 20px;

    &.ivu-alert-with-icon {
      padding: 12px 48px 12px 40px;
    }

    .ivu-alert-desc {
      p {
        margin: 3px 0;
      }

      p:first-child {
        font-weight: 500;
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .account-settings {
    /deep/ .ivu-col {
      margin-bottom: 20px;
    }

    /deep/ .ivu-form .ivu-form-item-label {
      text-align: left;
      padding-bottom: 5px;
    }
  }
}
</style>