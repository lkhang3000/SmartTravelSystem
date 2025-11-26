from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User

# --- Form cho tính năng Đổi Mật Khẩu AJAX ---
# Form này được views.py sử dụng để xử lý việc đổi mật khẩu bảo mật
class PasswordChangeAjaxForm(PasswordChangeForm):
    """
    Form dùng cho yêu cầu AJAX đổi mật khẩu.
    """
    old_password = forms.CharField(
        label="Mật khẩu cũ",
        widget=forms.PasswordInput(attrs={'placeholder': 'Mật khẩu cũ'})
    )
    new_password1 = forms.CharField(
        label="Mật khẩu mới",
        widget=forms.PasswordInput(attrs={'placeholder': 'Mật khẩu mới'})
    )
    new_password2 = forms.CharField(
        label="Xác nhận mật khẩu mới",
        widget=forms.PasswordInput(attrs={'placeholder': 'Xác nhận mật khẩu mới'})
    )

    class Meta:
        fields = ['old_password', 'new_password1', 'new_password2']

# --- Các Form Placeholder Khác (Để tránh lỗi ModuleNotFoundError) ---
# Vì views.py cố gắng import chúng, chúng ta phải định nghĩa chúng (dù chỉ là placeholder)
class UploadAvatarForm(forms.Form):
    avatar_file = forms.FileField()

class UserProfileForm(forms.Form):
    # Form này có thể được dùng cho việc xử lý các trường Profile khác nếu cần
    pass