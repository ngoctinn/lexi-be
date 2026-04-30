# Google OAuth Configuration Update

## ⚠️ Lỗi hiện tại

```
Error 400: redirect_uri_mismatch
```

**Nguyên nhân:** Google OAuth credentials có redirect URI cũ không khớp với Cognito domain mới.

---

## 🔧 Cách fix (5 phút)

### Bước 1: Truy cập Google Cloud Console

1. Mở: https://console.cloud.google.com/apis/credentials
2. Đăng nhập với tài khoản Google của bạn
3. Chọn project: **project-4c7cf909-53b0-4a3c-971**

### Bước 2: Chỉnh sửa OAuth 2.0 Client

1. Tìm OAuth 2.0 Client ID với Client ID: `227669726469-knlofr128dnehh7eu05ig31hg3r0i27g.apps.googleusercontent.com`
2. Click vào tên client để edit

### Bước 3: Update Authorized redirect URIs

Thêm URI mới này vào danh sách (giữ lại các URI cũ):

```
https://lexi-app-826229823693-prod.auth.ap-southeast-1.amazoncognito.com/oauth2/idpresponse
```

**Danh sách đầy đủ nên có:**

- ✅ `http://localhost:3000/oauth-callback`
- ✅ `https://ngoctin.me/oauth-callback`
- ✅ `https://lexi-app-826229823693-prod.auth.ap-southeast-1.amazoncognito.com/oauth2/idpresponse` **(MỚI)**
- ❌ Có thể xóa: `https://lexi-auth.auth.ap-southeast-1.amazoncognito.com/oauth2/idpresponse` (cũ)

### Bước 4: Update Authorized JavaScript origins

Thêm origin mới này vào danh sách:

```
https://lexi-app-826229823693-prod.auth.ap-southeast-1.amazoncognito.com
```

**Danh sách đầy đủ nên có:**

- ✅ `http://localhost:3000`
- ✅ `https://ngoctin.me`
- ✅ `https://lexi-app-826229823693-prod.auth.ap-southeast-1.amazoncognito.com` **(MỚI)**
- ❌ Có thể xóa: `https://lexi-auth.auth.ap-southeast-1.amazoncognito.com` (cũ)

### Bước 5: Save

Click **SAVE** ở cuối trang.

---

## ✅ Verify

Sau khi update, test lại Google Sign-In:

1. Mở: https://lexi-app-826229823693-prod.auth.ap-southeast-1.amazoncognito.com/login?client_id=2ldrbcns1pqk6llkum42n50rqi&response_type=code&scope=email+openid+profile&redirect_uri=http://localhost:3000/oauth-callback

2. Click "Sign in with Google"

3. Nếu thành công → redirect về `http://localhost:3000/oauth-callback?code=...`

---

## 📋 Thông tin Cognito mới

| Key               | Value                                                               |
| ----------------- | ------------------------------------------------------------------- |
| **User Pool ID**  | `ap-southeast-1_I9ri7n518`                                          |
| **Client ID**     | `2ldrbcns1pqk6llkum42n50rqi`                                        |
| **Domain**        | `lexi-app-826229823693-prod.auth.ap-southeast-1.amazoncognito.com`  |
| **Region**        | `ap-southeast-1`                                                    |
| **API URL**       | `https://mnjxcw3o1e.execute-api.ap-southeast-1.amazonaws.com/Prod/` |
| **WebSocket URL** | `wss://zxb7hmt5c4.execute-api.ap-southeast-1.amazonaws.com/Prod`    |

---

## 🔗 Links hữu ích

- **Google Cloud Console**: https://console.cloud.google.com/apis/credentials
- **Cognito Console**: https://ap-southeast-1.console.aws.amazon.com/cognito/v2/idp/user-pools/ap-southeast-1_I9ri7n518
- **Cognito Hosted UI**: https://lexi-app-826229823693-prod.auth.ap-southeast-1.amazoncognito.com/login?client_id=2ldrbcns1pqk6llkum42n50rqi&response_type=code&scope=email+openid+profile&redirect_uri=http://localhost:3000/oauth-callback

---

## 🎯 Tóm tắt

**Vấn đề:** Google không nhận redirect URI từ Cognito domain mới
**Giải pháp:** Thêm Cognito domain mới vào Google OAuth credentials
**Thời gian:** ~5 phút
**Không cần:** Deploy lại hay restart gì cả

---

## CLI manual path

The old `config/auth-providers.yaml` stack file has been removed. Use AWS CLI to keep the app client in sync with the manually managed Google provider.

```bash
REGION=ap-southeast-1
USER_POOL_ID=$(aws cloudformation list-exports \
	--query "Exports[?Name=='lexi-auth-base-UserPoolId'].Value" \
	--output text \
	--region "$REGION")
CLIENT_ID=$(aws cloudformation list-exports \
	--query "Exports[?Name=='lexi-auth-base-UserPoolClientId'].Value" \
	--output text \
	--region "$REGION")

aws cognito-idp list-identity-providers \
	--user-pool-id "$USER_POOL_ID" \
	--region "$REGION" \
	--output table

aws cognito-idp update-user-pool-client \
	--user-pool-id "$USER_POOL_ID" \
	--client-id "$CLIENT_ID" \
	--allowed-o-auth-flows-user-pool-client \
	--allowed-o-auth-flows code \
	--allowed-o-auth-scopes email openid profile \
	--callback-urls http://localhost:3000/oauth-callback https://ngoctin.me/oauth-callback \
	--logout-urls http://localhost:3000/login https://ngoctin.me/login \
	--supported-identity-providers COGNITO Google \
	--region "$REGION"
```

If `Google` does not appear in `list-identity-providers`, add the social IdP in the Cognito console first, then rerun the `update-user-pool-client` command.

Note: redeploying `config/auth-base.yaml` can clear the user pool `LambdaConfig`, so rerun the trigger attach command from `lexi-auth-lambdas` after any auth-base deploy.
