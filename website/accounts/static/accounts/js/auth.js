// basic client-side checks; does not replace server validation
document.addEventListener('DOMContentLoaded', () => {
  const loginForm = document.getElementById('loginForm');
  const signupForm = document.getElementById('signupForm');

  function showAlert(el, msg){
    let error = el.querySelector('.client-error');
    if(!error){
      error = document.createElement('div');
      error.className = 'field-error client-error';
      el.appendChild(error);
    }
    error.textContent = msg;
  }

  if(signupForm){
    signupForm.addEventListener('submit', (e) => {
      const p1 = signupForm.querySelector('input[name="password1"]').value;
      const p2 = signupForm.querySelector('input[name="password2"]').value;
      const username = signupForm.querySelector('input[name="username"]').value.trim();
      const email = signupForm.querySelector('input[name="email"]').value.trim();

      // simple checks
      if(!username){
        e.preventDefault();
        showAlert(signupForm, 'Vui lòng nhập username.');
        return;
      }
      if(!email.includes('@')){
        e.preventDefault();
        showAlert(signupForm, 'Email không hợp lệ.');
        return;
      }
      if(p1.length < 8){
        e.preventDefault();
        showAlert(signupForm, 'Mật khẩu phải lớn hơn 8 ký tự.');
        return;
      }
      if(p1 !== p2){
        e.preventDefault();
        showAlert(signupForm, 'Mật khẩu xác nhận không khớp.');
        return;
      }
    });
  }

  if(loginForm){
    loginForm.addEventListener('submit', (e) => {
      const email = loginForm.querySelector('input[name="username"]').value.trim();
      const pwd = loginForm.querySelector('input[name="password"]').value;
      if(!email || !pwd){
        e.preventDefault();
        showAlert(loginForm, 'Vui lòng cung cấp email và mật khẩu.');
        return;
      }
    });
  }

  // Google buttons - redirect to oauth endpoint (backend must configure)
  const googleBtn = document.getElementById('googleBtn');
  const googleBtnSignup = document.getElementById('googleBtnSignup');
  const googleUrl = '/accounts/google/login/'; // placeholder route used by django-allauth or social-auth
  if(googleBtn) googleBtn.addEventListener('click', () => { window.location = googleUrl; });
  if(googleBtnSignup) googleBtnSignup.addEventListener('click', () => { window.location = googleUrl; });
});
